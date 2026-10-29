def process_ride_admissions(groups, express_pass_fee):
    if not isinstance(groups, list) or express_pass_fee < 0:
        raise ValueError("Invalid groups list or pass fee")

    total_revenue = 0.0
    rejected_patrons = 0

    for group in groups:
        if not group.get("is_open", False):
            continue

        ride_type = group.get("ride_type", "family")
        patrons = group.get("patrons", [])

        if ride_type == "roller_coaster":
            base_ticket = 25.0
        elif ride_type == "water_ride":
            base_ticket = 18.0
        elif ride_type == "family":
            base_ticket = 10.0
        else:
            rejected_patrons += 1
            continue

        group_total = 0.0

        for patron in patrons:
            height_cm = patron.get("height_cm", 0)
            has_health_warning = patron.get("health_warning", False)
            is_child = patron.get("is_child", False)

            if height_cm <= 0:
                rejected_patrons += 1
                continue

            if has_health_warning:
                rejected_patrons += 1
                if ride_type == "roller_coaster":
                    group_total = 0.0
                    break
                group_total += 0.0
            elif height_cm < 120:
                rejected_patrons += 1
                continue
            elif is_child:
                group_total += base_ticket * 0.60
            else:
                group_total += base_ticket

        if group.get("has_fast_lane", False):
            group_total += express_pass_fee

        total_revenue += group_total

    if rejected_patrons > 4:
        return {"total_revenue": round(total_revenue, 2), "status": "SAFETY_AUDIT"}
    if total_revenue == 0.0:
        return {"total_revenue": 0.0, "status": "ZERO_ADMISSIONS"}
    return {"total_revenue": round(total_revenue, 2), "status": "COMPLETED"}


def inspect_safety_restraints(restraint_streams):
    if not restraint_streams:
        return "NO_DATA"

    for sensor_readings in restraint_streams:
        unlatched_streak = 0
        for sensor_val in sensor_readings:
            if sensor_val == 0:
                unlatched_streak += 1
                if unlatched_streak >= 2:
                    return "EMERGENCY_LOCK"
            else:
                unlatched_streak = 0
    return "SAFE"