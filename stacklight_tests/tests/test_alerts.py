import logging
import pytest

from stacklight_tests import settings

logger = logging.getLogger(__name__)


alert_skip_list = ['SystemDiskErrorsTooHigh']


alert_metrics = {
    "AlertmanagerAlertsInvalidWarning": [
        'increase(alertmanager_alerts_invalid_total[2m]) == 0'
    ],
    "AlertmanagerFailedReload": [
        'alertmanager_config_last_reload_successful != 0'
    ],
    "AlertmanagerMembersInconsistent": [
        'alertmanager_cluster_members == on(service) group_left() '
        'count by(service) (alertmanager_cluster_members)'
    ],
    "AlertmanagerNotificationFailureWarning": [
        'increase(alertmanager_notifications_failed_total[2m]) == 0'
    ],
    "CalicoDatapaneIfaceMsgBatchSizeHigh": [
        'felix_int_dataplane_iface_msg_batch_size_sum',
        'felix_int_dataplane_iface_msg_batch_size_count',
        '(felix_int_dataplane_iface_msg_batch_size_sum / '
        'felix_int_dataplane_iface_msg_batch_size_count) <= 5'
    ],
    "CalicoDataplaneAddressMsgBatchSizeHigh": [
        'felix_int_dataplane_addr_msg_batch_size_sum',
        'felix_int_dataplane_addr_msg_batch_size_count',
        '(felix_int_dataplane_addr_msg_batch_size_sum / '
        'felix_int_dataplane_addr_msg_batch_size_count) <= 5'
    ],
    "CalicoDataplaneFailuresHigh": [
        'felix_int_dataplane_failures',
        'increase(felix_int_dataplane_failures[1h]) <= 5'
    ],
    "CalicoIPsetErrorsHigh": [
        'felix_ipset_errors', 'increase(felix_ipset_errors[1h]) <= 5'
    ],
    "CalicoIptablesRestoreErrorsHigh": [
        'felix_iptables_restore_errors',
        'increase(felix_iptables_restore_errors[1h]) <= 5'
    ],
    "CalicoIptablesSaveErrorsHigh": [
        'felix_iptables_save_errors',
        'increase(felix_iptables_save_errors[1h]) <= 5'
    ],
    "ClockSkewDetected": [
        'abs(node_timex_offset_seconds{job="node-exporter"}) <= 0.03'
    ],
    "ContainerScrapeError": ['container_scrape_error == 0'],
    "CPUThrottlingHigh": [
        '100 * sum by(container, pod, namespace) '
        '(increase(container_cpu_cfs_throttled_periods_total'
        '{container!=""}[5m])) / sum by(container, pod, '
        'namespace) (increase(container_cpu_cfs_periods_total[5m])) <= 25'
    ],
    "ElasticClusterRed": [
        'elasticsearch_cluster_health_status{color="red"} != 1'
    ],
    "ElasticClusterYellow": [
        'elasticsearch_cluster_health_status{color="yellow"} != 1'
    ],
    "ElasticHeapUsageTooHigh": [
        '(elasticsearch_jvm_memory_used_bytes{area="heap"} / '
        'elasticsearch_jvm_memory_max_bytes{area="heap"}) * 100 <= 90'
    ],
    "ElasticHeapUsageWarning": [
        '(elasticsearch_jvm_memory_used_bytes{area="heap"} / '
        'elasticsearch_jvm_memory_max_bytes{area="heap"}) * 100 <= 80'
    ],
    "ElasticNoNewDocuments": [
        'rate(elasticsearch_indices_docs[10m]) >= 1'
    ],
    "KubeAPIErrorsHighCritical": [
        'sum(rate(apiserver_request_count{job="apiserver"}[5m]))'
    ],
    "KubeAPIErrorsHighWarning": [
        'sum(rate(apiserver_request_count{job="apiserver"}[5m]))'
    ],
    "KubeAPILatencyHighCritical": [
        'cluster_quantile:apiserver_request_latencies:histogram_quantile'
        '{job="apiserver",quantile="0.99",subresource!="log",'
        'verb!~"^(?:LIST|WATCH|WATCHLIST|PROXY|CONNECT)$"} <= 4'
    ],
    "KubeAPILatencyHighWarning": [
        'cluster_quantile:apiserver_request_latencies:histogram_quantile'
        '{job="apiserver",quantile="0.99",subresource!="log",'
        'verb!~"^(?:LIST|WATCH|WATCHLIST|PROXY|CONNECT)$"} <= 1'
    ],
    "KubeAPIResourceErrorsHighCritical": [
        'sum by(resource, subresource, verb) (rate(apiserver_request_count'
        '{job="apiserver"}[5m]))'
    ],
    "KubeAPIResourceErrorsHighWarning": [
        'sum by(resource, subresource, verb) (rate(apiserver_request_count'
        '{job="apiserver"}[5m]))'
    ],
    "KubeCPUOvercommitNamespaces": [
        'sum(kube_resourcequota'
        '{job="kube-state-metrics",resource="cpu",type="hard"}) '
        '/ sum(node:node_num_cpu:sum) <= 1.5'
    ],
    "KubeCPUOvercommitPods": [
        'sum('
        'namespace_name:kube_pod_container_resource_requests_cpu_cores:sum) / '
        'sum(node:node_num_cpu:sum) <= '
        '(count(node:node_num_cpu:sum) - 1) / count(node:node_num_cpu:sum)'
    ],
    "KubeClientCertificateExpirationInOneDay": [
        'apiserver_client_certificate_expiration_seconds_count'
        '{job="apiserver"} == 0 '
        'or histogram_quantile(0.01, sum by(job, le) '
        '(rate(apiserver_client_certificate_expiration_seconds_bucket'
        '{job="apiserver"}[5m]))) >= 86400'
    ],
    "KubeClientCertificateExpirationInSevenDays": [
        'apiserver_client_certificate_expiration_seconds_count'
        '{job="apiserver"} == 0 '
        'or histogram_quantile(0.01, sum by(job, le) '
        '(rate(apiserver_client_certificate_expiration_seconds_bucket'
        '{job="apiserver"}[5m]))) >= 604800'
    ],
    "KubeClientErrors": [
        '(sum by(instance, job) '
        '(rate(rest_client_requests_total{code=~"5.."}[5m])) / '
        'sum by(instance, job) '
        '(rate(rest_client_requests_total[5m]))) * 100 <= 1'
    ],
    "KubeCronJobRunning": [
        'time() - '
        'kube_cronjob_next_schedule_time{job="kube-state-metrics"} <= 3600'
    ],
    "KubeDaemonSetMisScheduled": [
        'kube_daemonset_status_number_misscheduled'
        '{job="kube-state-metrics"} == 0'
    ],
    "KubeDaemonSetNotScheduled": [
        'kube_daemonset_status_desired_number_scheduled'
        '{job="kube-state-metrics"} - '
        'kube_daemonset_status_current_number_scheduled'
        '{job="kube-state-metrics"} <= 0'
    ],
    "KubeDaemonSetRolloutStuck": [
        'kube_daemonset_status_number_ready{job="kube-state-metrics"} / '
        'kube_daemonset_status_desired_number_scheduled'
        '{job="kube-state-metrics"} * 100 >= 100'
    ],
    "KubeDeploymentGenerationMismatch": [
        'kube_deployment_status_observed_generation{job="kube-state-metrics"} '
        '== kube_deployment_metadata_generation{job="kube-state-metrics"}'
    ],
    "KubeDeploymentReplicasMismatch": [
        'kube_deployment_spec_replicas{job="kube-state-metrics"} == '
        'kube_deployment_status_replicas_available{job="kube-state-metrics"}'
    ],
    "KubeJobCompletion": [
        'absent(kube_job_spec_completions{job="kube-state-metrics"}) or '
        'absent(kube_job_status_succeeded{job="kube-state-metrics"}) or '
        'kube_job_spec_completions{job="kube-state-metrics"} - '
        'kube_job_status_succeeded{job="kube-state-metrics"} <= 0'
    ],
    "KubeJobFailed": [
        'kube_job_status_failed{job="kube-state-metrics"} == 0 or '
        'absent(kube_job_status_failed{job="kube-state-metrics"})'
    ],
    "KubeMemOvercommitNamespaces": [
        'sum(kube_resourcequota{job="kube-state-metrics",'
        'resource="memory",type="hard"}) '
        '/ sum(node_memory_MemTotal_bytes{job="node-exporter"}) <= 1.5'
    ],
    "KubeMemOvercommitPods": [
        'sum(namespace_name:'
        'kube_pod_container_resource_requests_memory_bytes:sum) / '
        'sum(node_memory_MemTotal_bytes) <= '
        '(count(node:node_num_cpu:sum) - 1) / count(node:node_num_cpu:sum)'
    ],
    "KubeNodeNotReady": [
        'kube_node_status_condition'
        '{condition="Ready",job="kube-state-metrics",status="true"} != 0'
    ],
    "KubePersistentVolumeErrors": [
        'kube_persistentvolume_status_phase'
        '{job="kube-state-metrics",phase=~"Failed|Pending"} <= 0'
    ],
    "KubePersistentVolumeFullInFourDays": [
        '100 * (kubelet_volume_stats_available_bytes{job="kubelet"} / '
        'kubelet_volume_stats_capacity_bytes{job="kubelet"}) >= 15 or '
        'predict_linear(kubelet_volume_stats_available_bytes{job="kubelet"}'
        '[12h], 4 * 24 * 3600) >= 0'
    ],
    "KubePersistentVolumeUsageCritical": [
        '100 * kubelet_volume_stats_available_bytes{job="kubelet"} / '
        'kubelet_volume_stats_capacity_bytes{job="kubelet"} >= 3'
    ],
    "KubePodCrashLooping": [
        'rate(kube_pod_container_status_restarts_total'
        '{job="kube-state-metrics"}[15m]) * 60 * 5 <= 0'
    ],
    "KubePodNotReady": [
        'sum by(namespace, pod) (kube_pod_status_phase'
        '{job="kube-state-metrics",phase=~"Pending|Unknown"}) <= 0'
    ],
    "KubeQuotaExceeded": [
        '100 * kube_resourcequota{job="kube-state-metrics",type="used"} / '
        'ignoring(instance, job, type) '
        '(kube_resourcequota{job="kube-state-metrics",type="hard"} > 0) <= 90'
    ],
    "KubeStatefulSetGenerationMismatch": [
        'kube_statefulset_status_observed_generation{job="kube-state-metrics"}'
        ' == kube_statefulset_metadata_generation{job="kube-state-metrics"}'
    ],
    "KubeStatefulSetReplicasMismatch": [
        'kube_statefulset_status_replicas_ready{job="kube-state-metrics"} == '
        'kube_statefulset_status_replicas{job="kube-state-metrics"}'
    ],
    "KubeStatefulSetUpdateNotRolledOut": [
        'max without(revision) '
        '(kube_statefulset_status_update_revision{job="kube-state-metrics"}) '
        '* (kube_statefulset_replicas{job="kube-state-metrics"} == '
        'kube_statefulset_status_replicas_updated{job="kube-state-metrics"})'
    ],
    "KubeVersionMismatch": [
        'count(count by(gitVersion) '
        '(label_replace(kubernetes_build_info{job!="kube-dns"}, '
        '"gitVersion", "$1", "gitVersion", "(v[0-9]*.[0-9]*.[0-9]*).*"))) <= 1'
    ],
    "KubeletTooManyPods": [
        'kubelet_running_pod_count{job="kubelet"} <= 110 * 0.9'
    ],
    "MongodbConnectionsTooMany": [
        'mongodb_connections{state="current"} <= 500'
    ],
    "MongodbCursorTimeouts": [
        'increase(mongodb_mongod_metrics_cursor_timed_out_total[10m]) <= 100'
    ],
    "MongodbCursorsOpenTooMany": [
        'absent(mongodb_mongod_metrics_cursor_open{state="total_open"}) or '
        'mongodb_mongod_metrics_cursor_open{state="total_open"} <= 10000'
    ],
    "MongodbMemoryUsageWarning": [
        'sum by(pod) (mongodb_memory{type="virtual"}) < 0.8 * sum by(pod) '
        '(container_memory_max_usage_bytes{container="mongodb"})'
    ],
    "NginxDroppedIncomingConnections": [
        'irate(nginx_connections_accepted[5m]) - '
        'irate(nginx_connections_handled[5m]) <= 0'
    ],
    "NginxServiceDown": ['nginx_up == 1'],
    "NodeDown": [
        'up{job="kubelet"} != 0 or on(node) kube_node_status_condition'
        '{condition="Ready",job="kube-state-metrics",status="true"} != 0'
    ],
    "NodeNetworkInterfaceFlapping": [
        'changes(node_network_up{device!~"veth.+",job="node-exporter"}[2m]) '
        '<= 2'
    ],
    "NumberOfInitializingShards": [
        'elasticsearch_cluster_health_initializing_shards <= 0'
    ],
    "NumberOfPendingTasks": [
        'elasticsearch_cluster_health_number_of_pending_tasks <= 0'
    ],
    "NumberOfRelocationShards": [
        'elasticsearch_cluster_health_relocating_shards <= 0'
    ],
    "NumberOfUnassignedShards": [
        'elasticsearch_cluster_health_unassigned_shards <= 0'
    ],
    "PrometheusConfigReloadFailed": [
        'prometheus_config_last_reload_successful != 0'
    ],
    "PrometheusErrorSendingAlertsCritical": [
        'prometheus_notifications_errors_total',
        'prometheus_notifications_sent_total'
    ],
    "PrometheusErrorSendingAlertsWarning": [
        'prometheus_notifications_errors_total',
        'prometheus_notifications_sent_total'
    ],
    "PrometheusNotConnectedToAlertmanagers": [
        'prometheus_notifications_alertmanagers_discovered >= 1'
    ],
    "PrometheusNotIngestingSamples": [
        'rate(prometheus_tsdb_head_samples_appended_total[5m]) > 0'
    ],
    "PrometheusNotificationQueueRunningFull": [
        'predict_linear(prometheus_notifications_queue_length[5m], 60 * 30) '
        '<= prometheus_notifications_queue_capacity'
    ],
    "PrometheusRuleEvaluationsFailed": [
        'rate(prometheus_rule_evaluation_failures_total[5m]) <= 0'
    ],
    "PrometheusTSDBCompactionsFailing": [
        'increase(prometheus_tsdb_compactions_failed_total[2h]) <= 0'
    ],
    "PrometheusTSDBReloadsFailing": [
        'increase(prometheus_tsdb_reloads_failures_total[2h]) <= 0'
    ],
    "PrometheusTSDBWALCorruptions": [
        'prometheus_tsdb_wal_corruptions_total <= 0',
    ],
    "PrometheusTargetScrapesDuplicate": [
        'increase'
        '(prometheus_target_scrapes_sample_duplicate_timestamp_total[5m]) <= 0'
    ],
    "SystemCpuFullWarning": [
        '100 - (avg by(instance) '
        '(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) <= 90'
    ],
    "SystemDiskErrorsTooHigh": ['increase(hdd_errors_total[1m]) <= 0'],
    "SystemDiskFullMajor": [
        '(1 - node_filesystem_free_bytes / node_filesystem_size_bytes * 100)'
        ' < 95'
    ],
    "SystemDiskFullWarning": [
        '(1 - node_filesystem_free_bytes / node_filesystem_size_bytes * 100)'
        ' < 85'
    ],
    "SystemDiskInodesFullMajor": [
        '100 - 100 * node_filesystem_files_free / node_filesystem_files < 95'
    ],
    "SystemDiskInodesFullWarning": [
        '100 - 100 * node_filesystem_files_free / node_filesystem_files < 85'
    ],
    "SystemLoadTooHighCritical": [
        'node_load5 / on(node) machine_cpu_cores <= 2'
    ],
    "SystemLoadTooHighWarning": [
        'node_load5 / on(node) machine_cpu_cores <= 1'
    ],
    "SystemMemoryFullMajor": [
        '100 * (node_memory_MemFree_bytes + node_memory_Cached_bytes + '
        'node_memory_Buffers_bytes) / node_memory_MemTotal_bytes >= 5 or '
        'node_memory_Active_bytes >= 4 * 2 ^ 30'
    ],
    "SystemMemoryFullWarning": [
        '100 * (node_memory_MemFree_bytes + node_memory_Cached_bytes + '
        'node_memory_Buffers_bytes) / node_memory_MemTotal_bytes >= 10 or '
        'node_memory_Active_bytes >= 8 * 2 ^ 30'
    ],
    "SystemRxPacketsDroppedTooHigh": [
        'increase(node_network_receive_drop_total{device!~"cali.*"}[1m]) <= 60'
    ],
    "SystemRxPacketsErrorTooHigh": [
        'rate(node_network_receive_errs_total'
        '{device!~"veth.+",job="node-exporter"}[2m]) <= 0'
    ],
    "SystemTxPacketsDroppedTooHigh": [
        'increase(node_network_transmit_drop_total{device!~"cali.*"}[1m]) '
        '<= 100'
    ],
    "SystemTxPacketsErrorTooHigh": [
        'rate(node_network_transmit_errs_total'
        '{device!~"veth.+",job="node-exporter"}[2m]) <= 0'
    ],
    "TargetDown": ['up != 0'],
    "etcdGRPCRequestsSlow": [
        'histogram_quantile(0.99, sum by(job, instance, grpc_service, '
        'grpc_method, le) (rate(grpc_server_handling_seconds_bucket'
        '{grpc_type="unary",job=~".*etcd.*"}[5m]))) <= 0.15'
    ],
    "etcdHTTPRequestsSlow": [
        'histogram_quantile(0.99, rate'
        '(etcd_http_successful_duration_seconds_bucket[5m])) <= 0.15'
    ],
    "etcdHighCommitDurations": [
        'histogram_quantile(0.99, rate'
        '(etcd_disk_backend_commit_duration_seconds_bucket'
        '{job=~".*etcd.*"}[5m])) <= 0.25'
    ],
    "etcdHighFsyncDurations": [
        'histogram_quantile(0.99, rate'
        '(etcd_disk_wal_fsync_duration_seconds_bucket'
        '{job=~".*etcd.*"}[5m])) <= 0.5'
    ],
    "etcdHighNumberOfFailedGRPCRequestsCritical": [
        '100 * sum by(job, instance, grpc_service, grpc_method) '
        '(rate(grpc_server_handled_total'
        '{grpc_code!="OK",job=~".*etcd.*"}[5m])) / '
        'sum by(job, instance, grpc_service, grpc_method) '
        '(rate(grpc_server_handled_total{job=~".*etcd.*"}[5m])) <= 5'
    ],
    "etcdHighNumberOfFailedGRPCRequestsWarning": [
        '100 * sum by(job, instance, grpc_service, grpc_method) '
        '(rate(grpc_server_handled_total'
        '{grpc_code!="OK",job=~".*etcd.*"}[5m])) / '
        'sum by(job, instance, grpc_service, grpc_method) '
        '(rate(grpc_server_handled_total{job=~".*etcd.*"}[5m])) <= 1'
    ],
    "etcdHighNumberOfFailedHTTPRequestsCritical": [
        'sum by(method) (rate(etcd_http_failed_total'
        '{code!="404",job=~".*etcd.*"}[5m])) / sum by(method) '
        '(rate(etcd_http_received_total{job=~".*etcd.*"}[5m])) <= 0.05'
    ],
    "etcdHighNumberOfFailedHTTPRequestsWarning": [
        'sum by(method) (rate(etcd_http_failed_total'
        '{code!="404",job=~".*etcd.*"}[5m])) / sum by(method) '
        '(rate(etcd_http_received_total{job=~".*etcd.*"}[5m])) <= 0.01'
    ],
    "etcdHighNumberOfFailedProposals": [
        'rate(etcd_server_proposals_failed_total{job=~".*etcd.*"}[15m]) <= 5'
    ],
    "etcdHighNumberOfLeaderChanges": [
        'rate(etcd_server_leader_changes_seen_total{job=~".*etcd.*"}[15m]) '
        '<= 3'
    ],
    "etcdInsufficientMembers": [
        'sum by(job) (up{job=~".*etcd.*"} == bool 1) >= ((count by(job) '
        '(up{job=~".*etcd.*"}) + 1) / 2)'
    ],
    "etcdMemberCommunicationSlow": [
        'histogram_quantile(0.99, rate'
        '(etcd_network_peer_round_trip_time_seconds_bucket'
        '{job=~".*etcd.*"}[5m])) <= 0.15'
    ],
    "etcdNoLeader": ['etcd_server_has_leader{job=~".*etcd.*"} != 0']
}


