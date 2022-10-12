#!/bin/bash

docker build -t tapapi . && docker run --mount type=bind,source="$(pwd)"/output,target=/project/output -it tapapi