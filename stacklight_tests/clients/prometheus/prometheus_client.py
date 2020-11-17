import json
import logging
import re

from stacklight_tests import utils
from stacklight_tests.clients import http_client
from stacklight_tests import settings

logger = logging.getLogger(__name__)


class PrometheusClient(http_client.HttpClient):
    measurements = None

    def get_updated_prometheus_query(self, query):
        updates = {'$__range': '1h',
                   '${__range_s}': '3600',
                   '$topx': '5',
                   '$ident': 'instance_name'}
        for k, v in updates.items():
            query = query.replace(k, v)
        return query

    def get_query(self, query, timestamp=None):
        params = {
            "query": self.get_updated_prometheus_query(query)
        }

        if timestamp is not None:
            params.update({"time": timestamp})

        resp = self.get("/api/v1/query", params=params).content

        query_result = json.loads(resp)

        if query_result["status"] != "success":
            raise Exception("Failed resp: {}".format(resp))

        return query_result["data"]["result"]

    def get_query_range(self, query, start_time, end_time, step):
        params = {
            "query": query,
            "start": start_time,
            "end": end_time,
            "step": step,
        }

        # TODO: Add proper return
        return self.get("/api/v1/query_range", params=params).content

    def get_series(self, match):
        if issubclass(list, match):
            match = [match]

        params = {
            "match[]": match
        }

        # TODO: Add proper return
        return self.get("/api/v1/series", params=params).content

    def get_label_values(self, label_name):
        resp = self.get("/api/v1/label/{}/values".format(label_name)).content
        query_result = json.loads(resp)
        if query_result["status"] != "success":
            raise Exception("Failed resp: {}".format(resp))
        return query_result["data"]

    def delete_series(self, match):
        if issubclass(list, match):
            match = [match]

        params = {
            "match[]": match
        }

        self.delete("/api/v1/series", params=params)

    def get_targets(self):
        resp = self.get("/api/v1/targets").content

        targets = json.loads(resp)
        return targets["data"]["activeTargets"]

    def get_alertmanagers(self):
        resp = self.get("/api/v1/alertmanagers").content

        alertmanagers = json.loads(resp)
        return alertmanagers["data"]["activeAlertmanagers"]

    def _do_label_values_query(self, label_values_query):
        pattern = (r"label_values\("
                   r"((?P<query>[\w:]*({.*}){0,1}),\s*){0,1}"
                   r"(?P<label>[\w$]*)\)")
        m = re.match(pattern, label_values_query)
        query = m.group("query")
        label = m.group("label")

        if query is None:
            return self.get_label_values(label)
        return list(
            {res['metric'][label] for res in self.get_query(query)
             if res.get('metric', {}).get(label)})

    def _do_query_result_query(self, query, regex=None):
        def convert_to_human_readable_string(metric):
            metric_string = metric["__name__"] + "{"
            items = ['{}="{}"'.format(name, value)
                     for name, value in metric.items()
                     if name != "__name__"]
            metric_string += ",".join(items)
            return metric_string + "}"

        pattern = r"query_result\((?P<query>.*)\)"
        m = re.match(pattern, query)
        query = m.group("query")
        result = [convert_to_human_readable_string(entity["metric"])
                  for entity in self.get_query(query)]
        if regex is not None:
            regex = regex.strip("/")
            result = [re.search(regex, item).group(1) for item in result]
        return result

    def do_query(self, query, regex=None, **kwargs):
        if "label_values" in query:
            return self._do_label_values_query(query)
        if "query_result" in query:
            return self._do_query_result_query(query, regex)
        return self.get_query(query, **kwargs)

    @staticmethod
    def compile_query(query, replaces):
        for pattern, value in replaces.items():
            query = query.replace(pattern, value)
        return query

    def get_all_measurements(self):
        if self.measurements is None:
            self.measurements = set(self.get_label_values("__name__"))
            self.measurements.discard("ALERTS")
        return self.measurements

    def parse_measurement(self, query):
        for measurement in self.get_all_measurements():
            if measurement in query:
                return measurement

    def check_metric_values(self, query, value, msg=None):
        def _verify_notifications(q, v):
            output = self.get_query(q)
            logger.info("Check '{}' value in {} metric values".format(
                v, output))
            if not output:
                logger.error('Empty results received, '
                             'check a query "{0}"'.format(q))
                return False
            return v in output[0]["value"]
        msg = msg if msg else 'Incorrect value in metric {}'.format(query)
        utils.wait(
            lambda: _verify_notifications(query, str(value)),
            interval=30, timeout=5 * 60, timeout_msg=msg
        )

    def get_rules(self):
        resp = self.get("/api/v1/rules").content

        targets = json.loads(resp)
        return targets["data"]['groups']

    def get_all_defined_alerts(self):
        rules = self.get_rules()
        alerts = {}
        for rule in rules:
            alerting_rules = filter(
                lambda x: x['type'] == 'alerting', rule['rules'])
            for alert in alerting_rules:
                alerts[alert['name']] = {
                    'query': alert['query'],
                    'severity': alert['labels']['severity']}
        return alerts


def get_prometheus_client(ip, port, user=None, password=None, url=None):
    api_client = PrometheusClient(
        base_url="http://{0}:{1}/".format(ip, port),
        user=user, password=password, keycloak_url=url,
        secret=settings.IAM_PROXY_PROMETHEUS_SECRET
    )
    return api_client
