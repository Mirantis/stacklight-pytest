import collections

import pytest


ignored_queries_for_fail = [
    # Cinder. Default installation does not contain cinder-volume
    'max(openstack_cinder_services{state="down", service="cinder-volume"})',
    'max(openstack_cinder_services{service="cinder-volume"}) by (state)',
    'max(openstack_cinder_services'
    '{state="disabled", service="cinder-volume"})',
    'max(openstack_cinder_services{state="up", service="cinder-volume"})',

    # Heat. By default metric is not present if no tracked value
    'irate(openstack_heat_http_response_times_count{http_status="5xx"}[5m])',

    # Partial Elasticsearch metric PROD-19161
    'quantile_over_time(0.9, elasticsearch_indices_flush_total_latency'
    '{host="$host"}[5m])',

    # Openstack. We can have situation without 5xx errors
    'sum(rate(openstack_http_response_times_count{http_status=~"5.."}'
    '[$rate_interval])) by (service)',

    # Cinder. We can have only enabled/up cinder services
    'max(count(openstack_cinder_service_state{binary="cinder-volume"} == 0 '
    'and openstack_cinder_service_status{binary="cinder-volume"} == 0) '
    'by (instance))',
    'max(count(openstack_cinder_service_state{binary="cinder-volume"} == 0 '
    'and openstack_cinder_service_status{binary="cinder-volume"} == 1) '
    'by (instance))',
    'max(count(openstack_cinder_service_state{binary="cinder-volume"} == 1 '
    'and openstack_cinder_service_status{binary="cinder-volume"} == 0) '
    'by (instance))',
    'max(count(openstack_cinder_service_state{binary="cinder-scheduler"} == 1 '
    'and openstack_cinder_service_status{binary="cinder-scheduler"} == 0) '
    'by (instance))',
    'max(count(openstack_cinder_service_state{binary="cinder-scheduler"} == 0 '
    'and openstack_cinder_service_status{binary="cinder-scheduler"} == 1) '
    'by (instance))',
    'max(count(openstack_cinder_service_state{binary="cinder-scheduler"} == 0 '
    'and openstack_cinder_service_status{binary="cinder-scheduler"} == 0) '
    'by (instance))',

    # Skip 0 as query, that is just visual line
    '0',

    # Haproxy. We can have installation without SSL on haproxy
    'max(haproxy_server_ssl_connections {host=~"$host"}) without(pid) > 0',

    # Influxdb. We can have no stopped instances of influxdb
    'count(influxdb_up == 0)',

    # Keepalived. Keepalived_state metric appears only after changing of status
    'keepalived_state{host="$host"}',
    'keepalived_state{host=~"$host"}',

    # Prometheus. Skip 1.x prometheus metric
    'prometheus_local_storage_target_heap_size_bytes'
    '{instance=~"$instance:[1-9][0-9]*"}',

    # Neutron. We can have only up and enabled agents
    'max(count(openstack_neutron_agent_state{binary="neutron-metadata-agent"} '
    '== 0 and openstack_neutron_agent_status{binary="neutron-metadata-agent"} '
    '== 0) by (instance))',
    'max(count(openstack_neutron_agent_state{binary="neutron-metadata-agent"} '
    '== 0 and openstack_neutron_agent_status{binary="neutron-metadata-agent"} '
    '== 1) by (instance))',
    'max(count(openstack_neutron_agent_state{binary="neutron-metadata-agent"} '
    '== 1 and openstack_neutron_agent_status{binary="neutron-metadata-agent"} '
    '== 0) by (instance))',
    'max(count(openstack_neutron_agent_state{binary=~"neutron-openvswitch-'
    'agent|neutron-linuxbridge-agent"} == 1 and openstack_neutron_agent_status'
    '{binary=~"neutron-openvswitch-agent|neutron-linuxbridge-agent"} == 0) '
    'by (instance))',
    'max(count(openstack_neutron_agent_state{binary=~"neutron-openvswitch-'
    'agent|neutron-linuxbridge-agent"} == 0 and openstack_neutron_agent_status'
    '{binary=~"neutron-openvswitch-agent|neutron-linuxbridge-agent"} == 1) '
    'by (instance))',
    'max(count(openstack_neutron_agent_state{binary=~"neutron-openvswitch-'
    'agent|neutron-linuxbridge-agent"} == 0 and openstack_neutron_agent_status'
    '{binary=~"neutron-openvswitch-agent|neutron-linuxbridge-agent"} == 0) '
    'by (instance))',
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

    # Neutron. Right after deployment we have no lbaases and instances
    'max(sum(openstack_neutron_ports{owner=~"compute:.*"}) by '
    '(instance,state)) by (state)',
    'max(openstack_neutron_lbaas_loadbalancers) by (status)',

    # Nova. We can have only up and enabled nova services
    'max(count(openstack_nova_service_state{service="nova-compute"} == 0 '
    'and openstack_nova_service_status{service="nova-compute"} == 1) by '
    '(instance))',
    'max(count(openstack_nova_service_state{service="nova-compute"} == 1 '
    'and openstack_nova_service_status{service="nova-compute"} == 0) by '
    '(instance))',
    'max(count(openstack_nova_service_state{service="nova-compute"} == 0 '
    'and openstack_nova_service_status{service="nova-compute"} == 0) by '
    '(instance))',

    'max(count(openstack_nova_service_state{binary="nova-scheduler"} == 0 '
    'and openstack_nova_service_status{binary="nova-scheduler"} == 1) by '
    '(instance))',
    'max(count(openstack_nova_service_state{binary="nova-scheduler"} == 1 '
    'and openstack_nova_service_status{binary="nova-scheduler"} == 0) by '
    '(instance))',
    'max(count(openstack_nova_service_state{binary="nova-scheduler"} == 0 '
    'and openstack_nova_service_status{binary="nova-scheduler"} == 0) by '
    '(instance))',

    'max(count(openstack_nova_service_state{binary="nova-consoleauth"} == 1 '
    'and openstack_nova_service_status{binary="nova-consoleauth"} == 0) by '
    '(instance))',
    'max(count(openstack_nova_service_state{binary="nova-consoleauth"} == 0 '
    'and openstack_nova_service_status{binary="nova-consoleauth"} == 1) by '
    '(instance))',
    'max(count(openstack_nova_service_state{binary="nova-consoleauth"} == 0 '
    'and openstack_nova_service_status{binary="nova-consoleauth"} == 0) by '
    '(instance))',

    'max(count(openstack_nova_service_state{binary="nova-conductor"} == 0 '
    'and openstack_nova_service_status{binary="nova-conductor"} == 1) by '
    '(instance))',
    'max(count(openstack_nova_service_state{binary="nova-conductor"} == 1 '
    'and openstack_nova_service_status{binary="nova-conductor"} == 0) by '
    '(instance))',
    'max(count(openstack_nova_service_state{binary="nova-conductor"} == 0 '
    'and openstack_nova_service_status{binary="nova-conductor"} == 0) by '
    '(instance))',

    'max(sum(openstack_nova_vcpus and on (hostname) '
    '(openstack_nova_service_status == 0 and '
    'openstack_nova_service_state == 0)) by (instance))',
    'max(sum(openstack_nova_vcpus and on (hostname) '
    '(openstack_nova_service_status == 0 and '
    'openstack_nova_service_state == 1)) by (instance))',
    'max(sum(openstack_nova_vcpus and on (hostname) '
    '(openstack_nova_service_status == 1 and '
    'openstack_nova_service_state == 0)) by (instance))',

    'max(sum(openstack_nova_ram and on (hostname) '
    '(openstack_nova_service_status == 0 and '
    'openstack_nova_service_state == 0)) by (instance))',
    'max(sum(openstack_nova_ram and on (hostname) '
    '(openstack_nova_service_status == 1 and '
    'openstack_nova_service_state == 0)) by (instance))',
    'max(sum(openstack_nova_ram and on (hostname) '
    '(openstack_nova_service_status == 0 and '
    'openstack_nova_service_state == 1)) by (instance))',

    'max(avg(openstack_nova_disk and on (hostname) '
    '(openstack_nova_service_status == 0 and '
    'openstack_nova_service_state == 1)) by (instance))',
    'max(avg(openstack_nova_disk and on (hostname) '
    '(openstack_nova_service_status == 1 and '
    'openstack_nova_service_state == 0)) by (instance))',
    'max(avg(openstack_nova_disk and on (hostname) '
    '(openstack_nova_service_status == 0 and '
    'openstack_nova_service_state == 0)) by (instance))',

    'max(sum(openstack_nova_disk and on (hostname) '
    '(openstack_nova_service_status == 0 and '
    'openstack_nova_service_state == 1)) by (instance))',
    'max(sum(openstack_nova_disk and on (hostname) '
    '(openstack_nova_service_status == 1 and '
    'openstack_nova_service_state == 0)) by (instance))',
    'max(sum(openstack_nova_disk and on (hostname) '
    '(openstack_nova_service_status == 0 and '
    'openstack_nova_service_state == 0)) by (instance))',

    # Kubernetes. We have no rkt containers by default
    'sum(rate(container_network_transmit_bytes_total{rkt_container_name!="",'
    'kubernetes_io_hostname=~"^$host$"}[$rate_interval])) by '
    '(kubernetes_io_hostname, rkt_container_name)',
    'sum(rate(container_network_transmit_bytes_total{rkt_container_name!="",'
    'kubernetes_io_hostname=~"^$host$"}[$rate_interval])) by '
    '(kubernetes_io_hostname, rkt_container_name)',
    'sum(rate(container_cpu_usage_seconds_total{rkt_container_name!="",'
    'kubernetes_io_hostname=~"^$host$"}[$rate_interval])) by '
    '(kubernetes_io_hostname, rkt_container_name)',
    'sum(container_memory_working_set_bytes{rkt_container_name!="",'
    'kubernetes_io_hostname=~"^$host$"}) by '
    '(kubernetes_io_hostname, rkt_container_name)',

    # Haproxy. We can have no failed backends
    'avg(sum(haproxy_active_servers{type="server"}) by (host, proxy) + '
    'sum(haproxy_backup_servers{type="server"}) by (host, proxy)) by (proxy) '
    '- avg(sum(haproxy_active_servers{type="backend"}) by (host, proxy) '
    '+ sum(haproxy_backup_servers{type="backend"}) by (host, proxy)) '
    'by (proxy) > 0',

    # Ceph. We may not have metrics for all Ceph resources right after
    # deployment
    # ceph-cluster
    'count(ceph_osd_stat_bytes >= 1099511627776 < 2199023255552)',
    'count(ceph_osd_stat_bytes >= 2199023255552 < 3298534883328)',
    'count(ceph_osd_stat_bytes >= 3298534883328 < 4398046511104)',
    'count(ceph_osd_stat_bytes >= 4398046511104 < 6597069766656)',
    'count(ceph_osd_stat_bytes >= 6597069766656 < 8796093022208)',
    'count(ceph_osd_stat_bytes >= 8796093022208 < 10995116277760)',
    'count(ceph_osd_stat_bytes >= 10995116277760 < 13194139533312)',
    'count(ceph_osd_stat_bytes >= 13194139533312)',
    'absent(ceph_bluefs_wal_total_bytes)*count(ceph_osd_metadata)',
    # ceph-rgw-instance-detail
    'rate(ceph_rgw_put{ceph_daemon=~"[[rgw_servers]]"}[$rate_interval])',
    'rate(ceph_rgw_get{ceph_daemon=~"[[rgw_servers]]"}[$rate_interval])',
    'rate(ceph_rgw_failed_req{ceph_daemon=~"[[rgw_servers]]"}'
    '[$rate_interval])',
    'rate(ceph_rgw_req{ceph_daemon=~\"[[rgw_servers]]\"}[$rate_interval]) -\n'
    '  (rate(ceph_rgw_get{ceph_daemon=~\"[[rgw_servers]]\"}[$rate_interval])'
    ' +\n   rate(ceph_rgw_put{ceph_daemon=~\"[[rgw_servers]]\"}'
    '[$rate_interval]))',
    'rate(ceph_rgw_get_b{ceph_daemon=~"[[rgw_servers]]"}[$rate_interval])',
    'rate(ceph_rgw_put_b{ceph_daemon=~"[[rgw_servers]]"}[$rate_interval])',
    # ceph-osd-device-details
    'label_replace(rate(diskio_io_time[$rate_interval]), "instance", "$1", '
    '"host", "(.*)") / 1000 and on (name,instance) label_replace('
    'label_replace(ceph_disk_occupation{ceph_daemon=~"osd.$osd_id"}, "name", '
    '"$1", "device", "/dev/(.*)"), "instance", "$1", "instance", "(.*)")',
    'label_replace(label_replace(rate(diskio_write_bytes[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") and '
    'on (name,instance) label_replace(label_replace(ceph_disk_occupation{'
    'ceph_daemon=~"osd.$osd_id"}, "name", "$1", "device", "/dev/(.*)"), '
    '"instance", "$1", "instance", "(.*)")',
    'label_replace(label_replace(rate(diskio_read_bytes[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") and '
    'on (name,instance) label_replace(label_replace(ceph_disk_occupation{'
    'ceph_daemon=~"osd.$osd_id"}, "name", "$1", "device", "/dev/(.*)"), '
    '"instance", "$1", "instance", "(.*)")',
    'rate(ceph_osd_op_r{ceph_daemon=~"osd.[[osd_id]]"}[$rate_interval])',
    'rate(ceph_osd_op_w_in_bytes{ceph_daemon=~"osd.[[osd_id]]"}'
    '[$rate_interval])',
    'rate(ceph_osd_op_r_out_bytes{ceph_daemon=~"osd.[[osd_id]]"}'
    '[$rate_interval])',
    'rate(ceph_osd_op_w_latency_sum{ceph_daemon=~"osd.[[osd_id]]"}'
    '[$rate_interval]) / on (ceph_daemon) rate(ceph_osd_op_w_latency_count'
    '[$rate_interval]) * 1000',
    'rate(ceph_osd_op_r_latency_sum{ceph_daemon=~"osd.[[osd_id]]"}'
    '[$rate_interval]) / on (ceph_daemon) rate(ceph_osd_op_r_latency_count'
    '[$rate_interval]) * 1000',
    'rate(ceph_osd_op_w{ceph_daemon=~"osd.[[osd_id]]"}[$rate_interval])',
    'label_replace(label_replace(rate(diskio_write_time[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") / '
    'label_replace(label_replace(rate(diskio_writes[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") and '
    'on (name,instance) label_replace(label_replace(ceph_disk_occupation{'
    'ceph_daemon=~"osd.$osd_id"}, "name", "$1", "device", "/dev/(.*)"), '
    '"instance", "$1", "instance", "(.*)")',
    'label_replace(label_replace(rate(diskio_read_time[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") / '
    'label_replace(label_replace(rate(diskio_reads[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") and '
    'on (name,instance) label_replace(label_replace(ceph_disk_occupation{'
    'ceph_daemon=~"osd.$osd_id"}, "name", "$1", "device", "/dev/(.*)"), '
    '"instance", "$1", "instance", "(.*)")',
    'label_replace(label_replace(rate(diskio_writes[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") and '
    'on (name,instance) label_replace(label_replace(ceph_disk_occupation{'
    'ceph_daemon=~"osd.$osd_id"}, "name", "$1", "device", "/dev/(.*)"), '
    '"instance", "$1", "instance", "(.*)")',
    'label_replace(label_replace(rate(diskio_reads[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") and '
    'on (name,instance) label_replace(label_replace(ceph_disk_occupation{'
    'ceph_daemon=~"osd.$osd_id"}, "name", "$1", "device", "/dev/(.*)"), '
    '"instance", "$1", "instance", "(.*)")',
    'label_replace(label_replace(rate(diskio_read_bytes[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") and '
    'on (name,instance) label_replace(label_replace(ceph_disk_occupation{'
    'ceph_daemon=~"osd.$osd_id"}, "name", "$1", "device", "(.*)"), '
    '"instance", "$1", "instance", "(.*)")',
    'label_replace(rate(diskio_io_time[$rate_interval]), "instance", "$1", '
    '"host", "(.*)") / 1000 and on (name,instance) label_replace('
    'label_replace(ceph_disk_occupation{ceph_daemon=~"osd.$osd_id"}, "name", '
    '"$1", "device", "(.*)"), "instance", "$1", "instance", "(.*)")',
    'label_replace(label_replace(rate(diskio_write_bytes[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") and '
    'on (name,instance) label_replace(label_replace(ceph_disk_occupation{'
    'ceph_daemon=~"osd.$osd_id"}, "name", "$1", "device", "(.*)"), '
    '"instance", "$1", "instance", "(.*)")',
    'label_replace(label_replace(rate(diskio_read_time[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") / '
    'label_replace(label_replace(rate(diskio_reads[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") and '
    'on (name,instance) label_replace(label_replace(ceph_disk_occupation{'
    'ceph_daemon=~"osd.$osd_id"}, "name", "$1", "device", "(.*)"), '
    '"instance", "$1", "instance", "(.*)")',
    'label_replace(label_replace(rate(diskio_write_time[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") / '
    'label_replace(label_replace(rate(diskio_writes[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") and '
    'on (name,instance) label_replace(label_replace(ceph_disk_occupation{'
    'ceph_daemon=~"osd.$osd_id"}, "name", "$1", "device", "(.*)"), '
    '"instance", "$1", "instance", "(.*)")',
    'label_replace(label_replace(rate(diskio_writes[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") and '
    'on (name,instance) label_replace(label_replace(ceph_disk_occupation{'
    'ceph_daemon=~"osd.$osd_id"}, "name", "$1", "device", "(.*)"), '
    '"instance", "$1", "instance", "(.*)")',
    'label_replace(label_replace(rate(diskio_reads[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") and '
    'on (name,instance) label_replace(label_replace(ceph_disk_occupation{'
    'ceph_daemon=~"osd.$osd_id"}, "name", "$1", "device", "(.*)"), '
    '"instance", "$1", "instance", "(.*)")',
    'label_replace(label_replace(irate(diskio_reads[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") and '
    'on (name,instance) label_replace(label_replace(ceph_disk_occupation'
    '{ceph_daemon=~"osd.$osd_id"}, "name", "$1", "device", "/dev/(.*)"), '
    '"instance", "$1", "instance", "(.*)")',
    'label_replace(label_replace(irate(diskio_writes[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") and '
    'on (name,instance) label_replace(label_replace(ceph_disk_occupation'
    '{ceph_daemon=~"osd.$osd_id"}, "name", "$1", "device", "/dev/(.*)"), '
    '"instance", "$1", "instance", "(.*)")',
    'label_replace(label_replace(irate(diskio_write_time[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") / '
    'label_replace(label_replace(irate(diskio_writes[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") and '
    'on (name,instance) label_replace(label_replace(ceph_disk_occupation'
    '{ceph_daemon=~"osd.$osd_id"}, "name", "$1", "device", "/dev/(.*)"), '
    '"instance", "$1", "instance", "(.*)")',
    'label_replace(label_replace(irate(diskio_read_time[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") / '
    'label_replace(label_replace(irate(diskio_reads[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") and '
    'on (name,instance) label_replace(label_replace(ceph_disk_occupation'
    '{ceph_daemon=~"osd.$osd_id"}, "name", "$1", "device", "/dev/(.*)"), '
    '"instance", "$1", "instance", "(.*)")',
    'label_replace(label_replace(irate(diskio_write_bytes[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") and '
    'on (name,instance) label_replace(label_replace(ceph_disk_occupation'
    '{ceph_daemon=~"osd.$osd_id"}, "name", "$1", "device", "/dev/(.*)"), '
    '"instance", "$1", "instance", "(.*)")',
    'label_replace(label_replace(irate(diskio_read_bytes[$rate_interval]), '
    '"instance", "$1", "host", "(.+)"), "device", "$1", "name", "(.+)") and '
    'on (name,instance) label_replace(label_replace(ceph_disk_occupation'
    '{ceph_daemon=~"osd.$osd_id"}, "name", "$1", "device", "/dev/(.*)"), '
    '"instance", "$1", "instance", "(.*)")',
    'label_replace(irate(diskio_io_time[$rate_interval]), '
    '"instance", "$1", "host", "(.*)") / 1000 and on '
    '(name,instance) label_replace(label_replace(ceph_disk_occupation'
    '{ceph_daemon=~"osd.$osd_id"}, "name", "$1", "device", "/dev/(.*)"), '
    '"instance", "$1", "instance", "(.*)")',

    # ceph-pools-overview
    'avg((rate(ceph_pool_rd_bytes{pool_id=~"[[pool_id]]"}[$rate_interval]) + '
    'rate(ceph_pool_wr_bytes{pool_id=~"[[pool_id]]"}[$rate_interval])) + '
    'on(pool_id,instance) group_left(name) '
    'ceph_pool_metadata{pool_id=~"[[pool_id]]"}) without (instance)',
    'topk(5,(label_replace((irate(ceph_pool_rd{pool_id=~"[[pool_id]]"}'
    '[$rate_interval]) + irate(ceph_pool_wr{pool_id=~"[[pool_id]]"}'
    '[$rate_interval])),"id", "$1", "pool_id", "(.*)") + on(pool_id) '
    'group_left(instance,name) ceph_pool_metadata{pool_id=~"[[pool_id]]"}) )',
    '(label_replace((irate(ceph_pool_rd_bytes{pool_id=~"[[pool_id]]"}'
    '[$rate_interval]) + irate(ceph_pool_wr_bytes{pool_id=~"[[pool_id]]"}'
    '[$rate_interval])),"id", "$1", "pool_id", "(.*)") + on(pool_id) '
    'group_left(instance,name) ceph_pool_metadata{pool_id=~"[[pool_id]]"}) ',
    'avg((rate(ceph_pool_rd{pool_id=~"[[pool_id]]"}[$rate_interval]) + '
    'rate(ceph_pool_wr{pool_id=~"[[pool_id]]"}[$rate_interval])) + '
    'on(pool_id,instance) group_left(name) '
    'ceph_pool_metadata{pool_id=~"[[pool_id]]"}) without (instance)',
    'avg(rate(ceph_pool_rd{pool_id=~"[[pool_id]]"}[$rate_interval]) * '
    'on(pool_id,instance) group_left(name) '
    'ceph_pool_metadata{pool_id=~"[[pool_id]]"}) without (instance)',
    'avg(rate(ceph_pool_rd_bytes{pool_id=~"[[pool_id]]"}[$rate_interval]) * '
    'on(pool_id,instance) group_left(name) '
    'ceph_pool_metadata{pool_id=~"[[pool_id]]"}) without (instance)',
    'avg(rate(ceph_pool_wr{pool_id=~"[[pool_id]]"}[$rate_interval]) * '
    'on(pool_id,instance) group_left(name) '
    'ceph_pool_metadata{pool_id=~"[[pool_id]]"}) without (instance)',
    'topk(5,avg(rate(ceph_pool_wr{pool_id=~"[[pool_id]]"}[$rate_interval]) * '
    'on(pool_id) group_left(instance,name) '
    'ceph_pool_metadata{pool_id=~"[[pool_id]]"}) without (instance))',
    'topk(5,avg(rate(ceph_pool_rd{pool_id=~"[[pool_id]]"}[$rate_interval]) * '
    'on(pool_id) group_left(instance,name) '
    'ceph_pool_metadata{pool_id=~"[[pool_id]]"}) without (instance))',
    'avg(rate(ceph_pool_wr_bytes{pool_id=~"[[pool_id]]"}[$rate_interval]) * '
    'on(pool_id,instance) group_left(name) '
    'ceph_pool_metadata{pool_id=~"[[pool_id]]"}) without (instance)',
    'topk(5,avg(rate(ceph_pool_wr_bytes{pool_id=~"[[pool_id]]"}'
    '[$rate_interval]) * on(pool_id) group_left(instance,name) '
    'ceph_pool_metadata{pool_id=~"[[pool_id]]"}) without (instance))',
    'topk(5,avg(rate(ceph_pool_rd_bytes{pool_id=~"[[pool_id]]"}'
    '[$rate_interval]) * on(pool_id) group_left(instance,name) '
    'ceph_pool_metadata{pool_id=~"[[pool_id]]"}) without (instance))',

    # Ceph, compatibility with 2019.2.x, x<4
    # ceph-rgw-instance-detail
    'rate(ceph_rgw_put{ceph_daemon=~"[[rgw_servers]]"}[1m])',
    'rate(ceph_rgw_get{ceph_daemon=~"[[rgw_servers]]"}[1m])',
    'rate(ceph_rgw_failed_req{ceph_daemon=~"[[rgw_servers]]"}[1m])',
    'rate(ceph_rgw_req{ceph_daemon=~\"[[rgw_servers]]\"}[1m]) -\n  '
    '(rate(ceph_rgw_get{ceph_daemon=~\"[[rgw_servers]]\"}[1m]) +\n   '
    'rate(ceph_rgw_put{ceph_daemon=~\"[[rgw_servers]]\"}[1m]))',
    'rate(ceph_rgw_get_b{ceph_daemon=~"[[rgw_servers]]"}[1m])',
    'rate(ceph_rgw_put_b{ceph_daemon=~"[[rgw_servers]]"}[1m])',
    # ceph-osd-device-details
    'label_replace(label_replace(irate(diskio_read_time[1m]), "instance", '
    '"$1", "host", "(.+)"), "device", "$1", "name", "(.+)") / '
    'label_replace(label_replace(irate(diskio_reads[1m]), "instance", "$1", '
    '"host", "(.+)"), "device", "$1", "name", "(.+)") and on '
    '(instance, device) ceph_disk_occupation{ceph_daemon=~"osd.[[osd_id]]"}',
    'label_replace(label_replace(irate(diskio_write_time[1m]), "instance", '
    '"$1", "host", "(.+)"), "device", "$1", "name", "(.+)") / '
    'label_replace(label_replace(irate(diskio_writes[1m]), "instance", "$1", '
    '"host", "(.+)"), "device", "$1", "name", "(.+)") and on '
    '(instance, device) ceph_disk_occupation{ceph_daemon=~"osd.[[osd_id]]"}',
    'irate(ceph_osd_op_w_in_bytes{ceph_daemon=~"osd.[[osd_id]]"}[1m])',
    'irate(ceph_osd_op_r_out_bytes{ceph_daemon=~"osd.[[osd_id]]"}[1m])',
    'label_replace(label_replace(irate(diskio_reads[1m]), "instance", "$1", '
    '"host", "(.+)"), "device", "$1", "name", "(.+)") and on '
    '(instance, device) ceph_disk_occupation{ceph_daemon=~"osd.[[osd_id]]"}',
    'label_replace(label_replace(irate(diskio_writes[1m]), "instance", "$1", '
    '"host", "(.+)"), "device", "$1", "name", "(.+)") and on '
    '(instance, device) ceph_disk_occupation{ceph_daemon=~"osd.[[osd_id]]"}',
    'irate(ceph_osd_op_r_latency_sum{ceph_daemon=~"osd.[[osd_id]]"}[1m]) / '
    'on (ceph_daemon) irate(ceph_osd_op_r_latency_count[1m]) * 1000',
    'label_replace(label_replace(irate(diskio_io_time[1m]), "instance", "$1", '
    '"host", "(.+)"), "device", "$1", "name", "(.+)") and on '
    '(instance, device) ceph_disk_occupation{ceph_daemon=~"osd.[[osd_id]]"}',
    'irate(ceph_osd_op_w_latency_sum{ceph_daemon=~"osd.[[osd_id]]"}[1m]) / '
    'on (ceph_daemon) irate(ceph_osd_op_w_latency_count[1m]) * 1000',
    'irate(ceph_osd_op_r{ceph_daemon=~"osd.[[osd_id]]"}[1m])',
    'irate(ceph_osd_op_w{ceph_daemon=~"osd.[[osd_id]]"}[1m])',
    'label_replace(label_replace(irate(diskio_write_bytes[1m]), "instance", '
    '"$1", "host", "(.+)"), "device", "$1", "name", "(.+)") and on '
    '(instance, device) ceph_disk_occupation{ceph_daemon=~"osd.[[osd_id]]"}',
    'label_replace(label_replace(irate(diskio_read_bytes[1m]), "instance", '
    '"$1", "host", "(.+)"), "device", "$1", "name", "(.+)") and on '
    '(instance, device) ceph_disk_occupation{ceph_daemon=~"osd.[[osd_id]]"}',
    # ceph-pools-overview
    'avg((rate(ceph_pool_rd_bytes{pool_id=~"[[pool_id]]"}[1m]) + '
    'rate(ceph_pool_wr_bytes{pool_id=~"[[pool_id]]"}[1m])) + '
    'on(pool_id,instance) group_left(name) '
    'ceph_pool_metadata{pool_id=~"[[pool_id]]"}) without (instance)',
    'topk(5,(label_replace((irate(ceph_pool_rd{pool_id=~"[[pool_id]]"}[1m]) + '
    'irate(ceph_pool_wr{pool_id=~"[[pool_id]]"}[1m])),"id", "$1", "pool_id", '
    '"(.*)") + on(pool_id) group_left(instance,name) '
    'ceph_pool_metadata{pool_id=~"[[pool_id]]"}) )',
    '(label_replace((irate(ceph_pool_rd_bytes{pool_id=~"[[pool_id]]"}[1m]) + '
    'irate(ceph_pool_wr_bytes{pool_id=~"[[pool_id]]"}[1m])),"id", "$1", '
    '"pool_id", "(.*)") + on(pool_id) group_left(instance,name) '
    'ceph_pool_metadata{pool_id=~"[[pool_id]]"}) ',
    'avg((rate(ceph_pool_rd{pool_id=~"[[pool_id]]"}[1m]) + '
    'rate(ceph_pool_wr{pool_id=~"[[pool_id]]"}[1m])) + '
    'on(pool_id,instance) group_left(name) '
    'ceph_pool_metadata{pool_id=~"[[pool_id]]"}) without (instance)',
]


