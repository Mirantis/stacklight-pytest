import logging
import pytest
import re

from stacklight_tests import utils

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def create_resources(request, os_clients, os_actions, k8s_api,
                     openstack_cr_exists):
    related_release = 'telegraf-openstack'
    releases = k8s_api.get_stacklight_chart_releases()
    if related_release in releases and openstack_cr_exists:

        logger.info("Creating a test image")
        image = os_actions.create_cirros_image()
        utils.wait_for_resource_status(
            os_clients.image.images, image.id, "active")

        logger.info("Creating a test flavor")
        flavor = os_actions.create_flavor(
            name="test_flavor", ram='64')

        logger.info("Creating a test volume")
        volume = os_clients.volume.volumes.create(size=1, name=utils.rand_name(
            "volume-"))
        utils.wait_for_resource_status(os_clients.volume.volumes, volume.id,
                                       'available')

        logger.info("Creating test network and subnet")
        project_id = os_clients.auth.projects.find(name='admin').id
        net = os_actions.create_network(project_id)
        subnet = os_actions.create_subnet(net, project_id, "192.168.100.0/24")

        logger.info("Creating a test instance")
        server = os_actions.create_basic_server(image, flavor, net)
        utils.wait_for_resource_status(
            os_clients.compute.servers, server, 'ACTIVE')
        logger.info("Created the test instance with id {}".format(server.id))

        def delete_resources():
            logger.info("Removing the test instance")
            os_clients.compute.servers.delete(server)
            utils.wait(
                lambda: (server.id not in [
                    s.id for s in os_clients.compute.servers.list()])
            )

            logger.info("Removing the test network and subnet")
            os_clients.network.delete_subnet(subnet['id'])
            os_clients.network.delete_network(net['id'])

            logger.info("Removing the test image")
            os_clients.image.images.delete(image.id)
            utils.wait(
                lambda: (image.id not in [
                    i["id"] for i in os_clients.image.images.list()])
            )

            logger.info("Removing the test flavor")
            os_clients.compute.flavors.delete(flavor)

            logger.info("Removing the test volume")
            os_clients.volume.volumes.delete(volume)
            utils.wait(
                lambda: (volume.id not in [
                    v.id for v in os_clients.volume.volumes.list()])
            )

        request.addfinalizer(delete_resources)
        return {'server': server, 'image': image, 'flavor': flavor, 'net': net,
                'subnet': subnet, 'volume': volume}


@pytest.mark.openstack_metrics
@pytest.mark.run(order=2)
def test_glance_metrics(prometheus_api, os_clients, create_resources,
                        chart_releases, openstack_cr_exists):
    related_release = 'telegraf-openstack'
    utils.skip_test(related_release, chart_releases)
    utils.skip_openstack_test(openstack_cr_exists)

    client = os_clients.image

    logger.info("Checking the glance metrics")
    filter = {"visibility": "public"}
    images_count = len([im for im in client.images.list(
                        filters=filter)])
    images_size = sum([im["size"] for im in client.images.list(
                       filters=filter)])

    count_query = ('{__name__="openstack_glance_images",'
                   'visibility="public",status="active"}')
    err_count_msg = "Incorrect image count in metric {}".format(
        count_query)
    prometheus_api.check_metric_values(
        count_query, images_count, err_count_msg)

    size_query = ('{__name__="openstack_glance_images_size",'
                  'visibility="public", status="active"}')
    error_size_msg = "Incorrect image size in metric {}".format(size_query)
    prometheus_api.check_metric_values(
        size_query, images_size, error_size_msg)


