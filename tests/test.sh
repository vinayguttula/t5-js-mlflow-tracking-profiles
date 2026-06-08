#!/bin/bash
set -uo pipefail

if [ "$PWD" = "/" ]; then
    echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
    mkdir -p /logs/verifier
    echo 0 > /logs/verifier/reward.txt
    exit 1
fi

# Install test dependencies at runtime (allowed in test.sh to keep Docker image clean of test logic)
pip install --no-index --find-links /tmp/test-wheels pytest==8.1.1 pytest-json-ctrf==0.5.0

mkdir -p /logs/verifier

# Run tests
python3 -m pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA
rc=$?

if [ "$rc" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
