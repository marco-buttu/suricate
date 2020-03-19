from flask import json, jsonify
import pytest


BASE_URL = '/publisher/api/v0.1'

DATA = {
    'container': 'PositionerContainer',
    'component': 'TestNamespace/Positioner',
    'attribute': 'position',
    'description': 'a brief description',
    'units': 'mm',
    'timer': 0.1,
    'type': 'property',
}


jobs_from_data = {
    'jobs':
        [
            {
                'id': '%s/%s' % (DATA['component'], DATA['attribute']),
                'timer': DATA['timer'],
            }
        ]
}


HEADERS = {'content-type':'application/json'}


def test_get_empty_jobs(client):
    """Upon start up, get an empty list of jobs"""
    response = client.get('%s/jobs' % BASE_URL)
    data = json.loads(response.data)
    assert not any(data['jobs'])


def test_create_jobs_returns_the_job(client):
    """Return the created job"""
    response = client.post(
        '%s/jobs' %BASE_URL, data=json.dumps(DATA), headers=HEADERS)
    answer = DATA.copy()
    del answer['type']
    assert json.loads(response.get_data()) == answer


def test_create_and_get_jobs(client):
    """GET jobs returns the content of POST jobs."""
    client.post('%s/jobs' %BASE_URL, data=json.dumps(DATA), headers=HEADERS)
    response = client.get('%s/jobs' % BASE_URL)
    assert json.loads(response.get_data()) == jobs_from_data


def test_create_jobs_invalid_json(client):
    # Do not json.dumps(DATA)
    response = client.post('%s/jobs' %BASE_URL, data=DATA, headers=HEADERS)
    assert response.status_code == 400


def test_create_jobs_empty_json(client):
    response = client.post('%s/jobs' %BASE_URL, data={})
    assert response.status_code == 400


def test_stop(client, monkeypatch):
    monkeypatch.setattr('suricate.server.publisher.shutdown', lambda: None)
    response = client.post('%s/stop' %BASE_URL)
    assert response.get_data() == 'Server stopped :-)'


def test_get_configuration(client):
    """Get the running configuration"""
    response = client.get('%s/config' % BASE_URL)
    from suricate.configuration import config
    response_config = json.loads(response.get_data())
    assert response_config == config


if __name__ == '__main__':
    pytest.main()
