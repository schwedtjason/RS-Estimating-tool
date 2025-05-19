import streamlit as st
from PIL import Image
import pandas as pd
import io
import datetime
import os
import matplotlib.pyplot as plt
from fpdf import FPDF
import math

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Rolling Suds Estimator",
    layout="wide",
    page_icon="🧼"
)

# --- CUSTOM THEME ---
st.markdown("""
<style>
    html, body, [class*="css"] {
        background-color: #013765;
        color: white;
        font-family: 'Segoe UI', sans-serif;
        font-size: 15px;
    }
    .stApp {
        max-width: 800px;
        margin: auto;
        padding: 2rem;
    }
    .stButton>button, .stDownloadButton>button {
        background-color: #27c7d9;
        color: black;
        font-weight: 600;
        border-radius: 10px;
        padding: 0.5rem 1rem;
    }
    .stSelectbox>div>label, .stNumberInput>div>label, .stCheckbox>div>label, .stTextInput>div>label {
        color: #d1ecf1;
        font-weight: 500;
    }
    h1, h2, h3, h4 {
        color: #27c7d9;
    }
    .stCaption {
        color: #a2e9f4;
    }
    .card {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.2);
        margin-bottom: 2rem;
    }
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #012b52;
        text-align: center;
        padding: 0.75rem;
        color: white;
        font-size: 0.9rem;
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
col_header1, col_header2 = st.columns([1, 3])
with col_header1:
    try:
        logo = Image.open("rolling_suds_logo.png")
        st.image(logo, width=150)
    except FileNotFoundError:
        st.warning("⚠️ Logo file not found.")

with col_header2:
    st.markdown("""
    <h1 style='margin-bottom: 0;'>Rolling Suds Job Estimator</h1>
    <p style='font-size: 1.2rem;'>Powered by <a href="https://www.rollingsudspowerwashing.com" target="_blank">RollingSudsPowerWashing.com</a></p>
    """, unsafe_allow_html=True)
st.markdown("Complete cost & pricing models based on truck days and hourly targets.")

# --- FOOTER ---
st.markdown("""
<div class='footer'>Rolling Suds Estimator — Powered by <a href='https://www.rollingsudspowerwashing.com' target='_blank' style='color:#27c7d9;'>rollingsudspowerwashing.com</a></div>
""", unsafe_allow_html=True)



# --- INPUTS ---
st.header("📋 Job & Structure Details")
col1, col2 = st.columns(2)
with col1:
    daily_hours = st.number_input("🕒 Daily Work Hours (per tech)", value=8.0, min_value=0.0)
    mileage = st.number_input("📍 Total Round-Trip Mileage", value=0, min_value=0)
    mileage_rate = st.number_input("💵 Mileage Rate ($/mile)", value=0.65, min_value=0.0)
    avg_speed = st.number_input("🚗 Average Travel Speed (mph)", value=50.0, min_value=10.0, max_value=100.0)
    
    trucks_input = st.number_input("🚚 Number of Trucks", min_value=1, value=1)
    experience = st.selectbox("🧠 Experience Level", ["Novice", "Medium", "Expert"])
    exp_factor_display = {"Novice": 1.2, "Medium": 1.0, "Expert": 0.8}
    st.caption(f"Experience Efficiency Factor: {exp_factor_display[experience]}")

    build_up = st.selectbox("🧱 Build-Up Level", ["Light", "Medium", "Heavy"])
    build_factor_display = {"Light": 1.0, "Medium": 1.5, "Heavy": 2.0}
    st.caption(f"Build-Up Factor: {build_factor_display[build_up]}")
build_factor_display = {"Light": 1.0, "Medium": 1.5, "Heavy": 2.0}
st.caption(f"Build-Up Factor: {build_factor_display[build_up]}")

with col2:
    stories = st.number_input("🏢 Stories", min_value=1, value=2)
    height = st.number_input("📏 Height per Story (ft)", value=10, min_value=0)
    front = st.number_input("📐 Front Wall (ft)", value=100, min_value=0)
    back = st.number_input("📐 Back Wall (ft)", value=100, min_value=0)
    left = st.number_input("📐 Left Wall (ft)", value=50, min_value=0)
    right = st.number_input("📐 Right Wall (ft)", value=50, min_value=0)
    buildings = st.number_input("🏘️ Buildings", min_value=1, value=1)

# --- CLEANING MODE ---
cleaning_mode = st.radio("🧮 Cleaning Time Calculation Mode", ["Parallel (Crew Efficient)", "Linear (Additive)"])

# --- ADD-ONS ---
st.header("🔧 Add-ons (SqFt)")
breezeways = st.number_input("🚪 Breezeways", value=0)
breezeway_rate = st.number_input("⚙️ Breezeway Cleaning Rate (sqft/hr)", value=300.0, min_value=1.0)
flatwork = st.number_input("🧼 Flatwork", value=0)
flatwork_rate = st.number_input("⚙️ Flatwork Cleaning Rate (sqft/hr)", value=400.0, min_value=1.0)

# --- SURFACE TYPE ---
st.header("🧱 Surface Type")
surface_type = st.selectbox("Surface Material", ["Vinyl", "Brick", "Concrete", "Wood", "Stone"])
surface_modifier = {"Vinyl": 1.00, "Brick": 1.10, "Concrete": 1.00, "Wood": 1.05, "Stone": 1.10}[surface_type]

# --- PATIOS & DECKS ---
st.header("🏞️ Decks & Patios")
patio_count = st.number_input("🔢 Total Patio/Deck Units", min_value=0, value=0)
patio_minutes = patio_count * 2
deck_sqft = st.number_input("📏 Total Deck/Patio SqFt", min_value=0, value=0)
deck_material = st.selectbox("🌲 Deck/Patio Material", ["Wood", "Composite"])
deck_rate = 80.0 if deck_material == "Wood" else 100.0

# --- AREA CALC ---
sqft_walls = (front + back + left + right) * stories * height * buildings
total_sqft = sqft_walls + breezeways + flatwork + deck_sqft

# --- CLEANING TIME ---
import math
reference_rate = st.number_input("📏 Reference Wall Cleaning Rate (sqft/min)", value=107.0)
adjusted_wall_sqft = sqft_walls * surface_modifier
build_factor = {"Light": 1.0, "Medium": 1.5, "Heavy": 2.0}[build_up]
exp_factor = {"Novice": 1.2, "Medium": 1.0, "Expert": 0.8}[experience]
wall_minutes = (adjusted_wall_sqft / reference_rate) * build_factor * exp_factor
lift_cost = st.number_input("🛠️ Lift/Drone Cost ($)", min_value=0.0, value=0.0)
lift_slowdown = 0.85 if lift_cost > 0 else 1.0
wall_minutes *= lift_slowdown
primary_clean_hours = wall_minutes / 60
parallel_clean_hours = max(
    (deck_sqft / deck_rate),
    (patio_minutes / 60),
    (breezeways / breezeway_rate),
    (flatwork / flatwork_rate)
)
total_parallelized_clean_time = wall_minutes
clean_minutes = wall_minutes + (deck_sqft / deck_rate) * 60 + patio_minutes
clean_minutes += (breezeways / breezeway_rate) * 60 + (flatwork / flatwork_rate) * 60
if cleaning_mode == "Parallel (Crew Efficient)":
    clean_hours = total_parallelized_clean_time / 60
else:
    clean_hours = clean_minutes / 60

setup_time = {"Novice": 0.33, "Medium": 0.25, "Expert": 0.17}[experience]
breakdown_time = {"Novice": 0.25, "Medium": 0.17, "Expert": 0.08}[experience]


# (moved below once drive_hours is defined)
tech_count = int(trucks_input * 2)
lead_rates = [st.number_input(f"Lead Tech #{i+1} Rate ($/hr)", value=21.0) for i in range(int(trucks_input))]
jr_rates = [st.number_input(f"Junior Tech #{i+1} Rate ($/hr)", value=19.0) for i in range(int(trucks_input))]
blended_rate = (sum(lead_rates) + sum(jr_rates)) / tech_count
if cleaning_mode == "Parallel (Crew Efficient)":
    base_clean = total_parallelized_clean_time / 60
else:
    base_clean = clean_minutes / 60

raw_hours = base_clean + setup_time + breakdown_time
crew_hours_per_day = daily_hours * trucks_input * 2
estimated_days = math.ceil(raw_hours / crew_hours_per_day)

manual_days_toggle = st.checkbox("Manually override day count", value=False)
if manual_days_toggle:
    days = st.number_input("📆 Days to Complete", min_value=1, value=estimated_days, key="override_days_input")
else:
    st.markdown(f"📆 **Estimated Days to Complete:** {estimated_days}")
    days = estimated_days

total_tech_hours = days * daily_hours * tech_count

raw_hours = base_clean + setup_time + breakdown_time
crew_hours_per_day = daily_hours * trucks_input * 2
estimated_days = math.ceil(raw_hours / crew_hours_per_day)

if manual_days_toggle:
    days = st.number_input("📆 Days to Complete", min_value=1, value=estimated_days)
else:
    st.markdown(f"📆 **Estimated Days to Complete:** {estimated_days}")
    days = estimated_days

drive_hours_per_day = mileage / avg_speed
drive_hours = drive_hours_per_day * days

hrs_per_building = clean_hours + setup_time + breakdown_time + drive_hours

drive_hours_per_day = mileage / avg_speed
drive_hours = drive_hours_per_day * days

usable_total_hours = tech_count * days * (daily_hours - (setup_time + breakdown_time + drive_hours_per_day))

drive_labor_cost = blended_rate * drive_hours * tech_count
drive_cost_mileage = mileage * mileage_rate * days
labor_cost = (sum(lead_rates) + sum(jr_rates)) * days * daily_hours + drive_labor_cost + drive_cost_mileage

# --- COST TARGETS ---
st.header("💵 Revenue & Profit Goals")
col3, col4 = st.columns(2)
with col3:
    target_daily = st.number_input("📈 Target Daily Revenue per Truck", value=3000.0)
    fuel_pct = st.number_input("⛽ Fuel % of Final Price", min_value=0.0, max_value=1.0, value=0.04, step=0.01)
    chem_pct = st.number_input("🧪 Chemical % of Final Price", min_value=0.0, max_value=1.0, value=0.05, step=0.01)
with col4:
    target_hourly = st.number_input("💲 Target Hourly Rate", value=250.0)
    mkt_pct = st.number_input("📣 Marketing % of Final Price", min_value=0.0, max_value=1.0, value=0.05, step=0.01)
    royalty_pct = 0.10
comp_adv = st.selectbox("📈 Competitive Advantage %", [0, 5, 10, 15, 20])

# --- MODEL A: Daily Revenue ---
totalA = target_daily * trucks_input * days
fuelA = totalA * (fuel_pct := 0.04)
chemA = totalA * (chem_pct := 0.05)
mktA = totalA * (mkt_pct := 0.05)
royaltyA = totalA * (royalty_pct := 0.10)
costA = labor_cost + fuelA + chemA + mktA + royaltyA
profitA = totalA - costA
marginA = (profitA / totalA) * 100

# --- MODEL B: Hourly Target ---
grossB = usable_total_hours * target_hourly
finalB = grossB * (1 + comp_adv / 100)
fuelB = finalB * (fuel_pct)
chemB = finalB * (chem_pct)
mktB = finalB * (mkt_pct)
costB = labor_cost + fuelB + chemB + mktB
net_profit = finalB - costB
net_margin = (net_profit / finalB) * 100
net_per_day = net_profit / days

# --- SUMMARY ---
st.header("📊 Summary")

usable_daily_hours = daily_hours - (setup_time + breakdown_time + drive_hours_per_day)

st.caption(f"Total Techs: {tech_count} | Blended Rate: ${blended_rate:.2f}/hr | Usable Hrs per Day: {usable_daily_hours:.2f}")
colL, colR = st.columns(2)
with colL:
    st.write(f"Total Walls SqFt: {sqft_walls:,.0f}")
    ...
with colR:
    st.write(f"Cleaning Time (hrs): {clean_hours:.2f}")
    st.write(f"Setup Time: {setup_time:.2f} hrs")
    st.write(f"Breakdown Time: {breakdown_time:.2f} hrs")
    st.write(f"Drive Time: {drive_hours:.2f} hrs")

st.subheader("Model A: Daily Revenue")
st.write(f"Price: ${totalA:,.2f}")
st.write(f"Profit: ${profitA:,.2f}")
st.write(f"Margin: {marginA:.1f}%")
with st.expander("💡 Cost Breakdown - Model A"):
    st.write(f"Labor: ${labor_cost:,.2f}")
    st.write(f"Fuel ({fuel_pct*100:.0f}%): ${fuelA:,.2f}")
    st.write(f"Chemicals ({chem_pct*100:.0f}%): ${chemA:,.2f}")
    st.write(f"Marketing ({mkt_pct*100:.0f}%): ${mktA:,.2f}")
    st.write(f"Royalty ({royalty_pct*100:.0f}%): ${royaltyA:,.2f}")

st.subheader("Model B: Hourly Target")
st.write(f"Final Adjusted Price: ${finalB:,.2f}")
st.write(f"Net Profit: ${net_profit:,.2f}")
st.write(f"Net Margin: {net_margin:.1f}%")
st.write(f"Net Profit per Day: ${net_per_day:,.2f}")
st.write(f"Net Profit per Usable Hour: ${net_profit / usable_total_hours:,.2f}")
with st.expander("💡 Cost Breakdown - Model B"):
    st.write(f"Labor: ${labor_cost:,.2f}")
    st.write(f"Fuel ({fuel_pct*100:.0f}%): ${fuelB:,.2f}")
    st.write(f"Chemicals ({chem_pct*100:.0f}%): ${chemB:,.2f}")
    st.write(f"Marketing ({mkt_pct*100:.0f}%): ${mktB:,.2f}")

# --- CHEMICAL RECOMMENDATIONS ---
st.header("🧪 Recommended Chemicals by Surface")
surface_chemicals = {
    "Vinyl": ["Surfactant + Soft Wash", "OneRestore (spot rust)", "Sodium Hypochlorite 12.5%"],
    "Brick": ["OneRestore", "LCS Graffiti Remover", "Surfactant", "NMD 80 (mortar/efflorescence)"],
    "Concrete": ["Hot Stain Remover", "Degreaser", "Rust Remover (OneRestore)"],
    "Wood": ["Oxygenated Bleach", "Deck Brightener", "Mild Surfactant"],
    "Stone": ["OneRestore", "Pump-Up Acid Wash", "Surfactant"]
}

if surface_type in surface_chemicals:
    st.markdown(f"**Suggested Chemicals for {surface_type}:**")
    for chem in surface_chemicals[surface_type]:
        st.write(f"- {chem}")

chemical_addons = st.multiselect("🧪 Optional Chemical Treatments", [
    "Sodium Hypochlorite (SH) 12.5%",
    "Hot Stain Remover",
    "OneRestore",
    "LCS Graffiti Remover",
    "NMD 80"
])

# --- DILUTION RECOMMENDATION ---
temp = st.slider("🌡️ Estimated Surface Temperature (°F)", 30, 110, 75)
if temp >= 95:
    dilution = "75% water / 25% chem"
elif temp >= 75:
    dilution = "50% water / 50% chem"
elif temp >= 60:
    dilution = "25% water / 75% chem"
else:
    dilution = "15% water / 85% chem"

if chemical_addons:
    st.markdown(f"**Recommended Dilution Based on {temp}°F:** {dilution}")

# --- JOB TYPE TIPS ---
st.header("🗂️ Job Type Guidance")
job_type = st.selectbox("🏢 Select Property Type", [
    "Apartment Complex",
    "Casino",
    "Retail Strip Mall",
    "Office Building",
    "HOA Community",
    "Parking Garage"
])

if job_type == "Apartment Complex":
    st.info("Ask about balconies, patios, and breezeways. Confirm unit counts and material type. Offer per-building or phased pricing.")
elif job_type == "Casino":
    st.warning("Plan for overnight work or low-traffic hours. Emphasize degreasing, rust, and window rinse services.")
elif job_type == "Retail Strip Mall":
    st.info("Focus on storefront consistency, rust removal under signage, and sidewalk pressure washing.")
elif job_type == "Office Building":
    st.info("Mention awnings, entry glass, and drive lanes. For chains, request contact for regional manager.")
elif job_type == "HOA Community":
    st.success("Provide options for common areas and resident notices. Offer bundling incentives for multiple buildings.")
elif job_type == "Parking Garage":
    st.warning("Be clear about stain removal limits. Quote for rinse-downs and dust control, not deep degreasing.")

# --- CHECKLIST ---
st.header("📋 On-Site Checklist & Scope Notes")
st.checkbox("✅ Water source on-site?")
st.checkbox("✅ Detailed scope confirmed?")
st.checkbox("✅ Before photos taken?")
st.checkbox("✅ Has this been cleaned before?")
st.checkbox("✅ Client budget known?")
st.checkbox("✅ Other quotes received?")
st.text_area("📝 Additional Scope Notes", height=150)

# --- EXPORT ---
st.header("📤 Export & Reporting")
customer_name = st.text_input("👤 Customer/Job Name")

export_data = {
    "Date": [datetime.date.today().isoformat()],
    "Customer": [customer_name],
    "Total SqFt": [total_sqft],
    "Wall SqFt": [sqft_walls],
    "Deck SqFt": [deck_sqft],
    "Total Hours": [clean_hours + setup_time + breakdown_time + drive_hours],
    "Labor Cost": [labor_cost],
    "Model A Price": [totalA],
    "Model A Profit": [profitA],
    "Model A Margin": [marginA],
    "Model B Price": [finalB],
    "Model B Net Profit": [net_profit],
    "Model B Net Margin": [net_margin]
}

export_df = pd.DataFrame(export_data)
csv_buffer = io.StringIO()
export_df.to_csv(csv_buffer, index=False)

st.download_button(
    label="⬇️ Download Estimate as CSV",
    data=csv_buffer.getvalue(),
    file_name=f"{customer_name or 'rolling_suds'}_estimate.csv",
    mime="text/csv"
)

# PDF EXPORT
pdf = FPDF()
pdf.add_page()

logo_path = "rolling_suds_logo.png"
if os.path.exists(logo_path):
    pdf.image(logo_path, x=10, y=8, w=60)
    pdf.ln(25)

pdf.set_font("Arial", size=12)
pdf.cell(200, 10, txt="Rolling Suds Estimate", ln=1, align='C')
pdf.ln(5)