<!-- ┌───────────────────────────────────────────────────────────────────────────┐
     │ USING THIS TEMPLATE — delete everything down to the "DELETE ABOVE" line      │
     │ once your integration repo is set up. What's left below is your own README.  │
     └───────────────────────────────────────────────────────────────────────────┘ -->

# Creating a new MajorDom integration from this template

Click **Use this template → Create a new repository** (name it `integration-<protocol>`,
e.g. `integration-hue`), then:

**1. Rename the placeholders** (find & replace across the repo)
- `integration-template` → your distribution name, by convention `majordom-<protocol>`
  (hyphens): in `pyproject.toml` (`[project].name`) and `.github/workflows/release.yml`
  (`pypi-package-name`).
- `integration_template` → your import name `majordom_<protocol>` (underscores): the
  `integration_template/` directory, plus the `--cov=` and `packages` references in
  `pyproject.toml`.
- Rename `ExampleController` and fill in `integration_template/controller.py` with real
  protocol logic. `tests/test_controller.py` is prefilled to fail until you do — work the
  **Progress** checklist below and tick items off as your CI goes green.
- In `.github/workflows/test.yml`, delete the `template-selfcheck` job and the `if:` guard
  on the `test` job — they exist only to keep the *template* repo green and aren't wanted in
  a real integration.
- Fill in the **About this integration** section below (it doubles as your PR summary — a
  reviewer reads the checklist to see what's actually implemented).

> CI needs `majordom-integration-sdk` published to PyPI to install. While it's unpublished,
> develop locally with the path-dependency block described above.

**2. Install + pre-commit hook**
```sh
pip install poetry poethepoet && poe install
```
Until `majordom-integration-sdk` is published, develop against a local checkout by
uncommenting the `[tool.poetry.dependencies]` path block in `pyproject.toml`.

**3. Create the `develop` branch**
```sh
git checkout -b develop && git push origin develop
```

**4. GitHub repo settings** — same as any package repo built on the shared workflows:
**General** → enable **Allow auto-merge**; **Branches** → protect `master` (require the
`test / check` status, restrict push to `github-actions[bot]`) and `develop` (require
`test / check`); **Environments** → create `release` (deployment branch `develop` only,
required reviewer). Then configure PyPI trusted publishing for your package (Owner
`MajorDom-Systems`, Workflow `release.yml`, Environment `release`).

The reusable CI/CD lives in [ParkerIndustries/workflows](https://github.com/ParkerIndustries/workflows).

<!-- ─────────────────────────────── DELETE ABOVE ─────────────────────────────── -->

# integration-template

A [MajorDom](https://majordom.io) integration — bridges the Example protocol into the
MajorDom language.

Built on the [MajorDom Integration SDK](https://github.com/MajorDom-Systems/integration-sdk).
The integration's entry point is a `Controller` (`integration_template/controller.py`) that
the Hub instantiates and drives through its lifecycle: discovery → pairing → commands →
teardown. It can also be run standalone (no Hub) via the SDK's dev runner while developing.

## About this integration

<!-- Fill this in. It's your PR summary — keep the checklist current so a reviewer sees at
     a glance what works. -->

- **Protocol / platform:** _e.g. Philips Hue (Zigbee via a bridge)_
- **Transport(s):** _wifi / ble / zigbee / …_
- **Supported devices:** _…_
- **Credentials needed to pair:** _none / code / secret / qr_

### Required harness

<!-- EXAMPLE — replace with your integration's real requirements (delete rows that don't
     apply). External things this integration needs to run, beyond `pip install`, so a
     deployment knows what to provide. -->

- **Hardware adapters:** _e.g. an 802.15.4 radio (SkyConnect / a Thread or Zigbee dongle), a
  USB serial gateway …_ — the Hub assigns OS device paths through
  `dependencies.hardware_interfaces` (e.g. `/dev/ttyACM0`).
- **Third-party software services:** _e.g. an OpenThread Border Router (OTBR), a vendor
  bridge/hub, an MQTT broker, a matter-server instance …_ — what must be running and reachable.
- **OS / permissions:** _e.g. Bluetooth access, host networking, mDNS/SSDP on the LAN …_

### Protocol stack (OSI)

<!-- EXAMPLE — the table below is a Matter-over-Thread illustration; replace every row with
     your own stack. Map the stack this integration bridges and mark which layers are THIS
     repo's code vs. provided by a library, the OS, or the harness above — it sets the scope
     of what the integration owns. Keep only the rows that apply. -->

| OSI layer | Protocol | Implemented by |
|-----------|----------|----------------|
| Application (7) | _Matter clusters / data model_ | **this integration** (via `chip` lib) |
| Session (5) | _CASE / PASE secure session_ | library |
| Transport (4) | _UDP_ | OS |
| Network (3) | _IPv6 · 6LoWPAN_ | OS · OTBR (harness) |
| Data link / Physical (1–2) | _Thread · IEEE 802.15.4_ | radio adapter (harness) |

### Progress

The canonical [Implementation Checklist](https://docs.majordom.io/device-integration) —
tick items as you implement them (and as the corresponding test in `tests/` goes green):

- [ ] Discovery services registered via `self.dependencies.zeroconf_discovery_service`, `ssdp_discovery_service`, and/or `ble_discovery_service` as appropriate; cancel closures saved and called in `stop`
- [ ] Discovery service listeners fire when devices are found, and the controller calls `self.dependencies.output.controller_did_receive_discovery`
- [ ] Discovery of devices already paired to the Hub on reconnect, e.g. after a reboot (`self.dependencies.output.controller_did_connect_device` is called)
- [ ] `start_pairing_window` is implemented but only if the protocol requires an explicit scan (like zigbee)
- [ ] Device pairing 
- [ ] Device schema is properly mapped: device info, parameter list, and each parameter's metadata are translated to MajorDom's domain model
- [ ] Hub → Device control (`send_command` is implemented)
- [ ] Device → Hub event subscription (`self.dependencies.output.controller_did_receive_events` is called on incoming events)
- [ ] `identify` is implemented
- [ ] `unpair` is implemented
- [ ] `fetch` is implemented
- [ ] Paired devices going offline/coming back online *while the Hub is running* (not just on reboot) — set `device.available` accordingly (report `controller_did_lose_device`), and clear/set `last_error` to match
- [ ] Graceful shutdown in `stop`, cancelling any running tasks, discovery stopped, all connections closed
- [ ] Tests pass against a virtual/simulated device (`tests/test_controller.py`)
- [ ] README fully filled in: delete the template-setup section above, complete **About this integration**, **Required harness**, and **Protocol stack (OSI)** with real content

## Documentation

Full integration-author docs — the controller lifecycle, data models, storing data,
discovery, and a worked example — live at **[docs.majordom.io](https://docs.majordom.io/device-integration)**.

## Development

```sh
poetry install && poetry run poe install
```

| Task | Description |
|------|-------------|
| `poe check` | Full quality pipeline (ruff, ty, pytest, poetry build/check) |
| `poe check --ci` | Same, plus `git diff --exit-code` |

Work lands on `develop`; `master` is protected and released via **Actions → Release**.
Tests drive the controller with the SDK's test doubles (`majordom_integration_sdk.testing`)
against a virtual/simulated device — see `tests/`.

## License

See [LICENSE](LICENSE). Your integration code is yours to license as you choose. For
commercial licensing or partnership inquiries regarding MajorDom, contact us via
[parker-industries.org/partnership](https://parker-industries.org/partnership).
