#! /usr/bin/env python
from __future__ import with_statement, print_function

import logging
import time
import sys
import socket
from datetime import datetime
from flask import jsonify, abort, request
from suricate.errors import CannotGetComponentError
from suricate.configuration import config
from suricate.monitor.core import Publisher
from suricate.app import db, app
import rq
from redis import Redis
from sqlalchemy import create_engine

publisher = None
logger = logging.getLogger('suricate')


class Command(db.Model):
    __tablename__ = 'commands'

    id = db.Column(db.String(128), primary_key=True)
    command = db.Column(db.String(128), nullable=False)
    stime = db.Column(db.DateTime, nullable=False)
    etime = db.Column(db.DateTime, nullable=False)
    complete = db.Column(db.Boolean, default=False)
    success = db.Column(db.Boolean, default=False)
    result = db.Column(db.String(128), default='unknown')
    seconds = db.Column(db.Float, default=0.0)

engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
Command.metadata.create_all(engine)


@app.route('/cmd/<command>', methods=['POST'])
def post_command(command):
    stime = datetime.utcnow()
    stimestr = stime.strftime("%Y-%m-%d~%H:%M:%S")
    job_id = '{}_{}'.format(command, stimestr)
    cmd = Command(
        id=job_id,
        command=command,
        stime=stime,
        etime=stime,
    )
    # Make the response before committing the command,
    # otherwise the commit will clean cmd.__dict__
    response = dict(cmd.__dict__)
    del response['_sa_instance_state']
    db.session.add(cmd)
    db.session.commit()
    job = app.cmd_queue.enqueue(
        'api.tasks.command',
        args=(command, job_id),
        job_id=job_id,
    )
    return jsonify(response)


@app.route('/cmd/<cmd_id>', methods=['GET'])
def get_command(cmd_id):
    cmd = Command.query.get(cmd_id)
    if not cmd:
        response = {
            'status_code': 404,
            'error_message': "'%s' not found in database" % cmd_id,
        }
        return jsonify(response)
    else:
        response = cmd.__dict__
        del response['_sa_instance_state']
        return jsonify(response)


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
        startup_delay = request.json.get('startup_delay')
        container = request.json.get('container')
        component = request.json.get('component')
        attribute = request.json.get('attribute')
        timer = request.json.get('timer')
        units = request.json.get('units', '')
        description = request.json.get('description', '')
        type_ = request.json.get('type', 'property')
        types = 'properties' if type_ == 'property' else 'methods'

    if not (component or not attribute or not timer or not container or not
            startup_delay
    ):
        logger.error('specify component, container, attribute, timer and '
                     'startup_delay')
        abort(400)
    else:
        try:
            timer = float(timer)
        except (TypeError, ValueError):
            logger.error('cannot convert %s to float' % timer)
            abort(400)

    job = {
        component: {
            "startup_delay": startup_delay,
            "container": container,
            types: [
                {
                    'name': attribute,
                    'description': description,
                    'timer': timer,
                    'units': units,
                }
            ]
        }
    }
    publisher.add_jobs(job)  # TODO: catch the exception in case of invalid job
    return jsonify({
            'component': component,
            'container': container,
            'startup_delay': startup_delay,
            'attribute': attribute,
            'description': description,
            'units': units,
            'timer': timer}
        ), 201


@app.route('/publisher/api/v0.1/config', methods=['GET'])
def get_config():
    return jsonify(config)


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
    logger.info('suricate server is starting...')
    start_publisher(components)
    start_webserver()


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, Command=Command)
