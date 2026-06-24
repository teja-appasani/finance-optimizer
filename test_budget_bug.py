from models.grocery import FOODS
from pulp import LpProblem, LpMinimize, LpVariable, PULP_CBC_CMD, value

prob = LpProblem("test", LpMinimize)
quantities = {
    f["name"]: LpVariable(f"q_{f['name']}", lowBound=f.get("min_qty", 0), upBound=f["max_qty"])
    for f in FOODS
}

prob += sum(f["cost"] / f["quality_score"] * quantities[f["name"]] for f in FOODS)
prob += sum(f["cost"]    * quantities[f["name"]] for f in FOODS) <= 25
prob += sum(f["protein"] * quantities[f["name"]] for f in FOODS) >= 850
prob += sum(f["carbs"]   * quantities[f["name"]] for f in FOODS) >= 2100

prob.solve(PULP_CBC_CMD(msg=0))

raw_cost = sum(f["cost"] * value(quantities[f["name"]]) for f in FOODS)
print("raw LP cost (fractional units):", round(raw_cost, 2))

print("\nFractional quantities the solver actually chose:")
for f in FOODS:
    qty = value(quantities[f["name"]])
    if qty and qty > 0.001:
        print(f"  {f['name']:<18} {qty:.3f} {f['fine_unit']}")