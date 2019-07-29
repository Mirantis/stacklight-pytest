import logging
import pytest

logger = logging.getLogger(__name__)


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
