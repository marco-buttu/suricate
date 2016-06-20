from collections import namedtuple

version_info_t = namedtuple(
    'version_info_t',
    ('major', 'minor', 'micro', 'releaselevel', 'serial')
)

SERIES = 'DEV'
VERSION = version_info_t(0, 1, 0, 'a1', '')

__version__ = '{0.major}.{0.minor}.{0.micro}{0.releaselevel}'.format(VERSION)
__author__ = 'Marco Buttu'
__contact__ = 'mbuttu@oa-cagliari.inaf.it'
__homepage__ = 'http://suricate.org'
__docformat__ = 'restructuredtext'