ignored_queries_for_partial_fail = [
    # Haproxy connections are not present on all nodes
    'max(haproxy_server_ssl_connections {host=~"$host"}) without(pid) > 0',
    'max(haproxy_server_connections {host=~"$host"}) without(pid) > 0',

    # Values coming only from two nodes PROD-19161
    'max(elasticsearch_indices_search_fetch_latency{host="$host"}',

    # K8s. We can have pods only on controllers
    'sum(rate(kubernetes_pod_container_cpu_usage_core_nanoseconds'
    '{host=~"^$host$"}[$rate_interval]) / 1000000000) / sum (system_n_cpus'
    '{host=~"^$host$"}) * 100',
    'sum(kubernetes_pod_container_memory_working_set_bytes{host=~"$host"}) '
    'by (pod_name)',
    'sum(kubernetes_pod_container_memory_working_set_bytes{host=~"$host"}) / '
    '(sum(kubernetes_node_memory_available_bytes{host=~"$host"}) + '
    'sum(kubernetes_node_memory_working_set_bytes{host=~"$host"})) * 100',
    'sum(kubernetes_pod_container_memory_working_set_bytes{host=~"$host"})',
    'sum(rate(kubernetes_pod_network_rx_bytes{host=~"^$host$"}'
    '[$rate_interval])) by (pod_name)',
    'sum(rate(kubernetes_pod_network_tx_bytes{host=~"^$host$"}'
    '[$rate_interval])) by (pod_name)',
    'sum(rate(kubernetes_pod_container_cpu_usage_core_nanoseconds'
    '{host=~"^$host$"}[$rate_interval]) / 1000000000)  ',
    'sum(rate(kubernetes_pod_container_cpu_usage_core_nanoseconds'
    '{host=~"^$host$"}[$rate_interval])) by (pod_name) / 1000000000',
    'kubernetes_pod_volume_available_bytes{host=~"^$host$"}',
    'sum(rate(kubernetes_pod_container_cpu_usage_core_nanoseconds'
    '{host=~"^$host$"}[$rate_interval]) / 1000000000)',
    'kubernetes_pod_volume_used_bytes{host=~"^$host$"}',
    'kubernetes_pod_container_rootfs_used_bytes{host=~"^$host$"}',

    # Ceph. We may not have metrics for all Ceph resources right after
    # deployment
    # ceph-pool-details
    '((ceph_pool_max_avail - ceph_pool_stored) / '
    'deriv(ceph_pool_stored[6h])) * on(pool_id) group_left(instance,name) '
    'ceph_pool_metadata{name=~"$pool_name"} > 0',
    '((ceph_pool_max_avail - ceph_pool_bytes_used) / '
    'deriv(ceph_pool_bytes_used[6h])) * on(pool_id) group_left(instance,name) '
    'ceph_pool_metadata{name=~"$pool_name"} > 0',
]


