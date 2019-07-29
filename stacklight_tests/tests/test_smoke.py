import json
import logging
import pytest

from stacklight_tests import utils

logger = logging.getLogger(__name__)


@pytest.mark.run(order=1)
@pytest.mark.smoke
@pytest.mark.logs
def test_elasticsearch_status(es_client):
    logger.info("Getting Elasticsearch status")
    status = es_client.health()

    logger.info("Elasticsearch cluster status is \n{}".format(status))
    assert status['status'] == 'green', \
        "Elasticsearch status is not 'green', current status is '{}'".format(
            status['status'])
    assert str(status['active_shards_percent_as_number']) == '100.0', \
        "Some shards are not in 'active' state"


@pytest.mark.run(order=1)
@pytest.mark.smoke
@pytest.mark.logs
def test_kibana_status(kibana_client):
    logger.info("Getting Kibana status")
    resp = utils.check_http_get_response(
        "{}/api/status".format(kibana_client.url))
    assert resp, ("Cannot get Kibana status through API, "
                  "check that Kibana is running")
    status = json.loads(resp.content)

    logger.info("Check overall Kibana status")
    assert status['status']['overall']['state'] == "green", \
        ("Kibana status is not 'green', current status is '{}'".format(
            status['status']['overall']))

    logger.info("Check status of Kibana plugins")
    msg = "Status of {} is not 'green', current status is '{}'"
    for plugin in status['status']['statuses']:
        assert plugin['state'] == "green", msg.format(
            plugin["id"], plugin["state"])


@pytest.mark.run(order=1)
@pytest.mark.smoke
@pytest.mark.prometheus
def test_prometheus_datasource(prometheus_api):
    assert prometheus_api.get_all_measurements()


@pytest.mark.run(order=1)
@pytest.mark.smoke
@pytest.mark.prometheus
def test_prometheus_metrics(prometheus_api):
    metric = prometheus_api.get_query("prometheus_build_info")
    assert len(metric) != 0


@pytest.mark.skip("Temporary skip")
def test_firing_alerts(prometheus_alerting):
    logger.info("Getting a list of firing alerts")
    alerts = prometheus_alerting.list_alerts()
    skip_list = ['SystemDiskFullWarning', 'SystemDiskFullCritical',
                 'NetdevBudgetRanOutsWarning', 'MemcachedItemsNoneMinor',
                 'SystemMemoryFullMajor', 'SystemMemoryFullWarning',
                 'SystemLoadTooHighCritical', 'SystemLoadTooHighWarning',
                 'ContrailBGPSessionsDown']
    for alert in alerts:
        msg = "Alert {} is fired".format(alert.name)
        if alert.host:
            msg += " for the node {}".format(alert.host)
        logger.warning(msg)
    alerts = filter(lambda x: x.name not in skip_list, alerts)
    assert len(alerts) == 0, \
        "There are some firing alerts in the cluster: {}".format(
            " ".join([a.name for a in alerts]))
