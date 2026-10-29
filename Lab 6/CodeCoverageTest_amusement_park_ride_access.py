"""Lab 6, stage 1: exercise application statements with realistic cases.

Run directly with pytest, collecting *line* coverage of the application module.
The production module is intentionally left unchanged.
"""

import pytest

from amusement_park_ride_access import (
    inspect_safety_restraints,
    process_ride_admissions,
)


def test_invalid_arguments_are_rejected():
    with pytest.raises(ValueError, match="Invalid groups list or pass fee"):
        process_ride_admissions(None, 5.0)
    with pytest.raises(ValueError, match="Invalid groups list or pass fee"):
        process_ride_admissions([], -1.0)


def test_closed_and_unknown_rides_do_not_admit_patrons():
    groups = [
        {"is_open": False, "ride_type": "family", "patrons": [{"height_cm": 150}]},
        {"is_open": True, "ride_type": "unknown", "patrons": [{"height_cm": 150}]},
    ]
    assert process_ride_admissions(groups, 5.0) == {
        "total_revenue": 0.0,
        "status": "ZERO_ADMISSIONS",
    }


def test_open_rides_child_discount_and_express_fee():
    groups = [
        {
            "is_open": True,
            "ride_type": "family",
            "has_fast_lane": True,
            "patrons": [
                {"height_cm": 140, "is_child": True},
                {"height_cm": 150, "is_child": False},
            ],
        },
        {"is_open": True, "ride_type": "water_ride", "patrons": [{"height_cm": 160}]},
        {"is_open": True, "ride_type": "roller_coaster", "patrons": [{"height_cm": 170}]},
    ]
    # 6.00 child + 10.00 adult + 4.50 fast lane + 18.00 water + 25.00 coaster.
    assert process_ride_admissions(groups, 4.5) == {
        "total_revenue": 63.5,
        "status": "COMPLETED",
    }


def test_height_and_health_checks_reject_unsafe_patrons():
    groups = [
        {
            "is_open": True,
            "ride_type": "water_ride",
            "patrons": [
                {"height_cm": 0},
                {"height_cm": 119},
                {"height_cm": 150, "health_warning": True},
            ],
        }
    ]
    assert process_ride_admissions(groups, 0.0) == {
        "total_revenue": 0.0,
        "status": "ZERO_ADMISSIONS",
    }


def test_coaster_health_warning_cancels_group_tickets():
    groups = [
        {
            "is_open": True,
            "ride_type": "roller_coaster",
            "patrons": [
                {"height_cm": 170},
                {"height_cm": 150, "health_warning": True},
                {"height_cm": 180},  # Unreachable because the safety check breaks.
            ],
        }
    ]
    assert process_ride_admissions(groups, 0.0) == {
        "total_revenue": 0.0,
        "status": "ZERO_ADMISSIONS",
    }


def test_more_than_four_rejections_trigger_safety_audit():
    groups = [
        {
            "is_open": True,
            "ride_type": "family",
            "patrons": [{"height_cm": -1}] * 5,
        }
    ]
    assert process_ride_admissions(groups, 0.0) == {
        "total_revenue": 0.0,
        "status": "SAFETY_AUDIT",
    }


def test_safety_restraints_no_data_and_normal_operation():
    assert inspect_safety_restraints([]) == "NO_DATA"
    assert inspect_safety_restraints([[1, 0, 1], [0, 1]]) == "SAFE"


def test_two_consecutive_unlatched_readings_trigger_emergency():
    assert inspect_safety_restraints([[1, 0, 0, 1]]) == "EMERGENCY_LOCK"
