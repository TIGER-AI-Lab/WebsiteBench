# Development

Run these commands from the repository root.

## Install dependencies

```sh
uv sync --locked --group dev
```

## Check task definitions

```sh
uv run python scripts/check_tasks.py --code-only
```

This checks the official Harbor configuration, entry points, Compose definitions, and runtime policies in the source checkout.

To inspect the application files of a local task bundle:

```sh
uv run python scripts/check_tasks.py --root ./local-tasks \
  --task medium --check-assets
```

Use `--task` to select individual task directories. Run `uv run python scripts/check_tasks.py --help` for all options.

## Unit tests and code style

```sh
uv run python -m unittest discover -s tests -v
uv run ruff check scripts src tests
uv run ruff format --check scripts src tests
```

The unit tests cover the task checker, the `websitebench` command, and `scripts/download_tasks.py` without network access, and check that the release index `src/websitebench/websitebench-v1.json` lists exactly the tasks under `tasks/`.

Format edited development code with:

```sh
uv run ruff format scripts src tests
```

## CI

[CI](../.github/workflows/ci.yml) runs on Python 3.12 and 3.13. It installs locked dependencies, checks source task definitions, runs the unit tests and Ruff checks, and verifies the official Harbor command's help output.

Task runtime and evaluation code live under `tasks/`; the development Ruff commands target the repository's checker, the `websitebench` package, and the unit tests. See [Task format](task-format.md) for the interfaces those checks cover.

## Package release

The [`websitebench`](https://pypi.org/project/websitebench/) package in `src/websitebench` contains the download command and the release index; `scripts/download_tasks.py` runs the same code. Build the sdist and wheel locally with:

```sh
uv build
```

The [publish workflow](../.github/workflows/publish.yml) uploads the package to PyPI with Trusted Publishing when a GitHub release is published. Set the new version with `uv version <version>`, which updates `pyproject.toml` and `uv.lock`, and tag the release `v<version>`, for example `v0.0.1`. The workflow stops if the tag and the version differ. Running the workflow manually builds and checks the distributions without uploading them. Release a new version whenever the index changes, so the installed command downloads the same files as this repository.
