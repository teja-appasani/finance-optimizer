from pulp import LpProblem, LpMaximize, LpVariable, LpStatus, value, PULP_CBC_CMD

def run_budget(income, min_rent, min_food, min_transport, min_utilities, savings_pct):

    prob = LpProblem("budget_allocation", LpMaximize)

    rent          = LpVariable("rent",          lowBound=min_rent)
    food          = LpVariable("food",          lowBound=min_food)
    transport     = LpVariable("transport",     lowBound=min_transport)
    utilities     = LpVariable("utilities",     lowBound=min_utilities)
    entertainment = LpVariable("entertainment", lowBound=0)
    savings       = LpVariable("savings",       lowBound=0)

    disposable = income - min_rent - min_food - min_transport - min_utilities

    prob += entertainment

    # named constraints — naming them is what lets us read shadow prices back out
    prob += rent + food + transport + utilities + entertainment + savings == income,  "total_spending"
    prob += savings == (savings_pct / 100) * disposable,                             "savings_rate"
    prob += entertainment <= disposable - savings,                                   "entertainment_cap"
    prob += rent      >= min_rent,                                                   "min_rent"
    prob += food      >= min_food,                                                   "min_food"
    prob += transport >= min_transport,                                              "min_transport"
    prob += utilities >= min_utilities,                                              "min_utilities"

    prob.solve(PULP_CBC_CMD(msg=0))

    # shadow prices — only meaningful when status is Optimal
    # positive shadow price = relaxing this constraint improves the objective
    # zero shadow price = this constraint isn't binding (relaxing it wouldn't help)
    shadow_prices = {}
    if LpStatus[prob.status] == "Optimal":
        for name, constraint in prob.constraints.items():
            shadow_prices[name] = round(constraint.pi, 4) if constraint.pi is not None else 0.0

    entertainment_val = round(value(entertainment), 2)
    savings_val       = round(value(savings),       2)

    return {
        "status":            LpStatus[prob.status],
        "income":            round(income,           2),
        "rent":              round(value(rent),      2),
        "food":              round(value(food),      2),
        "transport":         round(value(transport), 2),
        "utilities":         round(value(utilities), 2),
        "disposable":        round(disposable,       2),
        "savings":           savings_val,
        "savings_pct":       round((savings_val       / income) * 100, 1),
        "entertainment":     entertainment_val,
        "entertainment_pct": round((entertainment_val / income) * 100, 1),
        "shadow_prices":     shadow_prices,
    }


if __name__ == "__main__":
    result = run_budget(
        income=5000,
        min_rent=1200,
        min_food=400,
        min_transport=200,
        min_utilities=150,
        savings_pct=30
    )
    for key, val in result.items():
        if key != "shadow_prices":
            print(f"{key:>20}: {val}")

    print("\nShadow prices:")
    for constraint, price in result["shadow_prices"].items():
        print(f"{constraint:>20}: {price}")