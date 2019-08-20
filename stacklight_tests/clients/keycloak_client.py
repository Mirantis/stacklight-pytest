from keycloak import KeycloakOpenID


class KeycloakUserClient(object):

    def __init__(self, user, password, url,
                 verify=False, realm='iam', client_id='sl',
                 realm_name='iam', client_secret_key=""):
        self.user = user
        self.password = password
        self.client = KeycloakOpenID(server_url="{}/auth/".format(url),
                                     client_id=client_id,
                                     realm_name=realm_name,
                                     client_secret_key=client_secret_key,
                                     verify=verify)

    def get_token(self):
        return self.client.token(self.user, self.password)

    def refresh_token(self, token):
        return self.client.refresh_token(token['refresh_token'])


def get_keycloak_client(user, password, url):
    return KeycloakUserClient(user, password, url)
