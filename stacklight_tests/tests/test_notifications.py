import logging
import pytest

from stacklight_tests import file_cache
from stacklight_tests import settings
from stacklight_tests import utils

logger = logging.getLogger(__name__)


def check_service_notification_by_type(es_client, object_id, event_type):
    logger.info("Checking {} notification".format(event_type))
    q = '{{"query": {{"match": {{"event_type":"{0}"}}}}, "size": 100}}'.format(
        event_type)
    output = es_client.search(index='notification-*', body=q)
    return any(object_id in x for x in [
        p['_source']['Payload'] for p in output['hits']['hits']])


def test_glance_notifications(salt_actions, destructive, os_clients,
                              es_client):
    nodes = salt_actions.ping("I@glance:server")
    if not nodes:
        pytest.skip("Openstack is not installed in the cluster")

    image_name = utils.rand_name("image-")
    client = os_clients.image

    logger.info("Creating a test image")
    image = client.images.create(
        name=image_name,
        container_format="bare",
        disk_format="raw",
        visibility="public")
    client.images.upload(image.id, "dummy_data")
    destructive.append(lambda: client.images.delete(image.id))
    utils.wait_for_resource_status(client.images, image.id, "active")

    logger.info("Removing the test image")
    client.images.delete(image.id)
    utils.wait(
        lambda: (image.id not in [i["id"] for i in client.images.list()])
    )

    logger.info("Image id: {}".format(image.id))
    logger.info("Checking the glance notifications")
    event_list = ['image.create', 'image.upload', 'image.update',
                  'image.delete']

    for event in event_list:
        msg = "Didn't get a notification {} with expected image id {}".format(
            event, image.id)
        utils.wait(
            lambda: check_service_notification_by_type(
                es_client, image.id, event),
            interval=30, timeout=5 * 60, timeout_msg=msg
        )


def test_neutron_notifications(salt_actions, destructive, os_clients,
                               os_actions, es_client):
    nodes = salt_actions.ping("I@neutron:server")
    if not nodes:
        pytest.skip("Openstack is not installed in the cluster")

    logger.info("Creating test network and subnet")
    project_id = os_clients.auth.projects.find(name='admin').id
    net = os_actions.create_network(project_id)
    subnet = os_actions.create_subnet(net, project_id, "192.168.100.0/24")

    logger.info("Network name: {}, network id: {}, subnet id: {}".format(
        net['name'], net['id'], subnet['id']))
    destructive.append(lambda: os_clients.network.delete_subnet(
        subnet['id']))
    destructive.append(lambda: os_clients.network.delete_network(
        net['id']))

    logger.info("Removing the test network and subnet")
    os_clients.network.delete_subnet(subnet['id'])
    os_clients.network.delete_network(net['id'])

    net_create_event_list = ['network.create.start', 'network.create.end']
    net_delete_event_list = ['network.delete.start', 'network.delete.end']
    subnet_create_event_list = ['subnet.create.start', 'subnet.create.end']
    subnet_delete_event_list = ['subnet.delete.start', 'subnet.delete.end']
    for event in net_create_event_list:
        msg = "Didn't get a notification {} with expected net name {}".format(
            event, net['name'])
        utils.wait(
            lambda: check_service_notification_by_type(
                es_client, net['name'], event),
            interval=30, timeout=5 * 60, timeout_msg=msg
        )
    for event in net_delete_event_list:
        msg = "Didn't get a notification {} with expected net id {}".format(
            event, net['id'])
        utils.wait(
            lambda: check_service_notification_by_type(
                es_client, net['id'], event),
            interval=30, timeout=5 * 60, timeout_msg=msg
        )
    for event in subnet_create_event_list:
        msg = ("Didn't get a notification {} with expected subnet "
               "name {}".format(event, subnet['name']))
        utils.wait(
            lambda: check_service_notification_by_type(
                es_client, subnet['name'], event),
            interval=30, timeout=5 * 60, timeout_msg=msg
        )
    for event in subnet_delete_event_list:
        msg = "Didn't get a notification {} with expected subnet id {}".format(
            event, subnet['id'])
        utils.wait(
            lambda: check_service_notification_by_type(
                es_client, subnet['id'], event),
            interval=30, timeout=5 * 60, timeout_msg=msg
        )


def test_cinder_notifications(salt_actions, destructive, os_clients,
                              es_client):
    nodes = salt_actions.ping("I@cinder:controller")
    if not nodes:
        pytest.skip("Openstack is not installed in the cluster")

    volume_name = utils.rand_name("volume-")
    expected_volume_status = settings.VOLUME_STATUS
    client = os_clients.volume

    logger.info("Creating a test volume")
    volume = client.volumes.create(size=1, name=volume_name)
    destructive.append(lambda: client.volumes.delete(volume))
    utils.wait_for_resource_status(client.volumes, volume.id,
                                   expected_volume_status)
    logger.info("Volume id: {}".format(volume.id))

    logger.info("Removing the test volume")
    client.volumes.delete(volume)
    utils.wait(
        lambda: (volume.id not in [v.id for v in client.volumes.list()])
    )
    event_list = ['volume.create.start', 'volume.create.end',
                  'volume.delete.start', 'volume.delete.end']
    for event in event_list:
        msg = "Didn't get a notification {} with expected volume id {}".format(
            event, volume.id)
        utils.wait(
            lambda: check_service_notification_by_type(
                es_client, volume.id, event),
            interval=30, timeout=5 * 60, timeout_msg=msg
        )


def test_nova_notifications(salt_actions, os_clients, os_actions, es_client,
                            destructive):
    nodes = salt_actions.ping("I@nova:controller")
    if not nodes:
        pytest.skip("Openstack is not installed in the cluster")
    client = os_clients.compute

    logger.info("Creating a test image")
    image = os_clients.image.images.create(
        name="TestVM",
        disk_format='qcow2',
        container_format='bare')
    with file_cache.get_file(settings.CIRROS_QCOW2_URL) as f:
        os_clients.image.images.upload(image.id, f)
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

    event_list = ['compute.instance.create.start',
                  'compute.instance.create.end',
                  'compute.instance.delete.start',
                  'compute.instance.delete.end']

    for event in event_list:
        msg = ("Didn't get a notification {} with expected instance id "
               "{}".format(event, server.id))
        utils.wait(
            lambda: check_service_notification_by_type(
                es_client, server.id, event),
            interval=30, timeout=5 * 60, timeout_msg=msg
        )
