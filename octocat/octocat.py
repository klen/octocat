import logging
import requests as rs
import base64
from functools import wraps
from contextlib import contextmanager

logger = logging.getLogger(__name__)
rs_logger = logging.getLogger('requests')

if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


def _curry_method(method, *cargs, **ckwargs):

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        args = cargs + args
        kwargs.update(ckwargs)
        return method(self, *args, **kwargs)

    return wrapper


class OctocatException(Exception):
    pass


class OctocatAPIDescriptor(object):

    """ Proxy API methods. """

    def __init__(self, client):
        self.__client = client
        self.__session = []

    def __getattr__(self, method):
        self.__session.append(method)
        return self

    def __getitem__(self, method):
        self.__session.append(method)
        return self

    def __call__(self, *args, **data):
        """ Make request to github. """
        url = '/'.join(self.__session)
        return self.__client.get(url, data=data)


class OctocatClient(object):

    """ Client for github API. """

    default_options = dict(
        accept='application/vnd.github.v3+json',
        access_token=None,
        client_id=None,
        client_secret=None,
        domain='api.github.com',
        loglevel='info',
        user_agent='Octocat-App',
    )

    def __init__(self, **options):
        self.options = dict(self.default_options)
        self.options.update(options)

    @property
    def params(self):
        """ Get default request params. """
        params = dict()

        if self.options['client_id']:
            params['client_id'] = self.options['client_id']

        if self.options['client_secret']:
            params['client_secret'] = self.options['client_secret']

        if self.options['access_token']:
            params['access_token'] = self.options['access_token']

        return params

    @property
    def headers(self):
        """ Get default request headers. """
        return {
            'Accept': self.options['accept'],
            'User-Agent': self.options['user_agent'],
        }

    def request(self, method, url, params=None, headers=None, **kwargs):
        """ Make request to Github API. """

        loglevel = self.options.get('loglevel', 'info')
        logger.setLevel(loglevel.upper())
        rs_logger.setLevel(loglevel.upper())

        url = 'https://%s/%s' % (self.options['domain'], url.strip('/'))

        _params = self.params
        if params is not None:
            _params.update(params)

        _headers = self.headers
        if headers is not None:
            _headers.update(headers)

        try:
            response = rs.api.request(
                method, url, params=_params, headers=_headers, **kwargs)
            json = response.json()
            logger.debug(json)
            response.raise_for_status()

        except rs.HTTPError:
            message = "%s: %s" % (response.status_code, json.get('message'))
            raise OctocatException(message)

        except ValueError:
            message = "%s: %s" % (response.status_code, response.body)
            raise OctocatException(message)

        return json

    get = _curry_method(request, 'GET')
    post = _curry_method(request, 'POST')
    put = _curry_method(request, 'PUT')
    head = _curry_method(request, 'HEAD')
    patch = _curry_method(request, 'PATCH')
    delete = _curry_method(request, 'DELETE')

    @contextmanager
    def ctx(self, **options):
        """ Redefine context. """
        _opts = dict(self.options)
        try:
            self.options.update(options)
            yield self
        finally:
            self.options = _opts

    @property
    def api(self):
        return OctocatAPIDescriptor(self)

    def login(self, username, password):
        """ Login and get access token. """
        return self.get('authorizations', headers=dict(
            Authorization='Basic ' + base64.b64encode(
                '%s:%s' % (username, password)).strip()
        ))


# pylama:ignore=D
