"""Native destination and per-entity CRUD via HA config/options flows."""
from __future__ import annotations

import json

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import section
from homeassistant.helpers import selector

from .codec import default_key, validate_rule
from .const import (CONF_ENTITIES, CONF_INVALID_VALUE, CONF_MIN_INTERVAL, CONF_PERIODIC_RESEND,
                    CONF_STARTUP_RESYNC, DEFAULT_INVALID_VALUE, DEFAULT_PORT, DOMAIN)
from .management import PANEL_SETTINGS


def destination_schema(data):
    return vol.Schema({
        vol.Required("name", default=data.get("name", "Loxone Miniserver")): str,
        vol.Required("host", default=data.get("host", "192.168.1.50")): str,
        vol.Required("port", default=data.get("port", DEFAULT_PORT)):
            vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
        vol.Required("invalid_value", default=data.get("invalid_value", DEFAULT_INVALID_VALUE)): str,
        vol.Required("min_interval_seconds", default=data.get("min_interval_seconds", 0)):
            number_box(0, 86400),
        vol.Required("startup_resync", default=data.get("startup_resync", True)): bool,
    })


def number_box(minimum, maximum, step="any"):
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=minimum, max=maximum, step=step, mode=selector.NumberSelectorMode.BOX
        )
    )


def translation_rows(translations):
    return [
        {
            "source": source,
            "value": str(value).lower() if isinstance(value, bool) else str(value),
            "value_type": "boolean" if isinstance(value, bool) else
                          "text" if isinstance(value, str) else "number",
        }
        for source, value in translations.items()
    ]


def parse_translation_rows(rows):
    translations = {}
    if not isinstance(rows, list):
        raise ValueError("invalid_translations")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid_translations")
        source = row.get("source")
        value = row.get("value", "")
        value_type = row.get("value_type")
        if (not isinstance(source, str) or not source or source in translations
                or not isinstance(value, str) or value_type not in ("text", "number", "boolean")):
            raise ValueError("invalid_translations")
        if value_type == "boolean":
            if value not in ("true", "false"):
                raise ValueError("invalid_translations")
            value = value == "true"
        elif value_type == "number":
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError as exc:
                    raise ValueError("invalid_translations") from exc
        translations[source] = value
    return translations


def entity_schema(entity_id=None, rule=None, submitted=None):
    submitted = submitted or {}
    rule = {**(rule or {}), **submitted}
    rows = submitted.get("translation_settings", {}).get(
        "translation_rows", translation_rows(rule.get("translations", {}))
    )
    schema = {}
    if entity_id is None:
        entity_field = vol.Required("entity_id", default=rule["entity_id"]) if "entity_id" in rule else vol.Required("entity_id")
        schema[entity_field] = selector.EntitySelector()
    schema.update({
        vol.Required("key", default=rule.get("key", default_key(entity_id or "sensor.example"))): str,
        vol.Required("type", default=rule.get("type", "auto")):
            vol.In(["auto", "number", "boolean", "text"]),
        vol.Required("scale", default=rule.get("scale", 1)):
            vol.All(vol.Coerce(float)),
        vol.Required("precision", default=rule.get("precision", 3)):
            number_box(0, 10, step=1),
        vol.Required("min_interval_seconds", default=rule.get("min_interval_seconds", -1)):
            number_box(-1, 86400),
        vol.Required("min_delta", default=rule.get("min_delta", 0)):
            vol.All(vol.Coerce(float), vol.Range(min=0)),
        vol.Required("invalid_value", default=rule.get("invalid_value", "-9999")): str,
        vol.Required("translation_settings"): section(
            vol.Schema({
                vol.Optional("translation_rows", default=rows):
                    selector.ObjectSelector(selector.ObjectSelectorConfig(
                        multiple=True, label_field="source", description_field="value",
                        fields={
                            "source": {"label": "Home Assistant state", "required": True,
                                       "selector": selector.TextSelector()},
                            "value": {"label": "UDP value", "selector": selector.TextSelector()},
                            "value_type": {"label": "UDP value type", "required": True,
                                           "selector": selector.SelectSelector(
                                               selector.SelectSelectorConfig(options=[
                                                   {"value": "text", "label": "Text"},
                                                   {"value": "number", "label": "Number"},
                                                   {"value": "boolean", "label": "Boolean"},
                                               ])
                                           )},
                        },
                    )),
            }),
            {"collapsed": not rows},
        ),
    })
    return vol.Schema(schema)


