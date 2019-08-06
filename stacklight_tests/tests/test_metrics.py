import logging
import pytest

logger = logging.getLogger(__name__)


target_metrics = {
    "cpu": ['node_cpu_seconds_total', 'node_cpu_guest_seconds_total'],
    "mem": ['node_memory_MemFree_bytes', 'node_memory_Cached_bytes',
            'node_memory_Buffers_bytes', 'node_memory_MemTotal_bytes',
            'node_memory_Active_bytes', 'node_memory_MemAvailable_bytes',
            'node_memory_KernelStack_bytes'],
    "load": ['node_load1', 'node_load5', 'node_load15'],
    "disk": ['node_filesystem_free_bytes', 'node_filesystem_size_bytes',
             'node_filesystem_files_free', 'node_filesystem_files'],
    "swap": ['node_memory_SwapCached_bytes', 'node_memory_SwapFree_bytes',
             'node_memory_SwapTotal_bytes'],
    "process": ['process_cpu_seconds_total', 'process_max_fds',
                'process_open_fds', 'process_resident_memory_bytes',
                'process_start_time_seconds', 'process_virtual_memory_bytes',
                'process_virtual_memory_max_bytes'],
    "network": ['node_network_receive_errs_total',
                'node_network_transmit_errs_total',
                'node_network_receive_drop_total',
                'node_network_transmit_drop_total', 'node_network_up'],
    "time": ['node_timex_offset_seconds', 'node_timex_sync_status',
             'node_timex_status'],
    "calico": ['felix_int_dataplane_failures', 'felix_ipset_errors',
               'felix_iptables_save_errors', 'felix_iptables_restore_errors',
               'felix_int_dataplane_addr_msg_batch_size_sum',
               'felix_int_dataplane_addr_msg_batch_size_count',
               'felix_int_dataplane_iface_msg_batch_size_sum',
               'felix_int_dataplane_iface_msg_batch_size_count']
}


@pytest.mark.metrics
@pytest.mark.run(order=1)
@pytest.mark.parametrize("target,metrics", target_metrics.items(),
                         ids=target_metrics.keys())
def test_metrics(prometheus_api, nodes, target, metrics):
    nodenames = nodes.keys()
    for node in nodenames:
        for metric in metrics:
            q = ('{}{{node="{}"}}'.format(metric, node))
            logger.info('Checking metric {}'.format(q))
            msg = "Metric {} not found".format(q)
            output = prometheus_api.get_query(q)
            assert len(output) != 0, msg


@pytest.mark.metrics
@pytest.mark.run(order=1)
def test_daemonsets_metrics(prometheus_api, daemonsets):
    for ds in daemonsets.items():
        logger.info('Checking metrics for {} daemonset'.format(ds[0]))
        labels = '{{daemonset="{}", namespace="{}"}}'.format(
            ds[0], ds[1]['namespace'])
        q = 'kube_daemonset_updated_number_scheduled' + labels
        prometheus_api.check_metric_values(
            q, ds[1]['updated_number_scheduled'])
        q = 'kube_daemonset_created' + labels
        logger.info('Checking {} metric'.format(q))
        assert len(prometheus_api.get_query(q)) != 0
        for status in ds[1]['status'].items():
            query = 'kube_daemonset_status_{}'.format(status[0]) + labels
            prometheus_api.check_metric_values(query, status[1])


@pytest.mark.metrics
@pytest.mark.run(order=1)
def test_deployments_metrics(prometheus_api, deployments):
    for dm in deployments.items():
        logger.info('Checking metrics for {} daemonset'.format(dm[0]))
        labels = '{{deployment="{}", namespace="{}"}}'.format(
            dm[0], dm[1]['namespace'])
        q = 'kube_deployment_created' + labels
        logger.info('Checking {} metric'.format(q))
        assert len(prometheus_api.get_query(q)) != 0
        for status in dm[1]['status'].items():
            query = 'kube_deployment_status_{}'.format(status[0]) + labels
            prometheus_api.check_metric_values(query, status[1])
        for spec in dm[1]['spec'].items():
            query = 'kube_deployment_spec_{}'.format(spec[0]) + labels
            prometheus_api.check_metric_values(query, spec[1])


@pytest.mark.metrics
@pytest.mark.run(order=1)
def test_replicasets_metrics(prometheus_api, replicasets):
    for rs in replicasets.items():
        logger.info('Checking metrics for {} daemonset'.format(rs[0]))
        labels = '{{replicaset="{}", namespace="{}"}}'.format(
            rs[0], rs[1]['namespace'])
        q = 'kube_replicaset_created' + labels
        logger.info('Checking {} metric'.format(q))
        assert len(prometheus_api.get_query(q)) != 0
        logger.info('Checking {} metric'.format(q))
        q = 'kube_replicaset_spec_replicas' + labels
        prometheus_api.check_metric_values(
            q, rs[1]['spec_replicas'])
        for status in rs[1]['status'].items():
            query = 'kube_replicaset_status_{}'.format(status[0]) + labels
            prometheus_api.check_metric_values(query, status[1])


@pytest.mark.metrics
@pytest.mark.run(order=1)
def test_statefulsets_metrics(prometheus_api, statefulsets):
    for sfs in statefulsets.items():
        logger.info('Checking metrics for {} daemonset'.format(sfs[0]))
        labels = 'statefulset="{}", namespace="{}"'.format(
            sfs[0], sfs[1]['namespace'])
        q = 'kube_statefulset_created{' + labels + '}'
        logger.info('Checking {} metric'.format(q))
        assert len(prometheus_api.get_query(q)) != 0
        q = 'kube_statefulset_replicas{' + labels + '}'
        prometheus_api.check_metric_values(
            q, sfs[1]['spec_replicas'])
        q = ('kube_statefulset_status_current_revision{' + labels +
             ',revision="{}"'.format(sfs[1]['current_revision']) + '}')
        prometheus_api.check_metric_values(q, 1)
        q = ('kube_statefulset_status_update_revision{' + labels +
             ',revision="{}"'.format(sfs[1]['update_revision']) + '}')
        prometheus_api.check_metric_values(q, 1)
        for status in sfs[1]['status'].items():
            query = ('kube_statefulset_status_{}'.format(status[0]) +
                     '{' + labels + '}')
            prometheus_api.check_metric_values(query, status[1])
