#!/bin/bash
set -uo pipefail

if [ "$PWD" = "/" ]; then
    echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
    mkdir -p /logs/verifier
    echo 0 > /logs/verifier/reward.txt
    exit 1
fi

# Install test dependencies at runtime (allowed in test.sh to keep Docker image clean of test logic)
mkdir -p /logs/verifier

# Run tests
python3 -m pytest --ctrf /logs/verifier/ctrf.json /app/tests/test_outputs.py -rA
rc=$?

if [ -f /logs/verifier/ctrf.json ]; then
  python3 -c "
import json
data = json.load(open('/logs/verifier/ctrf.json'))
s = data['results']['summary']
total = s.get('tests', 1)
passed = s.get('passed', 0)
print(f'{passed/total:.2f}')
" > /logs/verifier/reward.txt
else
  if [ "$rc" -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
  else
    echo 0 > /logs/verifier/reward.txt
  fi
fi
