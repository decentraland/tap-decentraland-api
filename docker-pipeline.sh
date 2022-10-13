#!/bin/bash

/project/tap-decentraland-api.sh | /project/target-jsonl.sh
mv *.jsonl output/