from alertaclient.api import Client
from pymongo import MongoClient
import pytest

from stacklight_tests.clients import es_kibana_api
from stacklight_tests.clients import grafana_api
from stacklight_tests.clients.openstack import client_manager  # noqa
from stacklight_tests.clients.prometheus import alertmanager_client
from stacklight_tests.clients.prometheus import prometheus_client
from stacklight_tests.clients import k8s_client


@pytest.fixture(scope="session")
def k8s_api():
    api_client = k8s_client.get_k8s_client()
    return api_client


@pytest.fixture(scope="session")
def sl_services(k8s_api):
    return k8s_api.sl_services()


@pytest.fixture(scope="session")
def nodes(k8s_api):
    return k8s_api.nodes()


@pytest.fixture(scope="session")
def daemonsets(k8s_api):
    return k8s_api.daemonsets()


@pytest.fixture(scope="session")
def deployments(k8s_api):
    return k8s_api.deployments()


@pytest.fixture(scope="session")
def replicasets(k8s_api):
    return k8s_api.replicasets()


@pytest.fixture(scope="session")
def statefulsets(k8s_api):
    return k8s_api.statefulsets()


@pytest.fixture(scope="session")
def prometheus_api(sl_services):
    sl_services.get('prometheus-server')
    api_client = prometheus_client.get_prometheus_client(
        sl_services['prometheus-server']['ip'],
        sl_services['prometheus-server']['port'])
    return api_client


@pytest.fixture(scope="session")
def es_client(sl_services):
    elasticsearch_api = es_kibana_api.ElasticSearchApi(
        scheme='http',
        host=sl_services['elasticsearch-master']['ip'],
        port=sl_services['elasticsearch-master']['port'])
    return elasticsearch_api


@pytest.fixture(scope="session")
def kibana_client(sl_services):
    kibana_api = es_kibana_api.KibanaApi(
        host=sl_services['kibana']['ip'],
        port=sl_services['kibana']['port'],
    )
    return kibana_api


@pytest.fixture(scope="session")
def grafana_client(sl_services, prometheus_api):
    grafana = grafana_api.GrafanaApi(
        address=sl_services['grafana']['ip'],
        port=sl_services['grafana']['port'],
        datasource=prometheus_api,
    )
    return grafana


@pytest.fixture(scope="session")
def mongodb_api(sl_services):
    return MongoClient("mongodb://root:r00tme@{}:{}/admin".format(
        sl_services["mongodb"]["ip"], sl_services["mongodb"]["port"]))


@pytest.fixture(scope="session")
def alerta_api(sl_services):
    endpoint = "http://{0}:{1}/api".format(sl_services["alerta"]["ip"],
                                           sl_services["alerta"]["port"])
    client = Client(endpoint=endpoint, ssl_verify=False)
    return client


@pytest.fixture(scope="session")
def prometheus_native_alerting(sl_services):
    alerting = alertmanager_client.AlertManagerClient(
        "http://{0}:{1}/".format(
            sl_services["prometheus-alertmanager"]["ip"],
            sl_services["prometheus-alertmanager"]["port"])
    )
    return alerting
#
#
# @pytest.fixture(scope="session")
# def prometheus_alerting(prometheus_config, prometheus_native_alerting):
#     if not prometheus_config.get("use_prometheus_query_alert", True):
#         alerting = prometheus_native_alerting
#     else:
#         alerting = (
#             alertmanager_client.PrometheusQueryAlertClient(
#                 "http://{0}:{1}/".format(
#                     prometheus_config["prometheus_vip"],
#                     prometheus_config["prometheus_server_port"])
#             )
#         )
#     return alerting
#
#
# @pytest.fixture(scope="session")
# def os_clients(keystone_config):
#     auth_url = "{}://{}:{}/".format(
#         keystone_config["private_protocol"],
#         keystone_config["private_address"],
#         keystone_config["private_port"])
#     if "OS_ENDPOINT_TYPE" in os.environ.keys():
#         if os.environ["OS_ENDPOINT_TYPE"] in ["public", "publicURL"]:
#             auth_url = "{}://{}:{}/".format(
#                 keystone_config["private_protocol"],
#                 keystone_config["public_address"],
#                 keystone_config["private_port"])
#     openstack_clients = client_manager.OfficialClientManager(
#         username=keystone_config["admin_name"],
#         password=keystone_config["admin_password"],
#         tenant_name=keystone_config["admin_tenant"],
#         auth_url=auth_url,
#         cert=False,
#         domain=keystone_config.get("domain", "Default"),
#     )
#     return openstack_clients
#
#
# @pytest.fixture(scope="session")
# def os_actions(os_clients):
#     return client_manager.OSCliActions(os_clients)
