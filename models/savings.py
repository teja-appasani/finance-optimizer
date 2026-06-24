from pulp import LpProblem, LpMinimize, LpVariable, LpStatus, value, PULP_CBC_CMD

def run_savings(monthly_savings, goals):
    """
    monthly_savings : float         — from budget model's savings output
    goals           : list of dicts — each with keys: name, target, months
                      e.g. [{"name": "Vacation", "target": 2000.0, "months": 6}]
    """

    prob = LpProblem("savings_planner", LpMinimize)

    # one decision variable per goal — monthly contribution toward it
    contributions = {
        g["name"]: LpVariable(f"c_{g['name']}", lowBound=0)
        for g in goals
    }

    # objective — minimize total unmet amount across all goals
    shortfalls = {
        g["name"]: LpVariable(f"s_{g['name']}", lowBound=0)
        for g in goals
    }
    prob += sum(shortfalls[g["name"]] for g in goals)

    # constraints
    prob += sum(contributions[g["name"]] for g in goals) <= monthly_savings      # can't contribute more than savings

    for g in goals:
        # total saved by deadline = monthly contribution × months available
        prob += contributions[g["name"]] * g["months"] + shortfalls[g["name"]] >= g["target"]  # meet target or record shortfall
        prob += contributions[g["name"]] <= monthly_savings                                     # single goal can't exceed total savings

    prob.solve(PULP_CBC_CMD(msg=0))

    # build per-goal results
    allocation = []
    for g in goals:
        monthly    = round(value(contributions[g["name"]]), 2)
        shortfall  = round(value(shortfalls[g["name"]]),    2)
        total_saved = round(monthly * g["months"],          2)
        on_track   = shortfall == 0

        allocation.append({
            "name":         g["name"],
            "target":       g["target"],
            "months":       g["months"],
            "monthly":      monthly,
            "total_saved":  total_saved,
            "shortfall":    shortfall,
            "on_track":     on_track,
        })

    total_committed = round(sum(a["monthly"] for a in allocation), 2)
    unallocated     = round(monthly_savings - total_committed,     2)

    return {
        "status":           LpStatus[prob.status],
        "monthly_savings":  monthly_savings,
        "total_committed":  total_committed,
        "unallocated":      unallocated,
        "allocation":       allocation,
    }

    print(f"\n{'status':>18}: {result['status']}")
    print(f"{'monthly savings':>18}: ${result['monthly_savings']}")
    print(f"{'total committed':>18}: ${result['total_committed']}")
    print(f"{'unallocated':>18}: ${result['unallocated']}")
    print(f"\n{'goal':<18} {'target':>8} {'months':>7} {'monthly':>9} {'saved':>8} {'shortfall':>10} {'on track':>9}")
    print("-" * 75)
    for a in result["allocation"]:
        flag = "✓" if a["on_track"] else "✗"
        print(f"{a['name']:<18} ${a['target']:>7} {a['months']:>7} ${a['monthly']:>8} ${a['total_saved']:>7} ${a['shortfall']:>9} {flag:>9}")