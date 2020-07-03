import time
from datetime import datetime
from flask import json, jsonify
import pytest
from suricate.configuration import dt_format


BASE_URL = '/publisher/api/v0.1'

DATA = {
    'component': 'TestNamespace/Positioner',
    'startup_delay': 0,
    'container': 'PositionerContainer',
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
        '%s/jobs' % BASE_URL, data=json.dumps(DATA), headers=HEADERS)
    answer = DATA.copy()
    del answer['type']
    assert response.get_json() == answer


def test_create_and_get_jobs(client):
    """GET jobs returns the content of POST jobs."""
    client.post('%s/jobs' % BASE_URL, data=json.dumps(DATA), headers=HEADERS)
    response = client.get('%s/jobs' % BASE_URL)
    assert response.get_json() == jobs_from_data


def test_create_jobs_invalid_json(client):
    # Do not json.dumps(DATA)
    response = client.post('%s/jobs' % BASE_URL, data=DATA, headers=HEADERS)
    assert response.status_code == 400


def test_create_jobs_empty_json(client):
    response = client.post('%s/jobs' % BASE_URL, data={})
    assert response.status_code == 400


def test_stop(client, monkeypatch):
    monkeypatch.setattr('suricate.server.publisher.shutdown', lambda: None)
    response = client.post('%s/stop' % BASE_URL)
    assert response.get_data() == 'Server stopped :-)'


def test_get_configuration(client):
    """Get the running configuration"""
    response = client.get('%s/config' % BASE_URL)
    from suricate.configuration import config
    response_config = response.get_json()
    assert response_config == config


def test_post_command(client):
    """Call the server.post_command() method"""
    cmd = 'getTpi'
    raw_response = client.post('/cmd/%s' % cmd)
    response = raw_response.get_json()
    job_id = response['id']
    assert '_' in job_id
    assert cmd == job_id.split('_')[0]
    assert response['command'] == cmd
    assert response['stime'] == response['etime']
    assert not response['delivered']
    assert not response['complete']
    assert not response['success']
    assert response['result'] == 'unknown'
    assert response['seconds'] == 0.0


def test_execute_command(client):
    """Call the api.tasks.command() method"""
    cmd = 'getTpi'
    raw_response = client.post('/cmd/%s' % cmd)
    post_response = raw_response.get_json()
    job_id = post_response['id']
    # time.sleep(0.5)
    raw_response = client.get('/cmd/%s' % job_id)
    get_response = raw_response.get_json()
    assert get_response['command'] == cmd
    assert get_response['complete']
    assert get_response['delivered']
    assert get_response['stime'] <= get_response['etime']
    assert get_response['success']
    assert 'getTpi\\\n00)' in get_response['result']
    assert get_response['seconds'] > 0.0


def test_not_success(client):
    """Scheduler.command() unsuccessful."""
    cmd = 'wrongCommand'
    raw_response = client.post('/cmd/%s' % cmd)
    post_response = raw_response.get_json()
    job_id = post_response['id']
    # time.sleep(0.5)
    raw_response = client.get('/cmd/%s' % job_id)
    get_response = raw_response.get_json()
    assert get_response['command'] == cmd
    assert get_response['complete']
    assert get_response['delivered']
    assert get_response['stime'] <= get_response['etime']
    assert not get_response['success']
    assert 'wrongCommand?' in get_response['result']
    assert get_response['seconds'] > 0.0


def test_get_last_commands(client):
    """Get the last N executed commands.
    This test checks also the case of GET /cmds/N"""
    client.post('/cmd/moo')
    time.sleep(0.01)
    client.post('/cmd/foo')
    time.sleep(0.01)
    client.post('/cmd/getTpi')
    time.sleep(0.01)
    raw_response = client.get('/cmds/10')
    response = raw_response.get_json()
    assert len(response) == 3
    assert response[2]['command'] == 'moo'
    raw_response = client.get('/cmds/2')
    response = raw_response.get_json()
    assert len(response) == 2
    assert response[0]['command'] == 'getTpi'


def test_get_last_default_commands(client):
    """Without N, GET /cmds returns the last 10 commands"""
    for i in range(15):
        client.post('/cmd/foo')
    time.sleep(0.01)
    raw_response = client.get('/cmds')
    response = raw_response.get_json()
    assert len(response) == 10


def test_empty_commands_history(client):
    raw_response = client.get('/cmds')
    response = raw_response.get_json()
    assert response['status_code'] == 404
    assert response['error_message'] == 'empty command history'


def test_get_commands_from_datetimex(client):
    """Get all commands from datetime dtx until now"""
    client.post('/cmd/command_1')
    time.sleep(0.01)
    raw_response = client.post('/cmd/command_2')
    post_response = raw_response.get_json()
    dtx = post_response['stime']
    client.post('/cmd/command_3')
    client.post('/cmd/command_4')
    time.sleep(0.1)
    raw_response = client.get('/cmds')
    response = raw_response.get_json()
    assert len(response) == 4
    raw_response = client.get('/cmds/from/%s' % dtx)
    response = raw_response.get_json()
    assert len(response) == 3


def test_get_commands_from_invalid_datetimex(client):
    """Test invalid datetime format in GET /cmds/from/dtx"""
    raw_response = client.get('/cmds/from/wrong_dtx')
    response = raw_response.get_json()
    assert response['status_code'] == 400
    assert response['error_message'] == 'invalid datetime format'


def test_get_commands_from_datetimex_to_datetimey(client):
    """Get all commands from datetime dtx to dty"""
    client.post('/cmd/command_1')
    time.sleep(0.01)
    raw_response = client.post('/cmd/command_2')
    post_response = raw_response.get_json()
    dtx = post_response['stime']
    raw_response = client.post('/cmd/command_3')
    post_response = raw_response.get_json()
    dty = post_response['stime']
    client.post('/cmd/command_4')  # cmd n.4
    time.sleep(0.1)
    raw_response = client.get('/cmds')
    response = raw_response.get_json()
    assert len(response) == 4
    raw_response = client.get('/cmds/from/%s/to/%s' % (dtx, dty))
    response = raw_response.get_json()
    assert len(response) == 2


def test_get_commands_from_invalid_datetimex_to_datetimey(client):
    """Test invalid datetime format in GET /cmds/from/dtx/to/dty"""
    raw_response = client.get('/cmds/from/wrong_dtx/to/wrong_dty')
    response = raw_response.get_json()
    assert response['status_code'] == 400
    assert response['error_message'] == 'invalid datetime format'


def test_command_not_executed(client):
    """What heppens when the scheduler is not available?"""


if __name__ == '__main__':
    pytest.main()