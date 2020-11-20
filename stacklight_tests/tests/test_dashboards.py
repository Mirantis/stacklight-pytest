import collections
import pytest

from stacklight_tests import utils

ignored_queries_for_fail = [
    # Elasticsearch
    'count(elasticsearch_breakers_tripped{cluster="$cluster",name=~"$name"}'
    '>0)',
    # Kubernetes Cluster
    'sum(kube_node_status_condition{condition="OutOfDisk", node=~"$node", '
    'status="true"})',
    'sum(kube_job_status_succeeded{namespace=~"$namespace"})',
    'sum(kube_job_status_active{namespace=~"$namespace"})',
    'sum(kube_job_status_failed{namespace=~"$namespace"})',
    # MKE Cluster
    'count(count(ucp_engine_container_cpu_total_time_nanoseconds{stack!=""}) '
    'by (stack))',
    'count(ucp_engine_container_health{name=~"dtr-api-.*"})',
    'count(ucp_engine_containers{manager="false"}) - '
    '(count(ucp_engine_container_health{name=~"dtr-api-.*"}) or vector(0))',
    'count(ucp_engine_containers{manager="false"})',
    # Openstack Overview
    'max(openstack_nova_aggregate_disk - '
    'openstack_nova_aggregate_disk_available) by (aggregate)',
    'max(openstack_nova_aggregate_ram - '
    'openstack_nova_aggregate_free_ram) by (aggregate)',
    'max(openstack_nova_aggregate_used_vcpus) by (aggregate)',
    'sum(rate(nginx_ingress_controller_request_duration_seconds_bucket'
    '{status=~"5.."}[$rate_interval])) by (service)',
    # Neutron
    'max(count(openstack_neutron_agent_state{binary="neutron-metadata-agent"} '
    '== 0 and openstack_neutron_agent_status{binary="neutron-metadata-agent"} '
    '== 0) by (instance))',
    'max(count(openstack_neutron_agent_state{binary="neutron-metadata-agent"} '
    '== 0 and openstack_neutron_agent_status{binary="neutron-metadata-agent"} '
    '== 1) by (instance))',
    'max(count(openstack_neutron_agent_state{binary="neutron-metadata-agent"} '
    '== 1 and openstack_neutron_agent_status{binary="neutron-metadata-agent"} '
    '== 0) by (instance))',
    'max(count(openstack_neutron_agent_state{binary="neutron-openvswitch-'
    'agent"} == 1 and openstack_neutron_agent_status{binary="neutron-'
    'openvswitch-agent"} == 0) by (instance))',
    'max(count(openstack_neutron_agent_state{binary="neutron-openvswitch-'
    'agent"} == 0 and openstack_neutron_agent_status{binary="neutron-'
    'openvswitch-agent"} == 1) by (instance))',
    'max(count(openstack_neutron_agent_state{binary="neutron-openvswitch-'
    'agent"} == 0 and openstack_neutron_agent_status{binary="neutron-'
    'openvswitch-agent"} == 0) by (instance))',
    'max(count(openstack_neutron_agent_state{binary="neutron-l3-agent"} '
    '== 1 and openstack_neutron_agent_status{binary="neutron-l3-agent"} '
    '== 0) by (instance))',
    'max(count(openstack_neutron_agent_state{binary="neutron-l3-agent"} '
    '== 0 and openstack_neutron_agent_status{binary="neutron-l3-agent"} '
    '== 1) by (instance))',
    'max(count(openstack_neutron_agent_state{binary="neutron-l3-agent"} '
    '== 0 and openstack_neutron_agent_status{binary="neutron-l3-agent"} '
    '== 0) by (instance))',
    'max(count(openstack_neutron_agent_state{binary="neutron-dhcp-agent"} '
    '== 0 and openstack_neutron_agent_status{binary="neutron-dhcp-agent"} '
    '== 0) by (instance))',
    'max(count(openstack_neutron_agent_state{binary="neutron-dhcp-agent"} '
    '== 0 and openstack_neutron_agent_status{binary="neutron-dhcp-agent"} '
    '== 1) by (instance))',
    'max(count(openstack_neutron_agent_state{binary="neutron-dhcp-agent"} '
    '== 1 and openstack_neutron_agent_status{binary="neutron-dhcp-agent"} '
    '== 0) by (instance))',
    # Nova Overview
    'max(count(openstack_nova_service_state{service="nova-compute"} == 0 and '
    'openstack_nova_service_status{service="nova-compute"} == 0) '
    'by (instance))',
    'max(count(openstack_nova_service_state{service="nova-compute"} == 0 and '
    'openstack_nova_service_status{service="nova-compute"} == 1) '
    'by (instance))',
    'max(count(openstack_nova_service_state{service="nova-compute"} == 1 and '
    'openstack_nova_service_status{service="nova-compute"} == 0) '
    'by (instance))',
    'max(count(openstack_nova_service_state{binary="nova-scheduler"} == 0 and '
    'openstack_nova_service_status{binary="nova-scheduler"} == 1) '
    'by (instance))',
    'max(count(openstack_nova_service_state{binary="nova-scheduler"} == 1 and '
    'openstack_nova_service_status{binary="nova-scheduler"} == 0) '
    'by (instance))',
    'max(count(openstack_nova_service_state{binary="nova-scheduler"} == 0 and '
    'openstack_nova_service_status{binary="nova-scheduler"} == 0) '
    'by (instance))',
    'max(count(openstack_nova_service_state{binary="nova-conductor"} == 0 '
    'and openstack_nova_service_status{binary="nova-conductor"} == 1) '
    'by (instance))',
    'max(count(openstack_nova_service_state{binary="nova-conductor"} == 1 '
    'and openstack_nova_service_status{binary="nova-conductor"} == 0) '
    'by (instance))',
    'max(count(openstack_nova_service_state{binary="nova-conductor"} == 0 '
    'and openstack_nova_service_status{binary="nova-conductor"} == 0) '
    'by (instance))',
    'histogram_quantile(0.99, sum(rate'
    '(nginx_ingress_controller_request_duration_seconds_bucket'
    '{ingress=~"nova-(cluster|namespace)-fqdn"}[$rate_interval])) '
    'by (le,ingress,method))',
    'round(sum(irate(nginx_ingress_controller_requests'
    '{ingress=~"nova-(cluster|namespace)-fqdn"}[$rate_interval])) '
    'by (ingress, status), 0.001)',
    # Nova Utilization
    'max(sum(openstack_nova_ram and on (hostname) (openstack_nova_service_'
    'status == 0 and openstack_nova_service_state == 0)) by (instance))',
    'max(sum(openstack_nova_vcpus and on (hostname) (openstack_nova_service_'
    'status == 0 and openstack_nova_service_state == 0)) by (instance))',
    'max(sum(openstack_nova_vcpus and on (hostname) (openstack_nova_service_'
    'status == 0 and openstack_nova_service_state == 1)) by (instance))',
    'max(sum(openstack_nova_vcpus and on (hostname) (openstack_nova_service_'
    'status == 1 and openstack_nova_service_state == 0)) by (instance))',
    'max(sum(openstack_nova_ram and on (hostname) (openstack_nova_service_'
    'status == 1 and openstack_nova_service_state == 0)) by (instance))',
    'max(sum(openstack_nova_ram and on (hostname) (openstack_nova_service_'
    'status == 0 and openstack_nova_service_state == 1)) by (instance))',
    'max(sum(openstack_nova_disk and on (hostname) (openstack_nova_service_'
    'status == 0 and openstack_nova_service_state == 1)) by (instance))',
    'max(sum(openstack_nova_disk and on (hostname) (openstack_nova_service_'
    'status == 1 and openstack_nova_service_state == 0)) by (instance))',
    'max(sum(openstack_nova_disk and on (hostname) (openstack_nova_service_'
    'status == 0 and openstack_nova_service_state == 0)) by (instance))',
    # Cinder
    'max(count(openstack_cinder_service_state{binary="cinder-volume"} == 0 '
    'and openstack_cinder_service_status{binary="cinder-volume"} == 1) '
    'by (instance))',
    'max(count(openstack_cinder_service_state{binary="cinder-volume"} == 0 '
    'and openstack_cinder_service_status{binary="cinder-volume"} == 0) '
    'by (instance))',
    'max(count(openstack_cinder_service_state{binary="cinder-scheduler"} == 0 '
    'and openstack_cinder_service_status{binary="cinder-scheduler"} == 1) '
    'by (instance))',
    'max(count(openstack_cinder_service_state{binary="cinder-scheduler"} == 0 '
    'and openstack_cinder_service_status{binary="cinder-scheduler"} == 0) '
    'by (instance))',
    'max(count(openstack_cinder_service_state{binary="cinder-scheduler"} == 1 '
    'and openstack_cinder_service_status{binary="cinder-scheduler"} == 0) '
    'by (instance))',
    'max(count(openstack_cinder_service_state{binary="cinder-volume"} == 1 '
    'and openstack_cinder_service_status{binary="cinder-volume"} == 0) '
    'by (instance))',
    'histogram_quantile(0.99, '
    'sum(rate(nginx_ingress_controller_request_duration_seconds_bucket'
    '{ingress=~"cinder-(cluster|namespace)-fqdn"}[$rate_interval])) '
    'by (le,ingress,method))',
    'round(sum(irate(nginx_ingress_controller_requests'
    '{ingress=~"cinder-(cluster|namespace)-fqdn"}[$rate_interval])) '
    'by (ingress, status), 0.001)',
    # Heat
    'round(sum(irate(nginx_ingress_controller_requests'
    '{ingress=~"heat-(cluster|namespace)-fqdn"}[$rate_interval])) '
    'by (ingress, status), 0.001)',
    'histogram_quantile(0.99, '
    'sum(rate(nginx_ingress_controller_request_duration_seconds_bucket'
    '{ingress=~"heat-(cluster|namespace)-fqdn"}[$rate_interval])) '
    'by (le,ingress,method))',
    # Glance
    'histogram_quantile(0.99, '
    'sum(rate(nginx_ingress_controller_request_duration_seconds_bucket'
    '{ingress=~"glance-(cluster|namespace)-fqdn"}[$rate_interval])) '
    'by (le,ingress,method))',
    'round(sum(irate(nginx_ingress_controller_requests'
    '{ingress=~"glance-(cluster|namespace)-fqdn"}[$rate_interval])) '
    'by (ingress, status), 0.001)',
    # Keystone
    'histogram_quantile(0.99, '
    'sum(rate(nginx_ingress_controller_request_duration_seconds_bucket'
    '{ingress=~"keystone-(cluster|namespace)-fqdn"}[$rate_interval])) '
    'by (le,ingress,method))',
    'round(sum(irate(nginx_ingress_controller_requests'
    '{ingress=~"keystone-(cluster|namespace)-fqdn"}[$rate_interval])) '
    'by (ingress, status), 0.001)'
]


