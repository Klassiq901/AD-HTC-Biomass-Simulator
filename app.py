# ==============================================================================
# PROJECT: AD-HTC NEXUS INTEGRATED POWER PLANT
# AUTHOR: Ferdinand
# DESCRIPTION: Lead System Architect & Developer
# ------------------------------------------------------------------------------
# This code handles the thermodynamic modeling, cycle efficiencies,
# and the data visualization logic for the integrated power system.
# ==============================================================================

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io

# ==========================================================
# PAGE CONFIG
# ==========================================================
st.set_page_config(layout="wide", page_title="AD-HTC Nexus")

# ==========================================================
# CUSTOM DARK THEME (kept exactly as provided)
# ==========================================================
st.markdown("""
<style>

/* ==============================
   GLOBAL BACKGROUND
============================== */
.stApp {
    background: linear-gradient(180deg, #0b1220 0%, #0a0f1a 100%);
    color: #e5e7eb;
    font-family: 'Inter', sans-serif;
}

/* ==============================
   SIDEBAR
============================== */
section[data-testid="stSidebar"] {
    background-color: #0f172a;
    border-right: 1px solid #1f2937;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #f3f4f6;
}

/* ==============================
   HEADINGS
============================== */
h1 {
    font-size: 2.2rem;
    font-weight: 700;
}

h2, h3 {
    color: #f3f4f6;
}

/* ==============================
   INPUT FIELDS
============================== */
.stNumberInput input {
    background-color: #111827 !important;
    color: #e5e7eb !important;
    border: 1px solid #1f2937 !important;
    border-radius: 1px !important;
}

/* Sliders */
.stSlider > div > div {
    color: #ef4444 !important;
}

/* ==============================
   RADIO BUTTONS
============================== */
div[role="radiogroup"] {
    background-color: #111827;
    padding: 12px;
    border-radius: 12px;
    border: 1px solid #1f2937;
}

/* ==============================
   GLOWING ANALYZE BUTTON
============================== */
.stButton>button {
    background: linear-gradient(90deg, #7c3aed, #3b82f6);
    color: white;
    font-weight: 600;
    border-radius: 14px;
    height: 3.2em;
    border: none;
    box-shadow: 0 0 15px rgba(124,58,237,0.6),
                0 0 40px rgba(59,130,246,0.4);
    transition: all 0.3s ease-in-out;
}

.stButton>button:hover {
    transform: scale(1.01);
    box-shadow: 0 0 25px rgba(124,58,237,0.9),
                0 0 60px rgba(59,130,246,0.7);
}

/* ==============================
   TABS
============================== */
button[data-baseweb="tab"] {
    color: #9ca3af;
    font-weight: 500;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #ef4444 !important;
    border-bottom: 2px solid #ef4444 !important;
}

/* ==============================
   PDF DOWNLOAD BUTTON
============================== */
.stDownloadButton>button {
    background: linear-gradient(90deg, #10b981, #059669) !important;
    color: white !important;
    font-weight: 600 !important;
    border-radius: 14px !important;
    height: 3.2em !important;
    border: none !important;
    box-shadow: 0 0 15px rgba(16,185,129,0.6) !important;
    animation: glow 2s ease-in-out infinite !important;
}

.stDownloadButton>button:hover {
    transform: scale(1.02) !important;
    box-shadow: 0 0 25px rgba(16,185,129,0.9) !important;
}

@keyframes glow {
    0% { box-shadow: 0 0 15px rgba(16,185,129,0.6); }
    50% { box-shadow: 0 0 25px rgba(16,185,129,0.9); }
    100% { box-shadow: 0 0 15px rgba(16,185,129,0.6); }
}

/* ==============================
   HIDE INDEX COLUMN IN TABLES
============================== */
.dataframe thead tr th:first-child {
    display: none !important;
}

.dataframe tbody tr th:first-child {
    display: none !important;
}

.dataframe tbody tr td:first-child {
    display: none !important;
}

/* Ensure tables still look good without index */
.dataframe {
    width: 100% !important;
}

</style>
""", unsafe_allow_html=True)

# ==========================================================
# SIDEBAR INPUTS (10 total) - preserved layout and labels
# ==========================================================
st.sidebar.title("⚙ Input Parameters")

st.sidebar.subheader("Biomass Feedstock")
m_biomass = st.sidebar.number_input("Biomass Mass Flow Rate (kg/s)", value=10.0, min_value=0.01, max_value=1000.0, step=0.1)
MC = st.sidebar.slider("Moisture Content (fraction)", 0.0, 1.0, 0.25, step=0.01)
LHV = st.sidebar.number_input("Lower Heating Value (MJ/kg, dry basis)", value=18.0, min_value=5.0, max_value=30.0, step=0.1)

st.sidebar.subheader("Steam Cycle (Rankine)")
boiler_p = st.sidebar.number_input("Boiler Pressure (MPa)", value=8.0, min_value=0.1, max_value=30.0, step=0.1)
boiler_T = st.sidebar.number_input("Boiler Temperature (°C)", value=500.0, min_value=200.0, max_value=700.0, step=10.0)
cond_p = st.sidebar.number_input("Condenser Pressure (MPa)", value=0.01, min_value=0.001, max_value=1.0, step=0.001, format="%.3f")
eta_turbine = st.sidebar.slider("Turbine Efficiency", 0.5, 1.0, 0.85, step=0.01)

