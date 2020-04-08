import logging
import os


_boolean_states = {'1': True, 'yes': True, 'true': True, 'on': True,
                   '0': False, 'no': False, 'false': False, 'off': False}


def get_var_as_bool(name, default):
    value = os.environ.get(name, '')
    return _boolean_states.get(value.lower(), default)


# Logging settings
CONSOLE_LOG_LEVEL = os.environ.get('LOG_LEVEL', logging.DEBUG)
LOG_FILE = os.environ.get('LOG_FILE', 'test.log')

# Test settings
SL_NAMESPACE = os.environ.get("SL_NAMESPACE", 'stacklight')
TEST_FIRING_ALERTS = get_var_as_bool("TEST_FIRING_ALERTS", True)
STACKLIGHT_TEST_POD_NAME = os.environ.get("STACKLIGHT_TEST_POD_NAME",
                                          'test-stacklight')

# Images dir
IMAGES_PATH = os.environ.get("IMAGES_PATH", os.path.expanduser('~/images'))
CIRROS_QCOW2_URL = os.environ.get(
    "CIRROS_QCOW2_URL",
    "http://download.cirros-cloud.net/0.4.0/cirros-0.4.0-x86_64-disk.img"
)

VOLUME_STATUS = os.environ.get("VOLUME_STATUS", "available")

# Keycloak settings
KEYCLOAK_URL = os.environ.get('KEYCLOAK_URL', "https://172.19.116.60")
KEYCLOAK_USER = os.environ.get('KEYCLOAK_USER', "writer")
KEYCLOAK_PASSWORD = os.environ.get('KEYCLOAK_PASSWORD', "password")

IAM_PROXY_ALERTA_SECRET = os.environ.get('IAM_PROXY_ALERTA_SECRET', "")
IAM_PROXY_ALERTMANAGER_SECRET = os.environ.get('IAM_PROXY_ALERTMANAGER_SECRET',
                                               "")
IAM_PROXY_PROMETHEUS_SECRET = os.environ.get('IAM_PROXY_PROMETHEUS_SECRET', "")
IAM_PROXY_GRAFANA_SECRET = os.environ.get('IAM_PROXY_GRAFANA_SECRET', "")
IAM_PROXY_KIBANA_SECRET = os.environ.get('IAM_PROXY_KIBANA_SECRET', "")
