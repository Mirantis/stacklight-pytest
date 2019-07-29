import logging
import os

from kubernetes import client
from kubernetes.client.rest import ApiException

from stacklight_tests import settings

logger = logging.getLogger(__name__)


class NoApplication(Exception):
    pass


class K8sClient(object):
    def __init__(self, url, token):
        aConfiguration = client.Configuration()
        aConfiguration.host = url
        aConfiguration.verify_ssl = False
        aConfiguration.api_key = {"authorization": "Bearer " + token}
        aApiClient = client.ApiClient(aConfiguration)
        self.k8s_api = client.CoreV1Api(aApiClient)

    def sl_services(self, namespace=settings.SL_NAMESPACE):
        services = self.k8s_api.list_namespaced_service(namespace)
        sl_services = {}
        for item in services.items:
            sl_services[item.metadata.name] = {'ip': item.spec.cluster_ip,
                                               'port': item.spec.ports[0].port}
        return sl_services

    def nodes(self):
        nodes = self.k8s_api.list_node()
        nodes_dict = {}
        for node in nodes.items:
            nodes_dict[node.metadata.name] = {
                'internal_ip': node.status.addresses[0].address,
                'external_ip': node.status.addresses[1].address,
            }
        return nodes_dict

    def get_sl_service_ip(self, namespace, svc_name):
        ip = None
        try:
            service = self.k8s_api.read_namespaced_service(
                namespace=namespace, name=svc_name)
            if service is None:
                logger.error(
                    "Couldn't find {} service in "
                    "namespace {}".format(svc_name, namespace))
                return None
            if not service.spec.ports:
                logger.error("Service spec appears invalid. Erroring.")
                return None
            ip = service.spec.cluster_ip + ":" + str(
                service.spec.ports[0].port)
            logger.info("Found {} IP at: ".format(svc_name) + ip)

        except ApiException as e:
            print("Exception occurred trying to find %s service in "
                  "namespace %s: %s" % (svc_name, namespace, e))
            return None
        return ip

    def list_namespaced_service(self, namespace):
        return self.k8s_api.list_namespaced_service(namespace)

    def list_pod_for_all_namespaces(self):
        return self.k8s_api.list_pod_for_all_namespaces()

    def list_namespaced_pod(self, namespace):
        return self.k8s_api.list_namespaced_pod(namespace)


def get_k8s_client():
    if "TOKEN" in os.environ.keys() and "URL" in os.environ.keys():
        api_client = K8sClient(os.environ['URL'], os.environ['TOKEN'])
        return api_client
    else:
        raise EnvironmentError(
            "401 Not Authorised. Please specify URL and TOKEN "
            "environment variables.")