st.sidebar.subheader("Gas Cycle (Brayton)")
rp = st.sidebar.slider("Compressor Pressure Ratio", 2.0, 20.0, 8.0, step=0.5)
eta_comp = st.sidebar.slider("Compressor Efficiency", 0.5, 1.0, 0.88, step=0.01)
T3 = st.sidebar.number_input("Turbine Inlet Temperature (K)", value=1200.0, min_value=800.0, max_value=2000.0, step=10.0)

analyze = st.sidebar.button("🚀 Analyze System")

# ==========================================================
# SIMULATION FUNCTION (computes all expected outputs)
# ==========================================================
def run_simulation(m_biomass, MC, LHV, boiler_p, boiler_T, cond_p, rp, eta_comp, eta_turbine, T3):
    # ---------- 1-2 Mass splits (Inputs 1 & 2)
    m_dry = m_biomass * (1 - MC)           # kg/s
    m_moisture = m_biomass * MC            # kg/s

    # ---------- 3-6 Energy inputs (Input 3 LHV)
    # Convert LHV to kJ/kg
    LHV_kJ = LHV * 1000.0                  # kJ/kg
    # Fuel energy input (Brayton) from dry biomass
    Q_in_Brayton = m_dry * LHV_kJ          # kJ/s (kW)
    # Rankine heat input from moisture (uses enthalpy difference below)
    # Boiler enthalpy approximations (h3) will be computed later; placeholder for now
    # Q_in_Rankine computed after h3,h2 are known

    # ---------- Brayton cycle (Inputs 7,8,9,10)
    gamma = 1.4
    Cp = 1.005  # kJ/kg.K (approx for air)
    R = 0.287   # kJ/kg.K
    T1 = 298.15  # K ambient
    P1 = 0.1013  # MPa ambient
    P2 = P1 * rp

    # Isentropic compressor outlet temperature
    T2s = T1 * (rp) ** ((gamma - 1) / gamma)
    # Actual compressor outlet temperature using compressor efficiency
    T2 = T1 + (T2s - T1) / eta_comp
    # Compressor work per kg of working fluid (kJ/kg)
    W_comp_per_kg = Cp * (T2 - T1)

    # Choose a working fluid mass flow (kg/s) linked to fuel via an assumed AFR
    AFR = 20.0  # air-to-fuel mass ratio (assumption)
    working_flow = max(1.0, AFR * m_dry)  # kg/s of working fluid

    # Total compressor work (kJ/s)
    W_comp = W_comp_per_kg * working_flow

    # Heat added per kg working fluid (kJ/kg) and total Qin for Brayton (kJ/s)
    Qin_per_kg = Cp * (T3 - T2)
    Qin_total = Qin_per_kg * working_flow

    # Turbine expansion (isentropic then actual)
    T4s = T3 * (1 / rp) ** ((gamma - 1) / gamma)
    T4 = T3 - eta_turbine * (T3 - T4s)
    W_turbine_per_kg = Cp * (T3 - T4)
    W_turbine_brayton = W_turbine_per_kg * working_flow

    # Net Brayton work (kJ/s)
    W_net_brayton = W_turbine_brayton - W_comp

    # Brayton efficiency (use total Qin_total)
    eta_brayton = W_net_brayton / Qin_total if Qin_total > 0 else 0.0

    # ---------- Rankine cycle (Inputs 4,5,6)
    # Pump work per kg (kJ/kg) - incompressible approximation
    v_f = 0.00101  # m3/kg
    W_pump_per_kg = v_f * (boiler_p - cond_p) * 1000.0  # kJ/kg (MPa->kPa)
    # Saturated liquid enthalpy approx at condenser pressure
    if cond_p <= 0.01:
        h1 = 191.8
    elif cond_p <= 0.02:
        h1 = 251.4
    else:
        h1 = 300.0
    h2 = h1 + W_pump_per_kg

    # Boiler outlet enthalpy (approx from boiler temperature)
    h3 = 2800.0 + 2.0 * (boiler_T - 500.0)  # kJ/kg (approx)
    # Isentropic enthalpy drop (approx) and actual turbine work per kg
    delta_h_isentropic = 1200.0 * (1.0 - 0.03 * (boiler_p - 8.0))
    W_turbine_rankine_per_kg_isentropic = delta_h_isentropic
    W_turbine_rankine_per_kg_actual = W_turbine_rankine_per_kg_isentropic * eta_turbine
    h4 = h3 - W_turbine_rankine_per_kg_actual

    # Ensure physical bounds
    if h4 < h1:
        h4 = h1 + 50.0

    # Rankine heat input and turbine work based on moisture-derived steam
    Q_in_Rankine = m_moisture * (h3 - h2)   # kJ/s
    W_turbine_rankine = m_moisture * (h3 - h4)     # kJ/s
    W_pump = W_pump_per_kg * m_moisture       # kJ/s

    # Rankine efficiency
    eta_rankine = (W_turbine_rankine - W_pump) / Q_in_Rankine if Q_in_Rankine > 0 else 0.0

    # ---------- Combined cycle
    total_input_energy = Q_in_Brayton + Q_in_Rankine
    total_output_work = max(0.0, W_net_brayton) + max(0.0, W_turbine_rankine)
    eta_combined = total_output_work / total_input_energy if total_input_energy > 0 else 0.0

    # ---------- Energy flow analysis (Sankey data)
    Q_fuel = Q_in_Brayton  # kJ/s ~ kW
    Q_steam = Q_in_Rankine
    useful_work = total_output_work
    losses = Q_fuel + Q_steam - useful_work

    # ---------- Gas production (AD-HTC empirical approximations)
    gas_A = 0.568 * (rp / 8.0) ** 0.7 * (T3 / 1200.0) ** 0.5  # kg/hr
    gas_B = 1.716 * (rp / 8.0) ** 0.8 * (T3 / 1200.0) ** 0.6  # kg/hr
    methane = 1.029 * (T3 / 1200.0) ** 0.9 * (eta_combined / 0.5) ** 0.3  # kg/hr
    heating_energy = 928106.3 * (eta_combined / 0.6) * (gas_B / 1.5)  # kJ (approx)

    # ---------- Derived power outputs (kW)
    brayton_power = max(0.0, W_net_brayton)  # kJ/s -> kW
    rankine_power = max(0.0, W_turbine_rankine - W_pump)  # kJ/s -> kW
    total_power = brayton_power + rankine_power

    # ---------- Fuel consumption (kg/hr) using LHV_kJ
    # Use Q_in_Brayton (kJ/s) divided by LHV_kJ (kJ/kg) to get kg/s
    m_fuel_kg_s = Q_in_Brayton / LHV_kJ if LHV_kJ > 0 else 0.0
    fuel_consumption_kg_hr = m_fuel_kg_s * 3600.0

    # ---------- Package results (include all expected outputs)
    results = {
        # 1-2 Mass flows
        "m_dry": m_dry,
        "m_moisture": m_moisture,
        # 3-6 Energy & heat transfers
        "Q_in_Brayton": Q_in_Brayton,
        "Q_in_Rankine": Q_in_Rankine,
        "Q_fuel": Q_fuel,
        "Q_steam": Q_steam,
        # 7-10 Work terms
        "W_comp": W_comp,
        "W_turb_brayton": W_turbine_brayton,
        "W_turb_rankine": W_turbine_rankine,
        "W_pump": W_pump,
        # 11 Net work
        "W_net_brayton": W_net_brayton,
        # 12-14 Efficiencies
        "eta_brayton": eta_brayton,
        "eta_rankine": eta_rankine,
        "eta_combined": eta_combined,
        # 15-17 Power outputs
        "brayton_power": brayton_power,
        "rankine_power": rankine_power,
        "total_power": total_power,
        # 18 Fuel consumption
        "fuel_consumption_kg_hr": fuel_consumption_kg_hr,
        # 19 Energy flow summary
        "useful_work": useful_work,
        "losses": losses,
        # 20-23 Gas production & HTC
        "gas_A": gas_A,
        "gas_B": gas_B,
        "methane": methane,
        "heating_energy": heating_energy,
        # 24-25 State points and enthalpies for charts
        "T1": T1, "T2": T2, "T3": T3, "T4": T4,
        "P1": P1, "P2": P2,
        "h1": h1, "h2": h2, "h3": h3, "h4": h4,
        # Echo inputs for report
        "inputs": {
            "m_biomass": m_biomass, "MC": MC, "LHV_MJkg": LHV,
            "boiler_p": boiler_p, "boiler_T": boiler_T, "cond_p": cond_p,
            "rp": rp, "eta_comp": eta_comp, "eta_turbine": eta_turbine, "T3": T3
        }
    }

    return results

