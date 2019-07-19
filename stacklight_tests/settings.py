import logging
import os


# Logging settings
CONSOLE_LOG_LEVEL = os.environ.get('LOG_LEVEL', logging.DEBUG)
LOG_FILE = os.environ.get('LOG_FILE', 'test.log')

# Plugins info
SL_NAMESPACE = os.environ.get("SL_NAMESPACE", 'stacklight')

# Images dir
IMAGES_PATH = os.environ.get("IMAGES_PATH", os.path.expanduser('~/images'))
CIRROS_QCOW2_URL = os.environ.get(
    "CIRROS_QCOW2_URL",
    "http://download.cirros-cloud.net/0.4.0/cirros-0.4.0-x86_64-disk.img"
)

VOLUME_STATUS = os.environ.get("VOLUME_STATUS", "available")
