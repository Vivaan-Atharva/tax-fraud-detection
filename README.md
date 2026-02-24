# 🛡️ VeritaxAI — Tax Declaration Fraud Detection System

A multi-agent AI system that analyzes bank statements to detect potential tax fraud and financial inconsistencies. Built with Python and Streamlit.

![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red?style=flat-square&logo=streamlit)
![Plotly](https://img.shields.io/badge/Plotly-5.15+-purple?style=flat-square&logo=plotly)

---

## 🎯 What It Does

Tax authorities manually reviewing thousands of declarations is slow and error-prone. VeritaxAI automates the detection of financial anomalies by comparing a taxpayer's **declared income** against their **actual bank statement patterns** using a pipeline of intelligent agents.

Upload a bank statement CSV, enter the declared income, and the system flags inconsistencies automatically.

---

## 🧠 How It Works — Multi-Agent Architecture

The system uses three specialized agents working in a pipeline:

```
Bank Statement CSV
       │
       ▼
┌─────────────────────┐
│   Observation Agent  │  → Parses transactions, categorizes spending
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│   Reasoning Agent   │  → Runs fraud checks, generates risk score
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│    Action Agent     │  → Produces human-readable audit report
└─────────────────────┘
```

### Agent Responsibilities

**Observation Agent**
- Parses and cleans the uploaded CSV
- Categorizes transactions (Salary, Freelance, Fixed Obligations, Lifestyle)
- Extracts key financial signals: total inflow, outflow, fixed expenses

**Reasoning Agent**
- Compares observed inflows vs declared income
- Runs **Benford's Law** forensic analysis on transaction data
- Detects lifestyle-income gaps (high EMI/rent but near-zero daily spend)
- Generates a hypothesis (income underreporting / mild inconsistency / consistent)
- Assigns a risk score and level (Low / Medium / High)

**Action Agent**
- Constructs a context-aware audit narrative
- Provides actionable recommendations for tax officers

---

## 🔍 Fraud Detection Techniques

| Technique | Description |
|-----------|-------------|
| **Income Mismatch Check** | Flags if bank inflows exceed declared income by >20% |
| **Benford's Law Analysis** | Statistical test — natural financial data follows a predictable digit distribution; fabricated data often doesn't |
| **Lifestyle Gap Detection** | High fixed bills (rent/EMI) + near-zero daily spending = possible cash economy |
| **Sustainability Check** | Uses debt-to-income ratio to estimate minimum implied income |
| **Volatility Check** | Flags single large transactions exceeding 20% of declared income |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9 or higher

### Installation

```bash
# Clone the repository
git clone https://github.com/Vivaan-Atharva/tax-fraud-detection.git
cd tax-fraud-detection

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Usage

1. Enter the taxpayer's **declared annual income** in the sidebar
2. Upload a bank statement in **CSV format** (see format below)
3. Click **"Initialize Agents"**
4. View the forensic analysis across three tabs: Reasoning Agent, Lifestyle Logic, System Agent

### CSV Format

Your bank statement CSV must have these columns:

```
date, description, amount, type
```

- `date` — transaction date (any standard format)
- `description` — transaction label (e.g. "Salary Credit", "Rent Payment")
- `amount` — transaction amount (positive number)
- `type` — either `credit` or `debit`

A sample file is included: [`sample_bank_statement.csv`](./sample_bank_statement.csv)

---

## 📸 Features

- **Animated dark UI** with glassmorphism design
- **Interactive Benford's Law chart** (Plotly) — only rendered when risk hypothesis warrants it
- **Real-time agent reasoning trace** — see exactly what decisions each agent made and why
- **Behavioral profiling** — AI-generated lifestyle profile based on spending patterns
- **Risk badge** — Low / Medium / High risk classification

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| UI & App Framework | Streamlit |
| Data Processing | Pandas, NumPy |
| Visualizations | Plotly |
| Agent Logic | Custom Python classes |
| Styling | CSS (injected via Streamlit markdown) |

---

## 📁 Project Structure

```
tax-fraud-detection/
├── app.py                    # Main application — all agent logic and UI
├── requirements.txt          # Python dependencies
├── sample_bank_statement.csv # Sample data to test the app
└── README.md                 # This file
```

---

## 👨‍💻 Author

**Vivaan J Atharva**
B.Tech CSE (AI/ML) — PES University, Bengaluru
[GitHub](https://github.com/Vivaan-Atharva)