@pytest.mark.alerts
@pytest.mark.run(order=1)
@pytest.mark.parametrize("alert,metrics",
                         alert_metrics.items(),
                         ids=alert_metrics.keys())
def test_alert(prometheus_api, prometheus_native_alerting, alert, metrics):
    if (any("kube_resourcequota" in m for m in metrics) or
            alert in alert_skip_list):
        pytest.skip("Temporary skip test for {} alert".format(alert))
    prometheus_alerts = prometheus_api.get_all_defined_alerts().keys()
    firing_alerts = [a.name
                     for a in prometheus_native_alerting.list_alerts()]
    query_alerts = prometheus_api.get_query('ALERTS{alertstate="pending"}')
    pending_alerts = [item["metric"]['alertname'] for item in query_alerts]
    firing_alerts += pending_alerts
    if alert not in prometheus_alerts:
        pytest.skip("{} alert not found in Prometheus".format(alert))
    for metric in metrics:
        logger.info('\nChecking metric/expression "{}"'.format(metric))
        msg = 'Metric/expression "{}" not found'.format(metric)
        output = prometheus_api.get_query(metric)
        try:
            assert len(output) != 0
        except AssertionError:
            logger.warning(msg)
            logger.info("Checking that {} alert is firing".format(alert))
            err_msg = ("Something wrong with '{}' alert. Please check alert "
                       "definition and ensure alert expression is correct".
                       format(alert))
            assert alert in firing_alerts, err_msg


