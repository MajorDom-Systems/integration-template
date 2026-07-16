<!-- ┌───────────────────────────────────────────────────────────────────────────┐
     │ USING THIS TEMPLATE — delete everything down to the "DELETE ABOVE" line      │
     │ once your new repo is set up. What's left below is your project's own README.│
     └───────────────────────────────────────────────────────────────────────────┘ -->

# Creating a new repo from this template

Click **Use this template → Create a new repository** (this is a GitHub
[template repository](https://docs.github.com/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template)),
then:

**1. Rename the placeholders** (two tokens — find & replace across the repo)
- `project-template` → your PyPI/distribution name (hyphens): in `pyproject.toml`
  (`[project].name`), `.github/workflows/release.yml` (`pypi-package-name`), and `mkdocs.yml`.
- `project_template` → your import/package name (underscores): the `project_template/`
  directory, plus its `--cov=` / `packages` / `pythonpath` references in `pyproject.toml`.
- If not publishing docs, delete `mkdocs.yml`, `docs/`, and `.github/workflows/docs.yml`;
  otherwise set `docs-url` in `release.yml` and uncomment the `mkdocs-*` dev deps.

**2. Install + pre-commit hook**
```sh
pip install poetry poethepoet && poe install
```

**3. Create the `develop` branch**
```sh
git checkout -b develop && git push origin develop
```

**4. GitHub repo settings**
- **General** → enable **Allow auto-merge** (required for Dependabot auto-merge).
- **Branches** → your stable branch (`main` or `master`): read-only, require the
  `test / check` status, restrict push to `github-actions[bot]`; `develop`: require
  `test / check`. (`test / check` is the matrix gate — one stable check regardless of how
  many Python versions run.)
- **Environments** → create `release`: deployment branch `develop` only, required reviewer.

**5. PyPI trusted publishing** (once per package) — [pypi.org](https://pypi.org) → your
project → Publishing → Add trusted publisher: Owner `ParkerIndustries`, Repository = your
repo, Workflow `release.yml`, Environment `release`. No `PYPI_API_TOKEN` needed.

The reusable CI/CD lives in [ParkerIndustries/workflows](https://github.com/ParkerIndustries/workflows);
the `.github/workflows/*.yml` here are just the trigger stubs that call into it. See that
repo's README for the release flow, the Dependabot permissions requirement, and the
private-repo PAT setup.

<!-- ─────────────────────────────── DELETE ABOVE ─────────────────────────────── -->

# project-template

Short description of your package.

## Requirements

- Python 3.12+
- [Poetry](https://python-poetry.org/) 2.0+

---

## Setup

```sh
poetry install && poetry run poe install
```

This installs all dependencies and sets up the pre-commit hook that runs `poe check` before every commit.

---

## Branching & release flow

Two long-lived branches:

- **`develop`** — the integration branch. All work lands here.
- **`main`** (or `master`) — the stable/released branch. Protected and read-only; only the
  release automation pushes to it.

Day to day:

1. Branch off `develop` for your change (`feature/…`, `fix/…`).
2. Open a PR **into `develop`**. CI runs the QA matrix; the `test / check` gate must pass to merge.
3. Dependabot also opens dependency PRs into `develop`, auto-merged once their checks pass.

Releasing (maintainers) — **Actions → Release → Run workflow**, on `develop`:

```
QA matrix + pip-audit     ← release stops here on failure; nothing is pushed
bump patch version (develop)
build + publish to PyPI    ← trusted publishing; stops here on failure, stable untouched
fast-forward develop → main/master
tag vX.Y.Z + signed GitHub Release (auto changelog)
```

Releases are always cut from `develop`; the stable branch only ever moves forward via this
fast-forward, so it stays a clean linear history of released versions. The changelog is the
commit subjects since the last tag (plus changed docs pages if `docs-url` is set).

---

## Development

### Tasks

Tasks are managed with [poethepoet](https://github.com/nat-n/poethepoet) and run via `poetry run poe <task>`.

| Task | Description |
|------|-------------|
| `poe install` | Install deps and register the pre-commit hook |
| `poe check` | Run the full quality pipeline (lint, format, type-check, test, build) |
| `poe check --ci` | Same as above, plus `git diff --exit-code` to catch uncommitted changes |
| `poe docs` | Serve docs locally with live-reload (only if you kept `mkdocs.yml` + `docs/`) |

### Code Quality

The `poe check` pipeline runs the following steps in order, collecting all failures before exiting:
- ruff (lint + format)
- ty (type check)
- pytest
- poetry's `check` and `build`

The same pipeline is included in CI check and pre-commit hook, but still recommended to run manually after changes.

**Customizing the checks.** The whole QA stack is just the `[tool.poe.tasks.check]` shell
script in `pyproject.toml` — this repo owns it, not the shared CI. To swap the type checker
(the template defaults to [`ty`](https://github.com/astral-sh/ty)) for mypy or pyright, add
the tool to the dev deps and change the one line, e.g. `poetry run mypy . || code=1`. Add
or remove steps the same way. CI runs exactly this task (`poe check --ci`), so it stays in
sync automatically.

**Dependency vulnerability scan (`pip-audit`)** runs on **release only**, not on everyday
PRs/pushes — a newly-disclosed CVE in a transitive dep shouldn't red unrelated PRs, but it
should block a release. Run it locally anytime with `poetry run pip-audit`. When a CVE has
no fix yet, add `--ignore-vuln <ID>` where it runs.

### CI: Python version matrix

CI runs the QA pipeline across a matrix of Python versions (default `["3.12", "3.13"]`,
defined centrally in the shared `test.yml`). Override per-repo in `.github/workflows/test.yml`
with `python-versions: '[...]'`. Branch protection should require the single **`test / check`**
status — a gate over the whole matrix, so it doesn't change when the matrix does.

The stubs trigger on pushes to `main`/`master`/`develop` and on all PRs; if your stable
branch is `master`, the release workflow needs `stable-branch: master` (see the release stub).

### Compiled (Cython) extensions

Pure-Python by default. If you need Cython extensions, see the commented `setup.py` sketch
and dev deps in `pyproject.toml`, and set `matrix-build: true` in the release stub — compiled
wheels are Python-version-specific, so the release then builds a wheel per version (plus one
sdist) instead of the single pure-Python `py3-none-any` wheel.

### Testing

Tests are run with [pytest](https://docs.pytest.org/) with async support via `pytest-asyncio` (or `pytest-trio`), auto mode enabled. Shared fixtures go in `tests/conftest.py`.

```sh
poetry run pytest # run all tests
```

But pre-installed plugins may show a deeper insights (can be combined):

#### pytest-cov

```bash
pytest --cov=your_module
```

Shows what percentage of the code is tested and what code paths weren't called. `--cov-report` option saves the result to a file so that it can be viewed with other tools, tracked, compared, uploaded, etc.

#### pytest-timeout

```bash
pytest --timeout=2
```

Limits test execution time and avoid long (sometimes minutes-long and even hours-long) timeouts.

Alternative usage per test:

```python
import pytest

@pytest.mark.timeout(2) # seconds
def test_timeout():
    do_something()
```

#### pytest-repeat

Run each test multiple times. Useful for triggering not-consistent bugs, dealing with probabilities, and leaks.

```bash
pytest --count=10
```

Alternative usage per test:

```python
import pytest

@pytest.mark.repeat(10)
def test_repeat():
    do_something()
```

#### pytest-benchmark

Measures and compares execution time of a specific function, providing stats like min, max, mean, and median execution time, and allows saving/loading results for performance tracking. Pro tip: combine with pytest-profiling.

```python
@pytest.mark.benchmark
def test_my_function(benchmark):
    def func():
        sum(range(1000))
    benchmark(func) # wrap the func you want to benchmark
```

- wrap the func you want to measure in `benchmark`
- if pytest.mark.benchmark is added, the benchmark test is skipped during running normal tests
- use `pytest --benchmark-only` to run benchmarks

#### pytest-profiling

Tracks program’s function calls, execution time, and memory usage, helping find bottlenecks and optimise performance. ELI5: shows which function makes the code slow.

`pytest --profile` generates a profiling report which can be visualized with tools like [snakeviz](https://jiffyclub.github.io/snakeviz/) (more features). Alternatively, a simpler built-in option can be used - `pytest --profile-svg` generates an svg file that can be viewed in a web browser.

#### pytest-resource-usage

A basic alternative to bencmarking and profiling. Just log system resource usage and execution duration time.

```bash
pytest --resource-monitor --durations=0
```

--durations=N shows the slowest N tests. 0 to show all tests’ durations

---

## License

See [LICENSE](LICENSE). This template ships Apache-2.0 as a placeholder — replace it with
your project's own license (the template's own license is Apache-2.0 regardless).
