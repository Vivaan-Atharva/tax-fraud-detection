import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import random

# --- 1. CONFIGURATION & PAGE SETUP ---
st.set_page_config(
    page_title="VeritaxAI | Trust Layer Protocol",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    @keyframes gradient-animation {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .stApp {
        background: linear-gradient(-45deg, #020617, #0f172a, #1e1b4b, #312e81);
        background-size: 400% 400%;
        animation: gradient-animation 15s ease infinite;
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }

    /* Glass Cards */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
    }

    [data-testid="stMetricValue"] {
        background: linear-gradient(to right, #22d3ee, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem !important;
        font-weight: 800;
    }
    
    [data-testid="stMetricLabel"] {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
    }

    section[data-testid="stSidebar"] {
        background-color: rgba(2, 6, 23, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    div.stButton > button {
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        color: white;
        border: none;
        padding: 0.6rem 1.2rem;
        border-radius: 12px;
        font-weight: 600;
        text-transform: uppercase;
    }

    .console-text {
        font-family: 'Courier New', monospace;
        color: #34d399;
        font-size: 0.85rem;
        background: rgba(0,0,0,0.3);
        padding: 15px;
        border-radius: 8px;
        border-left: 3px solid #34d399;
    }
    
    .risk-badge {
        padding: 8px 20px;
        border-radius: 50px;
        font-weight: 800;
        font-size: 0.9rem;
        text-transform: uppercase;
        display: inline-block;
        margin-top: 10px;
    }
    .badge-high { background: rgba(239, 68, 68, 0.1); color: #fca5a5; border: 1px solid #ef4444; }
    .badge-med { background: rgba(249, 115, 22, 0.1); color: #fdba74; border: 1px solid #f97316; }
    .badge-low { background: rgba(34, 197, 94, 0.1); color: #86efac; border: 1px solid #22c55e; }

    .block-container { padding-top: 2rem; padding-bottom: 5rem; }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "report_generated" not in st.session_state:
    st.session_state.report_generated = False
if "report_data" not in st.session_state:
    st.session_state.report_data = None

# --- 3. AGENT LOGIC (OFFLINE-FIRST) ---

class ObservationAgent:
    def identify_fixed_obligations(self, df):
        keywords = ['rent', 'emi', 'loan', 'insurance', 'school', 'tuition', 'premium']
        mask = df['description'].str.contains('|'.join(keywords), case=False, na=False)
        fixed_obligations = df[mask & (df['type'].str.lower() == 'debit')]['amount'].sum()
        return fixed_obligations

    def observe(self, file_buffer):
        try:
            df = pd.read_csv(file_buffer)
            required_cols = ['date', 'description', 'amount', 'type']
            if not all(col in df.columns for col in required_cols):
                return {"error": "CSV must contain columns: date, description, amount, type (credit/debit)"}

            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            def categorize(desc):
                desc = desc.lower()
                if 'salary' in desc: return 'Salary'
                if 'freelance' in desc or 'client' in desc or 'upwork' in desc: return 'Freelance'
                if 'rent' in desc or 'emi' in desc or 'loan' in desc: return 'Fixed Obligations'
                if 'grocery' in desc or 'food' in desc or 'swiggy' in desc: return 'Lifestyle'
                return 'Other'
            df['category'] = df['description'].apply(categorize)

            total_inflow = df[df['type'].str.lower() == 'credit']['amount'].sum()
            total_outflow = df[df['type'].str.lower() == 'debit']['amount'].sum()
            fixed_expenses = self.identify_fixed_obligations(df)
            max_transaction = df['amount'].max() if not df.empty else 0

            return {
                "total_inflow": float(total_inflow),
                "total_outflow": float(total_outflow),
                "fixed_expenses": float(fixed_expenses),
                "max_transaction": float(max_transaction),
                "transaction_count": len(df),
                "raw_df": df
            }
        except Exception as e:
            return {"error": str(e)}

class ReasoningAgent:
    def __init__(self):
        pass

    def check_benford_stats(self, df):
        try:
            df_debits = df[df['type'].str.lower() == 'debit'].copy()
            if len(df_debits) < 5: return None
            df_debits = df_debits[df_debits['amount'] > 0]
            leading_digits = df_debits['amount'].astype(str).str.lstrip(' -').str[0]
            leading_digits = leading_digits[leading_digits.isin([str(i) for i in range(1, 10)])].astype(int)
            counts = leading_digits.value_counts(normalize=True).sort_index()
            for i in range(1, 10):
                if i not in counts: counts[i] = 0.0
            return counts
        except: return None

    def get_ai_lifestyle_profile(self, fixed, lifestyle, declared):
        """
        OFFLINE MODE: Simulates AI profiling using rule-based logic.
        """
        ratio = fixed / declared if declared > 0 else 1
        
        if ratio > 0.6:
            return "Profile: **High-Leverage Living**. Fixed obligations consume >60% of declared income, suggesting potential undisclosed liquidity sources."
        elif fixed > 20000 and lifestyle < 2000:
            return "Profile: **Shadow Consumer**. Significant home/loan payments visible, but daily living expenses are digitally invisible (likely Cash-based)."
        elif lifestyle > (declared * 0.5):
            return "Profile: **Discretionary Overspender**. Lifestyle spending exceeds 50% of declared income, leaving little room for savings or taxes."
        else:
            return "Profile: **Balanced Digital Footprint**. Spending patterns align reasonably with declared income tiers."

    def analyze(self, declared_income, observed_data):
        signals = []
        logs = []
        risk_score = 0
        df = observed_data['raw_df']
        
        # Calculate Percentage Difference
        mismatch_pct = ((observed_data['total_inflow'] - declared_income) / declared_income) * 100 if declared_income > 0 else 0

        # --- 1. HYPOTHESIS GENERATION ---
        hypothesis = None
        if mismatch_pct > 30:
            hypothesis = "income_underreporting"
            logs.append(f"[HYPOTHESIS] Possible income under-reporting detected. Mismatch: {mismatch_pct:.1f}%")
        elif mismatch_pct > 10:
            hypothesis = "mild_inconsistency"
            logs.append(f"[HYPOTHESIS] Minor financial inconsistency detected. Mismatch: {mismatch_pct:.1f}%")
        else:
            hypothesis = "consistent_profile"
            logs.append(f"[HYPOTHESIS] Profile appears consistent. Mismatch: {mismatch_pct:.1f}%")

        # --- 2. EXISTING CHECKS ---
        
        # Income Check
        if observed_data['total_inflow'] > declared_income * 1.2:
            signals.append(f"Inflows exceed declaration by {mismatch_pct:.1f}%")
            logs.append(f"[ABS_CHECK] FAIL: Observed {observed_data['total_inflow']} > Declared {declared_income}")
            risk_score += 2
        else:
            logs.append("[ABS_CHECK] PASS: Inflows within threshold.")

        # Lifestyle/Shadow Check
        fixed = observed_data['fixed_expenses']
        lifestyle = df[df['category'] == 'Lifestyle']['amount'].sum()
        ai_profile_text = self.get_ai_lifestyle_profile(fixed, lifestyle, declared_income)
        
        if fixed > 10000 and lifestyle < (fixed * 0.10):
             signals.append(f"⚠️ Digital Lifestyle Gap: High fixed bills (₹{fixed:,}) but near-zero daily spend.")
             logs.append(f"[LIFESTYLE_GAP] FAIL: Fixed={fixed} vs Lifestyle={lifestyle}")
             risk_score += 1
        
        # --- 3. CONDITIONAL SUSTAINABILITY CHECK ---
        implied_income = 0
        if hypothesis != "consistent_profile":
            logs.append("[TOOL_INVOKE] Running Sustainability Check due to hypothesis.")
            implied_income = (fixed / 0.40) if fixed > 0 else 0
            if declared_income < implied_income:
                 signals.append(f"Fixed costs imply income requirement of ~₹{implied_income:,.0f} (Sustainability Risk)")
                 logs.append(f"[SUSTAINABILITY] FAIL: Declared {declared_income} < Implied {implied_income}")
                 risk_score += 2
        else:
            logs.append("[TOOL_SKIP] Sustainability check skipped (profile consistent).")

        # --- 4. CONDITIONAL BENFORD ANALYSIS ---
        benford_counts = None
        if hypothesis == "income_underreporting":
            logs.append("[TOOL_INVOKE] Running Benford's Law Analysis due to high-risk hypothesis.")
            benford_counts = self.check_benford_stats(df)
            
            if benford_counts is not None:
                if benford_counts.get(1, 0) < 0.20:
                    signals.append(f"⚠️ Benford's Law Violation: Digit '1' freq is {benford_counts[1]*100:.1f}%")
                    logs.append(f"[STATISTICS] FAIL: Benford Digit 1 = {benford_counts[1]:.2f}")
                    risk_score += 1
                else:
                    logs.append(f"[STATISTICS] PASS: Benford Digit 1 = {benford_counts[1]:.2f}")
        else:
            logs.append("[TOOL_SKIP] Benford analysis skipped (no strong hypothesis).")

        # 5. Volatility (Always run as safety check)
        max_tx = observed_data['max_transaction']
        if max_tx > (declared_income * 0.20):
            signals.append(f"Single large transaction (₹{max_tx:,}) detected.")
            logs.append(f"[VOLATILITY] FAIL: Max Tx {max_tx} > 20% of Declared")
            risk_score += 1

        if risk_score >= 3: level = "High"
        elif risk_score >= 1: level = "Medium"
        else: level = "Low"
        
        return {
            "mismatch_ratio": mismatch_pct,
            "risk_level": level,
            "risk_score": risk_score,
            "signals": signals,
            "logs": logs,
            "benford_data": benford_counts,
            "implied_income": implied_income,
            "ai_profile": ai_profile_text,
            "lifestyle_spend": lifestyle,
            "hypothesis": hypothesis
        }

class ActionAgent:
    def explain(self, declared, observed, reasoning):
        """
        OFFLINE MODE: Context-Aware Report Constructor.
        Builds a custom narrative by analyzing specific signal combinations.
        """
        risk_score = reasoning['risk_score']
        signals = reasoning['signals']
        mismatch = reasoning['mismatch_ratio']
        hypothesis = reasoning['hypothesis']
        
        # 1. ESTABLISH TONE (The "Mood" of the Agent)
        if risk_score >= 3:
            opening = "🚨 **Critical Alert:** The financial profile shows significant deviations that require immediate attention."
            tone = "urgent"
        elif risk_score >= 1:
            opening = "⚠️ **Advisory:** Several inconsistencies were detected that may flag compliance reviews."
            tone = "cautionary"
        else:
            opening = "✅ **Clearance:** The financial footprint appears healthy and consistent with the declaration."
            tone = "reassuring"

        # 2. DIAGNOSTIC NARRATIVE (The "Why")
        narrative_parts = []
        
        if mismatch > 20:
            narrative_parts.append(f"The primary driver is a **{mismatch:.0f}% discrepancy** between banking inflows and declared income.")
        
        if any("Benford" in s for s in signals):
            narrative_parts.append("Furthermore, the **statistical distribution of expenses** (Benford's Law) appears unnatural, which is a common indicator of fabricated data.")
            
        if any("Lifestyle" in s for s in signals):
            narrative_parts.append("A **lifestyle-income gap** was identified, where fixed obligations (Rent/EMI) disproportionately consume the declared income.")

        if not narrative_parts and tone == "reassuring":
            narrative_parts.append("Spending patterns, volume, and frequency align well with standard profiles for this income bracket.")

        # Join narrative parts naturally
        body_text = " ".join(narrative_parts)

        # 3. STRATEGIC RECOMMENDATION (The "Next Steps")
        if "income_underreporting" in str(hypothesis):
            next_step = "**Recommended Action:** Review all revenue sources. Ensure freelance or cash-based income is fully documented to bridge the gap."
        elif any("Benford" in s for s in signals):
            next_step = "**Recommended Action:** Conduct a line-item audit of expense receipts. The unnatural data spread suggests potential errors in manual entry."
        elif "mild_inconsistency" in str(hypothesis):
             next_step = "**Recommended Action:** Re-categorize 'Transfer' and 'Self' transactions to ensure they are not falsely inflating inflow totals."
        else:
             next_step = "**Recommended Action:** Maintain current record-keeping practices. Periodic review of expense categorization is suggested."

        # 4. FINAL ASSEMBLY
        final_report = f"""
        {opening}
        
        {body_text}
        
        ---
        {next_step}
        """
        return final_report

# --- 4. VISUALIZATION FUNCTIONS ---

def create_benford_chart(counts):
    benford_probs = {d: np.log10(1 + 1/d) for d in range(1, 10)}
    digits = list(range(1, 10))
    expected = [benford_probs[d] * 100 for d in digits]
    observed = [counts.get(d, 0) * 100 for d in digits]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=digits, y=observed, name='Observed Frequency',
        marker_color='#f472b6', opacity=0.7
    ))
    fig.add_trace(go.Scatter(
        x=digits, y=expected, name='Benford Expected',
        line=dict(color='#22d3ee', width=4, dash='solid')
    ))
    fig.update_layout(
        title="<b>Forensic Analysis: Benford's Law</b>",
        xaxis_title="Leading Digit (1-9)",
        yaxis_title="Frequency (%)",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(family="Inter", color="#cbd5e1"),
        legend=dict(x=0.7, y=1),
        height=400
    )
    return fig

# --- 5. NAVIGATION & RENDER LOGIC ---

def render_sidebar():
    with st.sidebar:
        st.markdown("## 🛡️ VeritaxAI")
        st.caption("Trust Layer Protocol v12.0 (Final Agentic)")
        st.divider()
        
        page_mode = st.radio("System Mode", ["Dashboard", "Transaction Inspector", "Architecture"], label_visibility="collapsed")
        st.divider()
        
        analysis_view = "Reasoning Agent"
        if st.session_state.report_generated:
            st.markdown("### 🔍 Analysis Component")
            analysis_view = st.radio(
                "Select View", 
                ["Reasoning Agent", "Lifestyle Logic", "System Agent"],
                index=0
            )
            st.divider()

        st.markdown("### ⚙️ Parameters")
        declared = st.number_input("Declared Annual Income (₹)", value=500000, step=10000)
        
        return page_mode, analysis_view, declared

def render_dashboard(analysis_view, declared_income):
    st.markdown("### 📊 Financial Consistency Dashboard")
    st.write("")
    
    if not st.session_state.report_generated:
        c1, c2 = st.columns([3, 1])
        uploaded_file = c1.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")
        run_btn = c2.button("🚀 INITIALIZE AGENTS", type="primary", use_container_width=True)

        if run_btn and uploaded_file:
            observer = ObservationAgent()
            reasoner = ReasoningAgent()
            actor = ActionAgent()

            with st.spinner("🔮 Veritax Agents are analyzing financial patterns..."):
                obs_data = observer.observe(uploaded_file)
                if "error" in obs_data:
                    st.error(obs_data["error"])
                else:
                    reasoning_data = reasoner.analyze(declared_income, obs_data)
                    explanation = actor.explain(declared_income, obs_data, reasoning_data)
                    st.session_state.report_data = {"obs": obs_data, "reasoning": reasoning_data, "explanation": explanation, "declared": declared_income}
                    st.session_state.report_generated = True
                    st.rerun()

    if st.session_state.report_generated:
        if st.button("🔄 Start New Analysis"):
            st.session_state.report_generated = False
            st.session_state.report_data = None
            st.rerun()

        data = st.session_state.report_data
        r_data = data['reasoning']
        obs = data['obs']

        # KPI Header
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1: st.metric("Declared Income", f"₹{data['declared']/1000:.0f}k")
        with kpi2: st.metric("Observed Inflow", f"₹{obs['total_inflow']/1000:.0f}k", delta=f"{r_data['mismatch_ratio']:.0f}% Gap", delta_color="inverse")
        with kpi3: st.metric("Burn Rate", f"₹{obs['total_outflow']/1000:.0f}k")
        with kpi4:
            lvl = r_data['risk_level']
            cls = f"badge-{lvl.lower()}"
            st.markdown(f"<div style='text-align: center; padding-top: 10px;'><div class='risk-badge {cls}'>{lvl.upper()} RISK</div></div>", unsafe_allow_html=True)
        st.divider()

        # --- VIEW: REASONING AGENT ---
        if analysis_view == "Reasoning Agent":
            st.markdown("## 🧠 Reasoning Agent: Forensic Analysis")
            
            if not r_data['signals']: 
                st.success("✅ Financial behavior aligns with declaration.")
            for sig in r_data['signals']: 
                st.warning(f"⚠️ {sig}")
            
            st.divider()
            
            # Benford Forensic Chart (Conditional Render)
            if r_data['benford_data'] is not None:
                st.markdown("#### 🔎 Statistical Forensics (Benford's Law)")
                st.caption("Agent invoked forensic analysis due to high-risk hypothesis.")
                st.plotly_chart(create_benford_chart(r_data['benford_data']), use_container_width=True)
                if r_data['benford_data'].get(1, 0) < 0.20:
                     st.error("⚠️ **Violation Detected:** Leading digit '1' frequency is unnaturally low.")
                else:
                     st.success("✅ Data Distribution appears natural.")
            else:
                st.info("ℹ️ **Statistical Analysis Skipped:** Agent determined profile risk was too low to warrant expensive forensic compute.")

            st.divider()
            st.markdown("#### 📝 Reasoning Trace Log (Agent Thinking)")
            st.caption("Live decision logic from the probabilistic engine.")
            log_text = "\n".join(r_data['logs'])
            st.markdown(f'<div class="console-text">{log_text}</div>', unsafe_allow_html=True)
        
        # --- VIEW: LIFESTYLE LOGIC ---
        elif analysis_view == "Lifestyle Logic":
            st.markdown("## 🏡 Lifestyle & Shadow Economy Analysis")
            
            fixed = obs['fixed_expenses']
            implied = r_data['implied_income']
            
            # Simulated AI Profile (Rule-Based)
            st.markdown("### 🤖 Behavioral Profiling")
            st.info(f"**Agent Insight:** {r_data['ai_profile']}")
            
            st.divider()
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px; text-align:center;">
                    <div style="font-size: 1rem; color: #94a3b8;">Detected Fixed Bill (Rent/EMI)</div>
                    <div style="font-size: 2.2rem; font-weight: bold; color: white;">₹{fixed:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                # Implied Income Card
                val = f"₹{implied:,.0f}" if implied > 0 else "N/A"
                st.markdown(f"""
                <div style="background: rgba(34, 211, 238, 0.1); border: 1px solid #22d3ee; padding: 20px; border-radius: 10px; text-align:center;">
                    <div style="font-size: 1rem; color: #94a3b8;">Implied Annual Income</div>
                    <div style="font-size: 2.2rem; font-weight: bold; color: #22d3ee;">{val}</div>
                    <div style="font-size: 0.8rem; margin-top:5px;">(Based on 40% Debt-to-Income Ratio)</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.write("")
            if fixed > 10000 and (obs['total_outflow'] - fixed) < (fixed * 0.1):
                st.warning(f"**Digital Lifestyle Gap Detected:** The user pays ₹{fixed:,} in bills but has near-zero daily living expenses.")

        # --- VIEW: SYSTEM AGENT ---
        elif analysis_view == "System Agent":
            st.markdown("## 💬 System Interpretation")
            st.info(f"{data['explanation']}")

    elif not run_btn:
        st.info("👈 Waiting for input... Please upload a bank statement.")

def render_inspector():
    st.subheader("🔎 Transaction Inspector")
    if st.session_state.report_generated:
        df = st.session_state.report_data['obs']['raw_df']
        st.dataframe(df, use_container_width=True, height=600)
    else:
        st.warning("Please run analysis first.")

def render_arch():
    st.subheader("⚙️ System Architecture")
    st.markdown("VeritaxAI operates on a localized, privacy-first multi-agent protocol.")

def main():
    page_mode, analysis_view, declared = render_sidebar()
    if page_mode == "Dashboard":
        render_dashboard(analysis_view, declared)
    elif page_mode == "Transaction Inspector":
        render_inspector()
    elif page_mode == "Architecture":
        render_arch()

if __name__ == "__main__":
    main()