@pytest.mark.openstack_metrics
@pytest.mark.run(order=2)
def test_keystone_metrics(prometheus_api, os_clients, create_resources,
                          chart_releases, openstack_cr_exists):
    related_release = 'telegraf-openstack'
    utils.skip_test(related_release, chart_releases)
    utils.skip_openstack_test(openstack_cr_exists)

    client = os_clients.auth
    tenants = client.projects.list()
    users = client.users.list()

    metric_dict = {
        '{__name__="openstack_keystone_tenants_total"}':
            [len(tenants), "Incorrect tenant count in metric {}"],

        'openstack_keystone_tenants{state="enabled"}':
            [len(filter(lambda x: x.enabled, tenants)),
             "Incorrect enabled tenant count in metric {}"],

        'openstack_keystone_tenants{state="disabled"}':
            [len(filter(lambda x: not x.enabled, tenants)),
             "Incorrect disabled tenant count in metric {}"],

        '{__name__="openstack_keystone_roles_roles"}':
            [len(client.roles.list()),
             "Incorrect roles count in metric {}"],

        '{__name__="openstack_keystone_users_total"}':
            [len(users), "Incorrect user count in metric {}"],

        'openstack_keystone_users{state="enabled"}':
            [len(filter(lambda x: x.enabled, users)),
             "Incorrect enabled user count in metric {}"],

        'openstack_keystone_users{state="disabled"}':
            [len(filter(lambda x: not x.enabled, users)),
             "Incorrect disabled user count in metric {}"]
    }

    for metric in metric_dict.keys():
        prometheus_api.check_metric_values(
            metric, metric_dict[metric][0],
            metric_dict[metric][1].format(metric))


@pytest.mark.openstack_metrics
@pytest.mark.run(order=2)
def test_neutron_metrics(prometheus_api, os_clients, create_resources,
                         chart_releases, openstack_cr_exists):
    related_release = 'telegraf-openstack'
    utils.skip_test(related_release, chart_releases)
    utils.skip_openstack_test(openstack_cr_exists)

    client = os_clients.network

    metric_dict = {
        '{__name__="openstack_neutron_networks_total"}':
            [len(client.list_networks()["networks"]),
             "Incorrect net count in metric {}"],
        '{__name__="openstack_neutron_subnets_total"}':
            [len(client.list_subnets()["subnets"]),
             "Incorrect subnet count in metric {}"],
        '{__name__="openstack_neutron_floatingips_total"}':
            [len(client.list_floatingips()["floatingips"]),
             "Incorrect floating ip count in metric {}"],
        '{__name__="openstack_neutron_routers_total"}':
            [len(client.list_routers()["routers"]),
             "Incorrect router count in metric {}"],
        'openstack_neutron_routers{state="active"}':
            [len(filter(lambda x: x["status"] == "ACTIVE",
                        client.list_routers()["routers"])),
             "Incorrect active router count in metric {}"],
        '{__name__="openstack_neutron_ports_total"}':
            [len(client.list_ports()["ports"]),
             "Incorrect port count in metric {}"]
    }

    for metric in metric_dict.keys():
        prometheus_api.check_metric_values(
            metric, metric_dict[metric][0],
            metric_dict[metric][1].format(metric))


@pytest.mark.openstack_metrics
@pytest.mark.run(order=2)
def test_cinder_metrics(prometheus_api, os_clients, create_resources,
                        chart_releases, openstack_cr_exists):
    related_release = 'telegraf-openstack'
    utils.skip_test(related_release, chart_releases)
    utils.skip_openstack_test(openstack_cr_exists)

    client = os_clients.volume

    logger.info("Checking the cinder metrics")
    filter = {'status': 'available', 'all_tenants': 1}
    volumes_count = len([vol for vol in client.volumes.list(
                         search_opts=filter)])
    volumes_size = sum([vol.size for vol in client.volumes.list(
                        search_opts=filter)]) * 1024**3

    count_query = ('{__name__="openstack_cinder_volumes", '
                   'status="available"}')
    err_count_msg = "Incorrect volume count in metric {}".format(
        count_query)
    prometheus_api.check_metric_values(
        count_query, volumes_count, err_count_msg)

    size_query = ('{__name__="openstack_cinder_volumes_size", '
                  'status="available"}')
    error_size_msg = "Incorrect volume size in metric {}".format(
        size_query)
    prometheus_api.check_metric_values(
        size_query, volumes_size, error_size_msg)