class Entity2UDPConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            host = user_input["host"].strip()
            name = user_input["name"].strip()
            if not host or any(c.isspace() for c in host) or not name:
                errors["base"] = "invalid_destination"
            else:
                await self.async_set_unique_id(f"{host.lower()}:{user_input['port']}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name, data={"host": host, "port": user_input["port"]},
                    options={CONF_ENTITIES: {}, CONF_INVALID_VALUE: user_input["invalid_value"],
                             CONF_MIN_INTERVAL: user_input["min_interval_seconds"],
                             CONF_PERIODIC_RESEND: user_input.get(CONF_PERIODIC_RESEND, 0),
                             CONF_STARTUP_RESYNC: user_input["startup_resync"]})
        return self.async_show_form(step_id="user", data_schema=destination_schema({}), errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry):
        return Entity2UDPOptionsFlow(config_entry)


class Entity2UDPOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._entry = config_entry
        self._rules = dict(config_entry.options.get(CONF_ENTITIES, {}))
        self._selected = None

    def _save(self, rules=None, extra=None):
        options = dict(self._entry.options)
        options[CONF_ENTITIES] = rules if rules is not None else self._rules
        if extra:
            options.update(extra)
        return self.async_create_entry(title="", data=options)

    async def async_step_init(self, user_input=None):
        return self.async_show_menu(step_id="init", menu_options=["sidebar", "legacy"])

    async def async_step_sidebar(self, user_input=None):
        panel = self.hass.data[PANEL_SETTINGS]
        if user_input is not None:
            await panel.async_set_sidebar(user_input["show_in_sidebar"])
            return self.async_create_entry(title="", data=dict(self._entry.options))
        return self.async_show_form(
            step_id="sidebar",
            data_schema=vol.Schema({
                vol.Required("show_in_sidebar", default=panel.show_in_sidebar): bool,
            }),
        )

    async def async_step_legacy(self, user_input=None):
        return self.async_show_menu(step_id="legacy", menu_options=[
            "destination", "add_entity", "edit_entity", "remove_entity", "import_json", "export_json"])

    async def async_step_destination(self, user_input=None):
        if user_input is not None:
            host = user_input["host"].strip()
            name = user_input["name"].strip()
            if not host or any(c.isspace() for c in host) or not name:
                return self.async_show_form(step_id="destination", data_schema=destination_schema(user_input), errors={"base": "invalid_destination"})
            if not user_input["invalid_value"] or not __import__("re").fullmatch(r"-?(?:\d+)(?:\.\d+)?", user_input["invalid_value"]):
                return self.async_show_form(step_id="destination", data_schema=destination_schema(user_input), errors={"base": "invalid_sentinel"})
            # Update host/port/title without replacing this config entry or its entities.
            self.hass.config_entries.async_update_entry(
                self._entry, title=name, data={"host": host, "port": user_input["port"]})
            return self._save(extra={CONF_INVALID_VALUE: user_input["invalid_value"], CONF_MIN_INTERVAL: user_input["min_interval_seconds"], CONF_STARTUP_RESYNC: user_input["startup_resync"]})
        return self.async_show_form(step_id="destination", data_schema=destination_schema({"name": self._entry.title, **self._entry.data, **self._entry.options}))

    async def async_step_add_entity(self, user_input=None):
        errors = {}
        if user_input is not None:
            entity_id = user_input["entity_id"]
            if entity_id in self._rules:
                errors["base"] = "already_exists"
            else:
                try:
                    rule = self._parse_rule(entity_id, user_input)
                    self._check_key(entity_id, rule)
                except (ValueError, TypeError, OverflowError) as exc:
                    errors["base"] = str(exc) if str(exc) in (
                        "invalid_json", "invalid_key", "duplicate_key", "invalid_translations",
                        "invalid_sentinel", "invalid_scale", "invalid_interval", "invalid_delta",
                        "invalid_type", "invalid_precision", "invalid_rule", "invalid_entity") else "invalid_rule"
                else:
                    self._rules[entity_id] = rule
                    return self._save()
        return self.async_show_form(step_id="add_entity", data_schema=entity_schema(submitted=user_input), errors=errors)

    async def async_step_edit_entity(self, user_input=None):
        if not self._rules:
            return self.async_abort(reason="no_entities")
        if user_input is not None:
            self._selected = user_input["entity_id"]
            return await self.async_step_edit_details()
        return self.async_show_form(step_id="edit_entity", data_schema=vol.Schema({
            vol.Required("entity_id"): vol.In(list(self._rules))}))

    async def async_step_edit_details(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                rule = self._parse_rule(self._selected, user_input)
                self._check_key(self._selected, rule)
            except (ValueError, TypeError, OverflowError) as exc:
                errors["base"] = str(exc) if str(exc) in (
                    "invalid_json", "invalid_key", "duplicate_key", "invalid_translations",
                    "invalid_sentinel", "invalid_scale", "invalid_interval", "invalid_delta",
                    "invalid_type", "invalid_precision") else "invalid_rule"
            else:
                self._rules[self._selected] = rule
                return self._save()
        return self.async_show_form(step_id="edit_details", data_schema=entity_schema(
            self._selected, self._rules[self._selected], user_input), errors=errors)

    async def async_step_remove_entity(self, user_input=None):
        if not self._rules:
            return self.async_abort(reason="no_entities")
        if user_input is not None:
            self._rules.pop(user_input["entity_id"], None)
            return self._save()
        return self.async_show_form(step_id="remove_entity", data_schema=vol.Schema({
            vol.Required("entity_id"): vol.In(list(self._rules))}))

    async def async_step_export_json(self, user_input=None):
        if user_input is not None:
            return await self.async_step_legacy()
        document = {
            "schema_version": 1,
            "project": "Entity2UDP",
            "destinations": [{
                "name": self._entry.title,
                "host": self._entry.data["host"],
                "port": self._entry.data["port"],
                "entities": self._entry.options.get(CONF_ENTITIES, {}),
            }],
        }
        return self.async_show_form(
            step_id="export_json",
            data_schema=vol.Schema({
                vol.Optional("json_data", default=json.dumps(document, indent=2, ensure_ascii=False)):
                    selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
            }),
            last_step=False,
        )

    async def async_step_import_json(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                document = json.loads(user_input["json_data"])
                if isinstance(document.get("destinations"), list):
                    if len(document["destinations"]) != 1:
                        raise ValueError("invalid_import")
                    document = {"schema_version": document.get("schema_version"), "entities": document["destinations"][0].get("entities")}
                if document.get("schema_version") != 1 or not isinstance(document.get("entities"), dict):
                    raise ValueError("invalid_import")
                incoming = {eid: validate_rule(eid, rule) for eid, rule in document["entities"].items()}
                merged = dict(self._rules) if user_input["mode"] == "merge" else {}
                merged.update(incoming)
                keys = [rule["key"] for rule in merged.values()]
                if len(keys) != len(set(keys)):
                    raise ValueError("duplicate_key")
                if len(merged) > 1000:
                    raise ValueError("invalid_import")
            except (ValueError, TypeError, AttributeError) as exc:
                errors["base"] = str(exc) if str(exc) in ("invalid_import", "duplicate_key") else "invalid_import"
            else:
                return self._save(rules=merged)
        return self.async_show_form(step_id="import_json", data_schema=vol.Schema({
            vol.Required("mode", default="merge"): vol.In(["merge", "replace"]),
            vol.Required("json_data"): selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
        }), errors=errors)

    def _parse_rule(self, entity_id, user_input):
        interval = user_input["min_interval_seconds"]
        if -1 < interval < 0:
            raise ValueError("invalid_interval")
        if int(user_input["precision"]) != user_input["precision"]:
            raise ValueError("invalid_precision")
        translations = parse_translation_rows(user_input.get("translation_settings", {}).get("translation_rows", []))
        rule = {**user_input, "translations": translations}
        existing = self._rules.get(entity_id, {})
        if "enabled" in existing:
            rule["enabled"] = existing["enabled"]
        if rule.get("min_interval_seconds") == -1:
            rule.pop("min_interval_seconds")
        return validate_rule(entity_id, rule)

    def _check_key(self, entity_id, rule):
        if any(other != entity_id and data.get("key", default_key(other)) == rule["key"]
               for other, data in self._rules.items()):
            raise ValueError("duplicate_key")
