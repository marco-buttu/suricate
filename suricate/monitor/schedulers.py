import redis

from apscheduler.schedulers.background import BackgroundScheduler
from suricate.monitor import jobs


__all__ = ['Scheduler']


class ACSScheduler(BackgroundScheduler):
    """TODO:
    - add_method_job: like add_property_job(), but for methods
    - It should delegate... or proxy
    """

    def add_attribute_job(
            self,
            component_ref,
            attr,
            timer,
            units='',
            description='',
            channel=''):
        """TODO: docstring. The component could be a name or an instance"""
        # Job identifier: namespace/component/attribute
        job_id = '/'.join([component_ref.name, attr])
        channel = channel if channel else job_id
        r = redis.StrictRedis()
        error_job_key = 'error_job:%s' % channel
        r.delete(error_job_key)
        return super(ACSScheduler, self).add_job(
            func=publisher,
            args=(channel, component_ref, attr, timer, units, description),
            id=job_id,
            trigger='interval',
            seconds=timer)


# TODO: check the configuration and bind the right scheduler
Scheduler = ACSScheduler
publisher = jobs.acs_publisher
