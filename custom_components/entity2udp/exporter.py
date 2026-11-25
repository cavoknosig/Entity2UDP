"""Async UDP sender with independent per-destination state and coalescing."""
from __future__ import annotations

import asyncio
import logging
import socket
from time import monotonic

from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event
from .activity import record_activity
from .codec import default_key, encode_value
from .const import CONF_ENTITIES, CONF_INVALID_VALUE, CONF_MIN_INTERVAL, CONF_PERIODIC_RESEND, DEFAULT_INVALID_VALUE

_LOGGER = logging.getLogger(__name__)


class UdpExporter:
    def __init__(self, hass, entry):
        self.hass, self.entry = hass, entry
        self.rules = {
            entity_id: rule
            for entity_id, rule in entry.options.get(CONF_ENTITIES, {}).items()
            if rule.get("enabled", True)
        }
        self.sentinel = str(entry.options.get(CONF_INVALID_VALUE, DEFAULT_INVALID_VALUE))
        self.interval = float(entry.options.get(CONF_MIN_INTERVAL, 0))
        self.sent, self.errors, self.last_error = 0, 0, None
        self._unsub = None
        self._periodic_interval = entry.options.get(CONF_PERIODIC_RESEND, 0)
        self._periodic_timer = None
        self._pending = {}
        self._last_sent = {}
        self._last_numeric = {}
        self._tasks = set()
        self._closed = False
        self._send_lock = asyncio.Lock()
        self._sync_lock = asyncio.Lock()
        self._socket = None
        self._address = None

    async def async_start(self):
        if self.rules:
            self._unsub = async_track_state_change_event(self.hass, list(self.rules), self._state_changed)
            self._schedule_periodic_resend()

    def _schedule_periodic_resend(self):
        if self._periodic_interval and not self._closed:
            self._periodic_timer = asyncio.get_running_loop().call_later(
                self._periodic_interval, self._start_periodic_resend
            )

    def _start_periodic_resend(self):
        self._periodic_timer = None
        if not self._closed:
            self._spawn(self._periodic_resend())

    async def _periodic_resend(self):
        try:
            await self.async_sync_all(source="Periodic")
        finally:
            self._schedule_periodic_resend()

    @callback
    def _state_changed(self, event):
        if self._closed:
            return
        entity_id = event.data["entity_id"]
        old, new = event.data.get("old_state"), event.data.get("new_state")
        if new is None or (old is not None and old.state == new.state):
            return
        rule = self.rules.get(entity_id)
        if rule is None:
            return
        _, invalid = encode_value(new.state, rule, self.sentinel, entity_id=entity_id)
        # Invalid transitions and valid recoveries bypass rate limiting.
        previous = None if old is None else encode_value(old.state, rule, self.sentinel, entity_id=entity_id)[1]
        urgent = invalid or (previous is True and not invalid)
        interval = float(rule.get("min_interval_seconds", self.interval))
        if urgent or interval <= 0 or monotonic() - self._last_sent.get(entity_id, -float("inf")) >= interval:
            self._cancel_pending(entity_id)
            self._spawn(self.async_send_entity(entity_id, force=urgent))
        elif entity_id not in self._pending:
            delay = interval - (monotonic() - self._last_sent[entity_id])
            self._pending[entity_id] = asyncio.get_running_loop().call_later(
                max(0, delay), self._flush_pending, entity_id)

    def _flush_pending(self, entity_id):
        self._pending.pop(entity_id, None)
        if not self._closed:
            self._spawn(self.async_send_entity(entity_id))

    def _cancel_pending(self, entity_id):
        timer = self._pending.pop(entity_id, None)
        if timer:
            timer.cancel()

    def _spawn(self, coro):
        task = self.hass.async_create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _resolve(self):
        results = await asyncio.get_running_loop().getaddrinfo(
            self.entry.data["host"], self.entry.data["port"], type=socket.SOCK_DGRAM)
        if not results:
            raise OSError("No UDP addresses returned")
        family, socktype, proto, _, address = results[0]
        sock = socket.socket(family, socktype, proto)
        sock.setblocking(False)
        if self._socket:
            self._socket.close()
        self._socket, self._address = sock, address

    def _can_send(self, entity_id):
        rule = self.entry.options.get(CONF_ENTITIES, {}).get(entity_id)
        return not self._closed and rule is not None and rule.get("enabled", True)

    async def async_send_entity(self, entity_id, force=False) -> bool | None:
        if self._closed or entity_id not in self.rules:
            return
        rule = self.rules[entity_id]
        state = self.hass.states.get(entity_id)
        raw_state = state.state if state is not None else None
        value, invalid = encode_value(raw_state, rule, self.sentinel, entity_id=entity_id)
        if invalid:
            _LOGGER.debug(
                "Entity2UDP destination %s is sending its fallback for %s (state %r, type %s)",
                self.entry.title, entity_id, raw_state, rule.get("type", "auto"),
            )
        key = rule.get("key", default_key(entity_id))
        # A numeric delta threshold only applies to valid numeric values.
        try:
            numeric = None if invalid else float(value)
        except ValueError:
            numeric = None
        delta = float(rule.get("min_delta", 0))
        if not force and delta and numeric is not None and entity_id in self._last_numeric:
            if abs(numeric - self._last_numeric[entity_id]) < delta:
                return
        try:
            payload = f"{key}={value}".encode("utf-8")
            if len(payload) > 1200:
                raise ValueError("UDP payload exceeds 1200 bytes")
            async with self._send_lock:
                if not self._can_send(entity_id):
                    return
                if self._socket is None:
                    await self._resolve()
                if not self._can_send(entity_id):
                    return
                try:
                    await asyncio.get_running_loop().sock_sendto(self._socket, payload, self._address)
                except OSError:
                    # Retry DNS resolution on the next send, not indefinitely.
                    self._socket.close()
                    self._socket = None
                    self._address = None
                    raise
                self.sent += 1
                self.last_error = None
                self._last_sent[entity_id] = monotonic()
                if numeric is not None:
                    self._last_numeric[entity_id] = numeric
                else:
                    self._last_numeric.pop(entity_id, None)
                return True
        except (OSError, ValueError, OverflowError) as exc:
            self.errors += 1
            self.last_error = str(exc)
            _LOGGER.warning("Entity2UDP send failed for %s: %s", self.entry.title, exc)
            record_activity(self.hass, self.entry, "error", f"Could not send {entity_id}: {exc}")
            return False

    async def async_sync_all(self, *, source: str = "Manual") -> tuple[int, int]:
        """Return the successful and failed UDP send counts for this pass."""
        sent = failed = 0
        async with self._sync_lock:
            for entity_id in self.rules:
                if self._closed:
                    break
                self._cancel_pending(entity_id)
                result = await self.async_send_entity(entity_id, force=True)
                sent += result is True
                failed += result is False
                await asyncio.sleep(0.025)
        if not self._closed:
            summary = f"{source} resend: {sent} sent, {failed} failed"
            record_activity(self.hass, self.entry, "resend", summary)
        return sent, failed

    async def async_stop(self):
        self._closed = True
        if self._periodic_timer is not None:
            self._periodic_timer.cancel()
            self._periodic_timer = None
        if self._unsub:
            self._unsub()
        for timer in self._pending.values():
            timer.cancel()
        self._pending.clear()
        for task in tuple(self._tasks):
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        async with self._send_lock:
            if self._socket:
                self._socket.close()
                self._socket = None
