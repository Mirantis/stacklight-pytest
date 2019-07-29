import json
import logging
import pytest

from stacklight_tests import utils


logger = logging.getLogger(__name__)


@pytest.mark.run(order=1)
@pytest.mark.smoke
@pytest.mark.logs
def test_elasticsearch_status(es_client):
    logger.info("Getting Elasticsearch status")
    status = es_client.health()

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
    resp = utils.check_http_get_response(
        "{}/api/status".format(kibana_client.url))
    assert resp, ("Cannot get Kibana status through API, "
                  "check that Kibana is running")
    status = json.loads(resp.content)

    logger.info("Check overall Kibana status")
    assert status['status']['overall']['state'] == "green", \
        ("Kibana status is not 'green', current status is '{}'".format(
            status['status']['overall']))

    logger.info("Check status of Kibana plugins")
    msg = "Status of {} is not 'green', current status is '{}'"
    for plugin in status['status']['statuses']:
        assert plugin['state'] == "green", msg.format(
            plugin["id"], plugin["state"])


@pytest.mark.smoke
@pytest.mark.logs
def test_pod_logs(k8s_api, es_client):
    ret = k8s_api.list_pod_for_all_namespaces()
    pods = [pod.metadata.name for pod in ret.items]
    q = {"size": "0",
         "aggs": {
             "uniq_logger": {
                 "terms":
                     {"field": "kubernetes.pod_name", "size": 500}}}}
    output = es_client.search(body=q)
    kibana_loggers = [log["key"] for log in
                      output["aggregations"]["uniq_logger"]["buckets"]]
    missing_loggers = []
    for pod in pods:
        if pod not in kibana_loggers:
            missing_loggers.append(pod)
    msg = ('Logs from {} pods not found in Kibana'.format(', '.join(
        missing_loggers)))
    assert len(missing_loggers) == 0, msg


@pytest.mark.smoke
@pytest.mark.logs
def test_node_count_in_es(es_client, nodes):
    expected_nodes = nodes.keys()
    q = {"size": "0",
         "aggs": {
             "uniq_hostnames": {
                 "terms": {"field": "kubernetes.host", "size": 500}}}}
    output = es_client.search(body=q)
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
