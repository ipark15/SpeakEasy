#!/bin/bash
# Run once from repo root: bash setup_venv.sh

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Venv ready. To activate: source .venv/bin/activate"
