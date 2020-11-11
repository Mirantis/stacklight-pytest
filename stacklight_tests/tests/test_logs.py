import json
import logging
import re
from datetime import timedelta
from dateutil.relativedelta import relativedelta

import pytest

from stacklight_tests import settings

logger = logging.getLogger(__name__)


@pytest.mark.run(order=-1)
@pytest.mark.smoke
@pytest.mark.logs
def test_elasticsearch_status(kibana_client):
    logger.info("Getting Elasticsearch status")
    status = json.loads(kibana_client.get_elasticsearch_status())

    logger.info("Elasticsearch cluster status is \n{}".format(status))
    assert status['status'] == 'green', \
        "Elasticsearch status is not 'green', current status is '{}'".format(
            status['status'])
    assert str(status['active_shards_percent_as_number']) == '100.0', \
        "Some shards are not in 'active' state"


@pytest.mark.run(order=-1)
@pytest.mark.smoke
@pytest.mark.logs
def test_kibana_status(kibana_client):
    logger.info("Getting Kibana status")
    status = json.loads(kibana_client.get_kibana_status())

    logger.info("Check overall Kibana status")
    assert status['status']['overall']['state'] == "green", \
        ("Kibana status is not 'green', current status is '{}'".format(
            status['status']['overall']))

    logger.info("Check status of Kibana plugins")
    msg = "Status of {} is not 'green', current status is '{}'"
    for plugin in status['status']['statuses']:
        assert plugin['state'] == "green", msg.format(
            plugin["id"], plugin["state"])


@pytest.mark.run(order=-1)
@pytest.mark.smoke
@pytest.mark.logs
def test_pod_logs(k8s_api, kibana_client):
    def err_msg(ml_info):
        node_name = ml_info[0]['node_name']
        one_node = True
        for info in ml_info:
            if info['node_name'] != node_name:
                one_node = False
        msg = ('Logs from {} pods not found in ES.'.format(ml_info))
        if one_node:
            msg += ' All pods are from the one node {}.'.format(node_name)
        return msg

    def pod_info(p):
        p_info = {'name': p.metadata.name,
                  'node_name': p.spec.node_name,
                  'namespace': p.metadata.namespace}
        return p_info

    def collect_pods(running_pods, jobs_ct,
                     r_u, r_u_c):
        if jobs_ct:
            retention_args = {r_u: r_u_c}
            last_job_time = max(jobs_ct)
            result = [pod_info(p)
                      for p in running_pods.items if p.metadata
                      .creation_timestamp +
                      relativedelta(**retention_args) > last_job_time]
        else:
            result = [pod_info(p) for p in running_pods.items]
        return result

    field_selector = 'status.phase=Running'
    namespace = 'stacklight'
    config_map_name = 'elasticsearch-curator-config'
    config_map = k8s_api.get_namespaced_config_map(config_map_name, namespace)
    retention_unit = re.search('unit:(.*)',
                               config_map.data['action_file.yml'])\
        .group(1).replace('"', '').strip()
    retention_unit_count = int(re.search('unit_count:(.*)',
                               config_map.data['action_file.yml'])
                               .group(1))
    logger.info("Retention Time for logs in ES is {} {}."
                .format(retention_unit_count, retention_unit))
    jobs = k8s_api.get_namespaced_jobs(namespace)
    jobs_creation_time = [job.metadata.creation_timestamp for job in jobs.items
                          if job.metadata.name
                          .startswith("elasticsearch-curator")]
    ret = k8s_api.list_pod_for_all_namespaces(field_selector=field_selector)
    pods = collect_pods(ret, jobs_creation_time, retention_unit,
                        retention_unit_count)
    if not pods:
        pytest.skip("This test is skipped due to the inability to check "
                    "logs from pods in ES. The time that was past from "
                    "the latest created pod is bigger than the "
                    "Retention Time for logs in ES.")
    q = ('{"size": "0", "aggs": {"uniq_logger": {"terms": '
         '{"field": "kubernetes.pod_name", "size": 5000}}}}')
    output = json.loads(kibana_client.get_query(q))
    kibana_loggers = [log["key"] for log in
                      output["aggregations"]["uniq_logger"]["buckets"]]
    missing_loggers = []
    skip_patterns = ['image-precaching-0']
    skip_list = []
    for pod in pods:
        if pod['name'] not in kibana_loggers:
            missing_loggers.append(pod['name'])
        for sp in skip_patterns:
            if sp in pod['name']:
                skip_list.append(pod['name'])
    if settings.STACKLIGHT_TEST_POD_NAME in missing_loggers:
        missing_loggers.remove(settings.STACKLIGHT_TEST_POD_NAME)
    missing_loggers = filter(lambda x: x not in skip_list, missing_loggers)
    missing_loggers_info = [pod for pod in pods
                            if pod['name'] in missing_loggers]
    assert len(missing_loggers) == 0, err_msg(missing_loggers_info)


