"""Admin-only WebSocket management API and built-in sidebar panel."""
from __future__ import annotations

import asyncio
import math
import re
from pathlib import Path

import voluptuous as vol
from homeassistant.components import frontend, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .activity import LIMIT, recent_activity
from .codec import validate_rule
from .const import DOMAIN, CONF_ENTITIES, CONF_INVALID_VALUE, CONF_MIN_INTERVAL, CONF_PERIODIC_RESEND, CONF_STARTUP_RESYNC

PANEL_PATH = 'entity2udp'
PANEL_SETTINGS = f'{DOMAIN}.panel_settings'


class ManagementPanel:
    """Keep the panel address available independently of sidebar visibility."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.store = Store(hass, 1, PANEL_SETTINGS)
        self.lock = asyncio.Lock()
        self.show_in_sidebar = True

    async def async_setup(self) -> None:
        stored = await self.store.async_load()
        if isinstance(stored, dict):
            self.show_in_sidebar = stored.get('show_in_sidebar') is not False
        self._register()

    async def async_set_sidebar(self, visible: bool) -> None:
        async with self.lock:
            if self.show_in_sidebar == visible:
                return
            await self.store.async_save({'show_in_sidebar': visible})
            self.show_in_sidebar = visible
            self._register(update=True)

    def _register(self, *, update: bool = False) -> None:
        frontend.async_register_built_in_panel(
            self.hass,
            component_name='custom',
            frontend_url_path=PANEL_PATH,
            sidebar_title='Entity2UDP',
            sidebar_icon='mdi:lightning-bolt',
            require_admin=True,
            config_panel_domain=DOMAIN,
            show_in_sidebar=self.show_in_sidebar,
            update=update,
            config={
                '_panel_custom': {
                    'name': 'entity2udp-panel',
                    'embed_iframe': False,
                    'trust_external': False,
                    'handle_safe_area': False,
                    'module_url': '/entity2udp_static/entity2udp-panel.js?v=1.0.0',
                },
            },
        )


def _admin(connection, msg):
    if not connection.user.is_admin:
        connection.send_error(msg['id'], 'unauthorized', 'Administrator access required')
        return False
    return True


def _entry(hass, entry_id):
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None or entry.domain != DOMAIN:
        raise ValueError('Unknown Entity2UDP destination')
    return entry


def _validated_rules(rules):
    if not isinstance(rules, dict) or len(rules) > 1000:
        raise ValueError('Invalid entity collection (maximum 1000)')
    clean = {entity: validate_rule(entity, rule) for entity, rule in rules.items()}
    keys = [rule['key'] for rule in clean.values()]
    if len(set(keys)) != len(keys):
        raise ValueError('Duplicate UDP keys')
    return clean


def _settings(data):
    host = str(data.get('host', '')).strip()
    name = str(data.get('name', '')).strip()
    if not host or len(host) > 253 or any(c.isspace() or ord(c) < 33 for c in host) or not name or len(name) > 100:
        raise ValueError('Invalid destination name or host')
    port = int(data.get('port', 7000))
    if not 1 <= port <= 65535:
        raise ValueError('Port must be between 1 and 65535')
    sentinel = str(data.get('invalid_value', '-9999'))
    if not re.fullmatch(r'-?(?:\d+)(?:\.\d+)?', sentinel):
        raise ValueError('Invalid numeric sentinel')
    interval = float(data.get('min_interval_seconds', 0))
    if not math.isfinite(interval) or not 0 <= interval <= 86400:
        raise ValueError('Invalid minimum interval')
    requested_periodic = data.get(CONF_PERIODIC_RESEND, 0)
    if type(requested_periodic) is not int or (requested_periodic and not 5 <= requested_periodic <= 86400):
        raise ValueError('Periodic resend must be off or between 5 and 86400 seconds')
    return {'name': name, 'host': host, 'port': port, 'invalid_value': sentinel,
            'min_interval_seconds': interval, CONF_PERIODIC_RESEND: requested_periodic, 'startup_resync': bool(data.get('startup_resync', True))}


@websocket_api.websocket_command({
    vol.Required('type'): 'entity2udp/panel_settings',
    vol.Optional('show_in_sidebar'): bool,
})
@websocket_api.async_response
async def ws_panel_settings(hass, connection, msg):
    if not _admin(connection, msg):
        return
    panel = hass.data[PANEL_SETTINGS]
    if 'show_in_sidebar' in msg:
        await panel.async_set_sidebar(msg['show_in_sidebar'])
    connection.send_result(msg['id'], {'show_in_sidebar': panel.show_in_sidebar})


@websocket_api.websocket_command({vol.Required('type'): 'entity2udp/activity'})
@websocket_api.async_response
async def ws_activity(hass, connection, msg):
    if _admin(connection, msg):
        connection.send_result(msg['id'], {'events': recent_activity(hass), 'limit': LIMIT})


@websocket_api.websocket_command({vol.Required('type'): 'entity2udp/list'})
@websocket_api.async_response
async def ws_list(hass, connection, msg):
    if not _admin(connection, msg):
        return
    items = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        exporter = hass.data.get(DOMAIN, {}).get(entry.entry_id)
        items.append({'id': entry.entry_id, 'name': entry.title, **entry.data,
                      'invalid_value': entry.options.get(CONF_INVALID_VALUE, '-9999'),
                      'min_interval_seconds': entry.options.get(CONF_MIN_INTERVAL, 0),
                      CONF_PERIODIC_RESEND: entry.options.get(CONF_PERIODIC_RESEND, 0),
                      'startup_resync': entry.options.get(CONF_STARTUP_RESYNC, True),
                      'pref_disable_new_entities': entry.pref_disable_new_entities,
                      'entities': entry.options.get(CONF_ENTITIES, {}),
                      'sent': exporter.sent if exporter else 0,
                      'errors': exporter.errors if exporter else 0,
                      'last_error': exporter.last_error if exporter else None})
    connection.send_result(msg['id'], items)


@websocket_api.websocket_command({vol.Required('type'): 'entity2udp/save', vol.Required('entry_id'): str,
                                  vol.Required('settings'): dict, vol.Required('entities'): dict})
@websocket_api.async_response
async def ws_save(hass, connection, msg):
    if not _admin(connection, msg):
        return
    try:
        entry = _entry(hass, msg['entry_id'])
        settings = _settings(msg['settings'])
        rules = _validated_rules(msg['entities'])
        # A single update avoids multiple reloads and keeps all rules consistent.
        hass.config_entries.async_update_entry(
            entry, title=settings['name'], data={'host': settings['host'], 'port': settings['port']},
            options={**entry.options, CONF_ENTITIES: rules,
                     CONF_INVALID_VALUE: settings['invalid_value'],
                     CONF_MIN_INTERVAL: settings['min_interval_seconds'],
                     CONF_PERIODIC_RESEND: settings[CONF_PERIODIC_RESEND],
                     CONF_STARTUP_RESYNC: settings['startup_resync']})
        connection.send_result(msg['id'], {'saved': True})
    except (ValueError, TypeError, OverflowError) as exc:
        connection.send_error(msg['id'], 'invalid_config', str(exc))


@websocket_api.websocket_command({
    vol.Required('type'): 'entity2udp/set_rule_enabled',
    vol.Required('entry_id'): str,
    vol.Required('entity_id'): str,
    vol.Required('enabled'): bool,
})
@websocket_api.async_response
async def ws_set_rule_enabled(hass, connection, msg):
    if not _admin(connection, msg):
        return
    try:
        entry = _entry(hass, msg['entry_id'])
        rules = dict(entry.options.get(CONF_ENTITIES, {}))
        entity_id = msg['entity_id']
        if entity_id not in rules:
            raise ValueError('Unknown export rule')
        rules[entity_id] = {**rules[entity_id], 'enabled': msg['enabled']}
        hass.config_entries.async_update_entry(entry, options={**entry.options, CONF_ENTITIES: rules})
        connection.send_result(msg['id'], {'enabled': msg['enabled']})
    except ValueError as exc:
        connection.send_error(msg['id'], 'invalid_config', str(exc))


@websocket_api.websocket_command({vol.Required('type'): 'entity2udp/sync', vol.Required('entry_id'): str})
@websocket_api.async_response
async def ws_sync(hass, connection, msg):
    if not _admin(connection, msg):
        return
    exporter = hass.data.get(DOMAIN, {}).get(msg['entry_id'])
    if exporter is None:
        connection.send_error(msg['id'], 'not_found', 'Destination is not loaded')
        return
    sent, failed = await exporter.async_sync_all()
    connection.send_result(msg['id'], {'sent': exporter.sent, 'resend_sent': sent, 'resend_failed': failed})


@websocket_api.websocket_command({vol.Required('type'): 'entity2udp/import', vol.Required('entry_id'): str,
                                  vol.Required('document'): dict,
                                  vol.Required('mode'): vol.In(['merge', 'replace'])})
@websocket_api.async_response
async def ws_import(hass, connection, msg):
    if not _admin(connection, msg):
        return
    try:
        entry = _entry(hass, msg['entry_id'])
        document = msg['document']
        if document.get('schema_version') != 1:
            raise ValueError('Unsupported configuration schema version')
        if isinstance(document.get('destinations'), list):
            destinations = document['destinations']
            if len(destinations) != 1:
                raise ValueError('Select a single destination export for import')
            incoming = destinations[0].get('entities')
        else:
            incoming = document.get('entities')
        incoming = _validated_rules(incoming)
        merged = dict(entry.options.get(CONF_ENTITIES, {})) if msg['mode'] == 'merge' else {}
        merged.update(incoming)
        merged = _validated_rules(merged)
        hass.config_entries.async_update_entry(entry, options={**entry.options, CONF_ENTITIES: merged})
        connection.send_result(msg['id'], {'imported': len(incoming)})
    except (ValueError, TypeError, OverflowError) as exc:
        connection.send_error(msg['id'], 'invalid_import', str(exc))


async def async_setup_management(hass: HomeAssistant):
    """Register once, including the static module served by HA itself."""
    integration_path = Path(__file__).parent
    js_path = integration_path / 'frontend' / 'entity2udp-panel.js'
    icon_path = integration_path / 'brand' / 'icon.png'
    await hass.http.async_register_static_paths([
        StaticPathConfig('/entity2udp_static/entity2udp-panel.js', str(js_path), False),
        StaticPathConfig('/entity2udp_static/icon.png', str(icon_path), True),
    ])
    panel = ManagementPanel(hass)
    await panel.async_setup()
    hass.data[PANEL_SETTINGS] = panel
    for command in (
        ws_list, ws_save, ws_sync, ws_import, ws_create, ws_delete,
        ws_set_rule_enabled, ws_panel_settings, ws_activity,
    ):
        websocket_api.async_register_command(hass, command)

@websocket_api.websocket_command({vol.Required('type'): 'entity2udp/create', vol.Required('settings'): dict})
@websocket_api.async_response
async def ws_create(hass, connection, msg):
    if not _admin(connection, msg):
        return
    try:
        settings = _settings(msg['settings'])
        result = await hass.config_entries.flow.async_init(DOMAIN, context={'source': 'user'}, data=settings)
        if result['type'].value != 'create_entry':
            connection.send_error(msg['id'], 'create_failed', str(result.get('errors', result.get('reason', 'Creation failed'))))
            return
        connection.send_result(msg['id'], {'created': True})
    except (ValueError, TypeError, OverflowError) as exc:
        connection.send_error(msg['id'], 'invalid_config', str(exc))


@websocket_api.websocket_command({vol.Required('type'): 'entity2udp/delete', vol.Required('entry_id'): str})
@websocket_api.async_response
async def ws_delete(hass, connection, msg):
    if not _admin(connection, msg):
        return
    try:
        _entry(hass, msg['entry_id'])
        success = await hass.config_entries.async_remove(msg['entry_id'])
        if not success:
            connection.send_error(msg['id'], 'delete_failed', 'Could not remove destination')
            return
        connection.send_result(msg['id'], {'deleted': True})
    except (ValueError, TypeError) as exc:
        connection.send_error(msg['id'], 'delete_failed', str(exc))
