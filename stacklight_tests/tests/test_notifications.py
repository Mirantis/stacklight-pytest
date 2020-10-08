import json
import logging
import pytest

from stacklight_tests import settings
from stacklight_tests import utils

logger = logging.getLogger(__name__)


def check_service_notification_by_type(kibana_client, object_id, event_type):
    logger.info("Checking {} notification".format(event_type))
    q = ('{{"_source": "Payload", "size": "1000", "query": {{"bool": '
         '{{"must": [{{"match": {{"event_type": "{0}"}}}}, {{"range": '
         '{{"Timestamp": {{"gte": "now-1h","lte": "now"'
         '}}}}}}]}}}}}}'.format(event_type))
    output = json.loads(kibana_client.get_query(q, "notification-*/_search"))
    return any(object_id in x for x in [
        p['_source']['Payload'] for p in output['hits']['hits']])


@pytest.mark.smoke
@pytest.mark.notifications
def test_glance_notifications(destructive, os_clients, kibana_client,
                              os_actions, chart_releases, openstack_cr_exists):
    related_release = 'fluentd-notifications'
    utils.skip_test(related_release, chart_releases)
    utils.skip_openstack_test(openstack_cr_exists)

    client = os_clients.image

    logger.info("Creating a test image")
    image = os_actions.create_cirros_image()
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
                kibana_client, image.id, event),
            interval=10, timeout=3 * 60, timeout_msg=msg
        )


@pytest.mark.smoke
@pytest.mark.notifications
def test_neutron_notifications(destructive, os_clients, os_actions,
                               kibana_client, chart_releases,
                               openstack_cr_exists):
    related_release = 'fluentd-notifications'
    utils.skip_test(related_release, chart_releases)
    utils.skip_openstack_test(openstack_cr_exists)

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
                kibana_client, net['name'], event),
            interval=10, timeout=3 * 60, timeout_msg=msg
        )
    for event in net_delete_event_list:
        msg = "Didn't get a notification {} with expected net id {}".format(
            event, net['id'])
        utils.wait(
            lambda: check_service_notification_by_type(
                kibana_client, net['id'], event),
            interval=10, timeout=3 * 60, timeout_msg=msg
        )
    for event in subnet_create_event_list:
        msg = ("Didn't get a notification {} with expected subnet "
               "name {}".format(event, subnet['name']))
        utils.wait(
            lambda: check_service_notification_by_type(
                kibana_client, subnet['name'], event),
            interval=10, timeout=3 * 60, timeout_msg=msg
        )
    for event in subnet_delete_event_list:
        msg = "Didn't get a notification {} with expected subnet id {}".format(
            event, subnet['id'])
        utils.wait(
            lambda: check_service_notification_by_type(
                kibana_client, subnet['id'], event),
            interval=10, timeout=3 * 60, timeout_msg=msg
        )


@pytest.mark.smoke
@pytest.mark.notifications
def test_cinder_notifications(destructive, os_clients, kibana_client,
                              chart_releases, openstack_cr_exists):
    related_release = 'fluentd-notifications'
    utils.skip_test(related_release, chart_releases)
    utils.skip_openstack_test(openstack_cr_exists)

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
                kibana_client, volume.id, event),
            interval=10, timeout=3 * 60, timeout_msg=msg
        )


@pytest.mark.smoke
@pytest.mark.notifications
def test_nova_notifications(os_clients, os_actions, kibana_client,
                            destructive, chart_releases, openstack_cr_exists):
    related_release = 'fluentd-notifications'
    utils.skip_test(related_release, chart_releases)
    utils.skip_openstack_test(openstack_cr_exists)

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
                kibana_client, server.id, event),
            interval=10, timeout=3 * 60, timeout_msg=msg
        )


