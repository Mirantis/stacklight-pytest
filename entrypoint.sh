#!/usr/bin/env bash

export URL=$(kubectl config view --minify | grep server | cut -f 2- -d ":" | tr -d " ")

export SECRETNAME=$(kubectl get secrets | grep $STACKLIGHT_TEST_POD_NAME | awk '{print $1}')
export TOKEN=$(kubectl describe secret $SECRETNAME | grep -E '^token' | cut -f2 -d':' | tr -d " ")

REPORT_DIR="${REPORT_DIR:-}"
if [[ -z "$REPORT_DIR" ]]; then
    echo "No REPORT_DIR variable specified or discovered. Default /report path will be used"
    REPORT_DIR="/report"
    export LOG_FILE="/report/test.log"
else
    echo "Using REPORT_DIR ${REPORT_DIR}"
    export LOG_FILE="${REPORT_DIR}/test.log"
fi
mkdir -p $REPORT_DIR

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

exec pytest --reruns 2 --reruns-delay 30 --junit-xml="${REPORT_DIR}"/report.xml --html="${REPORT_DIR}"/sl-tests.html --self-contained-html --tb=short -v --show-capture=stdout stacklight_tests/tests/
