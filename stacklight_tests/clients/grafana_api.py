import logging

from stacklight_tests.clients import grafana_templates_builder
from stacklight_tests.clients import http_client
from stacklight_tests import settings
from stacklight_tests import utils


check_http_get_response = utils.check_http_get_response

logger = logging.getLogger(__name__)


class Dashboard(object):
    def __init__(self, dash_dict, datasource):
        self.name = dash_dict["meta"]["slug"]
        self.dash_dict = dash_dict
        self._datasource = datasource
        self._templates_tree = self.get_templates_tree()

    def __repr__(self):
        return "{}: {}".format(self.__class__, self.name)

    @property
    def panels(self):
        # Handle old style nested panels
        if "rows" in self.dash_dict["dashboard"]:
            for row in self.dash_dict["dashboard"]["rows"]:
                for panel in row["panels"]:
                    yield panel, row

        # Handle new style flat panels
        if "panels" in self.dash_dict["dashboard"]:
            row = {"title": "No row"}
            for panel in self.dash_dict["dashboard"]["panels"]:
                if panel["type"] == "row":
                    row["title"] = panel["title"]
                else:
                    yield panel, row

    def get_templates_tree(self):
        if "templating" not in self.dash_dict["dashboard"]:
            template_queries = {}
        else:
            template_queries = {}
            defaults_update = {}

            for item in self.dash_dict["dashboard"]["templating"]["list"]:
                # Handle static templating variables
                if item["type"] in ["interval", "custom"]:
                    if isinstance(item["current"]["value"], list):
                        value = item["current"]["value"][0]
                    else:
                        value = item["current"]["value"]
                    defaults_update.update({"${}".format(item["name"]): value})

                # Handle query templating variables
                if item["type"] == "query":
                    template_queries.update({
                        "${}".format(
                            item["name"]): (item["query"], item["regex"])})

        return grafana_templates_builder.TemplatesTree(template_queries,
                                                       self._datasource,
                                                       defaults_update)

    def get_all_templates_for_query(self, query):
        return self._templates_tree.get_all_templates_for_query(query)

    @staticmethod
    def build_query(target, panel_name):
        if target.get("rawQuery"):
            return target["query"]
        if target.get("expr"):
            return target["expr"]
        raise Exception("Expression/Query for the panel '{}' at the ref '{}' "
                        "is empty.".format(panel_name, target.get("refId",
                                                                  "A")))

    def get_panel_queries(self):
        panel_queries = {}
        for panel, row in self.panels:
            panel_name = "{}->{}".format(row["title"], panel["title"] or "n/a")
            for target in panel.get("targets", []):
                query = self.build_query(target, panel_name)
                query_name = "{}:{}->RefId:{}".format(
                    panel["id"], panel_name, target.get("refId", "A"))
                panel_queries[query_name] = query
        return panel_queries


class GrafanaApi(object):
    def __init__(self, address, port, datasource, tls=False,
                 user=None, password=None, keycloak_url=None):
        super(GrafanaApi, self).__init__()
        self.address = address
        self.port = port
        self.datasource = datasource
        scheme = "https" if tls else "http"
        self.grafana_api_url = "{scheme}://{host}:{port}/".format(
            scheme=scheme, host=address, port=port)
        self.http = http_client.HttpClient(
            self.grafana_api_url, user, password, keycloak_url,
            secret=settings.IAM_PROXY_GRAFANA_SECRET)

    def check_grafana_online(self):
        self.http.get("/login")
        self.http.get("/api/org")

    def _get_raw_dashboard(self, name):
        response = self.http.get("/api/dashboards/db/{}".format(name))
        if response.status_code == 200:
            return response
        else:
            response.raise_for_status()

    def get_dashboard(self, name):
        raw_dashboard = self._get_raw_dashboard(name)
        if raw_dashboard:
            return Dashboard(raw_dashboard.json(),
                             self.datasource)

    def get_all_dashboards_names(self):
        result = self.http.get("/api/search")
        return [dash["uri"].replace("db/", "") for dash in result.json()]

    def is_dashboard_exists(self, name):
        if self._get_raw_dashboard(name):
            return True
        return False


def get_grafana_client(address, port, datasource, user=None, password=None,
                       keycloak_url=None):
    return GrafanaApi(address=address, port=port, datasource=datasource,
                      user=user, password=password, keycloak_url=keycloak_url)
