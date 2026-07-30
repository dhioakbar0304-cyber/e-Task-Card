import streamlit as st
import pandas as pd
from datetime import datetime
import time
import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
)

# ============================================================================
# 1. PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="GMF AeroAsia - Digital Task Card",
    page_icon="🛠️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

STATUS_OPTIONS = ["⚠️ Not Inspected", "✅ PASS", "❌ FAIL", "➖ N/A"]
CLEAN_STATUS_OPTIONS = ["⚠️ Not Completed", "✅ Completed", "➖ N/A"]

# Certifying staff directory — in production this should be pulled from GMF's
# licensing / HR system (e.g. AMOS crew database), never hard-coded like this.
CERTIFYING_STAFF_DB = {
    "1234": {"name": "Ahmad Fadli", "license_no": "AMEL A320/B737-2201-INA",
             "rating": "Airframe & Powerplant - A320 / B737", "auth_no": "GMF-CRS-002201"},
    "5678": {"name": "Budi Santoso", "license_no": "AMEL A320/B737-1187-INA",
             "rating": "Airframe & Powerplant - A320 / B737", "auth_no": "GMF-CRS-001187"},
}

OPERATORS = ["Citilink Indonesia", "Garuda Indonesia", "Batik Air", "Other / Third-Party Customer"]

# ============================================================================
# 2. CHECKLIST ITEM BUILDERS
# ============================================================================
def ck(code, skill, desc, status_options=None):
    return {"kind": "check", "code": code, "skill": skill, "desc": desc,
            "status_options": status_options or STATUS_OPTIONS}

def nt(text):
    return {"kind": "note", "text": text}

def wn(text):
    return {"kind": "warning", "text": text}

def tbl(code, skill, label, columns, rows, required_rows=None, unit_note=""):
    return {"kind": "table", "code": code, "skill": skill, "label": label,
            "columns": columns, "rows": rows,
            "required_rows": required_rows or [rows[0]], "unit_note": unit_note}

def meas(code, skill, label, unit=""):
    return {"kind": "measurement", "code": code, "skill": skill, "label": label, "unit": unit}

def find(code, skill, label, criteria=None):
    return {"kind": "finding", "code": code, "skill": skill, "label": label, "criteria": criteria}