@pytest.mark.alerts
def test_alert_watchdog(k8s_api, prometheus_api, prometheus_native_alerting):
    prometheus_chart = k8s_api.get_stacklight_chart("prometheus")
    override_alerts = prometheus_chart['values']['alertsOverride']

    if (not override_alerts.get('general', '') or
            "Watchdog" not in override_alerts['general'].keys()):
        pytest.skip("Watchdog alert is disabled on this environment")
    err_msg = "Something wrong with Watchdog alert. It should be always firing"
    logger.info('Checking that Watchdog alert is firing')
    firing_alerts = [a.name
                     for a in prometheus_native_alerting.list_alerts()]
    assert "Watchdog" in firing_alerts, err_msg
    metric = 'vector(1)'
    logger.info('Checking metric "{}"'.format(metric))
    output = prometheus_api.get_query(metric)
    assert len(output) != 0, err_msg


@pytest.mark.alerts
@pytest.mark.smoke
@pytest.mark.xfail
def test_firing_alerts(prometheus_native_alerting):
    if not settings.TEST_FIRING_ALERTS:
        pytest.skip('Test for firing alerts is disabled')
    logger.info("Getting a list of firing alerts")
    alerts = sorted(prometheus_native_alerting.list_alerts(),
                    key=lambda x: x.name)
    skip_list = ['Watchdog']
    logger.warning(
        "+" + "+".join(["-" * 45, "-" * 50, "-" * 20, "-" * 50]) + "+")
    logger.warning("|{:^45}|{:^50}|{:^20}|{:^50}|".format(
        "Name", "Pod", "Namespace", "Node"))
    logger.warning(
        "+" + "+".join(["-" * 45, "-" * 50, "-" * 20, "-" * 50]) + "+")
    for alert in alerts:
        logger.warning("|{:^45}|{:^50}|{:^20}|{:^50}|".format(
            alert.name,
            alert.pod or alert.pod_name,
            alert.namespace,
            alert.node))
    logger.warning(
        "+" + "+".join(["-" * 45, "-" * 50, "-" * 20, "-" * 50]) + "+")
    alerts = filter(lambda x: x.name not in skip_list, alerts)
    assert len(alerts) == 0, \
        "There are some firing alerts in the cluster: {}".format(
            " ".join([a.name for a in alerts]))
