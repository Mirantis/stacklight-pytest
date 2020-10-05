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


@pytest.mark.run(order=1)
@pytest.mark.smoke
def test_stacklight_helmbundle(charts_statuses):
    err_msg = "These charts '{}' were not deployed properly."
    failed_charts = {}
    for name, info in charts_statuses.items():
        if not info['success'] or info['status'] != 'DEPLOYED':
            failed_charts[name] = {'success': info['success'],
                                   'status': info['status']}
    assert len(failed_charts) == 0, err_msg.format(failed_charts)


@pytest.mark.run(order=1)
@pytest.mark.smoke
def test_patroni_pods(k8s_api):
    label_selector = 'app=patroni'
    ret = k8s_api.list_pod_for_all_namespaces_by_label(
        label_selector=label_selector)
    pods = ret.items
    failed_pods = []
    for pod in pods:
        if pod.status.phase != 'Running':
            failed_pods.append(
                {'name': pod.metadata.name,
                 'node_name': pod.spec.node_name,
                 'namespace': pod.metadata.namespace,
                 'status': pod.status.phase}
            )
    assert len(failed_pods) == 0, \
        "These pods {} are not in the status 'Running'".format(failed_pods)


@pytest.mark.run(order=1)
@pytest.mark.smoke
def test_patroni_containers(k8s_api):
    label_selector = 'app=patroni'
    ret = k8s_api.list_pod_for_all_namespaces_by_label(
        label_selector=label_selector)
    pods = ret.items
    failed_containers = []
    for pod in pods:
        for c in pod.status.container_statuses:
            if c.state.running is None:
                failed_containers.append(
                    {'pod_name': pod.metadata.name,
                     'node_name': pod.spec.node_name,
                     'namespace': pod.metadata.namespace,
                     'container_info': c}
                )
    assert len(failed_containers) == 0, \
        "These containers {} are not in the proper state" \
        .format(failed_containers)


@pytest.mark.run(order=1)
@pytest.mark.smoke
def test_stacklight_pods_resources(k8s_api):
    def create_err_msg(by_requests, by_limits):
        msg = ''
        template = 'These containers {} have no resources {} for cpu ' \
                   'or(and) memory.\n'
        if len(by_requests) != 0:
            msg += template.format(by_requests, 'requests')
        if len(by_limits) != 0:
            msg += template.format(by_limits, 'limits')
        return msg

    def check_container(resources, failed_containers, skip_list_common,
                        skip_list_special):
        if check_skip(c.name, skip_list_common, skip_list_special):
            pass
        elif resources is None:
            add_container_to_failed(failed_containers, pod, c)
        else:
            check_partially_failed(failed_containers, resources)

    def add_container_to_failed(arr, pod, c):
        arr.append(
            {'pod_name': pod.metadata.name,
             'container_name': c.name,
             'resources_requests': c.resources.requests,
             'resources_limits': c.resources.limits}
        )

    def check_skip(name, common, special):
        if name in (common + special):
            return True
        else:
            return False

    def check_partially_failed(failed_containers, resources):
        if (resources.get('cpu') is None or
                resources.get('memory') is None):
            add_container_to_failed(failed_containers,
                                    pod, c)

    namespace = 'stacklight'
    ret = k8s_api.list_namespaced_pod(namespace)
    pods = ret.items
    skip_list = {'common': ['configmap-reload',
                            'elasticsearch-master-graceful-termination'
                            '-handler',
                            'grafana-sc-dashboard',
                            'prometheus-server-configmap-reload',
                            'prometheus-alertmanager-configmap-reload',
                            'dashboardimport', 'delete-logging-pvcs'],
                 'limits': ['netchecker-agent', 'netchecker-agent-hostnet',
                            'netchecker-server', 'iam-proxy', 'alerta',
                            'elasticsearch-exporter', 'grafana',
                            'blackbox-exporter',
                            'prometheus-kube-state-metrics',
                            'prometheus-libvirt-exporter',
                            'prometheus-node-exporter',
                            'prometheus-node-exporter',
                            'prometheus-pushgateway', 'metricbeat', 'metrics',
                            'prometheus-nginx-exporter'],
                 'requests': []
                 }
    failed_containers_by_requests = []
    failed_containers_by_limits = []
    for pod in pods:
        for c in pod.spec.containers:
            check_container(c.resources.requests,
                            failed_containers_by_requests,
                            skip_list['common'], skip_list['requests'])
            check_container(c.resources.limits,
                            failed_containers_by_limits,
                            skip_list['common'], skip_list['limits'])

    assert (len(failed_containers_by_requests) +
            len(failed_containers_by_limits)) == 0, \
        create_err_msg(failed_containers_by_requests,
                       failed_containers_by_limits)
