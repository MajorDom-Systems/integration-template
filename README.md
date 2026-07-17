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

### Progress

Tick items as you implement them (and as the corresponding test in `tests/` goes green):

- [ ] `discoveries` — surfaces unpaired devices (register a discovery service in `start`)
- [ ] `pair_device` — pairs a discovery, reports `controller_did_connect_device`
- [ ] Credentials — declares `expected_credentials_options`, validates supplied credentials
- [ ] `fetch` — refreshes device + parameters, reports changes via `controller_did_receive_events`
- [ ] `send_command` — applies a parameter change on the device
- [ ] `identify` — makes the device blink/beep
- [ ] `unpair` — removes the device cleanly
- [ ] `start` / `stop` — starts services & reconciles paired devices / releases resources
- [ ] Availability — reports `controller_did_lose_device` when a paired device drops
- [ ] Tests — `tests/test_controller.py` filled in and passing (virtual/simulated device)
- [ ] Real-hardware suite (optional) — `real_iot_device`-marked tests on a rig

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
Tests drive the controller with the SDK's test doubles (`majordom_sdk.testing`) — see
`tests/`. Add a `real_iot_device`-marked suite if you validate against hardware.

## License

See [LICENSE](LICENSE). Your integration code is yours to license as you choose. For
commercial licensing or partnership inquiries regarding MajorDom, contact us via
[parker-industries.org/partnership](https://parker-industries.org/partnership).