# ==========================================================
# PDF GENERATION FUNCTION (uses results)
# ==========================================================
def generate_pdf_report(results):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)

    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#7c3aed'), alignment=1)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#94a3b8'), alignment=1)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#ef4444'))

    story.append(Paragraph("AD-HTC Nexus System Analysis Report", title_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", subtitle_style))
    story.append(Spacer(1, 12))

    # Inputs summary
    story.append(Paragraph("1. Inputs", heading_style))
    inputs = results["inputs"]
    data_inputs = [
        ["Parameter", "Value"],
        ["Biomass mass flow (kg/s)", f"{inputs['m_biomass']}"],
        ["Moisture content (fraction)", f"{inputs['MC']}"],
        ["LHV (MJ/kg)", f"{inputs['LHV_MJkg']}"],
        ["Boiler pressure (MPa)", f"{inputs['boiler_p']}"],
        ["Boiler temperature (°C)", f"{inputs['boiler_T']}"],
        ["Condenser pressure (MPa)", f"{inputs['cond_p']}"],
        ["Compressor ratio", f"{inputs['rp']}"],
        ["Compressor efficiency", f"{inputs['eta_comp']}"],
        ["Turbine efficiency", f"{inputs['eta_turbine']}"],
        ["Turbine inlet temp (K)", f"{inputs['T3']}"]
    ]
    table_inputs = Table(data_inputs, colWidths=[3.5*inch, 2.0*inch])
    table_inputs.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black)
    ]))
    story.append(table_inputs)
    story.append(Spacer(1, 12))

    # Efficiencies
    story.append(Paragraph("2. Cycle Efficiencies", heading_style))
    data_eff = [
        ["Cycle", "Efficiency (%)"],
        ["Rankine", f"{results['eta_rankine']*100:.2f}%"],
        ["Brayton", f"{results['eta_brayton']*100:.2f}%"],
        ["Combined", f"{results['eta_combined']*100:.2f}%"]
    ]
    table_eff = Table(data_eff, colWidths=[3.5*inch, 2.0*inch])
    table_eff.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black)
    ]))
    story.append(table_eff)
    story.append(Spacer(1, 12))

    # Energy summary
    story.append(Paragraph("3. Energy Summary", heading_style))
    data_energy = [
        ["Parameter", "Value"],
        ["Dry biomass mass flow (kg/s)", f"{results['m_dry']:.3f}"],
        ["Moisture mass flow (kg/s)", f"{results['m_moisture']:.3f}"],
        ["Fuel energy input (kW)", f"{results['Q_fuel']:.2f}"],
        ["Steam energy input (kW)", f"{results['Q_steam']:.2f}"],
        ["Brayton net work (kW)", f"{results['W_net_brayton']:.2f}"],
        ["Rankine turbine work (kW)", f"{results['W_turb_rankine']:.2f}"],
        ["Pump work (kW)", f"{results['W_pump']:.2f}"],
        ["Total power (kW)", f"{results['total_power']:.2f}"],
        ["Fuel consumption (kg/hr)", f"{results['fuel_consumption_kg_hr']:.3f}"]
    ]
    table_energy = Table(data_energy, colWidths=[3.5*inch, 2.0*inch])
    table_energy.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black)
    ]))
    story.append(table_energy)
    story.append(Spacer(1, 12))

    # Gas production
    story.append(Paragraph("4. AD-HTC Gas Production", heading_style))
    data_gas = [
        ["Parameter", "Value"],
        ["Gas A (kg/hr)", f"{results['gas_A']:.3f}"],
        ["Gas B (kg/hr)", f"{results['gas_B']:.3f}"],
        ["Methane (kg/hr)", f"{results['methane']:.3f}"],
        ["HTC Heating Load (kJ)", f"{results['heating_energy']:.0f}"]
    ]
    table_gas = Table(data_gas, colWidths=[3.5*inch, 2.0*inch])
    table_gas.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black)
    ]))
    story.append(table_gas)
    story.append(Spacer(1, 20))

    footer = Paragraph("AD-HTC Nexus - Integrated Anaerobic Digestion & Hydrothermal Carbonization Power Plant Analysis", styles['Italic'])
    story.append(footer)

    doc.build(story)
    buffer.seek(0)
    return buffer