@pytest.mark.openstack_metrics
@pytest.mark.run(order=2)
def test_nova_telegraf_metrics(prometheus_api, os_clients, create_resources,
                               chart_releases, openstack_cr_exists):
    related_release = 'telegraf-openstack'
    utils.skip_test(related_release, chart_releases)
    utils.skip_openstack_test(openstack_cr_exists)

    client = os_clients.compute

    def get_servers_count(st):
        return len(filter(
            lambda x: x.status == st, client.servers.list(
                search_opts={'all_tenants': 1})))

    err_msg = "Incorrect servers count in metric {}"
    for status in ["active", "error"]:
        q = 'openstack_nova_instances{' + 'state="{}"'.format(
            status) + '}'
        prometheus_api.check_metric_values(
            q, get_servers_count(status.upper()), err_msg.format(q))


@pytest.mark.openstack_metrics
@pytest.mark.run(order=2)
def test_nova_services_metrics(prometheus_api, os_clients, chart_releases,
                               openstack_cr_exists):
    related_release = 'telegraf-openstack'
    utils.skip_test(related_release, chart_releases)
    utils.skip_openstack_test(openstack_cr_exists)

    services = os_clients.compute.services.list()
    for service in services:
        q = ('openstack_nova_service_status{{binary="{}",'
             'hostname="{}"}}'.format(service.binary, service.host))
        print "Checking '1' value in '{}' metric values".format(q)
        prometheus_api.check_metric_values(q, 1)


@pytest.mark.openstack_metrics
@pytest.mark.run(order=1)
def test_openstack_api_check_status_metrics(prometheus_api, chart_releases,
                                            openstack_cr_exists):
    related_release = 'telegraf-openstack'
    utils.skip_test(related_release, chart_releases)
    utils.skip_openstack_test(openstack_cr_exists)

    metrics = prometheus_api.get_query('openstack_api_check_status')
    logger.info("openstack_api_check_status metrics list:")
    for metric in metrics:
        logger.info("Service: {:<25} Value: {}".format(
            metric['metric']['name'], metric['value']))

    msg = 'There are no openstack_api_check_status metrics'
    assert len(metrics) != 0, msg
    # TODO(vgusev): Refactor test after changes in telegraf are done
    allowed_values = ['1', '2']
    # '2' is allowed value because some services are not present in
    # hardcoded list in telegraf. Remove after changes in telegraf are done

    for metric in metrics:
        logger.info("Check allowed values {} for service {}".format(
            ' or '.join(allowed_values), metric['metric']['name']))
        msg = 'Incorrect value in metric {}'.format(metric)
        assert any(x in allowed_values for x in metric['value']), msg


@pytest.mark.openstack_metrics
@pytest.mark.run(order=2)
def test_libvirt_metrics(prometheus_api, create_resources, chart_releases,
                         openstack_cr_exists):
    related_release = 'telegraf-openstack'
    utils.skip_test(related_release, chart_releases)
    utils.skip_openstack_test(openstack_cr_exists)

    def _check_metrics(inst_id):
        logger.info("Getting libvirt metrics")
        query = '{{__name__=~"^libvirt.*", instance_uuid="{}"}}'.format(
            inst_id)
        output = prometheus_api.get_query(query)
        if len(output) == 0:
            logger.info("Libvirt metrics for the instance {} "
                        "not found".format(inst_id))
            return False

        metrics = list(set([m['metric']['__name__'] for m in output]))

        regexes = ['libvirt_domain_block_stats_read.*',
                   'libvirt_domain_block_stats_write.*',
                   'libvirt_domain_interface_stats_receive.*',
                   'libvirt_domain_interface_stats_transmit.*',
                   'libvirt_domain_info.*',
                   'libvirt_domain_info_state']
        for regex in regexes:
            regex = re.compile(r'{}'.format(regex))
            logger.info("Check metrics with mask {}".format(regex.pattern))
            found = filter(regex.search, metrics)
            logger.info("Found {} metrics for mask {}".format(
                found, regex.pattern))
            msg = "Metrics with mask '{}' not found in list {}".format(
                regex.pattern, metrics)
            if not found:
                logger.info(msg)
                return False
        return True

    server = create_resources['server']
    err_msg = ("Timeout waiting for all libvirt metrics "
               "for the instance {}".format(server.id))
    utils.wait(lambda: _check_metrics(server.id), interval=20,
               timeout=2 * 60, timeout_msg=err_msg)


