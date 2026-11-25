"""Resync button for each configured destination."""
from urllib.parse import urlencode

from homeassistant.components import logbook
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([UdpResyncButton(entry, hass.data[DOMAIN][entry.entry_id])])


class UdpResyncButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:sync"

    def __init__(self, entry, exporter):
        self._exporter = exporter
        self._destination_name = entry.title
        self._attr_name = f"Resend all values to {entry.title}"
        self._attr_unique_id = f"{entry.entry_id}_resync"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Entity2UDP",
            model="Entity2UDP Device",
            configuration_url=f"homeassistant://entity2udp?{urlencode({'destination': entry.entry_id, 'view': 'rules'})}",
        )

    async def async_press(self):
        context = self._context
        sent, failed = await self._exporter.async_sync_all()
        if not self._exporter.rules:
            message = "has no enabled values to resend"
        else:
            message = f"sent {sent} of {len(self._exporter.rules)} enabled values"
            if failed:
                message += f" ({failed} failed)"
        logbook.async_log_entry(
            self.hass, f"Entity2UDP · {self._destination_name}", message,
            entity_id=self.entity_id, context=context,
        )
