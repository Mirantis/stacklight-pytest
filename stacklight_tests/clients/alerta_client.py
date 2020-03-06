import json
import logging

from stacklight_tests.clients import http_client
from stacklight_tests import settings

logger = logging.getLogger(__name__)


class AlertaApi(http_client.HttpClient):
    def get_count(self):
        resp = self.get("/api/alerts/count").content
        query_result = json.loads(resp)
        return query_result

    def get_alerts(self, query=None):
        resp = self.get("/api/alerts", params=query).content
        query_result = json.loads(resp)
        return query_result['alerts']


def get_alerta_client(ip, port, user=None, password=None, url=None):
    api_client = AlertaApi(
        base_url="http://{0}:{1}/".format(ip, port),
        user=user, password=password, keycloak_url=url,
        secret=settings.IAM_PROXY_ALERTA_SECRET
    )
    return api_client
