import collections

import pytest

ignored_queries_for_fail = [
    # Elasticsearch
    'count(elasticsearch_breakers_tripped{cluster="$cluster",name=~"$name"}'
    '>0)',
    # MongoDB
    'mongodb_replset_oplog_size_bytes{instance=~"$env"}',
    # Prometheus. Skip 1.x prometheus metric
    'prometheus_local_storage_target_heap_size_bytes'
    '{instance=~"$instance:[1-9][0-9]*"}',
    # Kubernetes Cluster
    'sum(kube_node_status_condition{condition="OutOfDisk", node=~"$node", '
    'status="true"})',
    'sum(kube_job_status_succeeded{namespace=~"$namespace"})',
    'sum(kube_job_status_active{namespace=~"$namespace"})',
    'sum(kube_job_status_failed{namespace=~"$namespace"})',
]


ignored_queries_for_partial_fail = [
    # Kubernetes Deployments
    'kube_deployment_status_observed_generation{namespace=~"$namespace"}',
    # Kubernetes Cluster
    'sum(kube_pod_status_phase{namespace=~"$namespace", phase="Unknown"})',
    'sum(kube_deployment_status_replicas_unavailable'
    '{namespace=~"$namespace"})',
    'sum(kube_job_status_succeeded{namespace=~"$namespace"})',
    'sum(kube_pod_status_phase{namespace=~"$namespace", phase="Pending"})',
    'sum(kube_pod_container_status_running{namespace=~"$namespace"})',
    'kube_deployment_status_replicas{namespace=~"$namespace"}',
    'sum(kube_pod_status_phase{namespace=~"$namespace", phase="Succeeded"})',
    'sum(kube_job_status_active{namespace=~"$namespace"})',
    'sum(kube_pod_container_status_terminated{namespace=~"$namespace"})',
    'sum(kube_job_status_failed{namespace=~"$namespace"})',
    'sum(kube_pod_status_phase{namespace=~"$namespace", phase="Running"})',
    'sum(kube_pod_container_status_waiting{namespace=~"$namespace"})',
    'sum(kube_pod_status_phase{namespace=~"$namespace", phase="Failed"})',
    'sum(kube_deployment_status_replicas_updated{namespace=~"$namespace"})',
    'sum(kube_deployment_status_replicas{namespace=~"$namespace"})',
    # Kubernetes Namespace
    'sum(container_memory_usage_bytes{namespace=~"$namespace",'
    'pod=~".+",container=~".+"}) by (namespace)',
    'sum(rate(container_fs_reads_total{namespace=~"$namespace",'
    'pod=~".+",container=~".+"}[$rate_interval])) by (namespace)',
    'sum(rate(container_cpu_usage_seconds_total'
    '{namespace=~"$namespace",pod=~".+",container=~".+"}'
    '[$rate_interval])) by (namespace)',
    'sum(rate(container_fs_writes_bytes_total'
    '{namespace=~"$namespace",pod=~".+",container=~".+"}'
    '[$rate_interval])) by (namespace)',
    'sum(rate(container_fs_writes_total{namespace=~"$namespace",'
    'pod=~".+",container=~".+"}[$rate_interval])) by (namespace)',
    'sum(rate(container_fs_reads_bytes_total{namespace=~"$namespace",'
    'pod=~".+",container=~".+"}[$rate_interval])) by (namespace)',
    'sum(rate(container_network_receive_bytes_total'
    '{namespace=~"$namespace",pod=~".+",interface=~".+"}'
    '[$rate_interval])) by (namespace)',
    'sum(rate(container_network_transmit_bytes_total'
    '{namespace=~"$namespace",pod=~".+",interface=~".+"}'
    '[$rate_interval])) by (namespace)',
    # Kubernetes Pod
    'sum(container_memory_usage_bytes{pod=~"$pod",container=~".+"}) by (pod)',
    'sum(rate(container_fs_writes_bytes_total{pod=~"$pod",container=~".+"}'
    '[$rate_interval])) by (pod)',
    'sum(rate(container_cpu_usage_seconds_total{pod=~"$pod",container=~".+"}'
    '[$rate_interval])) by (pod)',
    'sum(rate(container_fs_reads_bytes_total{pod=~"$pod",container=~".+"}'
    '[$rate_interval])) by (pod)',
    'sum(rate(container_fs_reads_total{pod=~"$pod",container=~".+"}'
    '[$rate_interval])) by (pod)',
    'sum(rate(container_fs_writes_total{pod=~"$pod",container=~".+"}'
    '[$rate_interval])) by (pod)',
    'sum(rate(container_network_transmit_bytes_total'
    '{pod=~"$pod",interface=~".+"}[$rate_interval])) by (pod)',
    'sum(rate(container_network_receive_bytes_total'
    '{pod=~"$pod",interface=~".+"}[$rate_interval])) by (pod)',
    # Prometheus stats
    'rate(prometheus_http_request_duration_seconds_count'
    '{job="prometheus-server",handler=~"/api/v1/(query|query_range)",'
    'instance=~"$instance:[1-9][0-9]*"}[$rate_interval])'
]


