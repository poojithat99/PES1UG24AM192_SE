def validate_height_and_fastpass(rider_spec):
    height_str, pass_str = rider_spec.strip().split(':')
    height = int(height_str)
    pass_map = {"YES": True, "NO": False}
    has_fastpass = pass_map[pass_str.strip().upper()]
    eligible = height >= 120
    status = "FastPass Priority" if has_fastpass else "Standard Entry"
    return f"Height {height}cm: {'Approved' if eligible else 'Denied'} ({status})"

def compute_dispatch_throughput(ride_metric_str):
    riders_str, mins_str = ride_metric_str.split('/')
    riders = float(riders_str)
    cycle_mins = float(mins_str)
    rate = riders / cycle_mins
    return round(rate, 2)

def resolve_safety_restraint_code(zone_code):
    prefix = zone_code.strip().upper()[:3]
    restraint_types = {
        "CST": "Over-the-Shoulder Harness",
        "WTR": "Lap Bar and Seatbelt",
        "DRP": "Hydraulic Shoulder Vest",
        "WHL": "Manual Safety Bar"
    }
    return restraint_types[prefix]

def main():
    print("==== Running validate_height_and_fastpass ====")
    r_input = input("Enter rider spec (Height:FastPass, e.g. 140:YES): ")
    print(validate_height_and_fastpass(r_input))

    print("\n==== Running compute_dispatch_throughput ====")
    t_input = input("Enter riders/mins (e.g. 48/2.5): ")
    print("Throughput (riders/min):", compute_dispatch_throughput(t_input))

    print("\n==== Running resolve_safety_restraint_code ====")
    z_input = input("Enter ride zone code (e.g. CST_01, WTR_A): ")
    print("Restraint:", resolve_safety_restraint_code(z_input))

if __name__ == "__main__":
    main()
