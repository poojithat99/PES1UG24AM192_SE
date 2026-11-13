"""Fuzz invalid inputs and verify useful behaviour for all three functions."""
import math

import pytest
from hypothesis import example, given, settings, strategies as st
from processor import (validate_height_and_fastpass,
                       compute_dispatch_throughput,
                       resolve_safety_restraint_code)

settings.register_profile("lab", max_examples=300, derandomize=True, deadline=None)
settings.load_profile("lab")
unexpected = st.one_of(st.text(max_size=6000), st.none(), st.integers(),
                      st.floats(), st.booleans(), st.binary(),
                      st.lists(st.integers(), max_size=5),
                      st.dictionaries(st.text(max_size=5), st.integers(), max_size=3))


@given(unexpected)
def test_validate_height_and_fastpass_no_crash(s):
    try:
        result = validate_height_and_fastpass(s)
    except Exception as exc:
        pytest.fail(f"rider validation crashed for {s!r}: {exc!r}")
    assert isinstance(result, str)
    assert result.startswith(("Height ", "Invalid rider spec:"))


@given(unexpected)
def test_compute_dispatch_throughput_safe(s):
    try:
        result = compute_dispatch_throughput(s)
    except Exception as exc:
        pytest.fail(f"throughput crashed for {s!r}: {exc!r}")
    assert result is None or (isinstance(result, float)
                              and math.isfinite(result) and result >= 0)


@given(unexpected)
def test_resolve_safety_restraint_code_safe(s):
    try:
        result = resolve_safety_restraint_code(s)
    except Exception as exc:
        pytest.fail(f"restraint lookup crashed for {s!r}: {exc!r}")
    assert result in {"Over-the-Shoulder Harness", "Lap Bar and Seatbelt",
                      "Hydraulic Shoulder Vest", "Manual Safety Bar",
                      "Unknown restraint code"}


@given(st.integers(min_value=0, max_value=10000), st.booleans())
@example(119, False)
@example(120, True)
def test_valid_rider_spec(height, fastpass):
    flag = "yes" if fastpass else "no"
    expected = (f"Height {height}cm: {'Approved' if height >= 120 else 'Denied'} "
                f"({'FastPass Priority' if fastpass else 'Standard Entry'})")
    assert validate_height_and_fastpass(f" {height} : {flag} ") == expected


@given(st.integers(min_value=0, max_value=1000000),
       st.integers(min_value=1, max_value=1000000))
def test_valid_throughput(riders, minutes):
    assert compute_dispatch_throughput(f" {riders} / {minutes} ") == round(riders / minutes, 2)


@given(st.sampled_from([
    ("CST", "Over-the-Shoulder Harness"), ("WTR", "Lap Bar and Seatbelt"),
    ("DRP", "Hydraulic Shoulder Vest"), ("WHL", "Manual Safety Bar")]),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_", max_size=30))
def test_known_restraint_prefix(pair, suffix):
    code, expected = pair
    assert resolve_safety_restraint_code(f" {code.lower()}_{suffix} ") == expected


@pytest.mark.parametrize("value", [None, "", "120", "120:YES:extra", "abc:YES",
                                    "-1:NO", "120:MAYBE", "1.5:YES", "9" * 5000 + ":YES"])
def test_invalid_rider_rejected(value):
    assert validate_height_and_fastpass(value).startswith("Invalid rider spec:")


@pytest.mark.parametrize("value", [None, "", "48", "48/2/1", "x/2", "48/0",
                                    "-1/2", "1/-2", "nan/1", "1/inf", "inf/1",
                                    "1e308/1e-308", "1/1e-9999"])
def test_invalid_throughput_rejected(value):
    assert compute_dispatch_throughput(value) is None


@pytest.mark.parametrize("value", [None, "", "XYZ_01", 123, [], "CS"])
def test_invalid_restraint_rejected(value):
    assert resolve_safety_restraint_code(value) == "Unknown restraint code"