# ============================================================================
# 3. DIGITAL TASK CARD LIBRARY
#    Modeled on GMF AeroAsia / operator maintenance task card structure
#    (task card no., ATA reference, skill code, AMM cross-reference).
# ============================================================================
JOB_CARDS = {

    # ------------------------------------------------------------------ #
    "A320 Weekly Check": {
        "meta": {
            "Work Order No.": "GMF-WO-2026-071842", "Crew": "1", "Down Time": "4 hrs",
            "A/C Registration": "PK-GLV", "Event / Interval": "Weekly (WY)",
            "Task Card No.": "CT-2-01/A2-04", "A/C Type": "A320", "Operator": "Citilink Indonesia",
            "Station": "CGK", "Skill": "AP/EA",
            "ATA Reference": "05-20 / 11.02.04", "Planned Man-hours": "8.0",
        },
        "mode": "checklist",
        "sections": [
            {"no": 1, "title": "Arrival", "icon": "plane", "items": [
                ck("ARR-01", "SPC", "Prepare the parking bay and ground equipment 5 minutes prior to aircraft arrival; ensure the area is clean."),
                ck("ARR-02", "SPC", "Connect ground-to-cockpit interphone; confirm wheel chocks are installed."),
                ck("ARR-03", "SPC", "Connect the Ground Power Unit after 15 minutes of APU operation (if required and available); confirm all circuit breakers are closed."),
                wn("Pitot probe covers and static port covers are recommended whenever the aircraft is parked longer than a standard turnaround, or when dust, insect activity, or volcanic ash increases the risk of probe/port contamination."),
                ck("ARR-04", "SPC", "Install landing-gear lock pins and pitot/static covers if ground time will exceed 4 hours."),
                ck("ARR-05", "SPC", "Review AML/CML entries with the flight crew and carry out corrective action as required."),
                ck("ARR-06", "SPC", "Set the parking brake to OFF."),
                ck("ARR-07", "SPC", "Perform the ADIRS stop procedure (ref. AMM 34-10-00-860-005-A)."),
                ck("ARR-08", "SPC", "Confirm the cockpit and cabin emergency light switches are OFF."),
            ]},
            {"no": 2, "title": "Engine", "icon": "flame", "items": [
                nt("Applicable to Engine 1 and Engine 2."),
                ck("ENG-01", "VCK", "Check the engine forward acoustic panel condition (ref. AMM 72-23-00-280-005-A); if a fastener is loose, retorque to 126.35-139.65 lbf.in (ref. AMM 72-23-00-400-009)."),
                ck("ENG-02", "VCK", "Check engine oil level at the tank, 5-60 minutes after engine shutdown."),
            ]},
            {"no": 3, "title": "Engine Oil Service", "icon": "flame", "items": [
                wn("If the engine has been stopped for more than 1 hour, perform an idle run before servicing to prevent over-servicing."),
                ck("EOS-E1", "SVC", "Engine 1 - service oil if required (ref. AMM 12-13-79-610). Refill to the FULL mark, perform a sniff check, inspect cap and seal, and record any addition in the AML."),
                ck("EOS-E2", "SVC", "Engine 2 - service oil if required, same procedure as Engine 1."),
                nt("If oil consumption is abnormally high or fuel contamination is suspected, initiate further investigation."),
            ]},
            {"no": 4, "title": "Fuselage", "icon": "layers", "items": [
                ck("FUS-01", "GVI", "Check radome condition (ref. AMM 53-15-11-200-001)."),
                ck("FUS-02", "GVI", "Check cockpit window for obvious damage and security (ref. AMM 56-10-00-200-005)."),
                ck("FUS-03", "GVI", "Check crew oxygen discharge indicator disc (green) - intact."),
                ck("FUS-04", "GVI", "Check static port, pitot & TAT probe, and Angle-of-Attack sensor for damage and security."),
                ck("FUS-05", "GVI", "Check the fuselage skin condition in the vicinity of the static source (RVSM requirement)."),
                ck("FUS-06", "GVI", "Check communication/navigation antennas for condition and security, including surrounding skin."),
                ck("FUS-07", "GVI", "Check LH/RH air-conditioning ram-air inlet and exhaust for obstruction (FOD)."),
                ck("FUS-08", "GVI", "Check pressure relief valve and outflow valve for condition and obstruction."),
                ck("FUS-09", "GVI", "Check fastener/screw completeness on the fuselage."),
                ck("FUS-10", "GVI", "Check belly fairing seal for damage and security."),
                find("FUS-11", "GVI", "Fuselage section findings"),
            ]},
            {"no": 5, "title": "Placard and Marking - Fuselage", "icon": "layers", "items": [
                ck("PLM-01", "GVI", "Static port painted markings - general condition (ref. AMM Fig. 11-00-00-17000-A)."),
                ck("PLM-02", "GVI", "Angle-of-Attack sensor painted markings - general condition (ref. AMM Fig. 11-00-00-18000-A)."),
                ck("PLM-03", "GVI", "Ram Air Turbine painted markings - general condition (ref. AMM Fig. 11-00-00-15000-A)."),
                ck("PLM-04", "GVI", "Passenger door operation and warning painted markings - general condition."),
                nt("If any placard or painted marking is partially missing, unreadable, or unclear, report to MCC and take corrective action immediately."),
            ]},
            {"no": 6, "title": "Fwd, Aft and Bulk Cargo Compartments", "icon": "cone", "items": [
                ck("CGO-01", "GVI", "Check all cargo door seal conditions before closing; rectify any defect found (ref. AMM Fig. 52-31-18-991-00100-C)."),
                ck("CGO-02", "GVI", "Check fly-away kit availability and security."),
                ck("CGO-03", "GVI", "Check cargo door operation and warning painted markings - general condition."),
                ck("CGO-04", "GVI", "Visual check of the cargo compartment (MP 2550002004) - decompression, lining, floor panels, and pressure compensation valve (as far as visible) for damage, tears, punctures, and cleanliness."),
            ]},
            {"no": 7, "title": "Landing Gear & Wheel Well - General Inspection", "icon": "wheel", "items": [
                ck("LG-01", "GVI", "Check nose and main gear wheel-well door seals and components for abnormalities."),
                ck("LG-02", "GVI", "General visual inspection of L/G brake units for hydraulic leaks (ref. AMM 32-40-00-210-801)."),
                ck("LG-03", "FNC", "Check hydraulic reservoir/system pressure indication and accumulator charge pressure (ref. AMM 29-30-00-200-001/002, 29-10-00-200-008, 32-44-11-200-001) - record readings in the table below."),
            ]},
            {"no": 8, "title": "Landing Gear - Hydraulic Accumulator Reading", "icon": "wheel", "items": [
                tbl("LG-ACC", "FNC", "Accumulator Pressure & Temperature (psi / degC)",
                    columns=["G Hyd - Pressure", "G Hyd - Temp", "B Hyd - Pressure", "B Hyd - Temp",
                             "Y Hyd - Pressure", "Y Hyd - Temp", "Brake Acc - Pressure", "Brake Acc - Temp"],
                    rows=["Before", "After"], required_rows=["Before"]),
                ck("LG-04", "GVI", "Check NLG and MLG shock struts for leaks; wipe exposed surfaces with a cloth moistened with MIL-PRF-5606 hydraulic fluid, then dry."),
                ck("LG-05", "GVI", "Confirm the RAT is in the stowed position with doors closed."),
            ]},
            {"no": 9, "title": "Landing Gear - Brake Wear Pin", "icon": "wheel", "items": [
                ck("LG-06", "FNC", "Functional check of the brake heat-pack wear indicator (MP 3242272000, ref. AMM 32-42-27-210-003, parking brake applied) - record the pin length in the table below."),
                tbl("LG-PIN", "FNC", "Brake Wear Pin Length (mm)",
                    columns=["LH MLG - Pin 1", "LH MLG - Pin 2", "RH MLG - Pin 3", "RH MLG - Pin 4"],
                    rows=["Pin Length (mm)"], required_rows=["Pin Length (mm)"]),
                ck("LG-07", "LUB", "Lubricate the MLG main-fitting lower bearing gland housing (ref. AMM 12-22-32-640-001)."),
            ]},
            {"no": 10, "title": "Landing Gear - Tire Pressure", "icon": "wheel", "items": [
                ck("LG-08", "FNC", "Inspect/check tire pressure (MP 3241002003, ref. AMM 324100-210-003). Inflate with nitrogen only (AD 87-08-09). Record pressure before and after recharging in the table below; readings are for loaded tires (aircraft weight on wheels)."),
                tbl("LG-TIRE", "FNC", "Tire Pressure (psi) - Before / After Inflation",
                    columns=["NLG - LH", "NLG - RH", "MLG - 1", "MLG - 2", "MLG - 3", "MLG - 4"],
                    rows=["Before Inflation", "After Inflation"], required_rows=["Before Inflation"],
                    unit_note="Normal range reference (loaded): NLG 178-187 psi, MLG 209-219 psi."),
            ]},
            {"no": 11, "title": "Placard and Marking - Nose Gear", "icon": "wheel", "items": [
                ck("PLN-01", "GVI", "Nose gear leg door painted markings - general condition (ref. AMM Fig. 11-00-16000-A)."),
                ck("PLN-02", "GVI", "\"Inflate with Nitrogen Only\" and \"Tyre Press on Wheel\" markings on main/nose L/G (AD 87-08-09) - general condition."),
                ck("PLN-03", "GVI", "\"Max Tow Bar Angle\" red-line marking on the nose - general condition."),
            ]},
            {"no": 12, "title": "LH / RH Wing", "icon": "layers", "items": [
                ck("WNG-01", "GVI", "Wing upper surface - general condition (panels, flight control surfaces faired, engine pylon panels & fairing, vortex generators), viewed from the cabin window."),
                ck("WNG-02", "GVI", "Check fastener/screw completeness (upper surface)."),
                ck("WNG-03", "GVI", "Check wing fairing seal for damage and security."),
                ck("WNG-04", "GVI", "Wing lower surface - general condition (flight control surfaces, tank vents, leading/trailing edge, fuel leakage and static discharge seals)."),
                ck("WNG-05", "GVI", "Wing-to-body fairing and seals - damage and correct installation."),
                ck("WNG-06", "GVI", "Check fastener/screw completeness (lower surface)."),
            ]},
            {"no": 13, "title": "Placard and Marking - Wing", "icon": "layers", "items": [
                ck("PLW-01", "GVI", "Wing painted markings - general condition (ref. AMM Fig. 11-00-00-19000-A)."),
                ck("PLW-02", "GVI", "Escape area painted markings - general condition (ref. AMM Fig. 11-00-00-19100-A)."),
            ]},
            {"no": 14, "title": "LH / RH Engine", "icon": "flame", "items": [
                ck("ENG2-01", "GVI", "Engine air intake and fan blades - free rotation, check for FOD (ref. AMM 72-00-00-200)."),
                ck("ENG2-02", "DET", "Check abradable shroud, outer guide vanes, inner fan case, frame and frame strut."),
            ]},
            {"no": 15, "title": "LH / RH Engine - Outlet Guide Vane Finding", "icon": "flame", "items": [
                find("ENG2-03", "DET", "Outlet Guide Vane condition - describe any finding against the criteria below",
                     criteria=[
                        {"Criteria Set A": "Broken vane", "Criteria Set B": "Eroded surface (glass film)"},
                        {"Criteria Set A": "Missing vane", "Criteria Set B": "Unbonding of metal leading edge"},
                        {"Criteria Set A": "Cracks", "Criteria Set B": "Metal leading edge missing"},
                        {"Criteria Set A": "Missing material", "Criteria Set B": "Outer/inner platform debonding"},
                        {"Criteria Set A": "Delamination", "Criteria Set B": "Nicks/dents on leading & trailing edge, concave/convex side, inner/outer platform"},
                     ]),
                nt("If a finding is confirmed, perform a damage assessment per AMM 72-23-00-210-003-C (CFM56-5B). If within serviceable limits, record on the ASDCS sheet and inform MCC and Planning."),
            ]},
            {"no": 16, "title": "LH / RH Engine - Cowling & Fan Cowl", "icon": "flame", "items": [
                ck("ENG2-04", "GVI", "Engine cowling, including access panels and latches - secure."),
                ck("ENG2-05", "GVI", "Thrust reverser, exhaust tail plug, exhaust tail case strut, turbine blades - condition."),
                ck("ENG2-06", "GVI", "Perform external zonal inspection of the engine and pylon fairing."),
                ck("ENG2-07", "GVI", "Check for fluid leakage on the underside of the cowlings."),
                ck("ENG2-08", "GVI", "Open the engine fan cowl and inspect the starter for oil leakage; refill if necessary."),
                ck("ENG2-09", "DET", "Inspect the TGB housing area for oil trace using UV light. If any trace is found, perform AMM Task 79-00-00-210-003-A."),
            ]},
            {"no": 17, "title": "Placard and Marking - Fan Cowl", "icon": "flame", "items": [
                ck("PLF-01", "GVI", "Check Extinguisher 1 & 2 placards/markings on the pylon area."),
                ck("PLF-02", "GVI", "Check hazard-area, WARNING/CAUTION, and access-name placards on the fan cowl."),
            ]},
            {"no": 18, "title": "IDG Oil", "icon": "flame", "items": [
                nt("Applicable to Engine 1 and Engine 2 (MP 2421002102, 2421512010, 2421002000)."),
                ck("IDG-E1", "SVC", "Engine 1 - check IDG oil level and oil-filter differential pressure indicator; service if below the green band, above the yellow band, or if the red button is extended."),
                ck("IDG-E2", "SVC", "Engine 2 - same procedure as Engine 1."),
                wn("The IDG overflow-drain procedure can take up to 20 minutes to complete. Failing to observe this time may result in high IDG oil level and elevated operating temperature, damaging the IDG."),
            ]},
            {"no": 19, "title": "Empennage, APU Area and Stabilizers", "icon": "layers", "items": [
                ck("EMP-01", "GVI", "Check rear fuselage and APU area; drain if fluid leakage is present (ref. AMM 28-22-00-790-002)."),
                ck("EMP-02", "GVI", "Check APU inlet and exhaust for obvious damage."),
                ck("EMP-03", "GVI", "Check toilet, water & waste service panel for condition/leakage; safety plug present on fill/flush lines."),
                ck("EMP-04", "GVI", "Visual check from ground level - vertical fin/rudder, horizontal stabilizer/elevator, static discharge - for obvious damage or missing parts."),
                ck("EMP-05", "GVI", "Check fastener/screw completeness."),
                ck("EMP-06", "VCK", "Check APU oil level on the sight glass; replenish if required (ref. Task 12-13-49-612-001)."),
            ]},
            {"no": 20, "title": "Cabin", "icon": "users", "items": [
                wn("When opening a passenger door: ensure the door is disarmed and cross-checked. Stop the opening procedure immediately if the red warning light flashes - residual pressure could injure personnel and/or damage the aircraft."),
                ck("CAB-01", "GVI", "Check pressure of the passenger/crew door emergency cylinder/accumulator (MP 5210002101); recharge if incorrect (ref. AMM 52-10-00-614-001)."),
                ck("CAB-02", "GVI", "Cabin carpet, floor covering, and galley - general condition and cleanliness."),
                ck("CAB-03", "GVI", "Attendant seat covers and harness - damage and cleanliness."),
                ck("CAB-04", "GVI", "Passenger seat: covers, armrest, tray table, ashtray, seat belt, backrest - condition and cleanliness."),
                ck("CAB-05", "GVI", "Interior: sidewalls, ceiling panels, stowage bins, partitions, dado panel - damage and cleanliness."),
                ck("CAB-06", "GVI", "Confirm potable water and toilet waste tanks are serviced."),
                ck("CAB-07", "GVI", "Emergency equipment - check per the attached Emergency Equipment Checklist (EEL)."),
                ck("CAB-08", "GVI", "Lavatories - damage and cleanliness; test flush system and water system."),
            ]},
            {"no": 21, "title": "Placard and Marking - Cabin", "icon": "users", "items": [
                ck("PLC-01", "GVI", "Check cabin placards and markings - general condition."),
            ]},
            {"no": 22, "title": "Cockpit", "icon": "id", "items": [
                ck("CKP-01", "GVI", "Confirm all circuit breakers are closed."),
                ck("CKP-02", "GVI", "Cockpit - general condition and cleanliness."),
                ck("CKP-03", "GVI", "Windows, windshield, wiper blades; emergency exit handles - secured."),
                ck("CKP-04", "GVI", "Captain/FO/observer seats and harnesses - condition and security (ref. AMM 25-11-00-200-002; replace harness if necessary)."),
                ck("CKP-05", "OPC", "Check and test aircraft communications equipment - complete."),
                ck("CKP-06", "GVI", "All instrument panels and display units - cleanliness."),
                ck("CKP-07", "GVI", "IDG disconnect switches - normal (guarded/wired)."),
                ck("CKP-08", "GVI", "Check the Navigation Database (NDB) for expiry date."),
                ck("CKP-09", "GVI", "Hydraulic brake accumulator pre-charge pressure."),
                ck("CKP-10", "GVI", "Aircraft status on the upper/lower ECAM display - carry out corrective action as required."),
                ck("CKP-11", "GVI", "Check hydraulic fluid level via MCDU; refill as required and record in the AML (ref. AMM 29-10-00-200-001)."),
                ck("CKP-12", "SPC", "Review the PFR printout and take action as necessary."),
            ]},
            {"no": 23, "title": "Cockpit - Crew Oxygen", "icon": "id", "items": [
                meas("CKP-OXY", "GVI", "Record the crew oxygen bottle pressure (psi) - ref. FCOM A320/CT LIM-35 Oxygen for minimum dispatch pressure.", unit="psi"),
                nt("Minimum oxygen pressure reference tables vary by ambient temperature and crew/observer count, per aircraft MSN group - see FCOM LIM-35 pages 1-4."),
                ck("CKP-13", "GVI", "Check printer paper availability; replace as necessary."),
                ck("CKP-14", "GVI", "Confirm all aircraft documents are in place and valid per Form CT-1-23."),
                ck("CKP-15", "GVI", "Emergency equipment - check condition, function, and validity per the EEL."),
            ]},
            {"no": 24, "title": "Operational Checks", "icon": "radio", "items": [
                ck("OP-01", "OPC", "Operational check of the engine fire detection loop/squib (ref. AMM 26-12-00-710-001-A)."),
                ck("OP-02", "OPC", "Operational test of the APU fire and overheat detection system (ref. AMM 26-13-00-710-001-A)."),
                ck("OP-03", "OPC", "Check flight-deck lighting, including annunciator lights."),
                ck("OP-04", "OPC", "Check all exterior lights (runway turn-off, taxi, wing illumination, landing, anti-collision, position, strobe, logo) for illumination, beam, and damage."),
            ]},
            {"no": 25, "title": "CVR / DFDR", "icon": "radio", "items": [
                ck("CVR-01", "OPC", "Operational test of the Cockpit Voice Recorder - CVR (ref. AMM 23-71-00-710-001)."),
                ck("DFDR-01", "OPC", "Operational check of the DFDR system via MCDU (ref. AMM 31-33-00-710-006-A)."),
            ]},
            {"no": 26, "title": "Emergency Lights & AC Emergency Generation", "icon": "radio", "items": [
                ck("EML-01", "OPC", "Operational test of emergency lights (MP 3351007101). Press and hold the TEST EMER LIGHT/SYS switch for at least 3 seconds; SYS OK illuminates for approx. 30 s, then extinguishes after approx. 60 s."),
                wn("Before testing AC Emergency Generation: ensure flight control surface travel ranges are clear before pressurizing/depressurizing the hydraulic system."),
                ck("ACE-01", "OPC", "Operational test of the AC Emergency Generation System (MP 2424007001/2424007101, ref. AMM 242400-710-001) - pressurize the blue hydraulic system with the electric pump, press EMER GEN TEST P/B, verify the ECAM AC page, release and depressurize."),
            ]},
            {"no": 27, "title": "Fuel for Water Contamination", "icon": "droplet", "items": [
                ck("FWC-01", "SVC", "Drain water content from the main and center tanks (MP 1232282811, ref. AMM 123228-281-001) before flight/refuel, or a minimum of 1 hour afterward. Use the correct tool to open the water drain valve. Drain approximately 1.0 L until no water and no fuel leaks remain."),
            ]},
            {"no": 28, "title": "Final Work", "icon": "check", "items": [
                ck("FIN-01", "GVI", "Check for additional requested service (water disinfection, special inspection, TLW, etc.)."),
                ck("FIN-02", "GVI", "Check that all pilot reports, inspection findings, and open items (HIL) have been actioned; entries recorded in AML/CML."),
                ck("FIN-03", "GVI", "Confirm the aircraft is clear of ground equipment."),
                ck("FIN-04", "SPC", "De-energize electrical power; close and secure all doors and access panels."),
            ]},
        ],
    },

    # ------------------------------------------------------------------ #
    "Cabin Standard Check (24H)": {
        "meta": {
            "Work Order No.": "GMF-WO-2026-071901", "Crew": "1", "Down Time": "-",
            "A/C Registration": "PK-GLV", "Event / Interval": "24 Hours",
            "Task Card No.": "CT-2-01/A2-09", "A/C Type": "All", "Operator": "Citilink Indonesia",
            "Station": "CGK", "Skill": "Cabin",
            "ATA Reference": "12.02.01", "Planned Man-hours": "-",
        },
        "mode": "checklist",
        "sections": [
            {"no": 1, "title": "Open Items Review", "icon": "clipboard", "items": [
                nt("Where possible, perform this task card after cabin interior cleaning is complete."),
                ck("OPN-01", "SPC", "Check the Cabin Maintenance Log Book (CML) for open items."),
            ]},
            {"no": 2, "title": "Cabin - Floor", "icon": "layers", "items": [
                ck("FLR-01", "GVI", "Carpet throughout the cabin - obvious damage and condition."),
                ck("FLR-02", "GVI", "Floor covering in the entry area - obvious damage and contamination."),
            ]},
            {"no": 3, "title": "Cabin - Galleys", "icon": "layers", "items": [
                ck("GAL-01", "GVI", "Galley - general condition, obvious damage, contamination."),
                ck("GAL-02", "GVI", "Floor covering in the galley - obvious damage and contamination."),
            ]},
            {"no": 4, "title": "Cabin - Coatroom", "icon": "layers", "items": [
                ck("COT-01", "GVI", "Coatroom - obvious damage."),
            ]},
            {"no": 5, "title": "Cabin - Seats", "icon": "users", "items": [
                ck("SEA-01", "VCK", "Seats and seat covers - obvious damage and contamination."),
                ck("SEA-02", "VCK", "Seat backs for vertical position; ashtrays and seat belts - presence and condition (ref. AMM 25-21-00-210-001; replace if necessary)."),
                ck("SEA-03", "GVI", "F/C seat covers - correct fit."),
                ck("SEA-04", "OPC", "Attendant seats - function and condition (ref. AMM 25-22-00-210-001; replace harness if necessary)."),
            ]},
            {"no": 6, "title": "Cabin - Interior", "icon": "layers", "items": [
                ck("INT-01", "GVI", "Sidewall and ceiling panels, bins, partitions and curtains - obvious damage and contamination."),
                ck("INT-02", "GVI", "Ceiling panel - proper installation."),
                ck("INT-03", "GVI", "Dado panel - general condition."),
            ]},
            {"no": 7, "title": "Cabin - Lavatories", "icon": "layers", "items": [
                ck("LAV-01", "VCK", "Lavatories - obvious damage and contamination."),
                ck("LAV-02", "OPC", "Operate the lavatory flushing system and confirm proper flushing."),
            ]},
            {"no": 8, "title": "Final Work", "icon": "check", "items": [
                ck("FNW-01", "GVI", "If additional deficiencies are found during the check, initiate corrective action; record in the CML as \"Cabin Standard Check Performed\". Log any unrectified findings in the HIL."),
            ]},
        ],
    },

    # ------------------------------------------------------------------ #
    "Daily Interior Cleaning": {
        "meta": {
            "Work Order No.": "GMF-WO-2026-071955", "Crew": "9", "Down Time": "-",
            "A/C Registration": "PK-GLV", "Event / Interval": "Interior Cleaning",
            "Task Card No.": "CT-2-01/A2-10", "A/C Type": "All", "Operator": "Citilink Indonesia",
            "Station": "CGK", "Skill": "Cabin",
            "ATA Reference": "14.02.98", "Planned Man-hours": "A320: 13.5 / B737: 9.0",
        },
        "mode": "checklist",
        "sections": [
            {"no": 1, "title": "Cockpit", "icon": "id", "items": [
                ck("CLN-01", "CLN",
                   "Windows (clean with wet leather) - Ashtray & waste box (empty and clean) - "
                   "Seat covers (brush or vacuum) - Floor (wet cleaning and vacuum carpet).",
                   status_options=CLEAN_STATUS_OPTIONS),
            ]},
            {"no": 2, "title": "Entry Areas", "icon": "door", "items": [
                ck("CLN-02", "CLN",
                   "Sidewalls, ceiling panels, doors and door frames at attendant stations (clean with appropriate solution, wipe dry) - "
                   "Attendant seat covers (brush or vacuum) - Floors (wet cleaning, wipe dry).",
                   status_options=CLEAN_STATUS_OPTIONS),
            ]},
            {"no": 3, "title": "Galleys", "icon": "layers", "items": [
                ck("CLN-03", "CLN",
                   "Galley, ceiling, control panels, working area (clean with appropriate solution, wipe dry) - Waste containers (empty, clean, deodorize) - "
                   "Ovens & coffee maker (clean with damp cloth without chemicals, polish oven door if necessary) - Grills (clean, wipe dry) - "
                   "Sinks (clean, wipe dry) - Floor if necessary (wet cleaning) - Mirrors (clean, wipe dry).",
                   status_options=CLEAN_STATUS_OPTIONS),
            ]},
            {"no": 4, "title": "Cabin", "icon": "layers", "items": [
                ck("CLN-04", "CLN",
                   "Sidewall, dado, and ceiling panels, stowage bins, window shades, coat stowage, bar and partitions (clean, wipe dry) - "
                   "Cabin window inner pane & TV monitor screens (clean, wipe dry) - Carpet floor (vacuum) - Window shades (upright position).",
                   status_options=CLEAN_STATUS_OPTIONS),
            ]},
            {"no": 5, "title": "Cabin Seats", "icon": "users", "items": [
                ck("CLN-05", "CLN",
                   "Seat pockets (empty and clean) - Seat covers (brush or vacuum) - Seat fairings & armrests (clean, wipe dry) - "
                   "Food tables, upper and lower (clean, wipe dry) - Ashtrays (empty, clean, close cover) - "
                   "Seat backrests (upright position) - Seat belts (clean, present, buckled).",
                   status_options=CLEAN_STATUS_OPTIONS),
            ]},
            {"no": 6, "title": "Lavatories", "icon": "layers", "items": [
                ck("CLN-06", "CLN",
                   "Sidewalls, ceiling panels, doors and door frames (clean, wipe dry) - Wash basins (clean and polish) - "
                   "Mirrors (clean, wipe dry) - Ashtrays (empty, clean, close cover) - Waste containers (empty, clean, deodorize) - "
                   "Lavatory seat assembly (clean, wipe dry) - Lavatory bowls (clean per surface type) - Floors (wet cleaning, wipe dry).",
                   status_options=CLEAN_STATUS_OPTIONS),
            ]},
            {"no": 7, "title": "Cargo Compartment", "icon": "cone", "items": [
                ck("CLN-07", "CLN",
                   "Forward and aft cargo compartments (vacuum and wet cleaning) - Ceiling panels (wet cleaning) - "
                   "Sidewall panels, B737 only (wet cleaning) - Cargo nets (installed).",
                   status_options=CLEAN_STATUS_OPTIONS),
            ]},
            {"no": 8, "title": "Final Work", "icon": "check", "items": [
                ck("CLN-08", "CLN",
                   "Mechanic supervisor to review daily interior cleaning results; record in the CML as \"Daily Interior Cleaning Performed\".",
                   status_options=CLEAN_STATUS_OPTIONS),
            ]},
        ],
    },

    # ------------------------------------------------------------------ #
    "Emergency Equipment Checklist": {
        "meta": {
            "Work Order No.": "GMF-WO-2026-072004", "Crew": "-", "Down Time": "-",
            "A/C Registration": "PK-GLV", "Event / Interval": "Per Effectivity",
            "Task Card No.": "Attachment CT-2-01", "A/C Type": "A320", "Operator": "Citilink Indonesia",
            "Station": "CGK", "Skill": "Cabin / AP-EA",
            "ATA Reference": "25-60 / 25-65 / 25-66", "Planned Man-hours": "-",
        },
        "mode": "equipment_log",
        "sections": [
            {"no": 1, "title": "Page 1 of 3 - Evacuation & Rescue Equipment", "icon": "shield", "rows": [
                ("Crash Axe", "Check for availability and good condition (ref. AMM 25-65-00)"),
                ("Crew Life Vest", "Check for validity, quantity, and sealed protective package (ref. AMM 25-66-00)"),
                ("Portable ELT", "Check for validity / date"),
                ("Fixed ELT", "Check for validity / date"),
                ("Escape Path with Rope (Cockpit)", "Check for availability and condition"),
                ("Escape Slide/Raft (Passenger Wing & Door)", "Check for validity and pressure / green band (ref. AMM 25-62-00)"),
                ("Overwing Escape Slide Container", "Check condition for cracks and delamination (ref. AMM 25-62-42)"),
                ("Exit Path with Escape Slide", "Operational test (ref. AMM 25-63-00)"),
                ("Fire Extinguisher BCF", "Check for validity and pressure / green band (ref. AMM 26-24-00)"),
                ("Fire Extinguisher Water", "Check for validity, pressure / green band, and quantity (ref. AMM 26-24-00)"),
                ("First Aid Kit", "Check for validity, quantity, and sealed protective package"),
            ]},
            {"no": 2, "title": "Page 2 of 3 - Personal Protection Equipment", "icon": "shield", "rows": [
                ("Flashlight", "Check for functional charging cycle and quantity"),
                ("Heat Resistant Gloves", "Check for condition, quantity, and sealed protective package"),
                ("Infant Belt", "Check for good condition, quantity, and sealed protective package"),
                ("Lavatory Fire Extinguisher", "Check for validity/date and temperature indicator (ref. AMM 26-25-00)"),
                ("Additional Life Raft (if installed)", "Check for validity/date and pressure / green band"),
                ("Megaphone", "Check for quantity and operational test (ref. AMM 25-65-51)"),
                ("Pax Life Vest", "Check for validity, quantity, and sealed protective package (ref. AMM 25-66-00)"),
                ("Infant Life Vest", "Check for validity, quantity, and sealed protective package (ref. AMM 25-66-00)"),
                ("PBE / Smoke Hood with Oxygen", "Check for validity, quantity, and sealed protective package"),
                ("Portable Oxygen Bottle & Mask", "Check for validity, quantity, and pressure / green band (ref. AMM 35-30-00)"),
                ("Demo Kit - Safety Belt", "Check for condition and quantity"),
            ]},
            {"no": 3, "title": "Page 3 of 3 - Demo Kit & Medical Equipment", "icon": "shield", "rows": [
                ("Demo Kit - Life Vest", "Check for condition, quantity, and sealed protective package"),
                ("Demo Kit - Oxygen Mask", "Check for condition, quantity, and sealed protective package"),
                ("Life Vest (spare)", "Check for condition, quantity, and sealed protective package"),
                ("Life Line", "Check for condition and quantity"),
                ("Survival Kit (if available)", "Check for condition, quantity, and sealed protective package"),
                ("Emergency Medical Kit", "Check for condition and sealed protective package"),
                ("Extension Belt", "Check for condition and quantity"),
                ("Manual Release Tool", "Check for condition and quantity"),
            ]},
        ],
    },
}

