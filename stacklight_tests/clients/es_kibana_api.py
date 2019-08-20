import logging

import elasticsearch

from stacklight_tests.clients import http_client
from stacklight_tests import utils

logger = logging.getLogger(__name__)


class ElasticSearchApi(object):
    def __init__(self, scheme, host, port=9200):
        super(ElasticSearchApi, self).__init__()
        self.url = "{scheme}://{host}:{port}".format(
            scheme=scheme, host=host, port=port)
        auth_dict = {'scheme': scheme, 'host': host, 'port': port}
        if scheme == 'https':
            auth_dict.update({'use_ssl': True, 'verify_certs': False})
        self.es = elasticsearch.Elasticsearch(**auth_dict)
        self._kibana_protocol = None

    def query_elasticsearch(self, index_type="log", time_range="now-1h",
                            query_filter="*", size=100):
        return self.es.search(
            index="log-*",
            body={"query": {
                "query_string": {
                    "fields": ["Logger", "programname"],
                    "query": query_filter
                }
            }
            })

    def search(self, index='logstash-*', body={}):
        return self.es.search(index=index, body=body)

    def health(self):
        return self.es.cluster.health()

    def check_notifications(self, expected_notifications,
                            index_type="notification", timeout=5 * 60,
                            interval=10, **kwargs):
        def _verify_notifications(expected_list):
            output = self.query_elasticsearch(index_type=index_type, **kwargs)
            got = set(hit["_source"]["event_type"]
                      for hit in output["hits"]["hits"])
            delta = set(expected_list) - got
            if delta:
                logger.info("{} event type not found in {}".format(delta, got))
                return False
            return True

        logger.info("Waiting to get all notifications")
        msg = "Timed out waiting to get all notifications"
        utils.wait(
            lambda: _verify_notifications(expected_notifications),
            timeout=timeout, interval=interval, timeout_msg=msg)

    def log_is_presented(self, query_filter, time_range="now-1m"):
        # type: (str) -> None
        res = self.query_elasticsearch(
            query_filter=query_filter, time_range=time_range)
        return len(res['hits']['hits']) > 0

    def get_absent_programs_for_group(self, program_group, **kwargs):
        return {program for program in program_group
                if not self.log_is_presented(program, **kwargs)}

    def list_loggers(self):
        q = {"size": "0",
             "aggs": {
                 "uniq_logger": {
                     "terms": {"field": "Logger.keyword", "size": 500}}}}
        output = self.search(body=q)
        return [log["key"] for log in
                output["aggregations"]["uniq_logger"]["buckets"]]


class KibanaApi(http_client.HttpClient):
    def get_query(self, query, path='_search', method='POST'):
        url = "/api/console/proxy?path={}&method={}".format(path, method)
        resp = self.post(url, body=query)
        return resp.content

    def get_elasticsearch_status(self):
        status = self.get_query(
            query='{}', path='_cluster/health', method='GET')
        return status

    def get_kibana_status(self):
        status = self.get('/api/status')
        return status.content


def get_kibana_client(ip, port, user, password, url):
    api_client = KibanaApi(
        base_url="http://{0}:{1}/".format(ip, port),
        user=user, password=password, keycloak_url=url,
        headers={'kbn-version': '7.1.0'}
    )
    return api_client