def idfy_name(name):
    return name.lower().replace(" ", "-").replace("(", "").replace(")", "")


def query_dict_to_string(query_dict):
    return "\n\n".join(
        [panel + "\n" + query for panel, query in query_dict.items()])


def get_all_grafana_dashboards_names():
    # { Name in Grafana: name in Stacklight CRD }
    dashboards = {
        "Alertmanager": 'alertmanager',
        "ElasticSearch": 'elasticsearch',
        "Grafana": 'grafana',
        "Kubernetes Calico": 'calico',
        "Kubernetes Cluster": 'kubernetes-cluster',
        "Kubernetes Deployments": 'kubernetes-deployment',
        "Kubernetes Namespace": 'kubernetes-namespace',
        "Kubernetes Node": 'kubernetes-node',
        "Kubernetes Pod": 'kubernetes-pod',
        "MongoDB": 'mongodb',
        "NGINX": 'nginx',
        "Prometheus Performances": 'prometheus-performance',
        "Prometheus Stats": 'prometheus-stats',
        "Pushgateway": 'pushgateway',
        "Relay": 'relay',
        "System": 'node-exporter',
        # Ceph
        "Ceph Cluster": 'ceph-cluster',
        "Ceph Hosts Overview": 'ceph-hosts-overview',
        "Ceph OSD device details": 'ceph-osds-details',
        "Ceph OSD Overview": 'ceph-osds-overview',
        "Ceph Pools Overview": 'ceph-pool-overview',
        # Openstack
        "MySQL": 'mysql',
        "Memcached": 'memcached',
        "RabbitMQ": 'rabbitmq',
        "Cinder": 'cinder',
        "Glance": 'glance',
        "Heat": 'heat',
        "Keystone": 'keystone',
        "Neutron": 'neutron',
        "Nova Hypervisor Overview": 'nova-hypervisor',
        "Nova Instances": 'nova-instances',
        "Nova Overview": 'nova-overview',
        "Nova Utilization": 'nova-utilization',
        "Openstack Overview": 'openstack-overview',
        "Openstack Tenants": 'openstack-tenants',
        "Ironic": 'ironic'
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
def dashboard_name(request, k8s_api):
    dash_name, chart_dash_name = request.param
    grafana_chart = k8s_api.get_stacklight_chart('grafana')
    chart_dashboards = grafana_chart['values']['dashboards']['default'].keys()

    if chart_dash_name not in chart_dashboards:
        pytest.skip("Dashboard {} not found in Stacklight CRD".format(
            dash_name))

    return dash_name


@pytest.mark.dashboards
@pytest.mark.run(order=-2)
def test_grafana_dashboard_panel_queries(
        dashboard_name, grafana_client, prometheus_api):

    grafana_client.check_grafana_online()
    dashboard = grafana_client.get_dashboard(dashboard_name)

    assert grafana_client.is_dashboard_exists(dashboard_name), \
        "Dashboard {name} is not present".format(name=dashboard_name)

    dashboard_results = collections.defaultdict(list)

    for location, raw_query in dashboard.get_panel_queries().items():
        possible_templates = dashboard.get_all_templates_for_query(raw_query)

        panel = Panel(location, raw_query)

        for template in possible_templates:
            # W/A for Elasticsearch dashboard
            if ("$interval" in template.keys() and
                    template['$interval'] == '$__auto_interval'):
                template['$interval'] = '3m'
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
@pytest.mark.run(order=-2)
def test_panels_fixture(grafana_client):
    fixture_dashboards = get_all_grafana_dashboards_names().keys()

    dashboards = grafana_client.get_all_dashboards_names()
    missing_dashboards = set(dashboards).difference(set(fixture_dashboards))

    assert len(missing_dashboards) == 0, \
        ("Update test data fixture with the missing dashboards: "
         "{}".format(missing_dashboards))
