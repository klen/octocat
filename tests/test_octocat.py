""" Tests for `octocat` module. """

import pytest

import octocat as oc


params = dict(
    # Demo credentials dont use them in production
    client_id='e8f9ebe239374201c0fc',
    client_secret='b541a98555a0e01a85baef38dd2859d7335eba68',
)


def test_octocat():
    from octocat.octocat import OctocatAPIDescriptor
    client = oc.OctocatClient()
    assert isinstance(client.api, OctocatAPIDescriptor)
    assert isinstance(client.api.test, OctocatAPIDescriptor)


def test_anonimous():
    client = oc.OctocatClient()

    with pytest.raises(oc.OctocatException):
        client.api.unknown()

    repo = client.api.repos.klen.pylama()
    assert repo['full_name']


def test_client():
    client = oc.OctocatClient(loglevel='debug', **params)
    repo = client.api.repos.klen.pylama()
    assert repo['full_name']


# pylama:ignore=W0611,D
