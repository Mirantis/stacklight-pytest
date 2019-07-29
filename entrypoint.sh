#!/usr/bin/env bash

POD_REPORT_DIR="${POD_REPORT_DIR:-report}"

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

exec pytest --junitxml=/${POD_REPORT_DIR}/report.xml --html=/${POD_REPORT_DIR}/sl-tests.html --self-contained-html --tb=short -sv stacklight_tests/tests/
