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
  protocol logic.

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

## Documentation

Full integration-author docs — the controller lifecycle, data models, storing data,
discovery, and a worked example — live at **[docs.majordom.io](https://docs.majordom.io)**.

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
