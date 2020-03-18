import json
import datetime
import logging

import redis
import suricate.services
from suricate.errors import (
    CannotGetComponentError,
    ComponentAttributeError,
    ACSNotRunningError,
)


logger = logging.getLogger('suricate')
logger_dbg = logging.getLogger('suricate_dbg')
r = redis.StrictRedis()


def acs_publisher(channel, component, attribute, units='', description=''):
    """Get the component reference and a property as a dict object."""
    data_dict = {
        'value': '',
        'error': '',
        'units': units,
        'description': description,
        'timestamp': str(datetime.datetime.utcnow()),
    }
    try:
        if component.name in component.unavailables:
            raise CannotGetComponentError()
        if hasattr(component, '_get_' + attribute):  # It is a property
            get_property_obj = getattr(component, '_get_' + attribute)
            property_obj = get_property_obj()
            value, comp = property_obj.get_sync()
            # TODO: check Acspy.Common.TimeHelper for right conversion
            epoch = (comp.timeStamp - 122192928000000000) / 10000000.
            t = datetime.datetime.fromtimestamp(epoch)
        else:  # It is a method, just call it
            method = getattr(component, attribute)
            t = datetime.datetime.utcnow()
            value = method()
        if isinstance(value, list):
            value = tuple(value)  # Convert the value to a tuple
        value = str(value)
        data_dict.update({'value': value, 'timestamp': str(t)})
        # Update the components redis key
        if r.hget('components', component.name) != 'available':
            logger.info('OK - component %s is online' % component.name)
            r.hmset('components', {component.name: 'available'})
    except CannotGetComponentError:
        if not suricate.services.is_manager_online():
            message = 'ACS not running'
            Exc = ACSNotRunningError
        else:
            message = 'cannot get component %s' % component.name
            Exc = CannotGetComponentError
        data_dict.update({'error': message})
        logger.error(message)
        r.hmset('components', {component.name: 'unavailable'})
        raise Exc(message)
    except AttributeError:
        message = 'cannot get attribute %s from %s' % (
                attribute, component.name)
        data_dict.update({'error': message})
        logger.error(message)
        r.hmset('components', {component.name: 'unavailable'})
        raise ComponentAttributeError(message)
    except Exception, ex:
        if not suricate.services.is_manager_online():
            message = 'ACS not running'
            Exc = ACSNotRunningError
        else:
            message = 'cannot get component %s' % component.name
            Exc = CannotGetComponentError
        data_dict.update({'error': message})
        logger.error(message)
        r.hmset('components', {component.name: 'unavailable'})
        raise Exc(message)
    finally:
        if not r.hmset(channel, data_dict):
            logger.error('cannot write data on redis for %s' % channel)
        r.publish(channel, json.dumps(data_dict))
        healthy_job_key = 'healthy_job:%s' % channel
        if not r.set(healthy_job_key, 1):
            logger.error('cannot set %s' % healthy_job_key)
