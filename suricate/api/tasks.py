import logging
from datetime import datetime
from suricate.app import db
from suricate.server import Command
from suricate.errors import CannotGetComponentError

logger = logging.getLogger('suricate')


def command(line, job_id):
    from suricate.component import Component
    cmd = Command.query.get(job_id)
    try:
        scheduler = Component(
            name='MANAGEMENT/Gavino',
            container='ManagementContainer',
            startup_delay=0,
        )
        cmd.success, cmd.result = scheduler.command(line)
        etime = datetime.utcnow()
        cmd.etime = etime
        cmd.seconds = (etime - cmd.stime).total_seconds()
        cmd.complete = True
    except CannotGetComponentError:
        cmd.success = False
        cmd.result = 'DISCOS Scheduler not available'
        cmd.complete = True
    except AttributeError:
        logger.error("'%s' not found in database" % job_id)
    finally:
        db.session.commit()