@pytest.mark.openstack_metrics
@pytest.mark.run(order=2)
def test_kpi_metrics(prometheus_api, os_clients, os_actions, destructive,
                     chart_releases, openstack_cr_exists):
    related_release = 'telegraf-openstack'
    utils.skip_test(related_release, chart_releases)
    utils.skip_openstack_test(openstack_cr_exists)

    def _get_event_metric(query):
        value = prometheus_api.get_query(query)[0]['value'][1]
        logger.info("The current value of metric `{}` is {}".format(
            query, value))
        return value

    start_event = 'compute_instance_create_start_event_doc_count'
    end_event = 'compute_instance_create_end_event_doc_count'
    logger.info("Getting a current value for `{}` metric".format(
        start_event))
    start_value = _get_event_metric(start_event)
    logger.info("Getting a current value for `{}` metric".format(
        end_event))
    end_value = _get_event_metric(end_event)

    client = os_clients.compute
    logger.info("Creating a test image")
    image = os_actions.create_cirros_image()
    destructive.append(lambda: os_clients.image.images.delete(image.id))

    logger.info("Creating a test flavor")
    flavor = os_actions.create_flavor(
        name="test_flavor", ram='64')
    destructive.append(lambda: client.flavors.delete(flavor))

    logger.info("Creating test network and subnet")
    project_id = os_clients.auth.projects.find(name='admin').id
    net = os_actions.create_network(project_id)
    subnet = os_actions.create_subnet(net, project_id, "192.168.100.0/24")

    logger.info("Creating a test instance")
    server = os_actions.create_basic_server(image, flavor, net)
    destructive.append(lambda: client.servers.delete(server))
    destructive.append(lambda: os_clients.network.delete_subnet(
        subnet['id']))
    destructive.append(lambda: os_clients.network.delete_network(
        net['id']))
    utils.wait_for_resource_status(client.servers, server, 'ACTIVE')
    logger.info("Created an instance with id {}".format(server.id))

    logger.info("Checking KPI metrics for the instance")
    err_msg = "Value of `{}` metric was not increased"
    logger.info("Checking the `{}` metric".format(start_event))
    utils.wait(
        lambda: _get_event_metric(start_event) > start_value,
        interval=30, timeout=3 * 60,
        timeout_msg=err_msg.format(start_event))
    logger.info("Checking the `{}` metric".format(end_event))
    utils.wait(
        lambda: _get_event_metric(end_event) > end_value,
        interval=30, timeout=3 * 60,
        timeout_msg=err_msg.format(end_event))

    logger.info("Removing the test instance")
    client.servers.delete(server)
    utils.wait(
        lambda: (server.id not in [s.id for s in client.servers.list()])
    )

    logger.info("Removing the test network and subnet")
    os_clients.network.delete_subnet(subnet['id'])
    os_clients.network.delete_network(net['id'])

    logger.info("Removing the test image")
    os_clients.image.images.delete(image.id)

    logger.info("Removing the test flavor")
    client.flavors.delete(flavor)


@pytest.mark.openstack_metrics
@pytest.mark.run(order=2)
def test_prometheus_es_exporter_metrics(prometheus_api, os_clients,
                                        chart_releases, openstack_cr_exists,
                                        logging_enabled):
    if not logging_enabled:
        pytest.skip("Metrics related to this test are from the ES."
                    "Logging is disabled for this cluster.")
    related_release = 'telegraf-openstack'
    utils.skip_test(related_release, chart_releases)
    utils.skip_openstack_test(openstack_cr_exists)

    failed_metrics = []
    metrics = ['compute_instance_create_start_event_doc_count',
               'compute_instance_create_end_event_doc_count',
               'compute_instance_create_error_event_doc_count']
    for m in metrics:
        logger.info("Checking metric '{}'. ".format(m))
        output = prometheus_api.get_query(m)
        if not output:
            failed_metrics.append(m)
    msg = "These metrics are not presented in the Prometheus: {}."\
        .format(failed_metrics)
    assert len(failed_metrics) == 0, msg