STEP_LABELS = ["Work Order", "Inspection", "Authorization", "Complete"]

# ============================================================================
# 4. ICON SYSTEM
# ============================================================================
def icon(name, size=18, color="currentColor", stroke=1.8):
    paths = {
        "plane": '<path d="M2.5 16l19-6.5-2-2-7 2-6-4.5-2 .7 3.8 5.5-4.3 1.5z"/><path d="M8 18.5l2-.6.7 2-3.2 1z"/>',
        "wheel": '<circle cx="12" cy="12" r="7.5"/><circle cx="12" cy="12" r="2"/><path d="M12 4.5v3"/><path d="M12 16.5v3"/><path d="M4.5 12h3"/><path d="M16.5 12h3"/>',
        "flame": '<path d="M12 2.5c1.2 3 4 4 4 8a4 4 0 0 1-8 0c0-1.3.6-2 1.2-2.8.3 1 .9 1.4 1.3 1.1-.4-2.4.7-4.6 1.5-6.3z"/><path d="M9 16.5a3 3 0 0 0 6 0"/>',
        "users": '<path d="M17 21v-1.5a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4V21"/><circle cx="9.5" cy="7.5" r="3.5"/><path d="M22 21v-1.5a4 4 0 0 0-3-3.87"/><path d="M15 3.6a3.5 3.5 0 0 1 0 6.8"/>',
        "layers": '<path d="M12 2.5 2.5 7.5 12 12.5l9.5-5-9.5-5z"/><path d="M2.5 16.5 12 21.5l9.5-5"/><path d="M2.5 12 12 17l9.5-5"/>',
        "droplet": '<path d="M12 2.5s6.5 7.2 6.5 12a6.5 6.5 0 1 1-13 0c0-4.8 6.5-12 6.5-12z"/>',
        "radio": '<circle cx="12" cy="14.5" r="2.3"/><path d="M4.9 9.5a10 10 0 0 1 14.2 0"/><path d="M7.8 12.4a6 6 0 0 1 8.4 0"/><path d="M2 6.5a15 15 0 0 1 20 0"/>',
        "door": '<rect x="5" y="2.5" width="14" height="19" rx="1.2"/><circle cx="14.5" cy="12" r="0.9" fill="currentColor" stroke="none"/>',
        "cone": '<path d="M12 3l3.5 15h-7L12 3z"/><path d="M7.5 14h9"/><path d="M6.5 18h11"/>',
        "file": '<path d="M6 2.5h8l4 4v15H6z"/><path d="M14 2.5v4h4"/><path d="M9 12.5h6"/><path d="M9 16h6"/>',
        "check": '<circle cx="12" cy="12" r="9"/><path d="M7.5 12.5l3 3 6-6.5"/>',
        "alert": '<circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.2"/><circle cx="12" cy="16.3" r="0.4" fill="currentColor" stroke="none"/>',
        "lock": '<rect x="5" y="10.5" width="14" height="9.5" rx="2"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3"/>',
        "id": '<rect x="2.5" y="5.5" width="19" height="13" rx="2.2"/><circle cx="8" cy="12" r="2.1"/><path d="M5.5 16c.6-1.4 1.6-2.1 2.5-2.1s1.9.7 2.5 2.1"/><path d="M14 9.5h4"/><path d="M14 13h4"/>',
        "shield": '<path d="M12 21.5S4.5 17.8 4.5 11V5.3L12 2.5l7.5 2.8V11c0 6.8-7.5 10.5-7.5 10.5z"/>',
        "clipboard": '<rect x="6" y="4" width="12" height="17" rx="2"/><rect x="9" y="2" width="6" height="3.5" rx="1"/><path d="M9 11h6"/><path d="M9 15h6"/>',
        "stamp": '<rect x="5" y="13" width="14" height="7" rx="1.4"/><path d="M9 13V9a3 3 0 0 1 6 0v4"/><path d="M4 20h16"/>',
    }
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-4px;">{paths.get(name, "")}</svg>'

