#!/usr/bin/env bash

cd /kaas-stacklight-pytest
source venv/bin/activate
pytest -s stacklight_tests/tests/test_smoke.py
