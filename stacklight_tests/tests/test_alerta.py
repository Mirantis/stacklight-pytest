import logging
import pytest
import datetime

from stacklight_tests import utils

logger = logging.getLogger(__name__)


@pytest.mark.alerta
@pytest.mark.smoke
def test_alerta_smoke(alerta_api):
    count = alerta_api.get_count()
    assert count['status'] == 'ok'


@pytest.mark.alerta
@pytest.mark.smoke
@pytest.mark.run(order=-1)
def test_alerta_alerts_consistency(prometheus_native_alerting, alerta_api):
    def check_alerts(alert_age=300):
        time_now = datetime.datetime.now()
        alerta_alerts = {"{0} {1}".format(i['event'], i['resource']).replace(
            "n/a", "") for i in alerta_api.get_alerts({"status": "open"})}
        alertmanager_alerts = {
            "{0} {1}".format(i.name, i.instance)
            for i in prometheus_native_alerting.list_alerts()
            if (prometheus_native_alerting.get and
                utils.difference_in_seconds(utils.convert_unicode_to_datetime(
                    list(i.time)[0]), time_now, alert_age))}
        logger.info(list(prometheus_native_alerting.list_alerts()[0].time)[0])
        print alerta_alerts
        print alertmanager_alerts
        if alertmanager_alerts.issubset(alerta_alerts):
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


@pytest.mark.alerta
@pytest.mark.smoke
@pytest.mark.skip("Skip test for MongoDB")
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
