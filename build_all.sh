#!/usr/bin/env bash
# Rebuild every deliverable from the source modules, in dependency order.
# Run from the repository root.
set -euo pipefail

echo "== classical checks =="
python3 -I src/verify_model.py

echo "== scaling study (writes results/bonus.json) =="
python3 -I -u src/run_bonus.py

echo "== figures =="
python3 -I src/build_figures.py

echo "== README.md =="
python3 -I src/build_readme.py

echo "== slides.pptx =="
node src/build_slides.js

echo "== solution.ipynb (executed, outputs saved) =="
python3 -I src/build_notebook.py
python3 -m jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=1800 solution.ipynb

echo "== done =="
