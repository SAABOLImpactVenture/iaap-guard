#!/usr/bin/env bash
set -euo pipefail

source .venv/bin/activate

python --version
make --version | head -n 1
gh --version | head -n 1
aws --version
sam --version
docker --version
make validate
