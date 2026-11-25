"""Entity2UDP integration: independent UDP destinations and export/import services."""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

import voluptuous as vol
from homeassistant.config_entries import OperationNotAllowed, UnknownEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv

from .activity import record_activity
from .const import CONF_ENTITIES, CONF_STARTUP_RESYNC, DOMAIN, EXPORT_FILENAME, STARTUP_DELAY_SECONDS
from .exporter import UdpExporter
from .management import async_setup_management

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["button"]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    await async_setup_management(hass)

    async def sync_service(call):
        destination = call.data.get("destination")
        exporters = hass.data[DOMAIN]
        selected = [exp for entry_id, exp in exporters.items()
                    if destination is None or destination == entry_id]
        if destination is not None and not selected:
            _LOGGER.warning("Unknown Entity2UDP destination: %s", destination)
            return
        await asyncio.gather(*(exp.async_sync_all(source="Action") for exp in selected))

    async def export_service(call):
        destination = call.data.get("destination")
        entities = set(call.data.get("entities", []))
        exports = []
        for entry_id, exporter in hass.data[DOMAIN].items():
            if destination is not None and entry_id != destination:
                continue
            rules = exporter.entry.options.get(CONF_ENTITIES, {})
            selected = {eid: rule for eid, rule in rules.items() if not entities or eid in entities}
            exports.append({"name": exporter.entry.title, "host": exporter.entry.data["host"],
                            "port": exporter.entry.data["port"], "entities": selected})
        if destination is not None and not exports:
            _LOGGER.warning("Unknown Entity2UDP destination: %s", destination)
            return
        document = {"schema_version": 1, "project": "Entity2UDP", "destinations": exports}
        path = Path(hass.config.path(EXPORT_FILENAME))
        # Fixed export filename: do not accept arbitrary paths from service calls.
        await hass.async_add_executor_job(path.write_text, json.dumps(document, indent=2, ensure_ascii=False), "utf-8")
        _LOGGER.info("Entity2UDP configuration exported to %s", path)

    hass.services.async_register(DOMAIN, "sync_all", sync_service,
        schema=vol.Schema({vol.Optional("destination"): cv.string}))
    hass.services.async_register(DOMAIN, "export_config", export_service,
        schema=vol.Schema({vol.Optional("destination"): cv.string,
                           vol.Optional("entities"): vol.All(cv.ensure_list, [cv.entity_id])}))
    return True


async def async_setup_entry(hass, entry):
    exporter = UdpExporter(hass, entry)
    await exporter.async_start()
    hass.data[DOMAIN][entry.entry_id] = exporter
    entry.async_on_unload(entry.add_update_listener(_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if entry.options.get(CONF_STARTUP_RESYNC, True):
        async def delayed_sync():
            await asyncio.sleep(STARTUP_DELAY_SECONDS)
            if hass.data.get(DOMAIN, {}).get(entry.entry_id) is exporter:
                await exporter.async_sync_all(source="Startup")

        @callback
        def schedule_sync(_event=None) -> None:
            if hass.data.get(DOMAIN, {}).get(entry.entry_id) is not exporter:
                return
            task = hass.async_create_task(delayed_sync())

            def cancel_sync() -> None:
                if not task.done():
                    task.cancel()

            entry.async_on_unload(cancel_sync)

        if hass.is_running:
            schedule_sync()
        else:
            entry.async_on_unload(
                hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, schedule_sync)
            )
    return True


async def _options_updated(hass, entry):
    try:
        reloaded = await hass.config_entries.async_reload(entry.entry_id)
    except UnknownEntry:
        return
    except OperationNotAllowed as exc:
        _LOGGER.error("Could not reload Entity2UDP destination %s: %s", entry.title, exc)
        record_activity(hass, entry, "error", f"Could not reload destination: {exc}")
        return
    if not reloaded:
        _LOGGER.error("Could not reload Entity2UDP destination %s", entry.title)
        record_activity(hass, entry, "error", "Could not reload destination")


async def async_unload_entry(hass, entry):
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        exporter = hass.data[DOMAIN].pop(entry.entry_id, None)
        if exporter:
            await exporter.async_stop()
    return ok
