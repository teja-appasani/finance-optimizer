import math
import random
from pulp import LpProblem, LpMaximize, LpVariable, LpBinary, LpStatus, value, PULP_CBC_CMD

# ── Hardcoded food database (Walmart prices, June 2026) ────────────────────────
# quality_score (1-10): based on micronutrient density — vitamins, minerals,
# omega-3s, fiber, antioxidants. Higher = more nutritionally complete per unit.
FOODS = [
    # ── Proteins ──────────────────────────────────────────────────────────────
    {"name": "Chicken breast",   "fine_unit": "lb",    "cost": 3.16,  "cal": 490,  "protein": 102, "carbs": 0,   "quality_score": 9,  "min_qty": 3,  "max_qty": 6,
     "package_unit": "3lb pack",      "package_size": 3,    "package_cost": 9.47},
    {"name": "Ground beef 80/20","fine_unit": "lb",    "cost": 8.00,  "cal": 1152, "protein": 76,  "carbs": 0,   "quality_score": 8,  "min_qty": 0,  "max_qty": 3,
     "package_unit": "lb pack",       "package_size": 1,    "package_cost": 8.00},
    {"name": "Frozen salmon",    "fine_unit": "fillet","cost": 3.00,  "cal": 350,  "protein": 34,  "carbs": 0,   "quality_score": 10, "min_qty": 3,  "max_qty": 3,
     "package_unit": "3-fillet bag",  "package_size": 3,    "package_cost": 9.00},
    {"name": "Eggs",             "fine_unit": "egg",   "cost": 0.12,  "cal": 70,   "protein": 6,   "carbs": 0.5, "quality_score": 10, "min_qty": 0,  "max_qty": 24,
     "package_unit": "dozen",         "package_size": 12,   "package_cost": 1.47},
    # ── Dairy ─────────────────────────────────────────────────────────────────
    {"name": "Greek yogurt",     "fine_unit": "cup",   "cost": 0.88,  "cal": 130,  "protein": 23,  "carbs": 9,   "quality_score": 8,  "min_qty": 4,  "max_qty": 8,
     "package_unit": "32oz tub",      "package_size": 4,    "package_cost": 3.50},
    {"name": "Milk",             "fine_unit": "cup",   "cost": 0.25,  "cal": 150,  "protein": 8,   "carbs": 12,  "quality_score": 7,  "min_qty": 16, "max_qty": 16,
     "package_unit": "gallon",        "package_size": 16,   "package_cost": 4.00},
    {"name": "Cheddar cheese",   "fine_unit": "oz",    "cost": 0.25,  "cal": 113,  "protein": 7,   "carbs": 0.4, "quality_score": 6,  "min_qty": 0,  "max_qty": 8,
     "package_unit": "8oz block",     "package_size": 8,    "package_cost": 2.00},
    # ── Grains ────────────────────────────────────────────────────────────────
    {"name": "Instant ramen",    "fine_unit": "pack",  "cost": 0.70,  "cal": 380,  "protein": 8,   "carbs": 51,  "quality_score": 2,  "min_qty": 0,  "max_qty": 4,
     "package_unit": "pack",          "package_size": 1,    "package_cost": 0.70},
    {"name": "Pasta",            "fine_unit": "lb",    "cost": 1.30,  "cal": 1700, "protein": 57,  "carbs": 332, "quality_score": 6,  "min_qty": 0,  "max_qty": 3,
     "package_unit": "16oz box",      "package_size": 1,    "package_cost": 1.30},
    {"name": "Tortillas",        "fine_unit": "pack",  "cost": 2.00,  "cal": 1200, "protein": 32,  "carbs": 200, "quality_score": 2,  "min_qty": 0,  "max_qty": 2,
     "package_unit": "pack (10ct)",   "package_size": 1,    "package_cost": 2.00},
    {"name": "Bread",            "fine_unit": "slice", "cost": 0.20,  "cal": 80,   "protein": 3,   "carbs": 14,  "quality_score": 6,  "min_qty": 20, "max_qty": 60,
     "package_unit": "loaf (20ct)",   "package_size": 20,   "package_cost": 4.00},
    {"name": "Brown rice",       "fine_unit": "lb",    "cost": 0.52,  "cal": 1685, "protein": 35,  "carbs": 350, "quality_score": 7,  "min_qty": 1,  "max_qty": 6,
     "package_unit": "32oz bag",      "package_size": 2,    "package_cost": 1.67},
    {"name": "Oats",             "fine_unit": "lb",    "cost": 1.68,  "cal": 1700, "protein": 57,  "carbs": 306, "quality_score": 9,  "min_qty": 0,  "max_qty": 4,
     "package_unit": "42oz canister", "package_size": 2.6,  "package_cost": 4.38},
    # ── Vegetables ────────────────────────────────────────────────────────────
    {"name": "Potatoes",         "fine_unit": "lb",    "cost": 0.76,  "cal": 350,  "protein": 9,   "carbs": 79,  "quality_score": 7,  "min_qty": 0,  "max_qty": 5,
     "package_unit": "5lb bag",       "package_size": 5,    "package_cost": 3.80},
    {"name": "Spinach",          "fine_unit": "bag",   "cost": 3.00,  "cal": 35,   "protein": 4.3, "carbs": 5.5, "quality_score": 10, "min_qty": 0,  "max_qty": 3,
     "package_unit": "5oz bag",       "package_size": 1,    "package_cost": 3.00},
    {"name": "Broccoli",         "fine_unit": "bag",   "cost": 2.50,  "cal": 100,  "protein": 12,  "carbs": 16,  "quality_score": 10, "min_qty": 1,  "max_qty": 3,
     "package_unit": "12oz bag",      "package_size": 1,    "package_cost": 2.50},
    {"name": "Frozen mixed veg", "fine_unit": "bag",   "cost": 1.00,  "cal": 230,  "protein": 9,   "carbs": 47,  "quality_score": 9,  "min_qty": 1,  "max_qty": 3,
     "package_unit": "12oz bag",      "package_size": 1,    "package_cost": 1.00},
    {"name": "Bell peppers",     "fine_unit": "each",  "cost": 1.00,  "cal": 30,   "protein": 1,   "carbs": 7,   "quality_score": 9,  "min_qty": 0,  "max_qty": 5,
     "package_unit": "each",          "package_size": 1,    "package_cost": 1.00},
    {"name": "Lettuce",          "fine_unit": "head",  "cost": 2.00,  "cal": 25,   "protein": 2,   "carbs": 5,   "quality_score": 7,  "min_qty": 0,  "max_qty": 2,
     "package_unit": "head",          "package_size": 1,    "package_cost": 2.00},
    {"name": "Tomatoes",         "fine_unit": "each",  "cost": 1.20,  "cal": 22,   "protein": 1,   "carbs": 5,   "quality_score": 8,  "min_qty": 0,  "max_qty": 5,
     "package_unit": "each",          "package_size": 1,    "package_cost": 1.20},
    {"name": "Onions",           "fine_unit": "each",  "cost": 1.20,  "cal": 45,   "protein": 1,   "carbs": 11,  "quality_score": 6,  "min_qty": 0,  "max_qty": 3,
     "package_unit": "each",          "package_size": 1,    "package_cost": 1.20},
    {"name": "Carrots",          "fine_unit": "lb",    "cost": 1.13,  "cal": 175,  "protein": 4,   "carbs": 41,  "quality_score": 9,  "min_qty": 0,  "max_qty": 2,
     "package_unit": "2lb bag",       "package_size": 2,    "package_cost": 2.26},
    {"name": "Asparagus",        "fine_unit": "bunch", "cost": 3.00,  "cal": 135,  "protein": 9,   "carbs": 22,  "quality_score": 10, "min_qty": 0,  "max_qty": 2,
     "package_unit": "bunch",         "package_size": 1,    "package_cost": 3.00},
    # ── Fruits ────────────────────────────────────────────────────────────────
    {"name": "Bananas",          "fine_unit": "each",  "cost": 0.29,  "cal": 105,  "protein": 1.3, "carbs": 27,  "quality_score": 8,  "min_qty": 6,  "max_qty": 14,
     "package_unit": "bunch (6)",     "package_size": 6,    "package_cost": 1.74},
    {"name": "Apples",           "fine_unit": "each",  "cost": 0.67,  "cal": 95,   "protein": 0.5, "carbs": 25,  "quality_score": 8,  "min_qty": 0,  "max_qty": 12,
     "package_unit": "3lb bag (~6)",  "package_size": 6,    "package_cost": 4.00},
    {"name": "Oranges",          "fine_unit": "each",  "cost": 0.83,  "cal": 62,   "protein": 1.2, "carbs": 15,  "quality_score": 9,  "min_qty": 0,  "max_qty": 6,
     "package_unit": "3lb bag (~6)",  "package_size": 6,    "package_cost": 5.00},
    {"name": "Avocado",          "fine_unit": "each",  "cost": 1.00,  "cal": 234,  "protein": 3,   "carbs": 12,  "quality_score": 9,  "min_qty": 1,  "max_qty": 3,
     "package_unit": "each",          "package_size": 1,    "package_cost": 1.00},
    # ── Legumes ───────────────────────────────────────────────────────────────
    {"name": "Black beans",      "fine_unit": "can",   "cost": 1.00,  "cal": 350,  "protein": 22,  "carbs": 63,  "quality_score": 8,  "min_qty": 0,  "max_qty": 4,
     "package_unit": "15oz can",      "package_size": 1,    "package_cost": 1.00},
    {"name": "Chickpeas",        "fine_unit": "can",   "cost": 1.00,  "cal": 420,  "protein": 22,  "carbs": 70,  "quality_score": 8,  "min_qty": 0,  "max_qty": 4,
     "package_unit": "15oz can",      "package_size": 1,    "package_cost": 1.00},
    {"name": "Baked beans",      "fine_unit": "can",   "cost": 2.50,  "cal": 470,  "protein": 24,  "carbs": 92,  "quality_score": 7,  "min_qty": 0,  "max_qty": 3,
     "package_unit": "28oz can",      "package_size": 1,    "package_cost": 2.50},
]

