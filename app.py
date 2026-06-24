import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from models.budget  import run_budget
from models.savings import run_savings
from models.grocery import run_grocery, FOODS

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Personal Finance Optimizer",
    page_icon="💰",
    layout="wide"
)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("💰 Personal Finance Optimizer")
st.caption("Built with Python · PuLP · Streamlit · IE Portfolio Project")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_dashboard, tab_budget, tab_savings, tab_grocery = st.tabs([
    "📈 Dashboard", "📊 Budget", "🎯 Savings Goals", "🛒 Grocery"
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
with tab_dashboard:
    st.header("Your Financial Overview")
    st.caption("Run each model first — results will appear here automatically")

    budget_result  = st.session_state.get("budget_result",  None)
    savings_result = st.session_state.get("savings_result", None)
    grocery_result = st.session_state.get("grocery_result", None)

    any_result = budget_result or savings_result or grocery_result
    if not any_result:
        st.info("No results yet — head to the Budget, Savings, or Grocery tabs and run the optimizer.")

    # ── Budget summary ────────────────────────────────────────────────────────
    if budget_result:
        st.subheader("💵 Budget")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Monthly income",    f"${budget_result['income']:,.2f}")
        m2.metric("Monthly savings",   f"${budget_result['savings']:,.2f}",
                  f"{budget_result['savings_pct']}% of income")
        m3.metric("Entertainment",     f"${budget_result['entertainment']:,.2f}",
                  f"{budget_result['entertainment_pct']}% of income")
        m4.metric("Weekly food budget",f"${st.session_state.get('weekly_food', 0):,.2f}")

        # mini pie
        labels = ["Rent", "Food", "Transport", "Utilities", "Savings", "Entertainment"]
        values = [budget_result["rent"], budget_result["food"], budget_result["transport"],
                  budget_result["utilities"], budget_result["savings"], budget_result["entertainment"]]
        fig = px.pie(names=labels, values=values, title="Budget breakdown",
                     color_discrete_sequence=px.colors.qualitative.Pastel,
                     height=300)
        fig.update_layout(margin=dict(t=40, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

        # binding constraints callout
        sp = budget_result.get("shadow_prices", {})
        binding = {k: v for k, v in sp.items() if v != 0}
        if binding:
            st.markdown("**🔴 Binding constraints on your budget:**")
            for k, v in binding.items():
                label = k.replace("_", " ").title()
                st.warning(f"**{label}** — shadow price: {v:+.2f}")

        st.divider()

    # ── Savings summary ───────────────────────────────────────────────────────
    if savings_result:
        st.subheader("🎯 Savings Goals")
        m1, m2, m3 = st.columns(3)
        m1.metric("Monthly savings",  f"${savings_result['monthly_savings']:,.2f}")
        m2.metric("Total committed",  f"${savings_result['total_committed']:,.2f}")
        m3.metric("Unallocated",      f"${savings_result['unallocated']:,.2f}")

        on_track  = [a for a in savings_result["allocation"] if a["on_track"]]
        off_track = [a for a in savings_result["allocation"] if not a["on_track"]]

        if on_track:
            st.success(f"✅ {len(on_track)} goal(s) on track: {', '.join(a['name'] for a in on_track)}")
        if off_track:
            st.error(f"⚠️ {len(off_track)} goal(s) have shortfalls: {', '.join(a['name'] for a in off_track)}")

        # progress bars per goal
        for a in savings_result["allocation"]:
            pct = min((a["total_saved"] / a["target"]) * 100, 100) if a["target"] > 0 else 0
            st.markdown(f"**{a['name']}** — ${a['monthly']:,.2f}/month → "
                        f"${a['total_saved']:,.2f} / ${a['target']:,.2f} by month {a['months']}")
            st.progress(int(pct))

        st.divider()

    # ── Grocery summary ───────────────────────────────────────────────────────
    if grocery_result:
        st.subheader("🛒 Weekly Grocery Plan")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Weekly budget",    f"${grocery_result['weekly_budget']:,.2f}")
        m2.metric("Total cost",       f"${grocery_result['total_cost']:,.2f}",
                  f"${grocery_result['remaining']:,.2f} left")
        m3.metric("Daily calories",   f"{grocery_result['daily_calories']:,.0f} kcal")
        m4.metric("Daily protein",    f"{grocery_result['daily_protein']}g",
                  f"{grocery_result['protein_pct']}% of target")
        m5.metric("Food quality",     f"{grocery_result['avg_quality']}/10")

        st.divider()

    # ── Combined insight ──────────────────────────────────────────────────────
    if budget_result and savings_result and grocery_result:
        st.subheader("🔗 Full Picture")
        total_monthly = (
            budget_result["rent"] +
            budget_result["food"] +
            budget_result["transport"] +
            budget_result["utilities"] +
            budget_result["savings"] +
            budget_result["entertainment"]
        )
        grocery_monthly = grocery_result["total_cost"] * 4
        food_budget     = budget_result["food"]
        grocery_vs_food = grocery_monthly - food_budget

        c1, c2, c3 = st.columns(3)
        c1.metric("Monthly income",        f"${budget_result['income']:,.2f}")
        c2.metric("Estimated grocery cost",f"${grocery_monthly:,.2f}/month",
                  f"${grocery_vs_food:+,.2f} vs food budget")
        c3.metric("Goals on track",
                  f"{len([a for a in savings_result['allocation'] if a['on_track']])} / "
                  f"{len(savings_result['allocation'])}")

        if grocery_vs_food > 0:
            st.warning(f"Your grocery plan costs **${grocery_vs_food:.2f}/month more** than your "
                       f"food budget. Consider increasing your food minimum in the Budget tab.")
        else:
            st.success(f"Your grocery plan fits comfortably within your food budget "
                       f"(${abs(grocery_vs_food):.2f} to spare monthly).")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — BUDGET
# ══════════════════════════════════════════════════════════════════════════════
with tab_budget:
    st.header("Monthly Budget Allocation")
    st.caption("Maximize entertainment while locking in your savings rate")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Income")
        income      = st.number_input("Monthly income ($)",           min_value=0.0,   value=350.0,  step=50.0)
        savings_pct = st.slider("Savings % of disposable income",     min_value=0,     max_value=100, value=60, step=5)

    with col2:
        st.subheader("Monthly minimums")
        min_rent      = st.number_input("Rent ($)",      min_value=0.0, value=0.0,   step=50.0)
        min_food      = st.number_input("Food ($)",      min_value=0.0, value=200.0, step=10.0)
        min_transport = st.number_input("Transport ($)", min_value=0.0, value=20.0,  step=10.0)
        min_utilities = st.number_input("Utilities ($)", min_value=0.0, value=0.0,   step=10.0)

    if st.button("Run Budget Optimizer", type="primary"):
        fixed = min_rent + min_food + min_transport + min_utilities
        if fixed >= income:
            st.error("Your fixed expenses exceed your income. Adjust your minimums.")
        else:
            result = run_budget(income, min_rent, min_food, min_transport, min_utilities, savings_pct)

            if result["status"] != "Optimal":
                st.warning(f"Solver status: {result['status']}. Try adjusting your inputs.")
            else:
                st.session_state["budget_result"]  = result
                st.session_state["monthly_savings"] = result["savings"]
                st.session_state["weekly_food"]     = round(result["food"] / 4, 2)
                st.success("Optimal solution found!")

                # metrics
                m1, m2, m3, m4, m5, m6 = st.columns(6)
                m1.metric("Rent",          f"${result['rent']:,.2f}")
                m2.metric("Food",          f"${result['food']:,.2f}")
                m3.metric("Transport",     f"${result['transport']:,.2f}")
                m4.metric("Utilities",     f"${result['utilities']:,.2f}")
                m5.metric("Savings",       f"${result['savings']:,.2f}",
                          f"{result['savings_pct']}% of income")
                m6.metric("Entertainment", f"${result['entertainment']:,.2f}",
                          f"{result['entertainment_pct']}% of income")

                # pie chart
                labels = ["Rent", "Food", "Transport", "Utilities", "Savings", "Entertainment"]
                values = [result["rent"], result["food"], result["transport"],
                          result["utilities"], result["savings"], result["entertainment"]]
                fig = px.pie(names=labels, values=values, title="Budget breakdown",
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig, use_container_width=True)

                # pass-through info
                st.markdown(f"💡 Passing **${result['savings']:,.2f}/month** to Savings tab "
                            f"and **${st.session_state['weekly_food']:,.2f}/week** to Grocery tab")
                # ── Sensitivity analysis — tradeoff explorer ──────────────────
                st.subheader("Sensitivity Analysis")
                st.caption("How does changing your savings rate affect your entertainment budget?")

                disposable = income - min_rent - min_food - min_transport - min_utilities

                # build tradeoff data across all savings rates 0-100%
                rates       = list(range(0, 101, 5))
                savings_vals = [round(disposable * r / 100, 2) for r in rates]
                ent_vals     = [round(disposable - s, 2) for s in savings_vals]

                fig_tradeoff = go.Figure()
                fig_tradeoff.add_trace(go.Scatter(
                    x=rates, y=ent_vals,
                    name="Entertainment",
                    mode="lines+markers",
                    line=dict(color="#534AB7", width=2),
                    marker=dict(size=4),
                    fill="tozeroy",
                    fillcolor="rgba(83,74,183,0.08)",
                ))
                fig_tradeoff.add_trace(go.Scatter(
                    x=rates, y=savings_vals,
                    name="Savings",
                    mode="lines+markers",
                    line=dict(color="#1D9E75", width=2),
                    marker=dict(size=4),
                    fill="tozeroy",
                    fillcolor="rgba(29,158,117,0.06)",
                ))

                # vertical line at current savings rate
                fig_tradeoff.add_vline(
                    x=savings_pct,
                    line_dash="dash",
                    line_color="gray",
                    annotation_text=f"Your rate: {savings_pct}%",
                    annotation_position="top right"
                )

                fig_tradeoff.update_layout(
                    xaxis_title="Savings rate (%)",
                    yaxis_title="Dollars ($)",
                    height=300,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                    margin=dict(t=40, b=40, l=40, r=20),
                    hovermode="x unified",
                )
                st.plotly_chart(fig_tradeoff, use_container_width=True)

                # plain-language insight
                cost_per_10 = round(disposable * 0.10, 2)
                next_rate   = min(savings_pct + 10, 100)
                extra_saved = round(disposable * (next_rate - savings_pct) / 100, 2)
                st.markdown(
                    f"At **{savings_pct}% savings**: every 10% more you save costs you "
                    f"**${cost_per_10:.2f}** of entertainment. "
                    f"Going to **{next_rate}%** would save an extra **${extra_saved:.2f}/month**."
                )

                # binding constraint callout — simplified to one useful line
                if result["entertainment"] == 0:
                    st.warning("Your savings rate is consuming all disposable income — nothing left for entertainment.")
                elif result["entertainment"] < 20:
                    st.warning(f"Only ${result['entertainment']:.2f} left for entertainment — consider lowering your savings rate slightly.")
                else:
                    st.success(f"${result['entertainment']:.2f} available for entertainment this month.")

               

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — SAVINGS GOALS
# ══════════════════════════════════════════════════════════════════════════════
with tab_savings:
    st.header("Savings Goal Planner")
    st.caption("Allocate your monthly savings across custom goals by deadline")

    monthly_savings = st.session_state.get("monthly_savings", 0.0)
    if monthly_savings > 0:
        st.success(f"Using **${monthly_savings:,.2f}/month** from your budget plan")
    else:
        st.warning("Run the Budget tab first, or enter a monthly savings amount manually")
        monthly_savings = st.number_input("Monthly savings ($)", min_value=0.0, value=78.0, step=10.0)

    st.subheader("Your goals")
    st.caption("Add as many goals as you like")

    if "goals" not in st.session_state:
        st.session_state["goals"] = [{"name": "", "target": 0.0, "months": 1}]

    for i, goal in enumerate(st.session_state["goals"]):
        c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
        with c1:
            st.session_state["goals"][i]["name"]   = st.text_input("Goal name",  value=goal["name"],   key=f"gname_{i}")
        with c2:
            st.session_state["goals"][i]["target"] = st.number_input("Target ($)", value=goal["target"], key=f"gtarget_{i}", min_value=0.0, step=50.0)
        with c3:
            st.session_state["goals"][i]["months"] = st.number_input("Months",    value=goal["months"], key=f"gmonths_{i}", min_value=1, step=1)
        with c4:
            st.write("")
            st.write("")
            if st.button("✕", key=f"gdel_{i}") and len(st.session_state["goals"]) > 1:
                st.session_state["goals"].pop(i)
                st.rerun()

    if st.button("＋ Add goal"):
        st.session_state["goals"].append({"name": "", "target": 0.0, "months": 1})
        st.rerun()

    if st.button("Run Savings Optimizer", type="primary"):
        goals = [g for g in st.session_state["goals"] if g["name"].strip() and g["target"] > 0]
        if not goals:
            st.error("Add at least one goal with a name and target amount.")
        else:
            result = run_savings(monthly_savings, goals)

            if result["status"] != "Optimal":
                st.warning(f"Solver status: {result['status']}. Try adjusting your inputs.")
            else:
                st.session_state["savings_result"] = result
                st.success("Optimal solution found!")

                m1, m2, m3 = st.columns(3)
                m1.metric("Monthly savings",  f"${result['monthly_savings']:,.2f}")
                m2.metric("Total committed",  f"${result['total_committed']:,.2f}")
                m3.metric("Unallocated",      f"${result['unallocated']:,.2f}")

                st.subheader("Goal breakdown")
                for a in result["allocation"]:
                    status_icon = "✅" if a["on_track"] else "⚠️"
                    with st.expander(f"{status_icon} {a['name']} — ${a['target']:,.2f} in {a['months']} months"):
                        g1, g2, g3, g4 = st.columns(4)
                        g1.metric("Monthly contribution",   f"${a['monthly']:,.2f}")
                        g2.metric("Total saved by deadline",f"${a['total_saved']:,.2f}")
                        g3.metric("Target",                 f"${a['target']:,.2f}")
                        g4.metric("Shortfall",              f"${a['shortfall']:,.2f}")
                        if not a["on_track"]:
                            st.warning(f"You'll be ${a['shortfall']:,.2f} short. "
                                       f"Try extending the deadline or reducing the target.")

                # horizontal progress chart
                goal_names = [a["name"] for a in result["allocation"]]
                saved_pct  = [round((a["total_saved"] / a["target"]) * 100, 1)
                              if a["target"] > 0 else 0 for a in result["allocation"]]
                saved_amt  = [a["total_saved"] for a in result["allocation"]]
                target_amt = [a["target"]      for a in result["allocation"]]
                bar_colors = ["mediumseagreen" if a["on_track"] else "salmon"
                              for a in result["allocation"]]

                fig = go.Figure(go.Bar(
                    x=saved_pct, y=goal_names, orientation="h",
                    marker_color=bar_colors,
                    text=[f"${s:,.0f} / ${t:,.0f}" for s, t in zip(saved_amt, target_amt)],
                    textposition="outside",
                ))
                fig.update_layout(
                    title="Savings progress by goal",
                    xaxis_title="% of target saved by deadline",
                    xaxis_range=[0, max(110, max(saved_pct) + 15 if saved_pct else 110)],
                    yaxis=dict(autorange="reversed"),
                    height=120 + len(goal_names) * 60,
                    showlegend=False,
                )
                fig.add_vline(x=100, line_dash="dash", line_color="gray",
                              annotation_text="100% target", annotation_position="top")
                st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — GROCERY (reframed as supply chain)
# ══════════════════════════════════════════════════════════════════════════════
with tab_grocery:
    st.header("Weekly Grocery Optimizer")
    st.caption("""
        **Supply chain framing:** you are a procurement manager with a fixed weekly budget.
        You source from a set of suppliers (food items), each with a known unit cost and
        nutritional yield. Your goal is to meet weekly demand targets (protein, carbs, calories)
        at minimum quality-adjusted cost, subject to supplier capacity constraints (max quantities)
        and mandatory supplier contracts (min quantity floors). This is the classic diet problem —
        one of the original LP formulations from the 1940s, still used in food manufacturing,
        military ration planning, and hospital nutrition today.
    """)

    weekly_food = st.session_state.get("weekly_food", 0.0)
    if weekly_food > 0:
        st.success(f"Using **${weekly_food:,.2f}/week** from your budget plan")
    else:
        st.warning("Run the Budget tab first, or enter a weekly food budget manually")
        weekly_food = st.number_input("Weekly food budget ($)", min_value=0.0, value=50.0, step=5.0)

    col1, col2 = st.columns(2)
    with col1:
        protein_target = st.number_input("Weekly protein target (g)", min_value=0, value=850, step=10)
    with col2:
        carb_target = st.number_input("Weekly carb target (g)", min_value=0, value=2100, step=10)

    with st.expander("📋 Supplier catalogue — 29 food items with Walmart pricing"):
        st.caption("In supply chain terms: each row is a supplier. Cost = unit price. "
                   "Min qty = contracted minimum. Max qty = supplier capacity.")
        st.table([
            {
                "Supplier (food)":  f["name"],
                "Unit":             f["package_unit"],
                "Unit cost":        f"${f['package_cost']:.2f}",
                "Protein yield":    f"{f['protein']}g",
                "Carb yield":       f"{f['carbs']}g",
                "Min order":        f.get("min_qty", 0),
                "Capacity":         f["max_qty"],
                "Quality score":    f"{f['quality_score']}/10",
            }
            for f in FOODS
        ])

    if st.button("Run Grocery Optimizer", type="primary"):
        result = run_grocery(weekly_food, protein_target=protein_target, carb_target=carb_target)
        if result["status"] != "Optimal":
            st.warning(
                f"Solver status: {result['status']}. Your budget of ${weekly_food:,.2f}/week "
                f"isn't enough to hit {protein_target}g protein and {carb_target}g carbs. "
                f"Try increasing your budget or lowering your targets."
            )
        else:
            st.session_state["grocery_result"] = result

    # ── Results (always shown from session state so other buttons don't wipe them) ──
    result = st.session_state.get("grocery_result")
    if result:
        st.success("Optimal procurement plan found!")

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Weekly budget",    f"${result['weekly_budget']:,.2f}")
        m2.metric("Total cost",       f"${result['total_cost']:,.2f}",
                  f"${result['remaining']:,.2f} left")
        m3.metric("Daily calories",   f"{result['daily_calories']:,.0f} kcal",
                  f"{result['cal_pct']}% of target")
        m4.metric("Daily protein",    f"{result['daily_protein']}g",
                  f"{result['protein_pct']}% of target")
        m5.metric("Avg food quality", f"{result['avg_quality']}/10")

        st.subheader("Procurement order")
        st.caption("Items sorted by cost descending — biggest spend first")
        sorted_list = sorted(result["shopping_list"], key=lambda x: x["cost"], reverse=True)
        for item in sorted_list:
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 2])
            c1.write(f"**{item['name']}**")
            c2.write(f"{item['buy_qty']} × {item['package_unit']}")
            c3.write(f"${item['cost']:,.2f}")
            c4.write(f"{item['protein']}g protein")
            c5.write(f"{item['carbs']}g carbs")

        fig_cost = px.bar(
            x=[i["name"] for i in sorted_list],
            y=[i["cost"] for i in sorted_list],
            labels={"x": "Food item", "y": "Cost ($)"},
            title="Procurement cost by supplier",
            color_discrete_sequence=["mediumseagreen"]
        )
        st.plotly_chart(fig_cost, use_container_width=True)

        fig_nutrition = go.Figure()
        fig_nutrition.add_trace(go.Bar(
            name="Protein (g)",
            x=[i["name"] for i in sorted_list],
            y=[i["protein"] for i in sorted_list],
            marker_color="#534AB7"
        ))
        fig_nutrition.add_trace(go.Bar(
            name="Carbs (g)",
            x=[i["name"] for i in sorted_list],
            y=[i["carbs"] for i in sorted_list],
            marker_color="#9FE1CB"
        ))
        fig_nutrition.update_layout(
            barmode="group",
            title="Nutritional yield by supplier",
            xaxis_title="Food item",
            yaxis_title="Grams"
        )
        st.plotly_chart(fig_nutrition, use_container_width=True)

        st.info("""
            **Supply chain insight:** the optimizer selected suppliers that maximize
            nutritional yield per dollar (quality-adjusted cost minimization), subject to
            contracted minimums and capacity constraints. Foods not selected were either
            dominated by cheaper alternatives or fell below the minimum viable order
            threshold (50% of package size). This mirrors real procurement logic in food
            manufacturing and hospital nutrition planning.
        """)