def idfy_name(name):
    return name.lower().replace(" ", "-").replace("(", "").replace(")", "")


def query_dict_to_string(query_dict):
    return "\n\n".join(
        [panel + "\n" + query for panel, query in query_dict.items()])


def get_all_grafana_dashboards_names():
    dashboards = {
        "Alertmanager": "I@prometheus:server",
        "Apache": "I@apache:server",
        # TODO(vgusev): change pillar for bond
        "Bond": "I@linux:network:interface:bond0",
        "Calico": "I@kubernetes:master:network:calico:enabled:True",
        "Cassandra": "I@opencontrail:database",
        "Ceph Cluster": "I@ceph:common",
        "Ceph Hosts Overview": "I@ceph:common",
        "Ceph OSD device details": "I@ceph:osd",
        "Ceph OSD Overview": "I@ceph:osd",
        "Ceph Pool Details": "I@ceph:common",
        "Ceph Pools Overview": "I@ceph:common",
        "Ceph RBD Overview": "I@ceph:common:rbd_monitoring_enabled",
        "Ceph RGW Instance Detail": "I@ceph:radosgw",
        "Ceph RGW Overview": "I@ceph:radosgw",
        "Cinder": "I@cinder:controller",
        "Docker": "I@docker:client",
        "Elasticsearch": "I@elasticsearch:server",
        "Etcd Cluster": "I@etcd:server",
        "Glance": "I@glance:server",
        "GlusterFS": "I@glusterfs:server",
        "Grafana": "I@grafana:client",
        "HAProxy": "I@haproxy:proxy",
        "Heat": "I@heat:server",
        "InfluxDB": "I@influxdb:server",
        "InfluxDB Relay": "I@influxdb:relay",
        "Ironic": "I@ironic:conductor",
        "Jenkins": "I@jenkins:client and I@docker:swarm:role:master",
        "Keepalived": "I@keepalived:cluster",
        "Keystone": "I@keystone:server",
        "Kibana": "I@kibana:server",
        "KPI Downtime":
            "I@linux:network:bridge:openvswitch or I@opencontrail:*",
        "KPI Provisioning": "I@nova:controller",
        "Kubernetes cluster monitoring": "I@kubernetes:pool",
        "Memcached": "I@memcached:server",
        "MySQL": "I@galera:master",
        "Neutron": "I@neutron:server",
        "Nginx": "I@nginx:server",
        "Nova Availability Zones": "I@nova:controller",
        "Nova Hypervisor Overview": "I@nova:compute",
        "Nova Instances": "I@nova:controller",
        "Nova Overview": "I@nova:controller",
        "Nova Tenants": "I@nova:controller",
        "Nova Users": "I@nova:controller",
        "Nova Utilization": "I@nova:controller",
        "Ntp": "I@linux:system",
        "Octavia": "I@octavia:api",
        "OpenContrail Controller": "I@opencontrail:control",
        "OpenContrail vRouter": "I@opencontrail:compute",
        "Openstack overview": "I@nova:controller",
        "Prometheus Performances": "I@prometheus:server",
        "Prometheus Relay": "I@prometheus:relay",
        "Prometheus Stats": "I@prometheus:server",
        "Pushgateway": "I@prometheus:server",
        "RabbitMQ": "I@rabbitmq:server",
        "Remote storage adapter": "I@prometheus:remote_storage_adapter",
        # System dasboard was divided into three, skip:
        # "System": "linux",
        "System Disk I O": "I@linux:system",
        "System Networking": "I@linux:system",
        "System Overview": "I@linux:system",
        "Zookeeper": "I@opencontrail:database",
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
def dashboard_name(request, salt_actions):
    dash_name, requirement = request.param

    if not salt_actions.ping(requirement):
        pytest.skip("No nodes with target {} for dashboard: {}".format(
            requirement, dash_name))

    return dash_name


@pytest.mark.dashboards
@pytest.mark.run(order=-1)
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


@pytest.mark.dashboards
def test_panels_fixture(grafana_client):
    dashboards = grafana_client.get_all_dashboards_names()
    # Workaround for Main dashboard
    dashboards.remove("main")
    fixture_dashboards = get_all_grafana_dashboards_names().keys()
    missing_dashboards = set(dashboards).difference(set(fixture_dashboards))

    assert len(missing_dashboards) == 0, \
        ("Update test data fixture with the missing dashboards: "
         "{}".format(missing_dashboards))


@pytest.mark.dashboards
def test_grafana_database_type(salt_actions):
    db_type = salt_actions.get_pillar_item(
        "I@grafana:client",
        "docker:client:stack:"
        "dashboard:service:grafana:"
        "environment:GF_DATABASE_TYPE")[0]

    assert db_type == "mysql"
