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