PROTEIN_TARGET       = 850
PROTEIN_MAX          = 1050
CARB_TARGET          = 2100
VITAMIN_TARGET       = 120
CAL_MIN              = 14000
CAL_MAX              = 17500
RANDOM_NOISE_RANGE   = 0.25
SHORTFALL_PENALTY    = 5.0
SEMI_CONTINUOUS_FRACTION = 0.5

# ── Floor drop priority — lower number = dropped first when budget is tight ───
# salmon is priority 5 — dropped after brown rice (4) but before apples (6)
FLOOR_DROP_PRIORITY = {
    "Frozen salmon":    1,
    "Frozen mixed veg": 2,
    "Broccoli":         3,
    "Greek yogurt":     4,
    "Brown rice":       5,
    "Bananas":          6,
    "Avocado":          7,
    "Bread":            8,
    "Milk":             9,
    "Chicken breast":   10,  # last to drop — core protein
}


def relax_floors_for_budget(foods, weekly_budget):
    """
    If mandatory floor costs exceed weekly_budget, progressively zero out
    floors in priority order (lowest number = drop first) until floors fit.
    """
    def floor_cost(foods):
        return sum(
            math.ceil(f["min_qty"] / f["package_size"]) * f["package_cost"]
            for f in foods if f.get("min_qty", 0) > 0
        )

    # sort droppable floors by priority ascending
    droppable = sorted(
        [f for f in foods if f.get("min_qty", 0) > 0 and f["name"] in FLOOR_DROP_PRIORITY],
        key=lambda f: FLOOR_DROP_PRIORITY[f["name"]]
    )

    for f in droppable:
        if floor_cost(foods) <= weekly_budget:
            break
        for item in foods:
            if item["name"] == f["name"]:
                item["min_qty"] = 0
                break

    return foods


