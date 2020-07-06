import logging
import pytest

from stacklight_tests import settings

logger = logging.getLogger(__name__)


alert_skip_list = ['SystemDiskErrorsTooHigh',
                   # TODO: To Delete from skip_list after
                   #  https://mirantis.jira.com/browse/PRODX-4598 is Done
                   'KubePersistentVolumeUsageCritical',
                   'KubePersistentVolumeFullInFourDays'
                   ]


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
        '(felix_int_dataplane_iface_msg_batch_size_sum/'
        'felix_int_dataplane_iface_msg_batch_size_count) <= 5'
    ],
    "CalicoDataplaneAddressMsgBatchSizeHigh": [
        'felix_int_dataplane_addr_msg_batch_size_sum',
        'felix_int_dataplane_addr_msg_batch_size_count',
        '(felix_int_dataplane_addr_msg_batch_size_sum/'
        'felix_int_dataplane_addr_msg_batch_size_count) <= 5'
    ],
    "CalicoDataplaneFailuresHigh": [
        'felix_int_dataplane_failures',
        'increase(felix_int_dataplane_failures[1h]) <= 5'
    ],
    "CalicoIPsetErrorsHigh": [
        'felix_ipset_errors',
        'increase(felix_ipset_errors[1h]) <= 5'
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
        '100 * sum(increase(container_cpu_cfs_throttled_periods_total'
        '{container!="", }[5m])) by (container, pod, namespace) / '
        'sum(increase(container_cpu_cfs_periods_total{}[5m])) '
        'by (container, pod, namespace) <= 25'
    ],
    "DockerNetworkUnhealthy": [
        'docker_networkdb_stats_netmsg * '
        '(docker_networkdb_stats_netmsg offset 5m) <= 0 and '
        'docker_networkdb_stats_qlen * '
        '(docker_networkdb_stats_qlen offset 5m) <= 0'
    ],
    "DockerNodeFlapping": [
        'changes(docker_swarm_node_ready[10m]) <= 3'
    ],
    "DockerServiceReplicasDown": [
        'docker_swarm_tasks_running == docker_swarm_tasks_desired'
    ],
    "DockerServiceReplicasFlapping": [
        'changes(docker_swarm_tasks_running[10m]) <= 0'
    ],
    "DockerServiceReplicasOutage": [
        'docker_swarm_tasks_running != 0 or docker_swarm_tasks_desired == 0'
    ],
    "DockerUCPAPIDown": [
        'probe_success{job="ucp-manager-api"} != 0'
    ],
    "DockerUCPAPIOutage": [
        'max(probe_success{job="ucp-manager-api"}) != 0'
    ],
    "DockerUCPContainerUnhealthy": [
        'ucp_engine_container_unhealth != 1'
    ],
    "DockerUCPInterlockReplicasMismatch": [
        'docker_swarm_tasks_running{service_name=~".*interlock.*"} >= '
        'docker_swarm_tasks_desired{service_name=~".*interlock.*"}'
    ],
    "DockerUCPInterlockServiceOutage": [
        'docker_swarm_tasks_running{service_name=~".*interlock.*"} != 0'
    ],
    "DockerUCPLeadElectionLoop": [
        'count(max_over_time(docker_swarm_node_manager_leader[10m]) == 1) <= 2'
    ],
    "DockerUCPNodeCPUFullMajor": [
        'sum by (instance) (ucp_engine_container_cpu_percent) / '
        'sum by (instance) (ucp_engine_num_cpu_cores) <= 90'
    ],
    "DockerUCPNodeCPUFullMinor": [
        'sum by (instance) (ucp_engine_container_cpu_percent) / '
        'sum by (instance) (ucp_engine_num_cpu_cores) <= 80'
    ],
    "DockerUCPNodeDiskFullCritical": [
        'sum by (instance) (ucp_engine_disk_free_bytes) / '
        'sum by (instance) (ucp_engine_disk_total_bytes) >= 0.05'
    ],
    "DockerUCPNodeDiskFullWarning": [
        'sum by (instance) (ucp_engine_disk_free_bytes) '
        '/ sum by (instance) (ucp_engine_disk_total_bytes) >= 0.15'
    ],
    "DockerUCPNodeDown": [
        'ucp_engine_node_health != 0'
    ],
    "DockerUCPNodeMemoryFullMajor": [
        '100 * sum by (instance) (ucp_engine_container_memory_usage_bytes) / '
        'sum by (instance) (ucp_engine_memory_total_bytes) <= 90'
    ],
    "DockerUCPNodeMemoryFullMinor": [
        '100 * sum by (instance) (ucp_engine_container_memory_usage_bytes) / '
        'sum by (instance) (ucp_engine_memory_total_bytes) <= 80'
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
    "ElasticNoNewData": [
        'rate(elasticsearch_indices_store_size_bytes[30m]) != 0'
    ],
    "ExternalEndpointDown": [
        'probe_success{job="blackbox-external-endpoint"} != 0'
    ],
    "ExternalEndpointTCPFailure": [
        'probe_http_ssl{job="blackbox-external-endpoint"} + on(instance) '
        'group_left probe_http_duration_seconds'
        '{job="blackbox-external-endpoint",phase="transfer"} != 0'
    ],
    "FileDescriptorUsageCritical": [
        'node_filefd_allocated / node_filefd_maximum <= 0.95'
    ],
    "FileDescriptorUsageMajor": [
        'node_filefd_allocated / node_filefd_maximum <= 0.9'
    ],
    "FileDescriptorUsageWarning": [
        'node_filefd_allocated / node_filefd_maximum <= 0.8'
    ],
    "KaasSSLCertExpirationCritical": [
        'max_over_time(probe_ssl_earliest_cert_expiry'
        '{job="kaas-blackbox"}[1h]) >= '
        'probe_success{job="kaas-blackbox"} * (time() + 86400 * 10)'
    ],
    "KaasSSLCertExpirationWarning": [
        'max_over_time(probe_ssl_earliest_cert_expiry'
        '{job="kaas-blackbox"}[1h]) >= '
        'probe_success{job="kaas-blackbox"} * (time() + 86400 * 30)'
    ],
    "KaasSSLProbesFailing": [
        'max_over_time(probe_success{job="kaas-blackbox"}[1h]) != 0'
    ],
    "KubeAPIDown": [
        'probe_success{job="kubernetes-master-api"} != 0'
    ],
    "KubeAPIErrorsHighCritical": [
        'sum(rate(apiserver_request_total{job="apiserver"}[5m]))'
    ],
    "KubeAPIErrorsHighWarning": [
        'sum(rate(apiserver_request_total{job="apiserver"}[5m]))'
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
    "KubeAPIOutage": [
        'max(probe_success{job="kubernetes-master-api"}) != 0'
    ],
    "KubeAPIResourceErrorsHighCritical": [
        'sum by(resource, subresource, verb) (rate(apiserver_request_total'
        '{job="apiserver"}[5m]))'
    ],
    "KubeAPIResourceErrorsHighWarning": [
        'sum by(resource, subresource, verb) (rate(apiserver_request_total'
        '{job="apiserver"}[5m]))'
    ],
    "KubeCPUOvercommitNamespaces": [
        'sum(kube_resourcequota'
        '{job="kube-state-metrics", type="hard", resource="cpu"}) / '
        'sum(node:node_num_cpu:sum) <= 1.5'
    ],
    "KubeCPUOvercommitPods": [
        'sum('
        'namespace_name:kube_pod_container_resource_requests_cpu_cores:sum) / '
        'sum(node:node_num_cpu:sum) <= '
        '(count(node:node_num_cpu:sum)-1) / count(node:node_num_cpu:sum)'
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
        '(sum(rate(rest_client_requests_total{code=~"5.."}[5m])) by '
        '(instance, job) / sum(rate(rest_client_requests_total[5m])) by '
        '(instance, job)) * 100 <= 1'
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
        'sum(kube_resourcequota{job="kube-state-metrics", '
        'type="hard", resource="memory"}) / '
        'sum(node_memory_MemTotal_bytes{job="node-exporter"}) <= 1.5'
    ],
    "KubeMemOvercommitPods": [
        'sum(namespace_name:'
        'kube_pod_container_resource_requests_memory_bytes:sum) / '
        'sum(node_memory_MemTotal_bytes) <= '
        '(count(node:node_num_cpu:sum)-1) / count(node:node_num_cpu:sum)'
    ],
    "KubeNodeNotReady": [
        'kube_node_status_condition'
        '{job="kube-state-metrics",condition="Ready",status="true"} != 0'
    ],
    "KubePersistentVolumeErrors": [
        'kube_persistentvolume_status_phase'
        '{phase=~"Failed|Pending",job="kube-state-metrics"} <= 0'
    ],
    "KubePersistentVolumeFullInFourDays": [
        '100 * ( kubelet_volume_stats_available_bytes{job="kubelet"} / '
        'kubelet_volume_stats_capacity_bytes{job="kubelet"} ) >= 15 or '
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
        'sum by (namespace, pod) (kube_pod_status_phase'
        '{job="kube-state-metrics", phase=~"Pending|Unknown"}) <= 0'
    ],
    "KubeQuotaExceeded": [
        '100 * kube_resourcequota{job="kube-state-metrics", type="used"} / '
        'ignoring(instance, job, type) (kube_resourcequota'
        '{job="kube-state-metrics", type="hard"} > 0) <= 90'
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
        'count(count by (gitVersion) '
        '(label_replace(kubernetes_build_info{job!="kube-dns"},'
        '"gitVersion","$1","gitVersion","(v[0-9]*.[0-9]*.[0-9]*).*"))) <= 1'
    ],
    "KubeletTooManyPods": [
        'kubelet_running_pod_count{job="kubelet"} <= 110 * 0.9'
    ],
    "NetCheckerAgentErrors": [
        'increase(ncagent_error_count_total[1h]) <= 10'
    ],
    "NetCheckerDNSSlow": [
        'delta(ncagent_http_probe_dns_lookup_time_ms[5m]) <= 300'
    ],
    "NetCheckerReportsMissing": [
        'increase(ncagent_report_count_total[5m]) != 0'
    ],
    "NetCheckerTCPServerDelay": [
        'delta(ncagent_http_probe_tcp_connection_time_ms'
        '{url="http://netchecker-service:8081/api/v1/ping"}[5m]) <= 100'
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
        'changes(node_network_up'
        '{job="node-exporter",device!~"veth.+"}[2m]) <= 2'
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
    "PostgresqlDataPageCorruption": [
        'sum by (namespace, cluster, pod) '
        '(rate(pg_stat_database_checksum_failures[5m])) <= 0'
    ],
    "PostgresqlDeadlocksDetected": [
        'sum by (namespace, cluster) '
        '(rate(pg_stat_database_deadlocks[5m])) <= 0'
    ],
    "PostgresqlInsufficientWorkingMemory": [
        'sum by (namespace, cluster) '
        '(rate(pg_stat_database_temp_bytes[5m])) <= 0'
    ],
    "PostgresqlPatroniClusterSplitBrain": [
        'count by (namespace, cluster) '
        '(patroni_patroni_info{role="master"}) <= 1'
    ],
    "PostgresqlPatroniClusterUnlocked": [
        'sum by (namespace, cluster) '
        '(patroni_patroni_cluster_unlocked) <= 0'
    ],
    "PostgresqlPrimaryDown": [
        'sum by (namespace, cluster) '
        '(patroni_patroni_info{role="master"} or on() vector(0)) >= 1'
    ],
    "PostgresqlReplicaDown": [
        'absent(count by (namespace, cluster) '
        '(patroni_patroni_info{role="replica",state!="running"})) or '
        'absent(count by (namespace, cluster) '
        '(patroni_patroni_info{role="replica"}))'
    ],
    "PostgresqlReplicationNonStreamingReplicas": [
        'count by (namespace, cluster) '
        '(patroni_replication_info{state="streaming"}) - '
        'count by (namespace, cluster) '
        '(patroni_patroni_info{state="running",role="replica"}) <= 0'
    ],
    "PostgresqlReplicationPaused": [
        'patroni_xlog_paused <= 0'
    ],
    "PostgresqlReplicationSlowWalApplication": [
        'patroni_xlog_replayed_location - on(namespace, cluster, pod) '
        'group_left patroni_xlog_received_location <= 0'
    ],
    "PostgresqlReplicationSlowWalDownload": [
        'patroni_xlog_received_location - on(namespace, cluster) '
        'group_left patroni_xlog_location <= 0'
    ],
    "PostgresqlReplicationWalArchiveWriteFailing": [
        'sum by (namespace, cluster, pod) '
        '(rate(pg_stat_archiver_failed_count[5m])) <= 0'
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
        '(1 - node_filesystem_free_bytes / node_filesystem_size_bytes) * 100 '
        ' < 95'
    ],
    "SystemDiskFullWarning": [
        '(1 - node_filesystem_free_bytes / node_filesystem_size_bytes) * 100 '
        ' < 85'
    ],
    "SystemDiskInodesFullMajor": [
        '100 - 100 * node_filesystem_files_free / node_filesystem_files < 95'
    ],
    "SystemDiskInodesFullWarning": [
        '100 - 100 * node_filesystem_files_free / node_filesystem_files < 85'
    ],
    "SystemLoadTooHighCritical": [
        'node_load5 / on (node) machine_cpu_cores <= 2'
    ],
    "SystemLoadTooHighWarning": [
        'node_load5 / on (node) machine_cpu_cores <= 1'
    ],
    "SystemMemoryFullMajor": [
        '100 * (node_memory_MemFree_bytes + node_memory_Cached_bytes + '
        'node_memory_Buffers_bytes) / node_memory_MemTotal_bytes >= 5 or '
        'node_memory_Active_bytes >= 4 * 2^30'
    ],
    "SystemMemoryFullWarning": [
        '100 * (node_memory_MemFree_bytes + node_memory_Cached_bytes + '
        'node_memory_Buffers_bytes) / node_memory_MemTotal_bytes >= 10 or '
        'node_memory_Active_bytes >= 8 * 2^30'
    ],
    "SystemRxPacketsDroppedTooHigh": [
        'increase(node_network_receive_drop_total{device!~"cali.*"}[1m]) <= 60'
    ],
    "SystemRxPacketsErrorTooHigh": [
        'rate(node_network_receive_errs_total'
        '{job="node-exporter",device!~"veth.+"}[2m]) <= 0'
    ],
    "SystemTxPacketsDroppedTooHigh": [
        'increase(node_network_transmit_drop_total'
        '{device!~"cali.*"}[1m]) <= 100'
    ],
    "SystemTxPacketsErrorTooHigh": [
        'rate(node_network_transmit_errs_total'
        '{job="node-exporter",device!~"veth.+"}[2m]) <= 0'
    ],
    "TargetDown": ['up != 0'],
    "TargetFlapping": ['changes(up[15m]) <= 0'],
    "etcdGRPCRequestsSlow": [
        'histogram_quantile(0.99, sum(rate(grpc_server_handling_seconds_bucket'
        '{job=~".*etcd.*", grpc_type="unary"}[5m])) by '
        '(job, instance, grpc_service, grpc_method, le)) <= 0.15'
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
        '100 * sum(rate(grpc_server_handled_total'
        '{job=~".*etcd.*", grpc_code!="OK"}[5m])) BY '
        '(job, instance, grpc_service, grpc_method) / '
        'sum(rate(grpc_server_handled_total{job=~".*etcd.*"}[5m])) BY '
        '(job, instance, grpc_service, grpc_method) <= 5'
    ],
    "etcdHighNumberOfFailedGRPCRequestsWarning": [
        '100 * sum(rate(grpc_server_handled_total'
        '{job=~".*etcd.*", grpc_code!="OK"}[5m])) BY '
        '(job, instance, grpc_service, grpc_method) / '
        'sum(rate(grpc_server_handled_total{job=~".*etcd.*"}[5m])) BY '
        '(job, instance, grpc_service, grpc_method) <= 1'
    ],
    "etcdHighNumberOfFailedProposals": [
        'rate(etcd_server_proposals_failed_total{job=~".*etcd.*"}[15m]) <= 5'
    ],
    "etcdHighNumberOfLeaderChanges": [
        'rate(etcd_server_leader_changes_seen_total{job=~".*etcd.*"}[15m]) '
        '<= 3'
    ],
    "etcdInsufficientMembers": [
        'sum(up{job=~".*etcd.*"} == bool 1) by '
        '(job) >= ((count(up{job=~".*etcd.*"}) by (job) + 1) / 2)'
    ],
    "etcdMemberCommunicationSlow": [
        'histogram_quantile(0.99, rate'
        '(etcd_network_peer_round_trip_time_seconds_bucket'
        '{job=~".*etcd.*"}[5m])) <= 0.15'
    ],
    "etcdNoLeader": ['etcd_server_has_leader{job=~".*etcd.*"} != 0'],
    # Ceph alerts
    "CephClusterCriticallyFull": [
        'sum(ceph_osd_stat_bytes_used) / sum(ceph_osd_stat_bytes) <= 0.95'
    ],
    "CephClusterHealthCritical": ['ceph_health_status <= 1'],
    "CephClusterHealthMinor": ['ceph_health_status != 1'],
    "CephClusterNearFull": [
        'sum(ceph_osd_stat_bytes_used) / sum(ceph_osd_stat_bytes) <= 0.85'
    ],
    "CephDataRecoveryTakingTooLong": ['ceph_pg_undersized <= 0'],
    "CephMonHighNumberOfLeaderChanges": [
        'rate(ceph_mon_num_elections{job="rook-ceph-mgr"}[5m]) * 60 <= 0.95'
    ],
    "CephMonQuorumAtRisk": [
        'count(ceph_mon_quorum_status{job="rook-ceph-mgr"} == 1) > '
        '((count(ceph_mon_metadata{job="rook-ceph-mgr"}) % 2) + 1)'
    ],
    "CephMonVersionMismatch": [
        'count(count(ceph_mon_metadata{job="rook-ceph-mgr"}) by '
        '(ceph_version)) <= 1'
    ],
    "CephNodeDown": ['cluster:ceph_node_down:join_kube != 0'],
    "CephOSDDiskNotResponding": [
        'label_replace((ceph_osd_in != 1 or ceph_osd_up != 0), "disk", "$1", '
        '"ceph_daemon", "osd.(.*)") + on(ceph_daemon) group_left(host, device)'
        ' label_replace(ceph_disk_occupation, "host", "$1", '
        '"exported_instance", "(.*)")'
    ],
    "CephOSDDiskUnavailable": [
        'label_replace((ceph_osd_in != 0 or ceph_osd_up != 0), "disk", "$1", '
        '"ceph_daemon", "osd.(.*)") + on(ceph_daemon) group_left(host, device)'
        ' label_replace(ceph_disk_occupation, "host", "$1", '
        '"exported_instance", "(.*)")'
    ],
    "CephOSDVersionMismatch": [
        'count(count(ceph_osd_metadata{job="rook-ceph-mgr"}) by '
        '(ceph_version)) <= 1'
    ],
    "CephOsdDownMinor": ['count(ceph_osd_up) - sum(ceph_osd_up) <= 0'],
    "CephOsdPgNumTooHighCritical": ['max(ceph_osd_numpg) <= 300'],
    "CephOsdPgNumTooHighWarning": ['max(ceph_osd_numpg) <= 200'],
    "CephPGRepairTakingTooLong": ['ceph_pg_inconsistent <= 0'],
    # Openstack alerts
    "BarbicanApiOutage": [
        'max(openstack_api_check_status{name="barbican"}) != 0'
    ],
    "CinderApiDown": ['openstack_api_check_status{name=~"cinderv.*"} != 0'],
    "CinderApiOutage": [
        'max(openstack_api_check_status{name=~"cinderv.*"}) != 0'
    ],
    "CinderServiceDown": ['openstack_cinder_service_state != 0'],
    "CinderServiceOutage": [
        'count by(binary) (openstack_cinder_service_state != 0) == on(binary) '
        'count by(binary) (openstack_cinder_service_state)'
    ],
    "CinderServicesDownMajor": [
        'count by(binary) (openstack_cinder_service_state != 0) >= on(binary) '
        'count by(binary) (openstack_cinder_service_state) * 0.6'
    ],
    "CinderServicesDownMinor": [
        'count by(binary) (openstack_cinder_service_state != 0) >= on(binary) '
        'count by(binary) (openstack_cinder_service_state) * 0.3'
    ],
    "DesignateApiOutage": [
        'max(openstack_api_check_status{name="designate"}) != 0'
    ],
    "GlanceApiOutage": ['openstack_api_check_status{name="glance"} != 0'],
    "HeatApiDown": ['openstack_api_check_status{name=~"heat.*"} != 0'],
    "HeatApiOutage": ['max(openstack_api_check_status{name=~"heat.*"}) != 0'],
    "IronicApiOutage": [
        'http_response_status{name=~"ironic-api"} == 1'
    ],
    "IronicMetricsMissing": [
        'openstack_ironic_nodes_total',
        'openstack_ironic_drivers_total'
    ],
    "KeystoneApiOutage": [
        'openstack_api_check_status{name=~"keystone.*"} != 0'
    ],
    "LibvirtDown": ['libvirt_up != 0'],
    "MariadbGaleraDonorFallingBehind": [
        '(mysql_global_status_wsrep_local_state != 2 or '
        'mysql_global_status_wsrep_local_recv_queue <= 100)'
    ],
    "MariadbGaleraNotReady": [
        'mysql_global_status_wsrep_ready == 1'
    ],
    "MariadbGaleraOutOfSync": [
        '(mysql_global_status_wsrep_local_state == 4 '
        'or mysql_global_variables_wsrep_desync != 0)'
    ],
    "MariadbInnodbLogWaits": [
        'rate(mysql_global_status_innodb_log_waits[15m]) <= 10'
    ],
    "MariadbInnodbReplicationFallenBehind": [
        '(mysql_global_variables_innodb_replication_delay <= 30) or on '
        '(instance) (predict_linear'
        '(mysql_global_variables_innodb_replication_delay[5m], 60*2) <= 0)'
    ],
    "MariadbTableLockWaitHigh": [
        '100 * mysql_global_status_table_locks_waited / '
        '(mysql_global_status_table_locks_waited + '
        'mysql_global_status_table_locks_immediate) <= 30'
    ],
    "MemcachedConnectionsNoneMajor": [
        'count(memcached_current_connections != 0) == count(memcached_up)'
    ],
    "MemcachedConnectionsNoneMinor": ['memcached_current_connections != 0'],
    "MemcachedEvictionsLimit": [
        'increase(memcached_items_evicted_total[1m]) <= 10'
    ],
    "MemcachedServiceDown": ['memcached_up != 0'],
    "NeutronAgentDown": ['openstack_neutron_agent_state != 0'],
    "NeutronAgentsDownMajor": [
        'count by(binary) (openstack_neutron_agent_state != 0) >= on(binary) '
        'count by(binary) (openstack_neutron_agent_state) * 0.6'
    ],
    "NeutronAgentsDownMinor": [
        'count by(binary) (openstack_neutron_agent_state != 0) >= on(binary) '
        'count by(binary) (openstack_neutron_agent_state) * 0.3'
    ],
    "NeutronAgentsOutage": [
        'count by(binary) (openstack_neutron_agent_state != 0) == on(binary) '
        'count by(binary) (openstack_neutron_agent_state)'
    ],
    "NeutronApiOutage": ['openstack_api_check_status{name="neutron"} != 0'],
    "NovaApiDown": [
        'openstack_api_check_status{name=~"nova.*|placement"} != 0'
    ],
    "NovaApiOutage": [
        'max(openstack_api_check_status{name=~"nova.*|placement"}) != 0'
    ],
    "NovaComputeServicesDownMajor": [
        'count(openstack_nova_service_state{binary="nova-compute"} != 0) >= '
        'count(openstack_nova_service_state{binary="nova-compute"}) * 0.5'
    ],
    "NovaComputeServicesDownMinor": [
        'count(openstack_nova_service_state{binary="nova-compute"} != 0) >= '
        'count(openstack_nova_service_state{binary="nova-compute"}) * 0.25'
    ],
    "NovaServiceDown": ['openstack_nova_service_state != 0'],
    "NovaServiceOutage": [
        'count by(binary) (openstack_nova_service_state != 0) == on(binary) '
        'count by(binary) (openstack_nova_service_state)'
    ],
    "NovaServicesDownMajor": [
        'count by(binary) (openstack_nova_service_state'
        '{binary!~"nova-compute"} != 0) >= on(binary) count by(binary) '
        '(openstack_nova_service_state{binary!~"nova-compute"}) * 0.6'
    ],
    "NovaServicesDownMinor": [
        'count by(binary) (openstack_nova_service_state'
        '{binary!~"nova-compute"} != 0) >= on(binary) count by(binary) '
        '(openstack_nova_service_state{binary!~"nova-compute"}) * 0.3'
    ],
    "OctaviaApiOutage": [
        'max(openstack_api_check_status{name="octavia"}) != 0'
    ],
    "OpenstackSSLCertExpirationCritical": [
        'max_over_time(probe_ssl_earliest_cert_expiry'
        '{job=~"openstack-blackbox.*"}[1h]) >= '
        'probe_success{job=~"openstack-blackbox.*"} * (time() + 86400 * 10)'
    ],
    "OpenstackSSLCertExpirationWarning": [
        'max_over_time(probe_ssl_earliest_cert_expiry'
        '{job=~"openstack-blackbox.*"}[1h]) >= '
        'probe_success{job=~"openstack-blackbox.*"} * (time() + 86400 * 30)'
    ],
    "OpenstackSSLProbesFailing": [
        'max_over_time(probe_success{job=~"openstack-blackbox.*"}[1h]) != 0'
    ],
    "RabbitMQDown": ['min(rabbitmq_up) by (pod) == 1'],
    "RabbitMQFileDescriptorUsagehigh": [
        'rabbitmq_fd_used * 100 / rabbitmq_fd_total <= 80'
    ],
    "RabbitMQNetworkPartitionsDetected": [
        'min(rabbitmq_partitions) by (pod) <= 0'
    ],
    "RabbitMQNodeDiskFreeAlarm": ['rabbitmq_node_disk_free_alarm <= 0'],
    "RabbitMQNodeMemoryAlarm": ['rabbitmq_node_mem_alarm <= 0'],
    "SfNotifierAuthFailure": ['sf_auth_ok != 0'],
    "SfNotifierDown": ['sf_auth_ok'],
    "SSLCertExpirationCritical": [
        'max_over_time(probe_ssl_earliest_cert_expiry'
        '{job!~"(openstack|kaas)-blackbox.*"}[1h]) - time() >= 86400 * 10'
    ],
    "SSLCertExpirationWarning": [
        'max_over_time(probe_ssl_earliest_cert_expiry'
        '{job!~"(openstack|kaas)-blackbox.*"}[1h]) - time() >= 86400 * 30'
    ],
    "TelemeterClientFederationFailed": [
        'increase(federate_errors[30m]) <= 2'
    ]
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