# ==========================================================
# RUN SIMULATION (triggered by analyze button)
# ==========================================================
if analyze:
    results = run_simulation(m_biomass, MC, LHV, boiler_p, boiler_T, cond_p, rp, eta_comp, eta_turbine, T3)
    st.sidebar.success("✅ Analysis Complete!")
else:
    results = run_simulation(m_biomass, MC, LHV, boiler_p, boiler_T, cond_p, rp, eta_comp, eta_turbine, T3)

# ==========================================================
# HEADER
# ==========================================================
st.title("AD-HTC Nexus")
st.caption("Integrated Anaerobic Digestion — Hydrothermal Carbonization Power Plant")

# ==========================================================
# TABS
# ==========================================================
dashboard_tab, report_tab, schematic_tab = st.tabs(
    ["📊 Dashboard", "📄 Report", "📐 Schematic"]
)

# ==========================================================
# DASHBOARD TAB
# ==========================================================
with dashboard_tab:
    st.subheader("Cycle Efficiencies")

    def custom_metric(label, value, unit=""):
        st.markdown(f"""
        <div style="padding:12px 0;">
            <div style="
                font-size:13px;
                color:#6b7280;
                font-weight:600;
                margin-bottom:6px;">
                {label}
            </div>
            <div style="
                font-size:38px;
                font-weight:800;
                color:#f3f4f6;
                line-height:1;">
                {value}
                <span style="
                    font-size:24px;
                    color:#4b5563;
                    font-weight:500;">
                    {unit}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        custom_metric("Rankine Efficiency", f"{results['eta_rankine'] * 100:.2f}", "%")
    with col2:
        custom_metric("Brayton Efficiency", f"{results['eta_brayton'] * 100:.2f}", "%")
    with col3:
        custom_metric("Overall Efficiency", f"{results['eta_combined'] * 100:.2f}", "%")

    st.divider()

    col4, col5, col6 = st.columns(3)
    with col4:
        custom_metric("Gas A (Base)", f"{results['gas_A']:.3f}", "kg/hr")
    with col5:
        custom_metric("Gas B (Enhanced)", f"{results['gas_B']:.3f}", "kg/hr")
    with col6:
        custom_metric("⚡ Total Power", f"{results['total_power']:.2f}", "kW")

    col7, col8, col9 = st.columns(3)
    with col7:
        custom_metric("Brayton Power", f"{results['brayton_power']:.2f}", "kW")
    with col8:
        custom_metric("Rankine Power", f"{results['rankine_power']:.2f}", "kW")
    with col9:
        custom_metric("Fuel Consumption", f"{results['fuel_consumption_kg_hr']:.3f}", "kg/hr")

    st.divider()

    # Thermodynamic diagrams
    col10, col11 = st.columns(2)

    # Rankine h-s Diagram (UNCHANGED)
    with col10:
        st.subheader("h-s Diagram (Rankine Cycle)")
        fig1, ax1 = plt.subplots(figsize=(8, 6))
        fig1.patch.set_facecolor('#0f172a')
        ax1.set_facecolor('#0f172a')

        s_liq = np.linspace(0.5, 3.0, 30)
        h_liq = 200 + 300 * s_liq
        s_vap = np.linspace(5.5, 8.5, 30)
        h_vap = 2500 + 200 * (s_vap - 5.5)

        ax1.plot(s_liq, h_liq, '--', color='#4b5563', alpha=0.7, linewidth=1.5)
        ax1.plot(s_vap, h_vap, '--', color='#4b5563', alpha=0.7, linewidth=1.5)

        pressure_factor = boiler_p / 8.0
        s1 = 0.8
        h1 = results['h1']
        s2 = 0.85
        h2 = results['h2']
        s3 = 6.5 + 0.5 * (pressure_factor - 1)
        h3 = results['h3']
        s4 = s3 + 0.8 * (1 - eta_turbine)
        h4 = results['h4']

        points_x = [s1, s2, s3, s4, s1]
        points_y = [h1, h2, h3, h4, h1]

        ax1.plot(points_x, points_y, 'o-', color='#ef4444', linewidth=2.5, markersize=8,
                 markerfacecolor='white', markeredgecolor='#ef4444')

        ax1.text(s1 - 0.1, h1 - 30, '1', color='white', fontsize=12, fontweight='bold')
        ax1.text(s2 + 0.1, h2 - 30, '2', color='white', fontsize=12, fontweight='bold')
        ax1.text(s3 + 0.1, h3 + 30, '3', color='white', fontsize=12, fontweight='bold')
        ax1.text(s4 + 0.1, h4 - 30, '4', color='white', fontsize=12, fontweight='bold')

        ax1.set_xlim(0, 9)
        ax1.set_ylim(0, 3500)
        ax1.set_xlabel("Entropy (kJ/kg·K)", color='white', fontsize=11)
        ax1.set_ylabel("Enthalpy (kJ/kg)", color='white', fontsize=11)
        ax1.tick_params(colors='white', labelsize=10)
        ax1.grid(True, alpha=0.15, linestyle='--')
        st.pyplot(fig1)

    # Brayton T-s Diagram (FIXED ONLY HERE)
    with col11:
        st.subheader("T-s Diagram (Brayton Cycle)")
        fig2, ax2 = plt.subplots(figsize=(8, 6))
        fig2.patch.set_facecolor('#0f172a')
        ax2.set_facecolor('#0f172a')

        Cp_diag = 1.005
        R_diag = 0.287
        eps = 1e-9

        T1 = max(results['T1'], eps)
        T2 = max(results['T2'], eps)
        T3 = max(results['T3'], eps)
        T4 = max(results['T4'], eps)

        P1 = max(results['P1'], eps)
        P2 = max(results['P2'], eps)

        # Correct entropy relations
        s1 = 0
        s2 = Cp_diag * np.log(T2 / T1) - R_diag * np.log(P2 / P1)
        s3 = s2 + Cp_diag * np.log(T3 / T2)
        s4 = s3 + Cp_diag * np.log(T4 / T3) - R_diag * np.log(P1 / P2)

        # 1-2 Isentropic Compression (vertical)
        ax2.plot([s1, s1], [T1, T2], '--', color='#3b82f6', linewidth=2.5)

        # 2-3 Heat Addition
        ax2.plot([s2, s3], [T2, T3], '-', color='#ef4444', linewidth=2.5)

        # 3-4 Isentropic Expansion (vertical)
        ax2.plot([s3, s3], [T3, T4], '--', color='#3b82f6', linewidth=2.5)

        # 4-1 Heat Rejection
        ax2.plot([s4, s1], [T4, T1], '-', color='#ef4444', linewidth=2.5)

        ax2.plot([s1, s2, s3, s4],
                 [T1, T2, T3, T4],
                 'o', color='white',
                 markersize=8,
                 markeredgecolor='#ef4444',
                 markeredgewidth=1.5)

        ax2.set_xlabel("Entropy (kJ/kg·K)", color='white', fontsize=11)
        ax2.set_ylabel("Temperature (K)", color='white', fontsize=11)
        ax2.tick_params(colors='white', labelsize=10)
        ax2.grid(True, alpha=0.15, linestyle='--')
        st.pyplot(fig2)

    st.divider()

    # Energy Flow Analysis (UNCHANGED)
    st.subheader("Energy Flow Analysis")
    energy_data = pd.DataFrame({
        'Component': ['Fuel Input (kW)', 'Steam Input (kW)', 'Useful Work (kW)', 'Losses (kW)'],
        'Energy (kW)': [results['Q_fuel'], results['Q_steam'], results['useful_work'], results['losses']]
    })
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.bar_chart(energy_data.set_index('Component'), height=400)
    with col_chart2:
        st.subheader("Gas Production Rates")
        gas_data = pd.DataFrame({
            'Gas Type': ['Gas A', 'Gas B', 'Methane'],
            'Production (kg/hr)': [results['gas_A'], results['gas_B'], results['methane']]
        })
        st.bar_chart(gas_data.set_index('Gas Type'), height=400)

    st.divider()
    st.subheader("Key Performance Indicators")
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    with kpi_col1:
        st.metric("Specific Work (Brayton)", f"{results['W_net_brayton']:.2f}", "kJ/s")
    with kpi_col2:
        st.metric("Heat Rate (Brayton)", f"{results['Q_in_Brayton']:.2f}", "kJ/s")
    with kpi_col3:
        st.metric("Pressure Ratio", f"{rp:.1f}", "")
    with kpi_col4:
        st.metric("TIT", f"{results['T3']:.0f}", "K")

# ==========================================================
# REPORT TAB (WITH PDF EXPORT)
# ==========================================================
with report_tab:
    st.markdown("""
        <div style='margin-bottom: 2rem;'>
            <h1 class='report-header'>📋 System Analysis Report</h1>
            <p style='color: #94A3B8; font-size: 1rem;'>Detailed thermodynamic breakdown and state point data based on current input parameters.</p>
        </div>
    """, unsafe_allow_html=True)

    # Table 1 - Cycle Efficiencies
    st.markdown("<h2 class='report-subheader'>1. Cycle Efficiencies</h2>", unsafe_allow_html=True)
    df1 = pd.DataFrame({
        "Parameter": ["Rankine Cycle", "Brayton Cycle", "Combined Cycle"],
        "Efficiency (%)": [
            f"{results['eta_rankine'] * 100:.2f}",
            f"{results['eta_brayton'] * 100:.2f}",
            f"{results['eta_combined'] * 100:.2f}"
        ]
    })
    st.dataframe(df1, hide_index=True, use_container_width=True)

    # Table 2 - State Points
    st.markdown("<h2 class='report-subheader'>2. Brayton Cycle State Points</h2>", unsafe_allow_html=True)
    df2 = pd.DataFrame({
        "State": ["Compressor Inlet", "Compressor Outlet", "Turbine Inlet", "Turbine Outlet"],
        "Temperature (K)": [
            f"{results['T1']:.1f}",
            f"{results['T2']:.1f}",
            f"{results['T3']:.1f}",
            f"{results['T4']:.1f}"
        ],
        "Pressure (MPa)": [
            f"{results['P1']:.3f}",
            f"{results['P2']:.3f}",
            f"{results['P2']:.3f}",
            f"{results['P1']:.3f}"
        ]
    })
    st.dataframe(df2, hide_index=True, use_container_width=True)

    # Table 3 - Energy Summary
    st.markdown("<h2 class='report-subheader'>3. Energy Summary</h2>", unsafe_allow_html=True)
    df3 = pd.DataFrame({
        "Parameter": ["Dry biomass (kg/s)", "Moisture (kg/s)", "Fuel Energy (kW)", "Steam Energy (kW)",
                      "Brayton Net Work (kW)", "Rankine Turbine Work (kW)", "Pump Work (kW)", "Total Power (kW)", "Fuel Consumption (kg/hr)"],
        "Value": [
            f"{results['m_dry']:.3f}",
            f"{results['m_moisture']:.3f}",
            f"{results['Q_fuel']:.2f}",
            f"{results['Q_steam']:.2f}",
            f"{results['W_net_brayton']:.2f}",
            f"{results['W_turb_rankine']:.2f}",
            f"{results['W_pump']:.2f}",
            f"{results['total_power']:.2f}",
            f"{results['fuel_consumption_kg_hr']:.3f}"
        ]
    })
    st.dataframe(df3, hide_index=True, use_container_width=True)

    # Table 4 - Gas Production
    st.markdown("<h2 class='report-subheader'>4. AD-HTC Gas Production</h2>", unsafe_allow_html=True)
    df4 = pd.DataFrame({
        "Parameter": ["Gas A (Base Rate)", "Gas B (Enhanced Rate)", "Methane Production", "HTC Heating Load"],
        "Value": [
            f"{results['gas_A']:.3f} kg/hr",
            f"{results['gas_B']:.3f} kg/hr",
            f"{results['methane']:.3f} kg/hr",
            f"{results['heating_energy']:,.0f} kJ"
        ]
    })
    st.dataframe(df4, hide_index=True, use_container_width=True)

    # PDF Export
    st.markdown("<br>", unsafe_allow_html=True)
    pdf_buffer = generate_pdf_report(results)
    st.download_button(
        label="📥 Download PDF Report",
        data=pdf_buffer.getvalue(),
        file_name=f"AD-HTC_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf"
    )

# ==========================================================
# SCHEMATIC TAB (placeholder kept)
# ==========================================================
# SCHEMATIC TAB (FULL SCREEN DIAGRAM ONLY)
# ==========================================================
with schematic_tab:
    # Read your HTML file

    with open("schematic.html", "r", encoding="utf-8") as f:
        html_content = f.read()

    # Extract just the diagram part and create minimal wrapper
    import re

    # Get the styles
    style_match = re.search(r'<style>(.*?)</style>', html_content, re.DOTALL)
    styles = style_match.group(1) if style_match else ""

    # Get the SVG content
    svg_match = re.search(r'<svg.*?</svg>', html_content, re.DOTALL)
    svg_content = svg_match.group(0) if svg_match else ""

    # Get the defs (gradients, markers, etc)
    defs_match = re.search(r'<defs>.*?</defs>', html_content, re.DOTALL)
    defs_content = defs_match.group(0) if defs_match else ""

    # Create minimal HTML with just the diagram
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        {styles}
        body {{
            margin: 0;
            padding: 0;
            background-color: #0b0f19;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            overflow: hidden;
        }}
        .diagram-container {{
            width: 100%;
            height: 100vh;
            background: rgba(15, 23, 42, 0.6);
            border: none;
            box-shadow: none;
            backdrop-filter: blur(12px);
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        svg {{
            width: 100%;
            height: 100%;
            min-height: 700px;
        }}
        /* Hide any header elements that might appear */
        .header, .container > .header, div[class*="header"] {{
            display: none !important;
        }}
    </style>
</head>
<body>
    <div class="diagram-container">
        <svg viewBox="0 70 1000 700" xmlns="http://www.w3.org/2000/svg">
            {defs_content}
            <!-- FLOW PATHS BASE (Static Background Lines) -->
            <path d="M 30 150 L 115 150" class="flow-path base" />
            <path d="M 220 130 L 710 130 L 710 200 L 690 200" class="flow-path base" />
            <path d="M 170 200 L 170 340 L 320 340" class="flow-path base" />
            <path d="M 630 175 L 400 175" class="flow-path base" />
            <path d="M 630 200 L 570 200 L 570 240" class="flow-path base" />
            <path d="M 400 300 L 480 300 L 480 200 L 570 200" class="flow-path base" />
            <path d="M 260 242 L 260 175 L 320 175" class="flow-path base" />
            <path d="M 400 190 L 440 190 L 440 310 L 400 310" class="flow-path base" />
            <path d="M 320 310 L 260 310 L 260 278" class="flow-path base" />
            <path d="M 360 360 L 360 430" class="flow-path base" />
            <path d="M 570 320 L 570 420" class="flow-path base" />
            <path d="M 610 280 L 800 280" class="flow-path base" />
            <path d="M 350 640 L 350 553" class="flow-path base" />
            <path d="M 420 525 L 470 525" class="flow-path base" />
            <path d="M 670 525 L 720 525" class="flow-path base" />
            <path d="M 790 554 L 790 640" class="flow-path base" />

            <!-- ANIMATED FLOW PATHS -->
            <path d="M 30 150 L 115 150" class="flow-path animated glow-green" marker-end="url(#arrow-green)" />
            <path d="M 220 130 L 710 130 L 710 200 L 695 200" class="flow-path animated glow-green"
                marker-end="url(#arrow-green)" />
            <path d="M 170 200 L 170 340 L 315 340" class="flow-path animated glow-orange"
                marker-end="url(#arrow-orange)" />
            <path d="M 630 175 L 405 175" class="flow-path animated glow-red" marker-end="url(#arrow-red)" />
            <path d="M 630 200 L 570 200 L 570 235" class="flow-path animated glow-yellow"
                marker-end="url(#arrow-yellow)" />
            <path d="M 400 300 L 480 300 L 480 200 L 565 200" class="flow-path animated glow-purple"
                marker-end="url(#arrow-purple)" />
            <path d="M 260 242 L 260 175 L 315 175" class="flow-path animated glow-blue"
                marker-end="url(#arrow-blue)" />
            <path d="M 400 190 L 440 190 L 440 310 L 405 310" class="flow-path animated glow-blue"
                marker-end="url(#arrow-blue)" />
            <path d="M 320 310 L 260 310 L 260 285" class="flow-path animated glow-blue"
                marker-end="url(#arrow-blue)" />
            <path d="M 360 360 L 360 425" class="flow-path animated glow-red" marker-end="url(#arrow-red)" />
            <path d="M 570 320 L 570 415" class="flow-path animated glow-yellow" marker-end="url(#arrow-yellow)" />
            <path d="M 610 280 L 795 280" class="flow-path animated glow-yellow" marker-end="url(#arrow-yellow)" />
            <path d="M 350 640 L 350 560" class="flow-path animated glow-blue" marker-end="url(#arrow-blue)" />
            <path d="M 420 525 L 465 525" class="flow-path animated glow-blue" marker-end="url(#arrow-blue)" />
            <path d="M 670 525 L 715 525" class="flow-path animated glow-red" marker-end="url(#arrow-red)" />
            <path d="M 790 554 L 790 635" class="flow-path animated glow-purple" marker-end="url(#arrow-purple)" />

            <!-- Shaft Line -->
            <line x1="220" y1="525" x2="920" y2="525" class="shaft-line" />

            <!-- COMPONENTS -->

            <!-- Homogenizer -->
            <g transform="translate(120, 100)">
                <rect width="100" height="100" class="node" />
                <text x="50" y="40" class="node-text">Biomass</text>
                <text x="50" y="55" class="node-text">Feedstock</text>
                <text x="50" y="70" class="node-subtext">Homogenizer</text>
            </g>

            <!-- Reactor -->
            <g transform="translate(320, 290)">
                <rect width="80" height="70" class="node" />
                <text x="40" y="40" class="node-text">Reactor</text>
            </g>

            <!-- Boiler -->
            <g transform="translate(320, 150)">
                <rect width="80" height="50" class="node" />
                <text x="40" y="30" class="node-text">Boiler</text>
            </g>

            <!-- Pump -->
            <g transform="translate(260, 260)">
                <circle cx="0" cy="0" r="18" fill="rgba(30, 41, 59, 1)" stroke="#38bdf8" stroke-width="2"
                    class="pulse-circle" />
                <polygon points="-8,8 0,-8 8,8" fill="#38bdf8" />
                <text x="-40" y="-20" class="node-text">Pump</text>
            </g>

            <!-- AD -->
            <g transform="translate(630, 170)">
                <rect width="60" height="60" class="node" />
                <text x="30" y="35" class="node-text">AD</text>
            </g>

            <!-- Collector -->
            <g transform="translate(530, 240)">
                <rect width="80" height="80" class="node" />
                <text x="40" y="35" class="node-text">Enhanced</text>
                <text x="40" y="50" class="node-text">Biogas</text>
                <text x="40" y="65" class="node-subtext">Collector</text>
            </g>

            <!-- Combustion Chamber -->
            <g transform="translate(470, 420)">
                <rect width="200" height="130" class="node" rx="16" ry="16" />
                <!-- Inner chamber visualization -->
                <path d="M 90,0 L 90,80 L 130,80 L 130,60 L 110,60 L 110,0 Z" fill="rgba(234, 179, 8, 0.15)"
                    stroke="var(--accent-yellow)" stroke-width="2"
                    filter="drop-shadow(0 0 10px rgba(234, 179, 8, 0.4))" />
                <text x="100" y="100" class="node-text">Biogas Combustion</text>
                <text x="100" y="115" class="node-subtext">Chamber</text>
            </g>

            <!-- Compressor -->
            <polygon points="320,490 420,510 420,540 320,560" class="node" />
            <text x="370" y="530" class="node-text">Compressor</text>

            <!-- Turbine -->
            <polygon points="720,510 820,490 820,560 720,540" class="node" />
            <text x="770" y="530" class="node-text">Turbine</text>

            <!-- Rotating Shaft Indicator -->
            <g class="shaft-rotator">
                <circle cx="900" cy="525" r="30" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="8" />
                <path d="M 900 495 A 30 30 0 0 1 930 525" fill="none" class="glow-blue" stroke-width="4"
                    marker-end="url(#arrow-blue)" />
                <path d="M 900 555 A 30 30 0 0 1 870 525" fill="none" class="glow-blue" stroke-width="4"
                    marker-end="url(#arrow-blue)" />
            </g>

            <!-- TEXT LABELS -->
            <text x="0" y="130" class="flow-label">Biomass Feedstock</text>
            <text x="600" y="100" class="flow-label" fill="#10b981">Moisture-rich Biomass</text>
            <text x="600" y="115" class="flow-label" fill="#10b981">Feedstock</text>
            <text x="140" y="360" class="flow-label" fill="#f59e0b">Moisture-lean Biomass</text>
            <text x="140" y="375" class="flow-label" fill="#f59e0b">Feedstock</text>
            <text x="300" y="250" class="flow-label" fill="#8b5cf6">HTC Steam Cycle</text>
            <text x="310" y="450" class="flow-label" fill="#8b5cf6">Volatile Matters</text>
            <text x="310" y="465" class="flow-label" fill="#8b5cf6">and Feedstock Waste</text>
            <text x="810" y="275" class="flow-label" fill="#eab308">Biogas to</text>
            <text x="810" y="290" class="flow-label" fill="#eab308">Building Envelopes</text>
            <text x="350" y="660" class="flow-label" fill="#3b82f6">Air In</text>
            <text x="790" y="660" class="flow-label" fill="#ef4444">Exhaust Gases</text>
        </svg>
    </div>
</body>
</html>"""

    # Display the diagram
    st.components.v1.html(full_html, height=750, scrolling=False)