@pytest.mark.smoke
@pytest.mark.notifications
def test_keystone_notifications(os_clients, kibana_client, destructive,
                                chart_releases, openstack_cr_exists):
    related_release = 'fluentd-notifications'
    utils.skip_test(related_release, chart_releases)
    utils.skip_openstack_test(openstack_cr_exists)

    client = os_clients.auth
    domain = os_clients.auth.project_domain_id

    logger.info("Creating a test project")
    project = client.projects.create(utils.rand_name("tenant-"), domain)
    destructive.append(lambda: client.projects.delete(project))

    password = "Stacklight_pytest_password_123456!"
    name = utils.rand_name("user-")
    logger.info("Creating a test user")
    user = client.users.create(name, domain=domain, password=password,
                               default_project=project)
    destructive.append(lambda: client.users.delete(user))

    logger.info("Creating a test role")
    role = client.roles.create(utils.rand_name("role-"))
    destructive.append(lambda: client.roles.delete(role))

    logger.info("Project id: {}, user id: {}, role id: {}".format(
        project.id, user.id, role.id))

    logger.info("Removing the test resources")
    client.roles.delete(role)
    client.users.delete(user)
    client.projects.delete(project)

    role_event_list = ["identity.role.created", "identity.role.deleted"]
    user_event_list = ["identity.user.created", "identity.user.deleted"]
    project_event_list = ["identity.project.created",
                          "identity.project.deleted"]

    for event in role_event_list:
        msg = ("Didn't get a notification {} with expected role id "
               "{}".format(event, role.id))
        utils.wait(
            lambda: check_service_notification_by_type(
                kibana_client, role.id, event),
            interval=10, timeout=3 * 60, timeout_msg=msg
        )
    for event in user_event_list:
        msg = ("Didn't get a notification {} with expected user id "
               "{}".format(event, user.id))
        utils.wait(
            lambda: check_service_notification_by_type(
                kibana_client, user.id, event),
            interval=10, timeout=3 * 60, timeout_msg=msg
        )
    for event in project_event_list:
        msg = ("Didn't get a notification {} with expected project id "
               "{}".format(event, project.id))
        utils.wait(
            lambda: check_service_notification_by_type(
                kibana_client, project.id, event),
            interval=10, timeout=3 * 60, timeout_msg=msg
        )


@pytest.mark.smoke
@pytest.mark.notifications
def test_heat_notifications(os_clients, kibana_client, os_actions,
                            destructive, chart_releases, openstack_cr_exists):
    related_release = 'fluentd-notifications'
    utils.skip_test(related_release, chart_releases)
    utils.skip_openstack_test(openstack_cr_exists)

    logger.info("Creating a test image")
    image = os_actions.create_cirros_image()
    destructive.append(lambda: os_clients.image.images.delete(image.id))

    logger.info("Creating a test flavor")
    name = utils.rand_name("heat-flavor-")
    flavor = os_actions.create_flavor(name)
    destructive.append(lambda: os_clients.compute.flavors.delete(flavor))

    logger.info("Creating test network and subnet")
    project_id = os_clients.auth.projects.find(name='admin').id
    net = os_actions.create_network(project_id)
    subnet = os_actions.create_subnet(net, project_id, "192.168.100.0/24")

    filepath = utils.get_fixture("heat_create_neutron_stack_template.yaml",
                                 parent_dirs=("heat",))
    with open(filepath) as template_file:
        template = template_file.read()

    logger.info("Creating a test stack")
    parameters = {
        'InstanceType': flavor.name,
        'ImageId': image.id,
        'network': net["id"],
    }
    stack = os_actions.create_stack(template, parameters=parameters)
    destructive.append(lambda: os_clients.orchestration.stacks.delete(
        stack.id))
    destructive.append(lambda: os_clients.network.delete_subnet(
        subnet['id']))
    destructive.append(lambda: os_clients.network.delete_network(
        net['id']))
    logger.info("Stack id: {}".format(stack.id))

    logger.info("Removing the test stack")
    os_clients.orchestration.stacks.delete(stack.id)
    utils.wait(
        lambda: (stack.id not in [
            s.id for s in os_clients.orchestration.stacks.list()])
    )

    logger.info("Removing the test flavor")
    os_clients.compute.flavors.delete(flavor.id)

    logger.info("Removing the test image")
    os_clients.image.images.delete(image.id)

    logger.info("Removing the test network and subnet")
    os_clients.network.delete_subnet(subnet['id'])
    os_clients.network.delete_network(net['id'])

    event_list = [
        "orchestration.stack.create.start",
        "orchestration.stack.create.end",
        "orchestration.stack.delete.start",
        "orchestration.stack.delete.end",
    ]

    for event in event_list:
        msg = ("Didn't get a notification {} with expected stack id "
               "{}".format(event, stack.id))
        utils.wait(
            lambda: check_service_notification_by_type(
                kibana_client, stack.id, event),
            interval=10, timeout=3 * 60, timeout_msg=msg
        )
