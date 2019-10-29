from suricate.errors import CannotGetComponentError

import pytest


def test_zero_argument_init(Publisher):
    publisher = Publisher()
    jobs_id = [job.id for job in publisher.get_jobs()]
    assert jobs_id == ['rescheduler']


def test_one_argument_init(Publisher):
    """In case of only one argument, the Publisher expects a dictionary"""
    config = {
        "TestNamespace/Positioner00":
            [
                {"attribute": "position", "timer": 0.1},
                {"attribute": "current", "timer": 0.1},
            ],
        "TestNamespace/Positioner01":
            [
                {"attribute": "current", "timer": 0.1},
            ]
    }
    publisher = Publisher(config)
    jobs_id = sorted([job.id for job in publisher.get_jobs()])
    assert jobs_id == [
        'TestNamespace/Positioner00/current',
        'TestNamespace/Positioner00/position',
        'TestNamespace/Positioner01/current',
        'rescheduler',
    ]


def test_three_arguments_init(Publisher):
    """In case of three arguments, they must be: component, attr, timer"""
    publisher = Publisher('TestNamespace/Positioner', 'position', 0.1)
    jobs_id = [job.id for job in publisher.get_jobs()]
    assert jobs_id == ['TestNamespace/Positioner/position', 'rescheduler']


def test_wrong_component_name(Publisher):
    """In case of wrong component name, raise a ValueError"""
    with pytest.raises(CannotGetComponentError):
        Publisher('foo', 'position', 0.1)


def test_wrong_attribute_name(Publisher):
    """In case of wrong component name, raise a ValueError"""
    with pytest.raises(ValueError):
        Publisher('TestNamespace/Positioner', 'foo', 0.1)


if __name__ == '__main__':
    pytest.main()
