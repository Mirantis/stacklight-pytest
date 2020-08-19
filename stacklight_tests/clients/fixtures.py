import pytest

from stacklight_tests import settings
from stacklight_tests.clients import alerta_client
from stacklight_tests.clients import es_kibana_api
from stacklight_tests.clients import grafana_api
from stacklight_tests.clients.openstack import client_manager  # noqa
from stacklight_tests.clients.prometheus import alertmanager_client
from stacklight_tests.clients.prometheus import prometheus_client
from stacklight_tests.clients import k8s_client
from stacklight_tests.clients import keycloak_client


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
def keycloak_api():
    client = keycloak_client.get_keycloak_client(
        settings.KEYCLOAK_USER, settings.KEYCLOAK_PASSWORD,
        settings.KEYCLOAK_URL)
    return client


@pytest.fixture(scope="session")
def prometheus_api(sl_services):
    if 'iam-proxy-prometheus' in sl_services.keys():
        api_client = prometheus_client.get_prometheus_client(
            sl_services['iam-proxy-prometheus']['external_ip'],
            sl_services['iam-proxy-prometheus']['port'],
            settings.KEYCLOAK_USER, settings.KEYCLOAK_PASSWORD,
            settings.KEYCLOAK_URL)
    else:
        api_client = prometheus_client.get_prometheus_client(
            sl_services['prometheus-server']['ip'],
            sl_services['prometheus-server']['port']
        )
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
    if not logging_enabled:
        pytest.skip("Logging is disabled for this cluster.")
    if 'iam-proxy-kibana' in sl_services.keys():
        kibana_api = es_kibana_api.get_kibana_client(
            sl_services['iam-proxy-kibana']['external_ip'],
            sl_services['iam-proxy-kibana']['port'],
            settings.KEYCLOAK_USER, settings.KEYCLOAK_PASSWORD,
            settings.KEYCLOAK_URL)
    else:
        kibana_api = es_kibana_api.get_kibana_client(
            sl_services['kibana']['ip'],
            sl_services['kibana']['port'])
    return kibana_api


@pytest.fixture(scope="session")
def grafana_client(sl_services, prometheus_api):
    if 'iam-proxy-grafana' in sl_services.keys():
        grafana = grafana_api.get_grafana_client(
            address=sl_services['iam-proxy-grafana']['external_ip'],
            port=sl_services['iam-proxy-grafana']['port'],
            datasource=prometheus_api,
            user=settings.KEYCLOAK_USER, password=settings.KEYCLOAK_PASSWORD,
            keycloak_url=settings.KEYCLOAK_URL)
    else:
        grafana = grafana_api.get_grafana_client(
            address=sl_services['grafana']['ip'],
            port=sl_services['grafana']['port'],
            datasource=prometheus_api
        )
    return grafana


@pytest.fixture(scope="session")
def alerta_api(sl_services):
    if 'iam-proxy-alerta' in sl_services.keys():
        api_client = alerta_client.get_alerta_client(
            sl_services['iam-proxy-alerta']['external_ip'],
            sl_services['iam-proxy-alerta']['port'],
            settings.KEYCLOAK_USER, settings.KEYCLOAK_PASSWORD,
            settings.KEYCLOAK_URL)
    else:
        api_client = alerta_client.get_alerta_client(
            sl_services['alerta']['ip'],
            sl_services['alerta']['port'])
    return api_client


@pytest.fixture(scope="session")
def prometheus_native_alerting(sl_services):
    if 'iam-proxy-alertmanager' in sl_services.keys():
        alerting = alertmanager_client.AlertManagerClient(
            base_url="http://{0}:{1}/".format(
                sl_services["iam-proxy-alertmanager"]["external_ip"],
                sl_services["iam-proxy-alertmanager"]["port"]),
            user=settings.KEYCLOAK_USER, password=settings.KEYCLOAK_PASSWORD,
            keycloak_url=settings.KEYCLOAK_URL,
            secret=settings.IAM_PROXY_ALERTMANAGER_SECRET
        )
    else:
        alerting = alertmanager_client.AlertManagerClient(
            base_url="http://{0}:{1}/".format(
                sl_services["prometheus-alertmanager"]["ip"],
                sl_services["prometheus-alertmanager"]["port"]))
    return alerting


@pytest.fixture(scope="session")
def os_clients(k8s_api):
    related_release = 'telegraf-openstack'
    releases = k8s_api.get_stacklight_chart_releases()
    if related_release in releases:
        creds = k8s_api.get_openstack_credentials()
        openstack_clients = client_manager.OfficialClientManager(
            username=creds["OS_USERNAME"],
            password=creds["OS_PASSWORD"],
            tenant_name=creds["OS_PROJECT_NAME"],
            auth_url=creds["OS_AUTH_URL"],
            cert=False,
            domain=creds["OS_DEFAULT_DOMAIN"],
        )
        return openstack_clients


@pytest.fixture(scope="session")
def os_actions(os_clients):
    return client_manager.OSCliActions(os_clients)


@pytest.fixture(scope="session")
def chart_releases(k8s_api):
    return k8s_api.get_stacklight_chart_releases()


@pytest.fixture(scope="session")
def charts_statuses(k8s_api):
    return k8s_api.get_stacklight_charts_statuses()


@pytest.fixture(scope="session")
def logging_enabled(k8s_api):
    return k8s_api.logging_enabled()
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
