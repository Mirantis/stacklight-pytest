import collections

import pytest

ignored_queries_for_fail = []


ignored_queries_for_partial_fail = []


def idfy_name(name):
    return name.lower().replace(" ", "-").replace("(", "").replace(")", "")


def query_dict_to_string(query_dict):
    return "\n\n".join(
        [panel + "\n" + query for panel, query in query_dict.items()])


def get_all_grafana_dashboards_names():
    dashboards = {
        "Alertmanager": True,
        "ElasticSearch": False,
        "Grafana": True,
        "Kubernetes Calico": False,
        "Kubernetes Cluster": False,
        "Kubernetes Container": False,
        "Kubernetes Deployments": False,
        "Kubernetes Node": True,
        "MongoDB": False,
        "Node Exporter Full": True,
        "Prometheus Performances": False,
        "Prometheus Stats": False,
        "Pushgateway": True
    }

    return {idfy_name(k): v for k, v in dashboards.items()}


class PanelStatus(object):
    ok = "Passed"
    partial_fail = "Partially failed"
    fail = "Failed"
    ignored = "Skipped"


class Panel(object):
    def __init__(self, location, raw_query):
        self.location = location
        self.raw_query = raw_query
        self.queries = {}

    def add_query(self, query, status):
        self.queries[query] = status

    @property
    def status(self):
        statuses = self.queries.values()

        if all([status == PanelStatus.ok for status in statuses]):
            return PanelStatus.ok

        if all([status == PanelStatus.fail for status in statuses]):
            if self.raw_query in ignored_queries_for_fail:
                return PanelStatus.ignored
            else:
                return PanelStatus.fail

        if any([status == PanelStatus.fail for status in statuses]):
            if self.raw_query in ignored_queries_for_partial_fail:
                return PanelStatus.ignored
            else:
                return PanelStatus.partial_fail

    def get_failed_queries(self):
        return [query for query, status in self.queries.items()
                if status == PanelStatus.fail]

    def print_panel(self):
        return '  Location "{}" \t Query "{}"'\
            .format(self.location, self.raw_query)

    def print_panel_detail(self):
        return '  Location "{}" \t Query "{}"\n    Failed queries:\n    {}'\
            .format(self.location,
                    self.raw_query,
                    '\n    '.join(self.get_failed_queries()))

    def __str__(self):
        if self.status != PanelStatus.partial_fail:
            return self.print_panel()
        return self.print_panel_detail()


@pytest.fixture(scope="module",
                params=get_all_grafana_dashboards_names().items(),
                ids=get_all_grafana_dashboards_names().keys())
def dashboard_name(request):
    dash_name, requirement = request.param

    if not requirement:
        pytest.skip("Temporary skip test for {} grafana dashboard".format(
            dash_name))

    return dash_name


@pytest.mark.dashboards
@pytest.mark.run(order=-1)
def test_grafana_dashboard_panel_queries(
        dashboard_name, grafana_client, prometheus_api):

    # grafana_client.check_grafana_online()
    dashboard = grafana_client.get_dashboard(dashboard_name)

    assert grafana_client.is_dashboard_exists(dashboard_name), \
        "Dashboard {name} is not present".format(name=dashboard_name)

    dashboard_results = collections.defaultdict(list)

    for location, raw_query in dashboard.get_panel_queries().items():
        possible_templates = dashboard.get_all_templates_for_query(raw_query)

        panel = Panel(location, raw_query)

        for template in possible_templates:
            query = prometheus_api.compile_query(raw_query, template)
            try:
                result = prometheus_api.do_query(query)
                if not result:
                    raise ValueError
                panel.add_query(query, PanelStatus.ok)
            except (KeyError, ValueError):
                panel.add_query(query, PanelStatus.fail)

        dashboard_results[panel.status].append(panel)

    error_msg = (
        "\nPassed panels:\n  {passed}"
        "\nIgnored panels:\n  {ignored}"
        "\nFailed panels:\n  {failed}"
        "\nPartially failed panels:\n  {partially_failed}").format(
            passed="\n  ".join(
                map(str, dashboard_results[PanelStatus.ok])),
            ignored="\n  ".join(
                map(str, dashboard_results[PanelStatus.ignored])),
            failed="\n  ".join(
                map(str, dashboard_results[PanelStatus.fail])),
            partially_failed="\n  ".join(
                map(str, dashboard_results[PanelStatus.partial_fail])))

    assert (len(dashboard_results[PanelStatus.fail]) == 0 and
            len(dashboard_results[PanelStatus.partial_fail]) == 0), error_msg


@pytest.mark.smoke
@pytest.mark.dashboards
def test_panels_fixture(grafana_client):
    fixture_dashboards = get_all_grafana_dashboards_names().keys()

    dashboards = grafana_client.get_all_dashboards_names()
    missing_dashboards = set(dashboards).difference(set(fixture_dashboards))

    assert len(missing_dashboards) == 0, \
        ("Update test data fixture with the missing dashboards: "
         "{}".format(missing_dashboards))
