# Entity2UDP 1.0

Entity2UDP forwards selected Home Assistant entity states to one or more UDP receivers, such as a Loxone Miniserver. Each datagram is a UTF-8 `key=value` message. Destinations have independent rules, filters and resend settings.

## Install or upgrade

1. Extract the release archive.
2. Copy `custom_components/entity2udp` into your Home Assistant configuration directory, so the manifest is at `/config/custom_components/entity2udp/manifest.json`.
3. Restart Home Assistant.
4. For a first install, go to **Settings → Devices & Services → Add integration → Entity2UDP** and add a UDP destination. Enter the receiver’s address and listening port.

For an upgrade, back up your Home Assistant configuration and replace the existing integration folder with the packaged copy. The integration uses the existing Entity2UDP config entries. The older `udp_entity_exporter` integration uses a different domain and has no automatic migration. If both are installed, overlapping rules can send duplicate packets.

## Open the management panel

Sign in as an administrator. Open **Settings → Devices & Services → Entity2UDP → Entity2UDP settings**, select **Entity2UDP** from the sidebar when enabled, or open `/entity2udp` on your Home Assistant server. The native destination device’s configuration link, shown as **Visit** in some Home Assistant versions, opens its filtered rule grid.

| Tab | What you can do |
| --- | --- |
| **Destinations** | Add or edit a receiver, set filtering and resends, and send all enabled values now. |
| **Configured entities** | Add, edit, pause, remove, import or export rules. Search by friendly name, entity ID or UDP key. Filter or group by destination and choose 25, 50 or 100 rows per page. |
| **Settings** | Show or hide the sidebar shortcut and manage Home Assistant system options for each destination. |
| **Activity** | Review resend summaries and send or reload errors. Filter by destination or event type and select **Refresh** for the latest activity. |

## Forward and translate values

In **Configured entities**, pick a destination and choose **Add entity rule**. Select a Home Assistant entity, set its UDP key and choose a value type. The editor shows the live state and recent history when Home Assistant records it. Choose **Apply rule**, then **Save changes**. The **Forwarding** switch saves immediately and pauses a rule without deleting its configuration.

Translations match the exact Home Assistant state before conversion and scaling. For example, set a washer-status rule to **Number** and add these rows:

| Home Assistant state | UDP value |
| --- | ---: |
| `idle` | 0 |
| `washing` | 1 |
| `rinsing` | 2 |
| `finished` | 3 |

For covers in **Auto** mode, the defaults are `closed=0`, `open=1`, `opening=2` and `closing=3`. Explicit translations override those defaults. Use **Text** to send textual values, or send numbers for receivers that expect numeric inputs. Unavailable entities and values that cannot be converted use the rule’s **Fallback value**, normally `-9999`.

## Filtering and resends

Entity2UDP forwards Home Assistant state changes as they occur.

Open **Filtering and resends** under **Destinations** to set a minimum interval or enable periodic resends. A rule can inherit the destination interval, use its own interval, or send without an interval limit. A numeric delta can suppress small numeric changes. Invalid-state transitions and recovery bypass throttling.

**Send all now**, the native **Resend all values** button, and the `entity2udp.sync_all` action resend enabled values without applying the interval or delta filters. Startup resync is enabled by default with a 30-second delay. Periodic resend is off by default. The suggested interval when enabled is 20 seconds.

Activity retains the latest 200 events in memory for the current Home Assistant session. It records resend summaries and errors, while regular successful state updates contribute to the destination’s sent count. A successful UDP send means Home Assistant handed a datagram to its local network stack. UDP provides no receiver acknowledgement.

## Back up and restore rules

In **Configured entities**, choose a destination and use **Download rules JSON** or **Import rules JSON**. Merge updates rules with matching entity IDs and retains the others. Replace replaces that destination’s rules while keeping its address and settings. Imports accept one destination at a time and preserve pause status.

For a server-side export, use **Developer tools → Actions → entity2udp.export_config**. It writes to `/config/entity2udp_export.json`, replacing the previous file. Use its optional destination and entity filters for a partial export. JSON exports contain destination network addresses and rule definitions. Use a Home Assistant backup to preserve the full configuration.

## Troubleshooting

- **The management panel is missing.** Sign in as an administrator and open `/entity2udp`. After an upgrade, restart Home Assistant and reload the browser page.
- **A rule appears paused or silent.** Confirm forwarding is enabled, then check the source state, translation, fallback value and filters. Use **Send all now** and check **Activity**.
- **Activity shows a send error.** Check the receiver’s address, name resolution, listening port and network access. Home Assistant’s system logs also contain Entity2UDP send and reload errors.
- **Activity shows a send but the receiver sees nothing.** Check the receiver’s UDP listener, firewall and expected key and value format.

See the [changelog](CHANGELOG.md) for release highlights.

Entity2UDP is available under the [MIT License](LICENSE).
