# Personal Finance Optimizer

A full-stack optimization web app built with Python, PuLP, and Streamlit that applies 
linear and mixed-integer programming to three real-world personal finance problems.

**Live demo:** [finance-optimizer.streamlit.app](https://your-app.streamlit.app)

---

## What it does

Most personal finance tools just track spending. This one optimizes it — using the 
same mathematical techniques applied in supply chain management, hospital nutrition 
planning, and production scheduling, applied to a college student's budget.

---

## Models

### 1. Budget allocation
Maximizes entertainment budget while locking in a user-defined savings rate, given 
fixed monthly expenses. Includes an interactive sensitivity analysis chart showing 
the full savings vs. entertainment tradeoff curve across all possible savings rates.

**LP formulation:** maximize entertainment subject to total spending = income, 
savings = savings_pct × disposable income, each expense category ≥ its minimum.

### 2. Savings goal planner
Allocates monthly savings across multiple custom goals by deadline, minimizing 
total shortfall when the budget is too tight to fully fund every goal simultaneously.

**LP formulation:** minimize Σ shortfalls subject to monthly contributions ≤ 
savings budget, each goal funded by its deadline or shortfall absorbs the gap.

### 3. Weekly grocery optimizer (MILP)
Modeled as a supply chain procurement problem — selects the highest-quality weekly 
grocery plan within a budget, treating each food item as a supplier with a unit cost, 
nutritional yield, capacity constraint, and minimum order quantity.

**MILP formulation:** maximize weighted nutrition quality score subject to protein, 
carbohydrate, calorie, and vitamin targets; budget ceiling; supplier capacity caps; 
and mandatory contract floors. Semi-continuous binary variables enforce realistic 
minimum order quantities — each food is either skipped entirely or purchased at 
at least half a package, eliminating fractional purchases that don't reflect 
real-world shopping.

---

## IE concepts demonstrated

- Linear programming (LP) and mixed-integer linear programming (MILP)
- Soft constraints with shortfall variables for graceful infeasibility handling
- Sensitivity analysis and shadow pricing
- Semi-continuous variable formulation (binary on/off switches)
- Supply chain procurement reframing of the classic diet problem
- Systematic constraint isolation for infeasibility diagnosis
- Probabilistic floor relaxation for adaptive budget management
- Multi-model pipeline where each model's output feeds the next

---

## Tech stack

| Tool | Purpose |
|---|---|
| Python | Core language |
| PuLP | LP/MILP formulation and CBC solver |
| Streamlit | Web app framework |
| Plotly | Interactive charts |
| CBC (via PuLP) | Open-source solver engine |

---

## Project structure

finance-optimizer/

├── app.py              # Streamlit UI — all four tabs

├── models/

│   ├── budget.py       # Budget LP model

│   ├── savings.py      # Savings goal LP model

│   └── grocery.py      # Grocery MILP model

└── requirements.txt

---

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Background

This project was built as an IE portfolio project to demonstrate applied operations 
research techniques. The grocery model is a direct implementation of the classic 
diet problem — one of the original LP formulations developed by George Stigler in 
1945 — extended with MILP techniques to handle realistic purchasing constraints.