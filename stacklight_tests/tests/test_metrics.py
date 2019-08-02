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
