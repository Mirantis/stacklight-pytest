import logging
import requests
import urlparse

from stacklight_tests.clients import keycloak_client


logger = logging.getLogger(__name__)


class HttpClient(object):
    def __init__(self, base_url=None, user=None, password=None,
                 keycloak_url=None, headers=None, verify=False):
        self.base_url = base_url
        self.headers = {'Content-Type': 'application/json'}
        self.kwargs = {"verify": verify}
        if headers:
            self.headers.update(**headers)
        if user and password and keycloak_url:
            self.keycloak = keycloak_client.get_keycloak_client(
                user, password, keycloak_url)
            self.token = self.keycloak.get_token()
            self.headers.update({
                'Cookie': 'kc-access={}'.format(self.token['access_token'])})

    def set_base_url(self, base_url):
        self.base_url = base_url

    def do_request(self, url, method, data=None, **kwargs):
        for _ in range(3):
            r = requests.request(
                method, url, headers=self.headers, data=data, **kwargs)
            if not r.ok:
                raise requests.HTTPError(r.content)
            if "IAM realm" in r.content or r.status_code == 401:
                self.token = self.keycloak.refresh_token(self.token)
                self.headers["Cookie"] = 'kc-access={}'.format(
                    self.token['access_token'])
                continue
            else:
                return r
        else:
            raise RuntimeError("Cannot authenticate in Keycloak")

    def request(self, url, method, body=None, **kwargs):
        url = urlparse.urljoin(self.base_url, url)
        logger.debug(
            "Sending request to: {}, body: {}, headers: {}, kwargs: {}".format(
                url, body, self.headers, kwargs))

        kwargs.update(self.kwargs)
        r = self.do_request(url, method, data=body, **kwargs)
        logger.debug(r.content)
        return r

    def post(self, url, body=None, **kwargs):
        return self.request(url, "POST", body=body, **kwargs)

    def get(self, url, **kwargs):
        return self.request(url, "GET", **kwargs)

    def put(self, url, body=None, **kwargs):
        return self.request(url, "PUT", body=body, **kwargs)

    def delete(self, url, **kwargs):
        return self.request(url, "DELETE", **kwargs)