# ============================================================================
# 5. SESSION STATE
# ============================================================================
_defaults = {
    "step": 0,
    "job_card_type": list(JOB_CARDS.keys())[0],
    "section_idx": 0,
    "responses": {},
    "remarks": {},
    "completed_at": {},
    "submitted_at": None,
    "staff_snapshot": None,
    "station_final": "CGK",
    "crs_number": None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def reset_all():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    for k, v in _defaults.items():
        st.session_state[k] = v

# ============================================================================
# 6. DESIGN SYSTEM
# ============================================================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800;900&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600;700&display=swap');

        :root {
            --navy-950: #070F1A; --navy-900: #0D1B2A;
            --steel-700: #0B4870; --steel-600: #0E5C8C; --steel-400: #3E93BE;
            --cyan-400: #22C3E6;
            --slate-50: #F7F9FC; --slate-100: #EEF2F7; --slate-200: #E4E9F0;
            --slate-400: #8D9BAF; --slate-500: #5B6B80; --ink-900: #0B1220;
            --success: #148F5E; --success-bg: #E7F6EF;
            --warning: #B8730F; --warning-bg: #FBF0DD;
            --danger: #C5303A; --danger-bg: #FBE7E8;
            --radius-lg: 16px; --radius-md: 12px;
            --shadow-sm: 0 1px 2px rgba(11,18,32,0.05);
            --shadow-md: 0 4px 16px rgba(11,18,32,0.07);
        }
        html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; color: var(--ink-900); }
        .mono { font-family: 'JetBrains Mono', monospace !important; }
        #MainMenu, footer { visibility: hidden; }
        .stApp { background-color: var(--slate-50); }
        .block-container { padding-top: 2.2rem !important; padding-bottom: 3rem !important; max-width: 760px; }

        .header-box {
            background: linear-gradient(135deg, var(--navy-950) 0%, var(--navy-900) 60%, var(--steel-700) 150%);
            color: white; padding: 26px 28px; border-radius: var(--radius-lg);
            margin-bottom: 20px; box-shadow: var(--shadow-md); position: relative; overflow: hidden;
        }
        .header-box::before {
            content:""; position:absolute; inset:0;
            background-image: linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px),
                               linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px);
            background-size: 26px 26px; pointer-events:none;
        }
        .header-eyebrow { color: var(--cyan-400); font-family:'JetBrains Mono',monospace; font-size:10.5px; letter-spacing:2px; text-transform:uppercase; font-weight:600; margin:0 0 6px 0; position:relative; }
        .header-title { margin:0; font-weight:900; font-size:21px; letter-spacing:0.3px; font-family:'Montserrat',sans-serif; position:relative; }
        .header-sub { margin:6px 0 0 0; font-size:12px; color:#A9BCCF; position:relative; }
        .header-foot { margin-top:14px; padding-top:12px; border-top:1px solid rgba(255,255,255,0.12); font-size:10.5px; color:#7E93A8; position:relative; font-family:'JetBrains Mono',monospace; letter-spacing:0.3px; }

        .stepper { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:22px; padding:0 4px; }
        .step-item { display:flex; flex-direction:column; align-items:center; flex:1; position:relative; }
        .step-item:not(:last-child)::after {
            content:""; position:absolute; top:15px; left:calc(50% + 22px); width:calc(100% - 44px); height:2px;
            background: var(--slate-200); z-index:0;
        }
        .step-item.done:not(:last-child)::after { background: var(--steel-600); }
        .step-circle {
            width:30px; height:30px; border-radius:50%; display:flex; align-items:center; justify-content:center;
            font-family:'JetBrains Mono',monospace; font-size:12px; font-weight:700; z-index:1;
            background:#fff; border:2px solid var(--slate-200); color: var(--slate-400);
        }
        .step-item.active .step-circle { border-color: var(--steel-600); color: var(--steel-600); box-shadow:0 0 0 4px rgba(14,92,140,0.10); }
        .step-item.done .step-circle { background: var(--steel-600); border-color: var(--steel-600); color:#fff; }
        .step-label { font-size:10px; font-weight:600; color: var(--slate-400); margin-top:7px; text-align:center; letter-spacing:0.2px; }
        .step-item.active .step-label, .step-item.done .step-label { color: var(--ink-900); }

        .sub-header {
            color: var(--ink-900); font-weight:700; font-size:13px; letter-spacing:0.4px; text-transform:uppercase;
            margin-top:4px; margin-bottom:14px; display:flex; align-items:center; gap:9px; font-family:'Montserrat',sans-serif;
        }
        .sub-header .sh-icon { width:26px; height:26px; border-radius:8px; background:var(--slate-100); color:var(--steel-600); display:flex; align-items:center; justify-content:center; flex-shrink:0; }

        .panel { background:#fff; border:1px solid var(--slate-200); border-radius: var(--radius-lg); padding:20px 22px; box-shadow: var(--shadow-md); margin-bottom:18px; }

        .task-card { background:#fff; border:1px solid var(--slate-200); border-radius: var(--radius-md); padding:16px 18px; margin-bottom:14px; box-shadow: var(--shadow-sm); }
        .task-top { display:flex; align-items:flex-start; gap:12px; margin-bottom:12px; }
        .task-icon { width:32px; height:32px; border-radius:9px; background:var(--slate-100); color:var(--steel-600); display:flex; align-items:center; justify-content:center; flex-shrink:0; font-family:'JetBrains Mono',monospace; font-size:10.5px; font-weight:700; }
        .task-code { font-family:'JetBrains Mono',monospace; font-size:10.5px; color:var(--slate-400); font-weight:600; letter-spacing:0.4px; }
        .task-desc { font-size:13.5px; color:var(--ink-900); line-height:1.5; margin:0; }

        div[role="radiogroup"] { gap:6px !important; }
        div[role="radiogroup"] label {
            border:1.5px solid var(--slate-200) !important; border-radius:9px !important; padding:8px 12px !important;
            background:#fff !important; transition: all 0.12s ease;
        }
        div[role="radiogroup"] label:hover { border-color: var(--steel-400) !important; }

        div.stButton > button {
            font-weight:700 !important; border-radius:11px !important; padding:14px !important; border:none !important;
            font-size:14px !important; letter-spacing:0.2px; transition: all 0.15s ease;
        }
        div.stButton > button[kind="primary"] { background: linear-gradient(135deg, var(--steel-600), var(--steel-700)) !important; color:#fff !important; box-shadow:0 6px 18px rgba(14,92,140,0.25); }
        div.stButton > button[kind="primary"]:hover:not(:disabled) { transform: translateY(-1px); box-shadow:0 8px 22px rgba(14,92,140,0.32); }
        div.stButton > button[kind="secondary"] { background:#fff !important; color: var(--ink-900) !important; border:1.5px solid var(--slate-200) !important; }
        div.stButton > button:disabled { opacity:0.45 !important; box-shadow:none !important; }

        .staff-card { display:flex; align-items:center; gap:14px; background: var(--success-bg); border:1px solid #BEE7D4; border-radius: var(--radius-md); padding:14px 16px; margin-bottom:16px; }
        .staff-avatar { width:42px; height:42px; border-radius:10px; background: linear-gradient(135deg, var(--steel-600), var(--cyan-400)); display:flex; align-items:center; justify-content:center; color:#fff; font-weight:800; font-family:'Montserrat',sans-serif; flex-shrink:0; }
        .staff-name { font-weight:700; font-size:14px; color: var(--ink-900); margin:0; }
        .staff-meta { font-size:11px; color: var(--slate-500); margin:1px 0 0 0; font-family:'JetBrains Mono',monospace; }

        .fail-summary-item { display:flex; gap:10px; padding:10px 0; border-bottom:1px solid var(--slate-100); font-size:12.5px; }
        .fail-summary-item:last-child { border-bottom:none; }

        .badge { display:inline-flex; align-items:center; gap:5px; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:700; }
        .badge-pass { color: var(--success); background: var(--success-bg); }
        .badge-fail { color: var(--danger); background: var(--danger-bg); }
        .badge-na { color: var(--slate-500); background: var(--slate-100); }

        .crs-block { border: 1.5px dashed var(--steel-400); border-radius: var(--radius-md); padding: 16px 18px; background: #F5FAFD; margin-top: 4px; }
        .crs-title { font-family:'Montserrat',sans-serif; font-weight:800; font-size:12px; letter-spacing:0.6px; text-transform:uppercase; color: var(--steel-700); margin-bottom:8px; }
        .crs-text { font-size:12.5px; line-height:1.55; color:#334155; font-style:italic; }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# 7. HEADER + STEPPER
# ============================================================================
st.markdown(f"""
    <div class="header-box">
        <p class="header-eyebrow">PT GMF AeroAsia Tbk &middot; Approved Maintenance Organization</p>
        <h2 class="header-title">{icon('clipboard', 19, '#FFFFFF')} Digital Task Card System</h2>
        <p class="header-sub">Paper task cards CT-2-01/A2-04, A2-09, A2-10 and Attachment CT-2-01, fully digitized — no page or sign-off can be skipped.</p>
        <div class="header-foot">CASR Part 145 &middot; Member of Garuda Indonesia Group</div>
    </div>
""", unsafe_allow_html=True)

def render_stepper(current):
    items = ""
    for i, label in enumerate(STEP_LABELS):
        state = "done" if i < current else ("active" if i == current else "")
        circle_content = icon("check", 13, "#FFFFFF") if i < current else str(i + 1)
        items += f'<div class="step-item {state}"><div class="step-circle">{circle_content}</div><div class="step-label">{label}</div></div>'
    st.markdown(f'<div class="stepper">{items}</div>', unsafe_allow_html=True)

render_stepper(st.session_state.step)

# ============================================================================
# 8. RENDER ITEM / SECTION HELPERS
# ============================================================================
def render_item(item):
    kind = item["kind"]

    if kind == "note":
        st.info(item["text"])
        return True

    if kind == "warning":
        st.warning(f"⚠️ {item['text']}")
        return True

    if kind == "check":
        code = item["code"]
        st.markdown(f"""
            <div class="task-card">
                <div class="task-top">
                    <div class="task-icon">{item['skill']}</div>
                    <div>
                        <div class="task-code">{code}</div>
                        <p class="task-desc">{item['desc']}</p>
                    </div>
                </div>
        """, unsafe_allow_html=True)
        val = st.radio(f"Status {code}", options=item["status_options"], horizontal=True,
                        key=f"radio_{code}", label_visibility="collapsed")
        st.session_state.responses[code] = val
        complete = val not in ("⚠️ Not Inspected", "⚠️ Not Completed")

        if complete and code not in st.session_state.completed_at:
            st.session_state.completed_at[code] = datetime.now().strftime("%H:%M:%S")
        elif not complete:
            st.session_state.completed_at.pop(code, None)

        if val == "❌ FAIL":
            remark = st.text_area("Finding remarks (required)", key=f"remark_{code}",
                                   placeholder="Describe the finding, condition, and corrective action taken...")
            st.session_state.remarks[code] = remark
            if not remark.strip():
                complete = False

            action = st.radio("Corrective action", options=["Rectified prior to release", "Deferred under MEL/CDL"],
                               horizontal=True, key=f"action_{code}", label_visibility="visible")
            st.session_state.responses[f"{code}__action"] = action

            if action == "Deferred under MEL/CDL":
                mel_ref = st.text_input("MEL / CDL reference number (required)", key=f"mel_{code}",
                                         placeholder="e.g. MEL 32-40-01A")
                st.session_state.responses[f"{code}__mel"] = mel_ref
                if not mel_ref.strip():
                    complete = False
            else:
                st.session_state.responses[f"{code}__mel"] = ""
        else:
            st.session_state.remarks[code] = ""
            st.session_state.responses[f"{code}__action"] = ""
            st.session_state.responses[f"{code}__mel"] = ""
        st.markdown("</div>", unsafe_allow_html=True)
        return complete

    if kind == "measurement":
        code = item["code"]
        st.markdown(f"""
            <div class="task-card">
                <div class="task-top">
                    <div class="task-icon">{item['skill']}</div>
                    <div>
                        <div class="task-code">{code}</div>
                        <p class="task-desc">{item['label']}</p>
                    </div>
                </div>
        """, unsafe_allow_html=True)
        val = st.number_input(f"Value ({item['unit']})", key=f"meas_{code}", value=None,
                               step=1.0, format="%.0f", label_visibility="visible")
        st.session_state.responses[code] = val
        st.markdown("</div>", unsafe_allow_html=True)
        return val is not None

    if kind == "finding":
        code = item["code"]
        st.markdown(f"""
            <div class="task-card">
                <div class="task-top">
                    <div class="task-icon">{item['skill']}</div>
                    <div>
                        <div class="task-code">{code}</div>
                        <p class="task-desc">{item['label']}</p>
                    </div>
                </div>
        """, unsafe_allow_html=True)
        if item.get("criteria"):
            with st.expander("View damage criteria (AMM reference)"):
                st.table(pd.DataFrame(item["criteria"]))
        nil = st.checkbox("No finding (NIL)", value=True, key=f"nil_{code}")
        if nil:
            st.session_state.responses[code] = "NIL"
            st.markdown("</div>", unsafe_allow_html=True)
            return True
        else:
            txt = st.text_area("Describe the finding in detail",
                                key=f"findtext_{code}", placeholder="Provide a detailed description of the finding...")
            st.session_state.responses[code] = txt
            st.markdown("</div>", unsafe_allow_html=True)
            return txt.strip() != ""

    if kind == "table":
        code = item["code"]
        st.markdown(f"""
            <div class="task-card">
                <div class="task-top">
                    <div class="task-icon">{item['skill']}</div>
                    <div>
                        <div class="task-code">{code}</div>
                        <p class="task-desc">{item['label']}</p>
                    </div>
                </div>
        """, unsafe_allow_html=True)
        if item.get("unit_note"):
            st.caption(item["unit_note"])
        init_df = pd.DataFrame(
            {c: [None] * len(item["rows"]) for c in item["columns"]},
            index=item["rows"]
        )
        col_config = {c: st.column_config.NumberColumn(format="%.1f") for c in item["columns"]}
        edited = st.data_editor(init_df, key=f"tbl_{code}", use_container_width=True,
                                 column_config=col_config)
        st.session_state.responses[code] = edited
        complete = True
        for r in item["required_rows"]:
            if r in edited.index and edited.loc[r].isna().any():
                complete = False
        st.markdown("</div>", unsafe_allow_html=True)
        return complete

    return True

def render_checklist_section(section):
    complete = True
    for item in section["items"]:
        ok = render_item(item)
        complete = complete and ok
    return complete

def render_equipment_section(section):
    df = pd.DataFrame(section["rows"], columns=["Equipment", "Description"])
    df["Remark"] = ""
    key = f"eq_{section['no']}"
    edited = st.data_editor(
        df, key=key, hide_index=True, use_container_width=True,
        column_config={
            "Equipment": st.column_config.TextColumn("Equipment", disabled=True, width="medium"),
            "Description": st.column_config.TextColumn("Description", disabled=True, width="large"),
            "Remark": st.column_config.TextColumn("Remark (required)", required=True, width="medium"),
        },
    )
    st.session_state.responses[key] = edited
    remarks = edited["Remark"].fillna("").astype(str).str.strip()
    return bool((remarks != "").all()) and len(remarks) > 0

def section_status(section, mode):
    """Read-only status check (no widgets created) — used by the page navigator."""
    if mode == "equipment_log":
        df = st.session_state.responses.get(f"eq_{section['no']}")
        if df is None:
            return "pending"
        remarks = df["Remark"].fillna("").astype(str).str.strip()
        return "done" if len(remarks) and (remarks != "").all() else "partial"

    touched, all_done = False, True
    for it in section["items"]:
        code = it.get("code")
        if it["kind"] == "check":
            val = st.session_state.responses.get(code)
            if val is None:
                all_done = False
                continue
            touched = True
            if val in ("⚠️ Not Inspected", "⚠️ Not Completed"):
                all_done = False
            if val == "❌ FAIL":
                if not st.session_state.remarks.get(code, "").strip():
                    all_done = False
                if st.session_state.responses.get(f"{code}__action") == "Deferred under MEL/CDL" \
                        and not st.session_state.responses.get(f"{code}__mel", "").strip():
                    all_done = False
        elif it["kind"] == "measurement":
            if st.session_state.responses.get(code) is None:
                all_done = False
            else:
                touched = True
        elif it["kind"] == "finding":
            if code not in st.session_state.responses:
                all_done = False
            else:
                touched = True
        elif it["kind"] == "table":
            df = st.session_state.responses.get(code)
            if df is None:
                all_done = False
            else:
                touched = True
                for r in it["required_rows"]:
                    if r in df.index and df.loc[r].isna().any():
                        all_done = False
    if not touched:
        return "pending"
    return "done" if all_done else "partial"

def render_navigator(sections, mode, current_idx):
    with st.expander(f"📑 Task Card Navigator ({current_idx + 1} / {len(sections)})", expanded=False):
        st.caption("Jump back to any page you've already started to review or correct an entry. Pages ahead of your progress stay locked until the current page is complete.")
        for i, s in enumerate(sections):
            status = section_status(s, mode)
            if i == current_idx:
                dot, label_extra = "🔵", " (current)"
            elif status == "done":
                dot, label_extra = "🟢", ""
            elif status == "partial":
                dot, label_extra = "🟡", " (incomplete)"
            else:
                dot, label_extra = "⚪", ""
            can_jump = (i <= current_idx) or status in ("done", "partial")
            cols = st.columns([0.08, 0.72, 0.2])
            cols[0].markdown(dot)
            cols[1].markdown(f"**{s['no']}. {s['title']}**{label_extra}")
            if i != current_idx and can_jump:
                if cols[2].button("Go", key=f"nav_{i}", use_container_width=True):
                    st.session_state.section_idx = i
                    st.rerun()

# ============================================================================
# 9. PDF GENERATOR — renders the completed task card as a filled-in PDF
# ============================================================================
def _esc(text):
    if text is None:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def _pdf_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="GMFEyebrow", fontSize=8.5, leading=10,
                               textColor=colors.HexColor("#0E5C8C"), fontName="Helvetica-Bold", spaceAfter=4))
    styles.add(ParagraphStyle(name="GMFTitle", fontSize=15, leading=18,
                               textColor=colors.HexColor("#0B1220"), fontName="Helvetica-Bold", spaceAfter=2))
    styles.add(ParagraphStyle(name="GMFSection", fontSize=10.5, leading=13,
                               textColor=colors.white, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="GMFCell", fontSize=8, leading=10, fontName="Helvetica"))
    styles.add(ParagraphStyle(name="GMFCellBold", fontSize=8, leading=10, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="GMFNote", fontSize=8, leading=10.5, fontName="Helvetica-Oblique",
                               textColor=colors.HexColor("#5B6B80")))
    styles.add(ParagraphStyle(name="GMFCrsTitle", fontSize=10.5, leading=13, fontName="Helvetica-Bold",
                               textColor=colors.HexColor("#0B4870")))
    styles.add(ParagraphStyle(name="GMFCrsText", fontSize=8.5, leading=11.5, fontName="Helvetica-Oblique",
                               textColor=colors.HexColor("#334155")))
    return styles

_ITEM_HEADER = ["Code", "Skill", "Description", "Status", "Remark / Value"]
_ITEM_COL_WIDTHS = [16 * mm, 13 * mm, 80 * mm, 24 * mm, 41 * mm]

def _status_hex(status):
    if status in ("✅ PASS", "✅ Completed"):
        return "148F5E"
    if status == "❌ FAIL":
        return "C5303A"
    if status in ("⚠️ Not Inspected", "⚠️ Not Completed", None):
        return "B8730F"
    return "5B6B80"

def _new_item_table_rows(styles):
    return [[Paragraph(f"<b>{h}</b>", styles["GMFCellBold"]) for h in _ITEM_HEADER]]

def _flush_item_rows(rows, flowables, styles):
    if len(rows) > 1:
        t = Table(rows, colWidths=_ITEM_COL_WIDTHS, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF2F7")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E4E9F0")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        flowables.append(t)
        flowables.append(Spacer(1, 6))
    rows.clear()
    rows.extend(_new_item_table_rows(styles))

def build_pdf(job_card_type, card, staff, crs_number, submitted_at, station_final):
    styles = _pdf_styles()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=16 * mm, bottomMargin=16 * mm,
                             leftMargin=15 * mm, rightMargin=15 * mm,
                             title=f"GMF Digital Task Card - {job_card_type}")
    story = []

    # ---- Header ----
    story.append(Paragraph("PT GMF AEROASIA TBK &mdash; APPROVED MAINTENANCE ORGANIZATION (CASR PART 145)", styles["GMFEyebrow"]))
    story.append(Paragraph(f"Digital Task Card &mdash; {_esc(job_card_type)}", styles["GMFTitle"]))
    story.append(Spacer(1, 6))

    meta_items = list(card["meta"].items())
    header_rows, row = [], []
    for k, v in meta_items:
        row.append(Paragraph(f"<b>{_esc(k)}</b><br/>{_esc(v)}", styles["GMFCell"]))
        if len(row) == 3:
            header_rows.append(row)
            row = []
    if row:
        while len(row) < 3:
            row.append(Paragraph("", styles["GMFCell"]))
        header_rows.append(row)
    header_table = Table(header_rows, colWidths=[58 * mm] * 3)
    header_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#E4E9F0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E4E9F0")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F9FC")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 12))

    sections = card["sections"]
    mode = card.get("mode", "checklist")

    if mode == "checklist":
        for s in sections:
            section_flow = []
            title_tbl = Table([[Paragraph(f"{s['no']}. {_esc(s['title'])}", styles["GMFSection"])]], colWidths=[174 * mm])
            title_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0D1B2A")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            section_flow.append(title_tbl)
            section_flow.append(Spacer(1, 4))

            item_rows = _new_item_table_rows(styles)

            for it in s["items"]:
                kind = it["kind"]
                if kind == "note":
                    _flush_item_rows(item_rows, section_flow, styles)
                    section_flow.append(Paragraph(f"&#8505; NOTE: {_esc(it['text'])}", styles["GMFNote"]))
                    section_flow.append(Spacer(1, 4))
                elif kind == "warning":
                    _flush_item_rows(item_rows, section_flow, styles)
                    section_flow.append(Paragraph(f"&#9888; WARNING: {_esc(it['text'])}", styles["GMFNote"]))
                    section_flow.append(Spacer(1, 4))
                elif kind == "check":
                    code = it["code"]
                    status = st.session_state.responses.get(code, "-")
                    remark = st.session_state.remarks.get(code, "")
                    action = st.session_state.responses.get(f"{code}__action", "")
                    mel = st.session_state.responses.get(f"{code}__mel", "")
                    extra_bits = []
                    if remark:
                        extra_bits.append(f"Remark: {remark}")
                    if action:
                        extra_bits.append(f"Action: {action}")
                    if mel:
                        extra_bits.append(f"MEL/CDL: {mel}")
                    extra = " | ".join(extra_bits)
                    item_rows.append([
                        Paragraph(_esc(code), styles["GMFCell"]),
                        Paragraph(_esc(it["skill"]), styles["GMFCell"]),
                        Paragraph(_esc(it["desc"]), styles["GMFCell"]),
                        Paragraph(f'<font color="#{_status_hex(status)}"><b>{_esc(status)}</b></font>', styles["GMFCell"]),
                        Paragraph(_esc(extra), styles["GMFCell"]),
                    ])
                elif kind == "measurement":
                    val = st.session_state.responses.get(it["code"])
                    display_val = f"{val:g} {it['unit']}" if val is not None else "-"
                    item_rows.append([
                        Paragraph(_esc(it["code"]), styles["GMFCell"]),
                        Paragraph(_esc(it["skill"]), styles["GMFCell"]),
                        Paragraph(_esc(it["label"]), styles["GMFCell"]),
                        Paragraph(_esc(display_val), styles["GMFCell"]),
                        Paragraph("", styles["GMFCell"]),
                    ])
                elif kind == "finding":
                    val = st.session_state.responses.get(it["code"], "NIL")
                    status_txt = "NIL" if val == "NIL" else "FINDING"
                    item_rows.append([
                        Paragraph(_esc(it["code"]), styles["GMFCell"]),
                        Paragraph(_esc(it["skill"]), styles["GMFCell"]),
                        Paragraph(_esc(it["label"]), styles["GMFCell"]),
                        Paragraph(_esc(status_txt), styles["GMFCell"]),
                        Paragraph(_esc(val if val != "NIL" else ""), styles["GMFCell"]),
                    ])
                elif kind == "table":
                    _flush_item_rows(item_rows, section_flow, styles)
                    df = st.session_state.responses.get(it["code"])
                    cols = it["columns"]
                    sub_header = [Paragraph("", styles["GMFCellBold"])] + \
                                 [Paragraph(f"<b>{_esc(c)}</b>", styles["GMFCellBold"]) for c in cols]
                    sub_rows = [sub_header]
                    for r in it["rows"]:
                        vals = []
                        for c in cols:
                            v = df.loc[r, c] if (df is not None and r in df.index) else None
                            vals.append("" if v is None or pd.isna(v) else f"{v:g}")
                        sub_rows.append([Paragraph(_esc(r), styles["GMFCell"])] +
                                         [Paragraph(_esc(v), styles["GMFCell"]) for v in vals])
                    n_cols = len(cols) + 1
                    label_col = 30 * mm
                    other_col = (174 - 30) / len(cols)
                    sub_table = Table(sub_rows, colWidths=[label_col] + [other_col * mm] * len(cols))
                    sub_table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF2F7")),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E4E9F0")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]))
                    section_flow.append(Paragraph(f"<b>{_esc(it['code'])}</b> &mdash; {_esc(it['label'])}", styles["GMFCellBold"]))
                    section_flow.append(sub_table)
                    section_flow.append(Spacer(1, 6))

            _flush_item_rows(item_rows, section_flow, styles)
            story.append(KeepTogether(section_flow[:2]))
            story.extend(section_flow[2:])
            story.append(Spacer(1, 8))
    else:
        for s in sections:
            section_flow = []
            title_tbl = Table([[Paragraph(_esc(s["title"]), styles["GMFSection"])]], colWidths=[174 * mm])
            title_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0D1B2A")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            section_flow.append(title_tbl)
            section_flow.append(Spacer(1, 4))

            df = st.session_state.responses.get(f"eq_{s['no']}")
            eq_rows = [[Paragraph("<b>Equipment</b>", styles["GMFCellBold"]),
                        Paragraph("<b>Description</b>", styles["GMFCellBold"]),
                        Paragraph("<b>Remark</b>", styles["GMFCellBold"])]]
            if df is not None:
                for _, r in df.iterrows():
                    eq_rows.append([
                        Paragraph(_esc(r["Equipment"]), styles["GMFCell"]),
                        Paragraph(_esc(r["Description"]), styles["GMFCell"]),
                        Paragraph(_esc(r["Remark"]), styles["GMFCell"]),
                    ])
            eq_table = Table(eq_rows, colWidths=[45 * mm, 89 * mm, 40 * mm], repeatRows=1)
            eq_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF2F7")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E4E9F0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            section_flow.append(eq_table)
            story.append(KeepTogether(section_flow[:2]))
            story.extend(section_flow[2:])
            story.append(Spacer(1, 8))

    # ---- CRS / release block ----
    story.append(Spacer(1, 6))
    crs_rows = [
        [Paragraph("CERTIFICATE OF RELEASE TO SERVICE (CRS)", styles["GMFCrsTitle"])],
        [Paragraph(
            'I certify that the work specified, except as otherwise stated, was carried out in accordance with the '
            'applicable requirements of the Indonesian Civil Aviation Safety Regulations (CASR) Part 145, and in that '
            'respect the aircraft / item is considered ready for release to service.', styles["GMFCrsText"])],
        [Paragraph(
            f'<b>CRS No.:</b> {_esc(crs_number)} &nbsp;&nbsp; <b>Station:</b> {_esc(station_final)} &nbsp;&nbsp; '
            f'<b>Date/Time:</b> {_esc(submitted_at.strftime("%d %b %Y %H:%M WIB"))}', styles["GMFCell"])],
        [Paragraph(
            f'<b>Certifying Staff:</b> {_esc(staff.get("name", "-"))} &nbsp;&nbsp; '
            f'<b>License:</b> {_esc(staff.get("license_no", "-"))} &nbsp;&nbsp; '
            f'<b>Rating:</b> {_esc(staff.get("rating", "-"))}', styles["GMFCell"])],
    ]
    crs_table = Table(crs_rows, colWidths=[174 * mm])
    crs_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#3E93BE")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5FAFD")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(crs_table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ============================================================================
# STEP 0 — WORK ORDER / SELECT TASK CARD

# ============================================================================
if st.session_state.step == 0:
    st.markdown(f"<div class='sub-header'><span class='sh-icon'>{icon('file', 14)}</span>A. Work Order Details</div>", unsafe_allow_html=True)
    st.markdown('<div class="panel">', unsafe_allow_html=True)

    job_card_type = st.selectbox("Task Card Type", options=list(JOB_CARDS.keys()),
                                  index=list(JOB_CARDS.keys()).index(st.session_state.job_card_type))
    card = JOB_CARDS[job_card_type]
    meta = dict(card["meta"])

    operator = st.selectbox("Operator / Customer", options=OPERATORS,
                             index=OPERATORS.index(meta.get("Operator", OPERATORS[0])) if meta.get("Operator") in OPERATORS else 0)
    meta["Operator"] = operator

    cols = st.columns(2)
    meta_items = [(k, v) for k, v in meta.items() if k != "Operator"]
    half = (len(meta_items) + 1) // 2
    for i, (k, v) in enumerate(meta_items):
        with cols[0 if i < half else 1]:
            st.text_input(k, value=v, disabled=True, key=f"meta_{job_card_type}_{k}")

    st.markdown('</div>', unsafe_allow_html=True)

    if job_card_type != st.session_state.job_card_type:
        st.session_state.job_card_type = job_card_type
        st.session_state.section_idx = 0
        st.session_state.responses = {}
        st.session_state.remarks = {}
        st.session_state.completed_at = {}

    n_sections = len(card["sections"])
    st.info(f"📋 **{job_card_type}** contains **{n_sections} inspection pages**. Each page must be completed in full before the next page can be opened.")

    if st.button("Start Inspection  →", use_container_width=True, type="primary"):
        st.session_state.step = 1
        st.rerun()

# ============================================================================
# STEP 1 — PAGINATED CHECKLIST (one section = one page, cannot be skipped)
# ============================================================================
elif st.session_state.step == 1:
    card = JOB_CARDS[st.session_state.job_card_type]
    sections = card["sections"]
    mode = card.get("mode", "checklist")
    idx = st.session_state.section_idx
    idx = max(0, min(idx, len(sections) - 1))
    st.session_state.section_idx = idx
    section = sections[idx]

    st.progress((idx) / len(sections), text=f"Page {idx + 1} of {len(sections)}")
    render_navigator(sections, mode, idx)
    st.markdown(f"<div class='sub-header'><span class='sh-icon'>{icon(section.get('icon', 'clipboard'), 14)}</span>{section['no']}. {section['title']}</div>", unsafe_allow_html=True)

    if mode == "equipment_log":
        st.markdown("🔒 The **Remark** column is required for every item of equipment (condition / expiry date / N/A).")
        complete = render_equipment_section(section)
        if not complete:
            st.warning("🚨 Some equipment rows still have an empty Remark. Complete them before continuing.")
    else:
        complete = render_checklist_section(section)
        if not complete:
            st.warning("🚨 Some items on this page are not yet fully completed (including required finding remarks for FAIL status). All items must be completed before continuing.")

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("←  Back", use_container_width=True, type="secondary"):
            if idx == 0:
                st.session_state.step = 0
            else:
                st.session_state.section_idx = idx - 1
            st.rerun()
    with col_next:
        is_last = idx == len(sections) - 1
        label = "Proceed to Authorization  →" if is_last else "Next Page  →"
        if st.button(label, use_container_width=True, type="primary", disabled=not complete):
            if is_last:
                st.session_state.step = 2
            else:
                st.session_state.section_idx = idx + 1
            st.rerun()

# ============================================================================
# STEP 2 — AUTHORIZATION & CERTIFICATE OF RELEASE TO SERVICE (CRS)
# ============================================================================
elif st.session_state.step == 2:
    card = JOB_CARDS[st.session_state.job_card_type]
    sections = card["sections"]
    mode = card.get("mode", "checklist")

    st.markdown(f"<div class='sub-header'><span class='sh-icon'>{icon('lock', 14)}</span>C. Authorization &amp; Release</div>", unsafe_allow_html=True)

    if mode == "checklist":
        all_checks = [it for s in sections for it in s["items"] if it["kind"] == "check"]
        fails = [it for it in all_checks if st.session_state.responses.get(it["code"]) == "❌ FAIL"]
        findings = [it for s in sections for it in s["items"]
                    if it["kind"] == "finding" and st.session_state.responses.get(it["code"], "NIL") != "NIL"]

        if fails or findings:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown(f"<div style='font-weight:700; font-size:12.5px; margin-bottom:6px; color:#C5303A;'>{icon('alert', 13, '#C5303A')} {len(fails) + len(findings)} item(s) require review before release</div>", unsafe_allow_html=True)
            for it in fails:
                note = st.session_state.remarks.get(it["code"], "").strip() or "(no remark)"
                st.markdown(f"""<div class="fail-summary-item"><span class="badge badge-fail">{it['code']}</span>
                    <div><b>FAIL</b><br><span style="color:#5B6B80;">{note}</span></div></div>""", unsafe_allow_html=True)
            for it in findings:
                note = st.session_state.responses.get(it["code"], "").strip()
                st.markdown(f"""<div class="fail-summary-item"><span class="badge badge-fail">{it['code']}</span>
                    <div><b>Finding</b><br><span style="color:#5B6B80;">{note}</span></div></div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="panel" style="display:flex; align-items:center; gap:10px;">{icon("check", 18, "#148F5E")} <span style="font-size:13px; font-weight:600;">All items PASS / N/A / Completed - no findings recorded.</span></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="panel" style="display:flex; align-items:center; gap:10px;">{icon("shield", 18, "#0E5C8C")} <span style="font-size:13px; font-weight:600;">All {sum(len(s["rows"]) for s in sections)} Emergency Equipment items have a recorded remark.</span></div>', unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("**Release Details** — replaces the Station / Date / Time / Sign fields on the paper task card.")
    c1, c2 = st.columns(2)
    with c1:
        station_final = st.text_input("Station", value=st.session_state.station_final, key="station_final_input")
        st.session_state.station_final = station_final
    with c2:
        st.text_input("Date / Time", value=datetime.now().strftime("%d %b %Y | %H:%M WIB"), disabled=True)

    st.markdown("🔒 **Digital sign-off** — enter your GMF employee PIN in place of a wet-ink signature. The PIN automatically confirms your identity and licensing details.")
    pin_input = st.text_input("Certifying Staff PIN (demo: 1234 or 5678)", type="password", max_chars=4,
                               placeholder="••••", key="pin_field")
    staff = CERTIFYING_STAFF_DB.get(pin_input) if len(pin_input) == 4 else None
    if len(pin_input) == 4 and staff is None:
        st.error("🚨 PIN not recognized in the system. Please confirm your employee PIN.")

    declaration = False
    if staff:
        st.markdown(f"""
            <div class="staff-card">
                <div class="staff-avatar">{staff['name'][:2].upper()}</div>
                <div>
                    <p class="staff-name">{staff['name']}</p>
                    <p class="staff-meta">{staff['license_no']} &middot; {staff['rating']}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="crs-block">
                <div class="crs-title">Certificate of Release to Service (CRS)</div>
                <p class="crs-text">"I certify that the work specified, except as otherwise stated, was carried out in accordance
                with the applicable requirements of the Indonesian Civil Aviation Safety Regulations (CASR) Part 145,
                and in that respect the aircraft / item is considered ready for release to service."</p>
            </div>
        """, unsafe_allow_html=True)
        declaration = st.checkbox(
            "I confirm the statement above and certify this task card as complete and accurate.",
            key="declaration_check"
        )
    st.markdown('</div>', unsafe_allow_html=True)

    can_submit = staff is not None and declaration

    col_back, col_submit = st.columns(2)
    with col_back:
        if st.button("←  Back to Last Page", use_container_width=True, type="secondary"):
            st.session_state.step = 1
            st.session_state.section_idx = len(sections) - 1
            st.rerun()
    with col_submit:
        if st.button("📤  Submit &amp; Release", use_container_width=True, type="primary", disabled=not can_submit):
            with st.spinner("Encrypting data and transmitting to the central server..."):
                time.sleep(1.4)
            st.session_state.submitted_at = datetime.now()
            st.session_state.staff_snapshot = staff
            st.session_state.crs_number = f"{staff['auth_no']}-{datetime.now().strftime('%y%m%d%H%M')}"
            st.session_state.step = 3
            st.rerun()

# ============================================================================
# STEP 3 — CONFIRMATION
# ============================================================================
elif st.session_state.step == 3:
    card = JOB_CARDS[st.session_state.job_card_type]
    sections = card["sections"]
    mode = card.get("mode", "checklist")
    staff = st.session_state.get("staff_snapshot") or {}

    st.markdown(f"<div class='sub-header'><span class='sh-icon'>{icon('stamp', 14)}</span>Task Card Released</div>", unsafe_allow_html=True)
    st.success("✅ **TASK CARD SUCCESSFULLY SUBMITTED AND RELEASED TO SERVICE**")

    if mode == "checklist":
        all_checks = [it for s in sections for it in s["items"] if it["kind"] == "check"]
        pass_count = sum(1 for it in all_checks if st.session_state.responses.get(it["code"]) in ("✅ PASS", "✅ Completed"))
        fail_count = sum(1 for it in all_checks if st.session_state.responses.get(it["code"]) == "❌ FAIL")
        na_count = sum(1 for it in all_checks if st.session_state.responses.get(it["code"]) == "➖ N/A")
        badges = f"""<span class="badge badge-pass">{pass_count} PASS/Completed</span>
            <span class="badge badge-fail">{fail_count} FAIL</span>
            <span class="badge badge-na">{na_count} N/A</span>"""
    else:
        total_rows = sum(len(s["rows"]) for s in sections)
        badges = f'<span class="badge badge-pass">{total_rows} Equipment Items Recorded</span>'

    st.markdown(f"""
        <div class="panel">
            <div style="display:flex; justify-content:space-between; margin-bottom:14px; flex-wrap:wrap; gap:10px;">
                <div><div class="task-code">Task Card</div><div style="font-weight:700;">{st.session_state.job_card_type}</div></div>
                <div><div class="task-code">Station</div><div style="font-weight:700;">{st.session_state.station_final}</div></div>
                <div><div class="task-code">Release Time</div><div class="mono" style="font-weight:700;">{st.session_state.submitted_at.strftime('%H:%M:%S WIB')}</div></div>
            </div>
            <div style="display:flex; gap:8px; margin-bottom:14px; flex-wrap:wrap;">{badges}</div>
            <div class="crs-block" style="margin-top:2px;">
                <div class="crs-title">Certificate of Release to Service</div>
                <p class="crs-text" style="margin-bottom:8px;">CRS No. <span class="mono" style="font-style:normal; font-weight:700; color:#0B1220;">{st.session_state.crs_number}</span></p>
                <p class="crs-text">Digitally certified by <b style="color:#0B1220; font-style:normal;">{staff.get('name', '-')}</b>
                ({staff.get('license_no', '-')}). Aircraft status has been automatically updated in the GMF Command Center dashboard.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ---- Build a downloadable compliance record (CSV) ----
    records = []
    if mode == "checklist":
        for s in sections:
            for it in s["items"]:
                code = it.get("code")
                if it["kind"] == "check":
                    records.append({
                        "Section": f"{s['no']}. {s['title']}", "Code": code, "Skill": it["skill"],
                        "Description": it["desc"], "Status": st.session_state.responses.get(code, ""),
                        "Remark": st.session_state.remarks.get(code, ""),
                        "Corrective Action": st.session_state.responses.get(f"{code}__action", ""),
                        "MEL/CDL Ref": st.session_state.responses.get(f"{code}__mel", ""),
                        "Completed At": st.session_state.completed_at.get(code, ""),
                    })
                elif it["kind"] == "measurement":
                    records.append({
                        "Section": f"{s['no']}. {s['title']}", "Code": code, "Skill": it["skill"],
                        "Description": it["label"], "Status": st.session_state.responses.get(code, ""),
                        "Remark": "", "Corrective Action": "", "MEL/CDL Ref": "",
                        "Completed At": st.session_state.completed_at.get(code, ""),
                    })
                elif it["kind"] == "finding":
                    records.append({
                        "Section": f"{s['no']}. {s['title']}", "Code": code, "Skill": it["skill"],
                        "Description": it["label"], "Status": st.session_state.responses.get(code, "NIL"),
                        "Remark": "", "Corrective Action": "", "MEL/CDL Ref": "",
                        "Completed At": "",
                    })
                elif it["kind"] == "table":
                    df = st.session_state.responses.get(code)
                    if df is not None:
                        for r in df.index:
                            for c in df.columns:
                                records.append({
                                    "Section": f"{s['no']}. {s['title']}", "Code": f"{code} / {r} / {c}",
                                    "Skill": it["skill"], "Description": it["label"],
                                    "Status": df.loc[r, c], "Remark": "", "Corrective Action": "",
                                    "MEL/CDL Ref": "", "Completed At": "",
                                })
    else:
        for s in sections:
            df = st.session_state.responses.get(f"eq_{s['no']}")
            if df is not None:
                for _, row in df.iterrows():
                    records.append({
                        "Section": s["title"], "Code": row["Equipment"], "Skill": "",
                        "Description": row["Description"], "Status": row["Remark"],
                        "Remark": "", "Corrective Action": "", "MEL/CDL Ref": "", "Completed At": "",
                    })

    records_df = pd.DataFrame(records)
    csv_bytes = records_df.to_csv(index=False).encode("utf-8")

    try:
        pdf_bytes = build_pdf(
            st.session_state.job_card_type, card, staff,
            st.session_state.crs_number, st.session_state.submitted_at, st.session_state.station_final
        )
    except Exception as e:
        pdf_bytes = None
        st.error(f"⚠️ Could not generate the PDF ({e}). The CSV record below is still available.")

    col_pdf, col_csv = st.columns(2)
    with col_pdf:
        if pdf_bytes is not None:
            st.download_button(
                "📄  Download Filled Task Card (PDF)",
                data=pdf_bytes,
                file_name=f"{st.session_state.crs_number}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary",
            )
    with col_csv:
        st.download_button(
            "⬇️  Download Compliance Record (CSV)",
            data=csv_bytes,
            file_name=f"{st.session_state.crs_number}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.balloons()

    if st.button("＋  Create New Task Card", use_container_width=True, type="primary"):
        reset_all()
        st.rerun()