def run_grocery(weekly_budget, foods=FOODS, protein_target=PROTEIN_TARGET,
                carb_target=CARB_TARGET, vitamin_target=VITAMIN_TARGET):

    # step 1: copy global list so we never mutate it
    foods = [dict(f) for f in foods]

    # step 2: coin flips for probabilistic foods
    for f in foods:
        if f["name"] == "Ground beef 80/20":
            f["min_qty"] = 1 if random.random() < 0.33 else 0
        if f["name"] == "Baked beans":
            f["min_qty"] = 1 if random.random() < 0.50 else 0

    # step 3: relax floors if budget is too tight to cover them all
    foods = relax_floors_for_budget(foods, weekly_budget)

    prob = LpProblem("grocery_optimizer", LpMaximize)

    quantities = {}
    buy_switch  = {}

    for f in foods:
        has_floor = f.get("min_qty", 0) > 0
        quantities[f["name"]] = LpVariable(
            f"q_{f['name']}", lowBound=0, upBound=f["max_qty"]
        )
        if has_floor:
            prob += quantities[f["name"]] >= f["min_qty"]
        else:
            switch = LpVariable(f"buy_{f['name']}", cat=LpBinary)
            buy_switch[f["name"]] = switch
            half_package = SEMI_CONTINUOUS_FRACTION * f["package_size"]
            prob += quantities[f["name"]] <= f["max_qty"] * switch
            prob += quantities[f["name"]] >= half_package * switch

    protein_shortfall = LpVariable("protein_shortfall", lowBound=0)
    carb_shortfall    = LpVariable("carb_shortfall",    lowBound=0)
    cal_shortfall     = LpVariable("cal_shortfall",     lowBound=0)

    noise = {
        f["name"]: random.uniform(1 - RANDOM_NOISE_RANGE, 1 + RANDOM_NOISE_RANGE)
        for f in foods
    }

    prob += (
        sum(f["quality_score"] * noise[f["name"]] * quantities[f["name"]] for f in foods)
        - 0.1 * sum((f["cost"] / f["quality_score"]) * quantities[f["name"]] for f in foods)
        - SHORTFALL_PENALTY * protein_shortfall
        - SHORTFALL_PENALTY * carb_shortfall
        - SHORTFALL_PENALTY * cal_shortfall
    )

    # soft constraints
    prob += sum(f["protein"] * quantities[f["name"]] for f in foods) + protein_shortfall >= protein_target
    prob += sum(f["carbs"]   * quantities[f["name"]] for f in foods) + carb_shortfall    >= carb_target
    prob += sum(f["cal"]     * quantities[f["name"]] for f in foods) + cal_shortfall     >= CAL_MIN

    # hard constraints
    prob += sum(f["protein"]       * quantities[f["name"]] for f in foods) <= PROTEIN_MAX
    prob += sum(f["quality_score"] * quantities[f["name"]] for f in foods) >= vitamin_target
    prob += sum(f["cal"]           * quantities[f["name"]] for f in foods) <= CAL_MAX
    prob += sum(f["cost"]          * quantities[f["name"]] for f in foods) <= weekly_budget

    prob.solve(PULP_CBC_CMD(msg=0))
    status = LpStatus[prob.status]

    if status != "Optimal":
        return {
            "status": status, "weekly_budget": weekly_budget,
            "total_cost": 0, "remaining": weekly_budget,
            "shopping_list": [], "total_calories": 0,
            "total_protein": 0, "total_carbs": 0, "total_vitamin": 0,
            "avg_quality": 0, "protein_target": protein_target,
            "carb_target": carb_target, "vitamin_target": vitamin_target,
            "protein_pct": 0, "carb_pct": 0, "cal_pct": 0,
            "daily_calories": 0, "daily_protein": 0, "daily_carbs": 0,
        }

    # ── Build initial shopping list ───────────────────────────────────────────
    shopping_list = []
    food_lookup   = {f["name"]: f for f in foods}

    for f in foods:
        fine_qty = value(quantities[f["name"]])
        if fine_qty and fine_qty > 0.001:
            packages_needed = math.ceil(fine_qty / f["package_size"])
            shopping_list.append({
                "name":         f["name"],
                "packages":     packages_needed,
                "package_unit": f["package_unit"],
                "package_cost": f["package_cost"],
                "package_size": f["package_size"],
                "quality_score":f["quality_score"],
                "has_floor":    f.get("min_qty", 0) > 0,
            })

    # ── Post-solve budget enforcement ─────────────────────────────────────────
    def total_package_cost(lst):
        return sum(i["packages"] * i["package_cost"] for i in lst)

    for _ in range(len(shopping_list) * 5):
        if total_package_cost(shopping_list) <= weekly_budget:
            break
        optional = [i for i in shopping_list if not i["has_floor"]]
        if not optional:
            break
        optional.sort(key=lambda x: x["package_cost"], reverse=True)
        priciest = optional[0]
        priciest["packages"] -= 1
        if priciest["packages"] <= 0:
            shopping_list.remove(priciest)

    # ── Build final output ────────────────────────────────────────────────────
    final_list = []
    total_cost = total_calories = total_protein = total_carbs = 0.0
    total_vitamin = total_quality_units = total_qty_for_avg = 0.0

    for item in shopping_list:
        if item["packages"] <= 0:
            continue
        f = food_lookup[item["name"]]
        actual_fine_qty = item["packages"] * item["package_size"]
        cost     = round(item["packages"] * item["package_cost"], 2)
        calories = round(actual_fine_qty * f["cal"],          0)
        protein  = round(actual_fine_qty * f["protein"],      1)
        carbs    = round(actual_fine_qty * f["carbs"],        1)
        vitamin  = round(actual_fine_qty * f["quality_score"],1)

        final_list.append({
            "name":         item["name"],
            "buy_qty":      item["packages"],
            "package_unit": item["package_unit"],
            "cost":         cost,
            "calories":     calories,
            "protein":      protein,
            "carbs":        carbs,
            "vitamin":      vitamin,
            "quality_score":item["quality_score"],
        })
        total_cost          += cost
        total_calories      += calories
        total_protein       += protein
        total_carbs         += carbs
        total_vitamin       += vitamin
        total_quality_units += actual_fine_qty * item["quality_score"]
        total_qty_for_avg   += actual_fine_qty

    avg_quality = round(total_quality_units / total_qty_for_avg, 1) if total_qty_for_avg else 0
    protein_pct = round((total_protein  / protein_target) * 100, 1) if protein_target else 0
    carb_pct    = round((total_carbs    / carb_target)    * 100, 1) if carb_target    else 0
    cal_pct     = round((total_calories / CAL_MIN)        * 100, 1) if CAL_MIN        else 0

    return {
        "status":          status,
        "weekly_budget":   weekly_budget,
        "total_cost":      round(total_cost, 2),
        "remaining":       round(weekly_budget - total_cost, 2),
        "shopping_list":   final_list,
        "total_calories":  total_calories,
        "total_protein":   total_protein,
        "total_carbs":     total_carbs,
        "total_vitamin":   total_vitamin,
        "avg_quality":     avg_quality,
        "protein_target":  protein_target,
        "carb_target":     carb_target,
        "vitamin_target":  vitamin_target,
        "protein_pct":     protein_pct,
        "carb_pct":        carb_pct,
        "cal_pct":         cal_pct,
        "daily_calories":  round(total_calories / 7, 0),
        "daily_protein":   round(total_protein  / 7, 1),
        "daily_carbs":     round(total_carbs    / 7, 1),
    }


if __name__ == "__main__":
    for budget in [30, 40, 50, 60, 70]:
        result = run_grocery(weekly_budget=budget)
        print(f"\n{'='*65}\n${budget}/week — status: {result['status']}")
        if result["status"] != "Optimal":
            continue
        print(f"  total cost:  ${result['total_cost']}  |  remaining: ${result['remaining']}")
        print(f"  protein:     {result['total_protein']}g / {result['protein_target']}g  ({result['protein_pct']}%)")
        print(f"  carbs:       {result['total_carbs']}g / {result['carb_target']}g  ({result['carb_pct']}%)")
        print(f"  calories:    {result['total_calories']} / {CAL_MIN}  ({result['cal_pct']}%)")
        print(f"  avg quality: {result['avg_quality']}/10")
        print(f"\n  {'item':<22} {'buy':>4}  {'unit':<18} {'cost':>7} {'quality':>8}")
        print("  " + "-" * 68)
        for i in result["shopping_list"]:
            print(f"  {i['name']:<22} {i['buy_qty']:>4}  {i['package_unit']:<18}"
                  f" ${i['cost']:>6} {i['quality_score']:>7}/10")