#!/bin/bash

set -e

sudo apt update
sudo apt install -y libffi-dev python3-dev python3-venv build-essential

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt