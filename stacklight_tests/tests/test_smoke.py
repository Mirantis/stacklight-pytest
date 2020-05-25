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
    err_msg = "Chart '{}' was not deployed properly.Chart info: {}"
    for name, info in charts_statuses.items():
        assert info['success'], \
            err_msg.format(name, info)


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
