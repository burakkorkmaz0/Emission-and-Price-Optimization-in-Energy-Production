# Emission and Price Optimization in Energy Production

This project focuses on restructuring national energy production portfolios to meet sustainability goals. The goal is to balance environmental impacts and economic costs using advanced optimization techniques.

### 💡 The Problem
European countries need to transition to renewable energy to fight climate change. However, this transition must not:
1. Increase electricity prices too much for consumers.
2. Reduce the total energy production needed for the country.

### 🛠️ Methodology
We developed a **multi-objective optimization model** that targets three main goals simultaneously:
* **Minimizing Greenhouse Gas Emissions** (at least 5% reduction).
* **Minimizing Electricity Prices** (maximum 10-12% increase allowed).
* **Maximizing the Share of Renewable Energy.**

We applied two different metaheuristic algorithms to solve this complex problem:
* **Genetic Algorithm (GA):** Used for deep exploration of the solution space.
* **Particle Swarm Optimization (PSO):** Provided faster convergence to find efficient energy mixes.

### 📊 Results & Evaluation
We tested the model using **Eurostat data (2022)** for **Germany** and **France**.
* **Findings:** Both algorithms successfully identified energy mixes that increased renewable shares while staying within price and emission limits.
* **Algorithm Comparison:** While PSO was faster at finding a good solution, GA often achieved a better overall balance (fitness score) in the German case.
  
### 🚀 Technologies Used
* **Python:** Core development and algorithm implementation.
* **Optimization Techniques:** Genetic Algorithms, Particle Swarm Optimization.
* **Data Source:** Eurostat (Energy production, electricity prices, and emission accounts).
* **Visualization:** Matplotlib for convergence and share change plots.