ignored_queries_for_partial_fail = [
    # Kubernetes Cluster
    'sum(kube_pod_status_phase{namespace=~"$namespace", phase="Unknown"})',
    'sum(kube_deployment_status_replicas_unavailable'
    '{namespace=~"$namespace"})',
    'sum(kube_job_status_succeeded{namespace=~"$namespace"})',
    'sum(kube_pod_status_phase{namespace=~"$namespace", phase="Pending"})',
    'sum(kube_pod_container_status_running{namespace=~"$namespace"})',
    'sum(kube_pod_status_phase{namespace=~"$namespace", phase="Succeeded"})',
    'sum(kube_job_status_active{namespace=~"$namespace"})',
    'sum(kube_pod_container_status_terminated{namespace=~"$namespace"})',
    'sum(kube_job_status_failed{namespace=~"$namespace"})',
    'sum(kube_pod_status_phase{namespace=~"$namespace", phase="Running"})',
    'sum(kube_pod_container_status_waiting{namespace=~"$namespace"})',
    'sum(kube_pod_status_phase{namespace=~"$namespace", phase="Failed"})',
    'sum(kube_deployment_status_replicas{namespace=~"$namespace"})',
    'sum(delta(kube_pod_container_status_restarts_total{'
    'namespace=~"$namespace"}[30m]))',
    # Kubernetes Namespace
    'sum(container_memory_usage_bytes{namespace=~"$namespace",'
    'pod=~".+",container=~".+"}) by (namespace)',
    'sum(rate(container_cpu_usage_seconds_total'
    '{namespace=~"$namespace",pod=~".+",container=~".+"}'
    '[$rate_interval])) by (namespace)',
    'sum(rate(container_fs_writes_bytes_total'
    '{namespace=~"$namespace",pod=~".+",container=~".+"}'
    '[$rate_interval])) by (namespace)',
    'sum(rate(container_fs_reads_bytes_total{namespace=~"$namespace",'
    'pod=~".+",container=~".+"}[$rate_interval])) by (namespace)',
    'sum(rate(container_network_receive_bytes_total'
    '{namespace=~"$namespace",pod=~".+",interface=~".+"}'
    '[$rate_interval])) by (namespace)',
    'sum(rate(container_network_transmit_bytes_total'
    '{namespace=~"$namespace",pod=~".+",interface=~".+"}'
    '[$rate_interval])) by (namespace)',
    'sum(rate(container_fs_reads_total{namespace=~"$namespace"}'
    '[$rate_interval])) by (namespace)',
    'sum(rate(container_fs_writes_total{namespace=~"$namespace"}'
    '[$rate_interval])) by (namespace)',
    # Kubernetes Pod
    'sum(rate(container_fs_reads_total{pod=~"$pod"}'
    '[$rate_interval])) by (pod)',
    'sum(rate(container_fs_writes_bytes_total{pod=~"$pod"}'
    '[$rate_interval])) by (pod)',
    'sum(rate(container_fs_reads_bytes_total{pod=~"$pod"}'
    '[$rate_interval])) by (pod)',
    'sum(rate(container_fs_writes_total{pod=~"$pod"}'
    '[$rate_interval])) by (pod)',
    # UCP Containers
    'sum(rate(ucp_engine_container_network_tx_bytes_total'
    '{instance=~"$hostname",name=~"$name"}[$rate_interval])) '
    'by (instance,name)',
    'sum(rate(ucp_engine_container_network_rx_bytes_total'
    '{instance=~"$hostname",name=~"$name"}[$rate_interval])) '
    'by (instance,name)'
]

