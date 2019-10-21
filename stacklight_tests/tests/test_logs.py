import json
import logging
import pytest

from stacklight_tests import settings

logger = logging.getLogger(__name__)


@pytest.mark.run(order=1)
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


@pytest.mark.run(order=1)
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


@pytest.mark.run(order=1)
@pytest.mark.smoke
@pytest.mark.logs
def test_pod_logs(k8s_api, kibana_client):
    ret = k8s_api.list_pod_for_all_namespaces()
    pods = [pod.metadata.name for pod in ret.items]
    q = ('{"size": "0", "aggs": {"uniq_logger": {"terms": '
         '{"field": "kubernetes.pod_name", "size": 500}}}}')
    output = json.loads(kibana_client.get_query(q))
    kibana_loggers = [log["key"] for log in
                      output["aggregations"]["uniq_logger"]["buckets"]]
    missing_loggers = []
    for pod in pods:
        if pod not in kibana_loggers:
            missing_loggers.append(pod)
    if settings.SL_TEST_POD in missing_loggers:
        missing_loggers.remove(settings.SL_TEST_POD)
    msg = ('Logs from {} pods not found in Kibana'.format(', '.join(
        missing_loggers)))
    assert len(missing_loggers) == 0, msg


@pytest.mark.run(order=1)
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
    msg = (
        'Logs from not all nodes are in Elasticsearch. '
        'Found {} nodes, expected {}. Missing nodes: {}'.format(
            len(found_nodes), len(expected_nodes), missing_nodes)
    )
    for node in expected_nodes:
        if node not in found_nodes:
            missing_nodes.append(node)
    assert len(missing_nodes) == 0, msg
