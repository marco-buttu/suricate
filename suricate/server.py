#! /usr/bin/env python
from __future__ import with_statement, print_function

import logging
import time
import sys
import socket
from flask import Flask, jsonify, abort, request
from suricate.core import Publisher
from suricate.errors import CannotGetComponentError


app = Flask(__name__)
publisher = None
logger = logging.getLogger('suricate')

@app.route('/publisher/api/v0.1/jobs', methods=['GET'])
def get_jobs():
    jobs = []
    for j in publisher.s.get_jobs():
        sec, mic = j.trigger.interval.seconds, j.trigger.interval.microseconds
        jobs.append({'id': j.id, 'timer': sec + mic / (1.0 * 10 ** 6)})
    return jsonify({'jobs': jobs})


@app.route('/publisher/api/v0.1/jobs', methods=['POST'])
def create_job():
    if not request.json:
        abort(400)
    else:
        component = request.json.get('component')
        attribute = request.json.get('attribute')
        timer = request.json.get('timer')
        description = request.json.get('description', '')

    if not component or not attribute or not timer:
        abort(400)
    else:
        try:
            timer = float(timer)
        except (TypeError, ValueError):
            abort(400)

    job = {
        component: [
            {'attribute': attribute, 'description': description, 'timer': timer}
        ]
    }
    publisher.add_jobs(job)  # TODO: catch the exception in case of invalid job
    return jsonify({
        'component': component,
        'attribute': attribute,
        'timer': timer}), 201


@app.route('/publisher/api/v0.1/stop', methods=['POST'])
def stop():  # pragma: no cover
    try:
        app_shutdown = request.environ.get('werkzeug.server.shutdown')
        if app_shutdown is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        app_shutdown()
        logger.info('the server has been stopped')
    except:
        logger.error('can not shutdown the Werkzeug server')
    finally:
        if publisher:
            publisher.shutdown()
            logger.info('all scheduled jobs have been closed')
        else:
            logger.error('there is no reference to the publisher')
    return 'Server stopped :-)'


def start_publisher(components=None):
    global publisher
    # In case a component is not available, Publisher.add_jobs()
    # writes a log an error message
    publisher = Publisher(components) if components else Publisher()
    publisher.start()


def stop_publisher():
    if publisher is not None:
        publisher.shutdown()


def start_webserver():
    try:
        app.run(debug=False)
    except socket.error, ex:
        logger.error(ex)
        sys.exit(1)


def start(components=None):
    start_publisher(components)
    start_webserver()