dashboards_openstack = {
    "MySQL": 'mysql',
    "Memcached": 'memcached',
    "RabbitMQ": 'rabbitmq',
    "Cinder": 'cinder',
    "Glance": 'glance',
    "Heat": 'heat',
    "Keystone": 'keystone',
    "KPI Provisioning": 'kpi-provisioning',
    "KPI Downtime": 'kpi-downtime',
    "Neutron": 'neutron',
    "NGINX Ingress controller": 'nginx-ingress-controller',
    "Nova Availability Zones": 'nova-az',
    "Nova Hypervisor Overview": 'nova-hypervisor',
    "Nova Overview": 'nova-overview',
    "Nova Instances": 'nova-top-instances',
    "Nova Tenants": 'nova-top-tenants',
    "Nova Users": 'nova-top-users',
    "Nova Utilization": 'nova-utilization',
    "Openstack Overview": 'openstack-overview',
    "Ironic": 'ironic-openstack'
}

dashboards_no_openstack = {
    "Alertmanager": 'alertmanager',
    "Clusters Overview": 'telemeter-clusters-overview',
    "ElasticSearch": 'elasticsearch',
    "Grafana": 'grafana',
    "Kubernetes Calico": 'calico',
    "Kubernetes Cluster": 'kubernetes-cluster',
    "Kubernetes Deployments": 'kubernetes-deployment',
    "Kubernetes Namespaces": 'kubernetes-namespace',
    "Kubernetes Nodes": 'kubernetes-node',
    "Kubernetes Pods": 'kubernetes-pod',
    # MKE
    "MKE Containers": 'mke-containers',
    "MKE Cluster": 'mke-cluster',
    "NGINX": 'nginx',
    "PostgreSQL": 'postgresql',
    "Prometheus": 'prometheus',
    "Pushgateway": 'pushgateway',
    "Relay": 'relay',
    "System": 'node-exporter',
    "Telemeter Server": 'telemeter-server',
    # Ceph
    "Ceph Cluster": 'ceph-cluster',
    "Ceph Nodes": 'ceph-nodes',
    "Ceph OSD": 'ceph-osds',
    "Ceph Pools": 'ceph-pools',
    # Ironic
    "Ironic BM": 'ironic'
}

dashboards_openstack_values = {
    dashboards_openstack[k] for k in dashboards_openstack
}


def idfy_name(name):
    return name.lower().replace(" ", "-").replace("(", "").replace(")", "")


def query_dict_to_string(query_dict):
    return "\n\n".join(
        [panel + "\n" + query for panel, query in query_dict.items()])


def get_all_grafana_dashboards_names():
    # { Name in Grafana: name in Stacklight CR}
    dashboards = dashboards_no_openstack.copy()
    dashboards.update(dashboards_openstack)

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
def dashboard_name(request, k8s_api, openstack_cr_exists):
    dash_name, chart_dash_name = request.param
    grafana_chart = k8s_api.get_stacklight_chart('grafana')
    chart_dashboards = grafana_chart['values']['dashboards']['default'].keys()

    if chart_dash_name not in chart_dashboards:
        pytest.skip("Dashboard {} not found in Stacklight CRD".format(
            dash_name))
    if chart_dash_name in dashboards_openstack_values:
        utils.skip_openstack_test(openstack_cr_exists)
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
            if ("$interval" in template.keys() and
                    template['$interval'] == '$__auto_interval_interval'):
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
