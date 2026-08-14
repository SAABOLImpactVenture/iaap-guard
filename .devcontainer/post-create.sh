#!/usr/bin/env bash
set -euo pipefail

if ! dpkg -s python3-venv >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y python3-venv
fi

python3 -m venv .venv
source .venv/bin/activate

if ! command -v make >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y make
fi

python -m pip install --upgrade pip
python -m pip install -r requirements-ci.txt
python -m pip install aws-sam-cli

make validate

printf '\nIaaP Guard development environment ready.\n'
python --version
make --version | head -n 1
gh --version | head -n 1
aws --version
sam --version
