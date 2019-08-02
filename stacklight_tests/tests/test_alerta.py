import logging
import pytest

from stacklight_tests import utils

logger = logging.getLogger(__name__)


@pytest.mark.alerta
@pytest.mark.smoke
def test_alerta_smoke(alerta_api):
    alerta_api.get_count()


@pytest.mark.alerta
@pytest.mark.smoke
def test_mongodb_status(mongodb_api):
    logger.info("Checking database `alerta` is present")
    assert 'alerta' in mongodb_api.list_database_names()
    logger.info("Checking Mongodb server status is ok")
    assert str(mongodb_api.server_info()['ok']) == '1.0'
    db = mongodb_api['alerta']
    logger.info("Checking authentication to database `alerta` "
                "with default credentials")
    assert db.authenticate('alerta', 'alertadb')
    mongo_status = db.command("serverStatus")
    logger.info("Checking database `alerta` status is ok")
    assert str(mongo_status['ok']) == '1.0'
    logger.info("Checking connections in database `alerta`")
    assert mongo_status['connections']['current'] != 0
    assert mongo_status['connections']['available'] != 0


@pytest.mark.alerta
@pytest.mark.smoke
def test_alerta_alerts_consistency(prometheus_native_alerting, alerta_api):
    def check_alerts():
        alerta_alerts = {"{0} {1}".format(i.event, i.resource).replace(
            "n/a", "") for i in alerta_api.get_alerts({"status": "open"})}
        alertmanager_alerts = {
            "{0} {1}".format(i.name, i.instance)
            for i in prometheus_native_alerting.list_alerts()}
        if alerta_alerts == alertmanager_alerts:
            return True
        else:
            logger.warning(
                "Alerts in Alerta and NOT in AlertManager: {0}\n"
                "Alerts in AlertManager and NOT in Alerta: {1}".format(
                    alerta_alerts.difference(alertmanager_alerts),
                    alertmanager_alerts.difference(alerta_alerts)))
            return False

    utils.wait(check_alerts, interval=30, timeout=6 * 60,
               timeout_msg="Alerts in Alertmanager and Alerta incosistent")
