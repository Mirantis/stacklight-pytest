import logging
import pytest
import socket

from stacklight_tests import utils
from stacklight_tests.clients.prometheus.prometheus_client import PrometheusClient  # noqa

logger = logging.getLogger(__name__)


@pytest.mark.prometheus
class TestPrometheusSmoke(object):
    @pytest.mark.run(order=1)
    @pytest.mark.smoke
    def test_prometheus_container(self, salt_actions):
        prometheus_nodes = salt_actions.ping(
            "prometheus:alertmanager", tgt_type="pillar")

        def test_prometheus_container_up(node):
            status = salt_actions.run_cmd(
                node,
                "docker ps --filter name=monitoring_server "
                "--format '{{.Status}}'")[0]
            return "Up" in status

        assert any([test_prometheus_container_up(node)
                    for node in prometheus_nodes])

    @pytest.mark.run(order=1)
    @pytest.mark.smoke
    def test_prometheus_datasource(self, prometheus_api):
        assert prometheus_api.get_all_measurements()

    @pytest.mark.run(order=1)
    def test_prometheus_relay(self, salt_actions):
        relays = salt_actions.ping("I@prometheus:relay")
        if not relays:
            pytest.skip("Prometheus relay is not installed in the cluster")
        hosts = [h["host"] for h in salt_actions.get_pillar_item(
            relays[0], "prometheus:relay:backends")[0]]
        port = salt_actions.get_pillar_item(
            relays[0], "prometheus:relay:bind:port")[0]

        # Create a dict {relay_ip: prometheus_metrics}
        metric_dict = {}
        for host in hosts:
            metric_dict.update(
                {host: PrometheusClient("http://{}:{}/".format(
                    host, port)).get_query('{__name__=~"^prometheus.*"}')})

        # Remove timestamp from each metric
        for output in metric_dict.values():
            for metric in output:
                metric['value'] = filter(lambda v: isinstance(v, unicode),
                                         metric['value'])

        # Check that all outputs are the same
        for x, y in zip(metric_dict.keys(), metric_dict.keys()[1:]):
            logger.info("Compare metrics from {} and {} relays".format(x, y))
            assert sorted(metric_dict[x]) == sorted(metric_dict[y])

    @pytest.mark.run(order=1)
    def test_prometheus_lts(self, prometheus_api, salt_actions):
        def compare_meas(sts_api, lts_api):
            sts_meas = sts_api.get_all_measurements()
            lts_meas = lts_api.get_all_measurements()

            # TODO(vgusev): W/A for PROD-26248. To be investigated and properly
            # fixed in Q1'19
            sts_meas.discard('prometheus_relay_success_requests')
            lts_meas.discard('prometheus_relay_success_requests')

            if sts_meas == lts_meas:
                return True
            else:
                logger.info(
                    "Measurements in Prometheus short term storage "
                    "and NOT in long term storage: {0}\n"
                    "Measurements in Prometheus long term storage "
                    "and NOT in short term storage: {1}".format(
                        sts_meas.difference(lts_meas),
                        lts_meas.difference(sts_meas)))
                return False

        hosts = salt_actions.ping("I@prometheus:relay")
        if not hosts:
            pytest.skip("Prometheus LTS is not used in the cluster")
        address = salt_actions.get_pillar_item(
            hosts[0], '_param:stacklight_telemetry_address')[0]
        port = salt_actions.get_pillar_item(
            hosts[0], "haproxy:proxy:listen:prometheus_relay:binds:port")[0]
        logger.info("Initializing prometheus client for LTS with the address "
                    "{}:{}".format(address, port))
        prometheus_lts = PrometheusClient(
            "http://{0}:{1}/".format(address, port))

        logger.info("Checking that target for Prometheus LTS is up")
        q = 'up{job="prometheus_federation"}'
        output = prometheus_lts.get_query(q)
        logger.info('Got {} metrics for {} query'.format(output, q))
        msg = 'There are no metrics for query'.format(q)
        assert len(output), msg
        logger.info("Check value '1' for metrics {}".format(q))
        msg = 'Incorrect value in metric {}'
        for metric in output:
            assert '1' in metric['value'], msg.format(metric)

        logger.info("Comparing lists of measurements in Prometheus long term "
                    "storage and short term storage")
        timeout_msg = "Measurements in Prometheus STS and LTS inconsistent"
        utils.wait(lambda: compare_meas(prometheus_api, prometheus_lts),
                   interval=30, timeout=2 * 60,
                   timeout_msg=timeout_msg)

    @pytest.mark.run(order=1)
    @pytest.mark.smoke
    def test_alertmanager_endpoint_availability(self, prometheus_config):
        """Check that alertmanager endpoint is available.

        Scenario:
            1. Get alertmanager endpoint
            2. Check that alertmanager endpoint is available
        Duration 1m
        """
        port = int(prometheus_config["prometheus_alertmanager"])
        alertmanager_ip = prometheus_config["prometheus_vip"]
        try:
            s = socket.socket()
            s.connect((alertmanager_ip, port))
            s.close()
            result = True
        except socket.error:
            result = False
        assert result

    @pytest.mark.run(order=1)
    @pytest.mark.smoke
    def test_alertmanager_ha(self, salt_actions, prometheus_config):
        """Check alertmanager HA .

        Scenario:
            1. Stop 1 alertmanager replic
            2. Get alertmanager endpoint
            3. Check that alertmanager endpoint is available
        Duration 1m
        """
        prometheus_nodes = salt_actions.ping(
            "I@prometheus:server and I@docker:client")
        for host in prometheus_nodes:
            alertmanager_docker_id = salt_actions.run_cmd(
                host,
                "docker ps | grep alertmanager | awk '{print $1}'")[0]
            if alertmanager_docker_id:
                command = "docker kill " + str(alertmanager_docker_id)
                salt_actions.run_cmd(host, command)
                return self.test_alertmanager_endpoint_availability(
                    prometheus_config)

    @pytest.mark.smoke
    def test_docker_service_replicas(self, salt_actions):
        node = salt_actions.ping("I@prometheus:server and I@docker:client")
        cmd = 'docker service ls --format "{{.Name}} {{.Mode}} {{.Replicas}}"'
        status = salt_actions.run_cmd(node, cmd)[0].split("\n")
        logger.info("\nCurrent status of docker services:")
        for service in status:
            service = service.split(" ")
            logger.info("{:<30} {:<15} {}".format(
                service[0], service[1], service[2]))
        wrong_replicas = []
        for service in status:
            service = service.split(" ")
            if service[2][0] != service[2][2]:
                msg = (
                    "Service '{}' in mode '{}' has incorrect count of "
                    "replicas: {}".format(service[0], service[1], service[2]))
                wrong_replicas.append(msg)
        assert len(wrong_replicas) == 0, \
            "Some docker services have incorrect count of replicas: {}".format(
                wrong_replicas)

    @pytest.mark.smoke
    def test_docker_container_status(self, salt_actions):
        node = salt_actions.ping("I@prometheus:server and I@docker:client")
        srv_cmd = (
            "docker service ps $(docker stack services -q {}) --format "
            "'{{{{.Name}}}}' | uniq"
        )
        stacks = ["monitoring", "dashboard"]
        status = []
        for stack in stacks:
            services = salt_actions.run_cmd(node, srv_cmd.format(stack))[
                0].split("\n")
            for service in services:
                st_cmd = (
                    "docker service ps $(docker stack services -q {}) "
                    "--no-trunc --format '{{{{.Name}}}}\t{{{{.Node}}}}"
                    "\t{{{{.DesiredState}}}}\t{{{{.CurrentState}}}}' "
                    "| grep {} | head -n1").format(
                    stack, service)
                status.append(salt_actions.run_cmd(node, st_cmd)[0])

        logger.info("\nCurrent status of docker containers:")
        for container in status:
            container = container.split("\t")
            logger.info("{:<50} {:<10} {:<15} {}".format(*container))

        failed_containers = []
        for container in status:
            if container.split("\t")[2].lower() != "running":
                msg = ("Container {} on the node {} has incorrect state '{}'. "
                       "Current state: '{}'")
                failed_containers.append(msg.format(*container.split("\t")))
        assert len(failed_containers) == 0, \
            "Some containers are in incorrect state: {}".format(
                failed_containers)
