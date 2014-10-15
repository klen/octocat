import logging
import os
import json
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

    __methods = 'get', 'post', 'put', 'patch', 'delete', 'head'

    def __init__(self, client, method='GET', session=None):
        self.__client = client
        self.__method = method
        self.__session = [] if session is None else session

    @property
    def __url(self):
        """ Return self url. """
        return "/".join(self.__session)

    def __getattr__(self, method):
        if method.lower() not in self.__methods:
            return OctocatAPIDescriptor(self.__client, self.__method, self.__session + [method])
        self.__method = method.upper()
        return self

    __getitem__ = __getattr__

    def __str__(self):
        return "%s %s" % (self.__method, self.__url)

    def __repr__(self):
        return 'API %s' % self

    def __call__(self, **data):
        """ Make request to github. """
        kwargs = dict(data=data)
        if self.__method.lower() == 'get':
            data = dict(
                (k, v if not isinstance(v, (list, tuple)) else ','.join(v))
                for (k, v) in data.items())
            kwargs = dict(params=data)

        return self.__client.request(self.__method, self.__url, **kwargs)


class OctocatClient(object):

    """ Client for github API. """

    default_options = dict(
        accept='application/vnd.github.v3+json',
        access_token=None,
        client_id=None,
        client_secret=None,
        domain='api.github.com',
        fixtures_dir=os.getcwd(),
        loglevel='info',
        mock=None,
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

        if self.options['mock'] and url in self.options['mock']:
            return self.__load_mock(self.options['mock'][url])

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
            logger.debug(response.content)
            response.raise_for_status()
            response = response.json()

        except (rs.HTTPError, ValueError):
            message = "%s: %s" % (response.status_code, response.content)
            raise OctocatException(message)

        return response

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

    def __load_mock(self, mock):
        """ Load mock from file or return an object. """

        if not isinstance(mock, str):
            return mock

        mock = os.path.join(self.options['fixtures_dir'], mock)
        with open(mock) as f:
            return json.load(f)


# pylama:ignore=D,E1120
