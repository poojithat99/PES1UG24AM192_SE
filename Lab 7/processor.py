"""Defensive input validation for the amusement park lab.

Invalid rider input returns an error message; invalid throughput returns None;
unknown zone input returns an explicit unknown-code message. Valid outputs and
original prefix-based zone lookup are preserved.
"""
import math

MAX_INPUT_LENGTH = 4096  # Bound conversion work for untrusted textual input.
RESTRAINT_TYPES = {
    "CST": "Over-the-Shoulder Harness",
    "WTR": "Lap Bar and Seatbelt",
    "DRP": "Hydraulic Shoulder Vest",
    "WHL": "Manual Safety Bar",
}


def _valid_text(value):
    return isinstance(value, str) and 0 < len(value) <= MAX_INPUT_LENGTH


def validate_height_and_fastpass(rider_spec):
    """Accept a nonnegative integer height and YES/NO flag, separated by ':'."""
    error = "Invalid rider spec: use a nonnegative integer height and YES or NO (140:YES)"
    if not _valid_text(rider_spec):
        return error
    parts = rider_spec.strip().split(':')
    if len(parts) != 2:
        return error
    height_str, pass_str = parts
    try:
        height = int(height_str)
    except ValueError:
        return error
    flag = pass_str.strip().upper()
    if height < 0 or flag not in ("YES", "NO"):
        return error
    eligible = height >= 120
    status = "FastPass Priority" if flag == "YES" else "Standard Entry"
    return f"Height {height}cm: {'Approved' if eligible else 'Denied'} ({status})"


def compute_dispatch_throughput(ride_metric_str):
    """Return a finite nonnegative rate, or None for invalid/unsafe metrics."""
    if not _valid_text(ride_metric_str):
        return None
    parts = ride_metric_str.split('/')
    if len(parts) != 2:
        return None
    try:
        riders, cycle_mins = map(float, parts)
    except ValueError:
        return None
    if (not math.isfinite(riders) or not math.isfinite(cycle_mins)
            or riders < 0 or cycle_mins <= 0):
        return None
    rate = riders / cycle_mins
    if not math.isfinite(rate):
        return None
    return round(rate, 2)


def resolve_safety_restraint_code(zone_code):
    """Resolve the first three characters; unknown/malformed input fails safely."""
    if not _valid_text(zone_code):
        return "Unknown restraint code"
    prefix = zone_code.strip().upper()[:3]
    return RESTRAINT_TYPES.get(prefix, "Unknown restraint code")


def main():
    try:
        print("==== Running validate_height_and_fastpass ====")
        r_input = input("Enter rider spec (Height:FastPass, e.g. 140:YES): ")
        print(validate_height_and_fastpass(r_input))

        print("\n==== Running compute_dispatch_throughput ====")
        t_input = input("Enter riders/mins (e.g. 48/2.5): ")
        rate = compute_dispatch_throughput(t_input)
        if rate is None:
            print("Invalid ride metrics: use finite riders >= 0 and minutes > 0")
        else:
            print("Throughput (riders/min):", rate)

        print("\n==== Running resolve_safety_restraint_code ====")
        z_input = input("Enter ride zone code (e.g. CST_01, WTR_A): ")
        print("Restraint:", resolve_safety_restraint_code(z_input))
    except (EOFError, KeyboardInterrupt):
        print("\nInput cancelled.")


if __name__ == "__main__":
    main()
