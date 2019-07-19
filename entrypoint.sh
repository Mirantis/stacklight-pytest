#!/usr/bin/env bash

function activate_venv(){
  set +x
  if [[ -f venv/bin/activate ]]; then
    echo "Activating venv in $(pwd)"
    source venv/bin/activate && echo "Activated succesfully"
  else
    echo "WARNING: No venv found in $(pwd)"
    return 1
  fi
  set -x
}

cd /stacklight-pytest
activate_venv

exec pytest --junitxml=/report/report.xml --tb=short -sv stacklight_tests/tests/test_smoke.py
