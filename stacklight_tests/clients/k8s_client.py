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
        self.core_api = client.CoreV1Api(aApiClient)
        self.extension_api = client.ExtensionsV1beta1Api(aApiClient)
        self.apps_api = client.AppsV1beta1Api(aApiClient)

    def sl_services(self, namespace=settings.SL_NAMESPACE):
        services = self.core_api.list_namespaced_service(namespace)
        sl_services = {}
        for item in services.items:
            sl_services[item.metadata.name] = {'ip': item.spec.cluster_ip,
                                               'port': item.spec.ports[0].port}
        return sl_services

    def nodes(self):
        nodes = self.core_api.list_node()
        nodes_dict = {}
        for node in nodes.items:
            nodes_dict[node.metadata.name] = {
                'internal_ip': node.status.addresses[0].address,
                'external_ip': node.status.addresses[1].address,
            }
        return nodes_dict

    def daemonsets(self):
        daemonsets = self.extension_api.list_daemon_set_for_all_namespaces()
        ds_dict = {}
        for ds in daemonsets.items:
            status = {
                'current_number_scheduled': ds.status.current_number_scheduled,
                'desired_number_scheduled': ds.status.desired_number_scheduled,
                'number_available': ds.status.number_available,
                'number_misscheduled': ds.status.number_misscheduled,
                'number_ready': ds.status.number_ready,
                'number_unavailable': ds.status.number_unavailable or 0,
            }
            ds_dict[ds.metadata.name] = {
                'namespace': ds.metadata.namespace,
                'updated_number_scheduled': ds.status.updated_number_scheduled,
                'status': status
            }
        return ds_dict

    def deployments(self):
        deployments = self.extension_api.list_deployment_for_all_namespaces()
        dm_dict = {}
        for dm in deployments.items:
            status = {
                'observed_generation': dm.status.observed_generation,
                'replicas': dm.status.replicas,
                'replicas_available': dm.status.available_replicas,
                'replicas_unavailable': dm.status.unavailable_replicas or 0,
                'replicas_updated': dm.status.updated_replicas,

            }
            spec = {
                'paused': dm.spec.paused or 0,
                'replicas': dm.spec.replicas,
            }
            dm_dict[dm.metadata.name] = {
                'namespace': dm.metadata.namespace,
                'spec': spec,
                'status': status
            }
        return dm_dict

    def replicasets(self):
        replicasets = self.extension_api.list_replica_set_for_all_namespaces()
        rs_dict = {}
        for rs in replicasets.items:
            status = {
                'observed_generation': rs.status.observed_generation,
                'replicas': rs.status.replicas,
                'ready_replicas': rs.status.ready_replicas or 0,
                'fully_labeled_replicas':
                    rs.status.fully_labeled_replicas or 0,
            }
            rs_dict[rs.metadata.name] = {
                'namespace': rs.metadata.namespace,
                'spec_replicas': rs.spec.replicas,
                'status': status
            }
        return rs_dict

    def statefulsets(self):
        statefulsets = self.apps_api.list_stateful_set_for_all_namespaces()
        sfs_dict = {}
        for sfs in statefulsets.items:
            status = {
                'observed_generation': sfs.status.observed_generation,
                'replicas': sfs.status.replicas,
                'replicas_ready': sfs.status.ready_replicas,
                'replicas_current': sfs.status.current_replicas,
                'replicas_updated': sfs.status.updated_replicas,
            }
            sfs_dict[sfs.metadata.name] = {
                'namespace': sfs.metadata.namespace,
                'spec_replicas': sfs.spec.replicas,
                'current_revision': sfs.status.current_revision,
                'update_revision': sfs.status.update_revision,
                'status': status
            }
        return sfs_dict

    def get_sl_service_ip(self, namespace, svc_name):
        ip = None
        try:
            service = self.core_api.read_namespaced_service(
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
        return self.core_api.list_namespaced_service(namespace)

    def list_pod_for_all_namespaces(self):
        return self.core_api.list_pod_for_all_namespaces()

    def list_namespaced_pod(self, namespace):
        return self.core_api.list_namespaced_pod(namespace)


def get_k8s_client():
    if "TOKEN" in os.environ.keys() and "URL" in os.environ.keys():
        api_client = K8sClient(os.environ['URL'], os.environ['TOKEN'])
        return api_client
    else:
        raise EnvironmentError(
            "401 Not Authorised. Please specify URL and TOKEN "
            "environment variables.")