@pytest.mark.run(order=-1)
@pytest.mark.smoke
@pytest.mark.logs
def test_node_count_in_es(kibana_client, nodes):
    expected_nodes = nodes.keys()
    q = ('{"size": "0", "aggs": {"uniq_hostnames": {"terms": '
         '{"field": "kubernetes.host", "size": 500}}}}')
    output = json.loads(kibana_client.get_query(q))
    found_nodes = [host["key"] for host in
                   output["aggregations"]["uniq_hostnames"]["buckets"]]
    logger.info("\nFound the following nodes in Elasticsearch: \n{}".format(
        found_nodes))
    missing_nodes = []
    for node in expected_nodes:
        if node not in found_nodes:
            missing_nodes.append(node)
    msg = (
        'Logs from not all nodes are in Elasticsearch. '
        'Found {} nodes, expected {}. Missing nodes: {}'.format(
            len(found_nodes), len(expected_nodes), missing_nodes)
    )
    assert len(missing_nodes) == 0, msg


@pytest.mark.run(order=-1)
@pytest.mark.logs
def test_metricbeat(k8s_api, kibana_client):
    field_selector = 'status.phase=Running'
    ret = k8s_api.list_pod_for_all_namespaces(field_selector=field_selector)
    mb_pod = [pod for pod in ret.items if pod.metadata.name
                                .startswith('metricbeat')][0]
    mb_started_time = mb_pod.status.container_statuses[0].state\
        .running.started_at
    delta_time = 120
    pods = []
    for pod in ret.items:
        if pod.status.container_statuses[-1].state.to_dict()\
                .get('running') is not None:
            if (pod.status.container_statuses[-1].state.running.started_at -
                    timedelta(seconds=delta_time)) > mb_started_time:
                pods.append(
                    {'name': pod.metadata.name,
                     'node_name': pod.spec.node_name,
                     'namespace': pod.metadata.namespace}
                )
    q = ('{"size": "0", "aggs": {"uniq_logger": {"terms": '
         '{"field": "kubernetes.event.involved_object.name", "size": 5000}}},'
         '"query": {"bool": {"filter": {"match_phrase": '
         '{"kubernetes.event.involved_object.kind": "Pod"}}}}}')
    output = json.loads(kibana_client.get_query(q))
    kibana_loggers = [log["key"] for log in
                      output["aggregations"]["uniq_logger"]["buckets"]]
    missing_loggers = []
    skip_patterns = []
    skip_list = []
    for pod in pods:
        if pod['name'] not in kibana_loggers:
            missing_loggers.append(pod['name'])
        for sp in skip_patterns:
            if sp in pod['name']:
                skip_list.append(pod['name'])
    if settings.STACKLIGHT_TEST_POD_NAME in missing_loggers:
        missing_loggers.remove(settings.STACKLIGHT_TEST_POD_NAME)
    missing_loggers = filter(lambda x: x not in skip_list, missing_loggers)
    missing_loggers_info = [pod for pod in pods
                            if pod['name'] in missing_loggers]
    msg = ('Kubernetes events from {} pods are not found in Kibana. '
           'Metricbeat doesn\'t capture kubernetes events from these pods.'
           .format(missing_loggers_info))
    assert len(missing_loggers) == 0, msg
