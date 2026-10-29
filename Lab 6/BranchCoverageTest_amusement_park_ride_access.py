"""Lab 6, stage 2: verify both outcomes of every application decision.

Run directly with pytest, collecting *branch* coverage of the application module.
The source application is not modified by these tests.
"""

import pytest

from amusement_park_ride_access import (
    inspect_safety_restraints,
    process_ride_admissions,
)


def ride(ride_type="family", patrons=None, **overrides):
    """Build an open ride group without hiding any application behavior."""
    group = {
        "is_open": True,
        "ride_type": ride_type,
        "patrons": [] if patrons is None else patrons,
    }
    group.update(overrides)
    return group


@pytest.mark.parametrize(
    ("groups", "fee"),
    [
        (None, 3.0),  # Invalid container: first part of the OR is true.
        ({"not": "a list"}, 3.0),
        ([], -0.01),  # Valid container but negative fee: second part is true.
    ],
)
def test_invalid_inputs_raise_value_error(groups, fee):
    with pytest.raises(ValueError, match="Invalid groups list or pass fee"):
        process_ride_admissions(groups, fee)


def test_empty_list_has_no_admissions():
    assert process_ride_admissions([], 0.0) == {
        "total_revenue": 0.0,
        "status": "ZERO_ADMISSIONS",
    }


def test_closed_group_is_skipped_but_later_group_is_processed():
    groups = [
        ride("roller_coaster", [{"height_cm": 180}], is_open=False),
        ride("family", [{"height_cm": 150}]),
    ]
    assert process_ride_admissions(groups, 1.0) == {
        "total_revenue": 10.0,
        "status": "COMPLETED",
    }


def test_default_family_type_and_missing_patrons():
    groups = [{"is_open": True, "patrons": [{"height_cm": 150}]}]
    assert process_ride_admissions(groups, 2.0) == {
        "total_revenue": 10.0,
        "status": "COMPLETED",
    }
    assert process_ride_admissions([{"is_open": True}], 2.0) == {
        "total_revenue": 0.0,
        "status": "ZERO_ADMISSIONS",
    }


def test_unknown_ride_type_is_rejected_and_other_ride_is_still_processed():
    groups = [
        ride("spaceship", [{"height_cm": 180}]),
        ride("water_ride", [{"height_cm": 155}]),
    ]
    assert process_ride_admissions(groups, 5.0) == {
        "total_revenue": 18.0,
        "status": "COMPLETED",
    }


@pytest.mark.parametrize(
    ("ride_type", "expected"),
    [
        ("family", 10.0),
        ("water_ride", 18.0),
        ("roller_coaster", 25.0),
    ],
)
def test_adult_ticket_prices_for_each_ride(ride_type, expected):
    assert process_ride_admissions(
        [ride(ride_type, [{"height_cm": 180, "is_child": False}])], 0.0
    ) == {"total_revenue": expected, "status": "COMPLETED"}


@pytest.mark.parametrize(
    ("ride_type", "expected"),
    [
        ("family", 6.0),
        ("water_ride", 10.8),
        ("roller_coaster", 15.0),
    ],
)
def test_child_gets_forty_percent_discount(ride_type, expected):
    assert process_ride_admissions(
        [ride(ride_type, [{"height_cm": 120, "is_child": True}])], 0.0
    ) == {"total_revenue": expected, "status": "COMPLETED"}


def test_fast_lane_fee_applied_once_per_group_even_without_patrons():
    assert process_ride_admissions([ride(has_fast_lane=True)], 5.75) == {
        "total_revenue": 5.75,
        "status": "COMPLETED",
    }
    assert process_ride_admissions([ride(has_fast_lane=False)], 5.75) == {
        "total_revenue": 0.0,
        "status": "ZERO_ADMISSIONS",
    }


@pytest.mark.parametrize("height", [-10, 0, 1, 119])
def test_nonpositive_and_too_short_riders_are_rejected(height):
    assert process_ride_admissions(
        [ride(patrons=[{"height_cm": height}])], 0.0
    ) == {"total_revenue": 0.0, "status": "ZERO_ADMISSIONS"}


def test_health_warning_on_noncoaster_rejects_only_affected_person():
    groups = [
        ride(
            "water_ride",
            [
                {"height_cm": 180, "health_warning": True},
                {"height_cm": 160, "health_warning": False},
            ],
        )
    ]
    assert process_ride_admissions(groups, 0.0) == {
        "total_revenue": 18.0,
        "status": "COMPLETED",
    }


def test_coaster_warning_resets_group_revenue_and_stops_its_queue():
    groups = [
        ride(
            "roller_coaster",
            [
                {"height_cm": 190},
                {"height_cm": 180, "health_warning": True},
                {"height_cm": 190},
            ],
        )
    ]
    assert process_ride_admissions(groups, 0.0) == {
        "total_revenue": 0.0,
        "status": "ZERO_ADMISSIONS",
    }


def test_health_warning_checked_only_after_valid_height():
    groups = [ride(patrons=[{"height_cm": 0, "health_warning": True}])]
    assert process_ride_admissions(groups, 0.0) == {
        "total_revenue": 0.0,
        "status": "ZERO_ADMISSIONS",
    }


def test_audit_threshold_four_versus_five_rejections():
    def bad_patrons(n):
        return [{"height_cm": 119}] * n

    assert process_ride_admissions([ride(patrons=bad_patrons(4))], 0.0) == {
        "total_revenue": 0.0,
        "status": "ZERO_ADMISSIONS",
    }
    assert process_ride_admissions([ride(patrons=bad_patrons(5))], 0.0) == {
        "total_revenue": 0.0,
        "status": "SAFETY_AUDIT",
    }


def test_safety_audit_priority_over_positive_revenue():
    groups = [ride(patrons=[{"height_cm": 180}] + [{"height_cm": 119}] * 5)]
    assert process_ride_admissions(groups, 0.0) == {
        "total_revenue": 10.0,
        "status": "SAFETY_AUDIT",
    }


@pytest.mark.parametrize(
    ("streams", "expected"),
    [
        (None, "NO_DATA"),
        ([], "NO_DATA"),
        ([[]], "SAFE"),
        ([[1, 1], [0, 1]], "SAFE"),
        ([[0, 1, 0]], "SAFE"),  # Nonzero reading resets the streak.
        ([[0], [0]], "SAFE"),  # Each sensor stream gets its own streak.
        ([[0, 0]], "EMERGENCY_LOCK"),
        ([[1, 0, 0, 1]], "EMERGENCY_LOCK"),
    ],
)
def test_safety_sensor_decision_paths(streams, expected):
    assert inspect_safety_restraints(streams) == expected
