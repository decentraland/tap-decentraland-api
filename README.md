# tap-decentraland-api

`tap-decentraland-api` is a Singer tap for the Decentraland API.

Build with the [Singer SDK](https://gitlab.com/meltano/singer-sdk).

## Installation


```bash
pipx install tap-decentraland-api
```

## Configuration

### Accepted Config Options

You need to specify if you are trying to get test or production data by setting property `api_url`, configs are provided in the config folder.

### Executing the Tap Directly

```bash
tap-decentraland-api --version
tap-decentraland-api --help
tap-decentraland-api --config CONFIG --discover > ./catalog.json
```

## Developer Resources

### Initialize your Development Environment

```bash
pipx install poetry
poetry install
```

### Create and Run Tests

Create tests within the `tap_decentraland_api/tests` subfolder and
  then run:

```bash
poetry run pytest
```

You can also test the `tap-decentraland-api` CLI interface directly using `poetry run`:

```bash
poetry run tap-decentraland-api --help
```

### Testing with [Meltano](meltano.com)

_**Note:** This tap will work in any Singer environment and does not require Meltano.
Examples here are for convenience and to streamline end-to-end orchestration scenarios._

Next, install Meltano (if you haven't already) and any needed plugins:

```bash
# Install meltano
pipx install meltano
# Initialize meltano within this directory
cd tap-decentraland-api
meltano install
```

Now you can test and orchestrate using Meltano:

```bash
# Test invocation:
meltano invoke tap-decentraland-api --version
# OR run a test `elt` pipeline:
meltano elt tap-decentraland-api target-jsonl
```
