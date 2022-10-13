#!/bin/bash

unset VIRTUAL_ENV

STARTDIR=$(pwd)
TOML_DIR=$(dirname "$0")

cd "$TOML_DIR" || exit
poetry run --quiet tap-decentraland-api