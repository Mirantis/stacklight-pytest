import json
import logging
import pytest

logger = logging.getLogger(__name__)


def idfy_name(name):
    return name.lower().replace(" ", "-")


def get_all_kibana_dashboards_names():
    dashboards = {"audit": 'Audit',
                  "kubernetes_events": 'K8S events',
                  "logs": 'Logs',
                  "notifications": 'Notifications'}
    return dashboards


@pytest.fixture(scope="module",
                params=get_all_kibana_dashboards_names().items(),
                ids=[idfy_name(v) for v in
                     get_all_kibana_dashboards_names().values()])
def dashboard_name(request):
    return request.param


@pytest.mark.dashboards
@pytest.mark.run(order=-2)
def test_kibana_dashboard(dashboard_name, kibana_client, k8s_api):
    name_in_chart, name = dashboard_name
    kibana_dashboards = (k8s_api.get_stacklight_chart('kibana')
                         ['values']['dashboardImport']['dashboards'].keys())
    if name_in_chart not in kibana_dashboards:
        pytest.skip("This dashboard is not in the 'kibana' chart."
                    "Thus it's not expected in the Kibana.")
    q = '{"query":{"match" : {"type": "dashboard"}}}'
    output = json.loads(kibana_client.get_query(q))
    actual_dashboards = [d['_source']['dashboard']['title'] for d in
                         output['hits']['hits']]
    assert name in actual_dashboards, \
        "The representation of this dashboard is not correct"
