import streamlit as st
import pandas as pd
from datetime import datetime
import time

# ============================================================================
# 1. KONFIGURASI HALAMAN
# ============================================================================
st.set_page_config(
    page_title="GMF - e-Task Card",
    page_icon="🛠️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

STATUS_OPTIONS = ["⚠️ Belum Dicek", "✅ PASS", "❌ FAIL", "➖ N/A"]
CLEAN_STATUS_OPTIONS = ["⚠️ Belum Dikerjakan", "✅ Selesai", "➖ N/A"]

TECHNICIAN_DB = {
    "1234": {"name": "Ahmad Fadli", "license": "AMEL A-2201", "rating": "A320/B737"},
    "5678": {"name": "Budi Santoso", "license": "AMEL A-1187", "rating": "A320/B737"},
}

# ============================================================================
# 2. HELPER BUILDERS UNTUK ITEM CHECKLIST
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
# 3. DIGITALISASI JOB CARD — berdasarkan Form CT-2-01/A2-04, A2-09, A2-10
#    dan Attachment CT-2-01 (Citilink A320)
# ============================================================================
JOB_CARDS = {

    # ------------------------------------------------------------------ #
    "Weekly Check (A320)": {
        "meta": {
            "WO Number": "WY-2026-000431", "A/C Type": "A320", "A/C Reg": "PK-GLV",
            "Station": "CGK", "Skill": "AP/EA", "Crew/Down Time": "3 / 4",
            "Event / Interval": "WY (Weekly)", "Chapter / Page": "11.02.04", "Manhours": "8",
        },
        "mode": "checklist",
        "sections": [
            {"no": 1, "title": "Arrival", "icon": "plane", "items": [
                ck("ARR-01", "SPC", "Siapkan area/bay untuk kedatangan pesawat, area & peralatan bersih (5 menit sebelum tiba)."),
                ck("ARR-02", "SPC", "Sambungkan interphone ground-to-cockpit; pastikan wheel chocks terpasang."),
                ck("ARR-03", "SPC", "Sambungkan Ground Power Unit setelah APU 15 menit beroperasi (bila diperlukan); seluruh CB tertutup."),
                wn("Pitot probe cover & static port cover direkomendasikan terpasang saat parkir lama, kondisi berdebu/abu vulkanik, atau risiko kontaminasi serangga, untuk mencegah pembacaan airspeed/altitude yang salah."),
                ck("ARR-04", "SPC", "Pasang L/G lock pin dan pitot & static cover apabila ground time akan lebih dari 4 jam."),
                ck("ARR-05", "SPC", "Review & diskusikan temuan AML/CML dengan flight crew; lakukan tindakan korektif sesuai kebutuhan."),
                ck("ARR-06", "SPC", "Set parking brake ke posisi OFF."),
                ck("ARR-07", "SPC", "Lakukan ADIRS Stop Procedure (ref. AMM 34-10-00-860-005-A)."),
                ck("ARR-08", "SPC", "Pastikan emergency light switch di cockpit & cabin dalam posisi OFF."),
            ]},
            {"no": 2, "title": "Engine", "icon": "flame", "items": [
                nt("Berlaku untuk Engine 1 & Engine 2."),
                ck("ENG-01", "VCK", "Check engine forward acoustic panel (ref. AMM 72-23-00-280-005-A); bila baut kendor, retorque 126.35–139.65 lbf.in (ref. AMM 72-23-00-400-009)."),
                ck("ENG-02", "VCK", "Check level oli engine di tank (5–60 menit setelah engine shut-down)."),
            ]},
            {"no": 3, "title": "Engine Oil Service", "icon": "flame", "items": [
                wn("Jika engine berhenti lebih dari 1 jam, lakukan idle run terlebih dahulu untuk mencegah over-servicing bila oli ditambahkan."),
                ck("EOS-E1", "SVC", "Engine 1 — Service oli bila diperlukan (AMM 12-13-79-610). Refill hingga FULL mark, sniff check tangki, periksa cap & seal, catat penambahan oli di AML."),
                ck("EOS-E2", "SVC", "Engine 2 — Service oli bila diperlukan, prosedur sama dengan Engine 1."),
                nt("Bila konsumsi oli tinggi atau ada indikasi kontaminasi bahan bakar, inisiasi tindakan lebih lanjut."),
            ]},
            {"no": 4, "title": "Fuselage", "icon": "layers", "items": [
                ck("FUS-01", "GVI", "Check kondisi radome (ref. AMM 53-15-11-200-001)."),
                ck("FUS-02", "GVI", "Check cockpit window — kerusakan/security (ref. AMM 56-10-00-200-005)."),
                ck("FUS-03", "GVI", "Check crew oxygen discharge indicator disc (hijau) — intact."),
                ck("FUS-04", "GVI", "Check static port, pitot & TAT port, serta Angle-of-Attack sensor — kerusakan/security."),
                ck("FUS-05", "GVI", "Check kondisi kulit fuselage di sekitar static source (RVSM requirement)."),
                ck("FUS-06", "GVI", "Check antena komunikasi/navigasi — kondisi & security, termasuk kulit fuselage sekitarnya."),
                ck("FUS-07", "GVI", "Check LH/RH air conditioning ram air inlet & exhaust — bebas FOD."),
                ck("FUS-08", "GVI", "Check pressure relief valve & outflow valve — kondisi & bebas obstruksi."),
                ck("FUS-09", "GVI", "Check kelengkapan fastener/screw pada fuselage."),
                ck("FUS-10", "GVI", "Check belly fairing seal — kerusakan/security."),
                find("FUS-11", "GVI", "Catatan temuan area Fuselage"),
            ]},
            {"no": 5, "title": "Placard and Marking — Fuselage", "icon": "layers", "items": [
                ck("PLM-01", "GVI", "Static port painted markings — kondisi umum (ref. AMM Fig. 11-00-00-17000-A)."),
                ck("PLM-02", "GVI", "Angle-of-Attack sensor painted markings — kondisi umum (ref. AMM Fig. 11-00-00-18000-A)."),
                ck("PLM-03", "GVI", "Ram Air Turbine painted markings — kondisi umum (ref. AMM Fig. 11-00-00-15000-A)."),
                ck("PLM-04", "GVI", "Pax door operation & warning painted markings — kondisi umum."),
                nt("Bila ada placard/painted marking yang hilang sebagian, tidak terbaca, atau tidak jelas — laporkan ke MCC dan tindak lanjuti segera."),
            ]},
            {"no": 6, "title": "FWD, AFT and Bulk Cargo Compartments", "icon": "cone", "items": [
                ck("CGO-01", "GVI", "Check kondisi seal seluruh pintu cargo sebelum ditutup; lakukan rektifikasi bila ada defect (ref. AMM Fig. 52-31-18-991-00100-C)."),
                ck("CGO-02", "GVI", "Check ketersediaan & security fly-away kit."),
                ck("CGO-03", "GVI", "Check operasi cargo doors & warning painted markings — kondisi umum."),
                ck("CGO-04", "GVI", "Visual check compartment cargo (MP 2550002004) — dekompresi, lining, floor panel & pressure compensation valve (sejauh terlihat), kerusakan/robek/tusukan/kebersihan."),
            ]},
            {"no": 7, "title": "Landing Gear & Wheelwell — General Inspection", "icon": "wheel", "items": [
                ck("LG-01", "GVI", "Check seal & komponen wheel-well door nose & main gear — abnormalitas."),
                ck("LG-02", "GVI", "General visual inspection L/G brake units — kebocoran hidrolik (ref. AMM 32-40-00-210-801)."),
                ck("LG-03", "FNC", "Check indikasi tekanan reservoir & sistem hidrolik, serta tekanan charge accumulator (ref. AMM 29-30-00-200-001/002, 29-10-00-200-008, 32-44-11-200-001) — catat di tabel di bawah."),
            ]},
            {"no": 8, "title": "Landing Gear — Hydraulic Accumulator Reading", "icon": "wheel", "items": [
                tbl("LG-ACC", "FNC", "Tekanan & Temperatur Accumulator (psi / °C)",
                    columns=["G Hyd - Pressure", "G Hyd - Temp", "B Hyd - Pressure", "B Hyd - Temp",
                             "Y Hyd - Pressure", "Y Hyd - Temp", "Brake Acc - Pressure", "Brake Acc - Temp"],
                    rows=["Before", "After"], required_rows=["Before"]),
                ck("LG-04", "GVI", "Check NLG & MLG shock struts — kebocoran; bersihkan permukaan exposed dengan kain lembab MIL-PRF-5606, lap kering."),
                ck("LG-05", "GVI", "Check RAT dalam posisi stowed dan doors tertutup."),
            ]},
            {"no": 9, "title": "Landing Gear — Brake Wear Pin", "icon": "wheel", "items": [
                ck("LG-06", "FNC", "Functional check brake heat pack wear indicator (MP 3242272000, ref. AMM 32-42-27-210-003, parking brake applied) — catat panjang pin di tabel di bawah."),
                tbl("LG-PIN", "FNC", "Brake Wear Pin Length (mm)",
                    columns=["LH MLG - Pin 1", "LH MLG - Pin 2", "RH MLG - Pin 3", "RH MLG - Pin 4"],
                    rows=["Pin Length (mm)"], required_rows=["Pin Length (mm)"]),
                ck("LG-07", "LUB", "Lubrikasi MLG main fitting lower bearing gland housing (ref. AMM 12-22-32-640-001)."),
            ]},
            {"no": 10, "title": "Landing Gear — Tire Pressure", "icon": "wheel", "items": [
                ck("LG-08", "FNC", "Inspeksi/check tekanan ban (MP 3241002003, ref. AMM 324100-210-003). Isi nitrogen saja (AD 87-08-09). Catat tekanan sebelum & sesudah recharge di tabel bawah. Ban dalam kondisi loaded (berat pesawat di roda)."),
                tbl("LG-TIRE", "FNC", "Tire Pressure (psi) — Before / After Inflation",
                    columns=["NLG - LH", "NLG - RH", "MLG - 1", "MLG - 2", "MLG - 3", "MLG - 4"],
                    rows=["Before Inflation", "After Inflation"], required_rows=["Before Inflation"],
                    unit_note="Referensi normal: NLG 178–187 psi, MLG 209–219 psi (kondisi loaded)."),
            ]},
            {"no": 11, "title": "Placard and Marking — Nose Gear", "icon": "wheel", "items": [
                ck("PLN-01", "GVI", "Nose gear leg door painted markings — kondisi umum (ref. AMM Fig. 11-00-16000-A)."),
                ck("PLN-02", "GVI", "Marking 'INFLATE WITH NITROGEN ONLY' & 'TYRE PRESS ON WHEEL' pada main/nose L/G (AD 87-08-09) — kondisi umum."),
                ck("PLN-03", "GVI", "Marking red-line 'MAX TOW BAR ANGLE' pada nose — kondisi umum."),
            ]},
            {"no": 12, "title": "LH / RH Wing", "icon": "layers", "items": [
                ck("WNG-01", "GVI", "Wing upper surface — kondisi umum (panel, flight control surface faired, engine pylon panel & fairing, vortex generator), dilihat dari jendela kabin."),
                ck("WNG-02", "GVI", "Check kelengkapan fastener/screw (upper)."),
                ck("WNG-03", "GVI", "Check wing fairing seal — kerusakan/security."),
                ck("WNG-04", "GVI", "Wing lower surface — kondisi umum (flight control surface, tank vent, leading/trailing edge, kebocoran bahan bakar & static discharge seal)."),
                ck("WNG-05", "GVI", "Wing-to-body fairing & seal — kerusakan & instalasi yang benar."),
                ck("WNG-06", "GVI", "Check kelengkapan fastener/screw (lower)."),
            ]},
            {"no": 13, "title": "Placard and Marking — Wing", "icon": "layers", "items": [
                ck("PLW-01", "GVI", "Wing painted markings — kondisi umum (ref. AMM Fig. 11-00-00-19000-A)."),
                ck("PLW-02", "GVI", "Escape area painted markings — kondisi umum (ref. AMM Fig. 11-00-00-19100-A)."),
            ]},
            {"no": 14, "title": "LH / RH Engine", "icon": "flame", "items": [
                ck("ENG2-01", "GVI", "Engine air intake, fan blades free rotation — check FOD (ref. AMM 72-00-00-200)."),
                ck("ENG2-02", "DET", "Check abradable shroud outer guide vanes, inner fan case, frame & frame strut."),
            ]},
            {"no": 15, "title": "LH / RH Engine — Outlet Guide Vane Finding", "icon": "flame", "items": [
                find("ENG2-03", "DET", "Kondisi Outlet Guide Vane — deskripsikan bila ada temuan",
                     criteria=[
                        {"Kriteria A": "Broken Vane", "Kriteria B": "Eroded surface (glass film)"},
                        {"Kriteria A": "Missing Vane", "Kriteria B": "Unbonding of metal leading edge"},
                        {"Kriteria A": "Cracks", "Kriteria B": "Metal leading edge missing"},
                        {"Kriteria A": "Missing Material", "Kriteria B": "Outer & inner platform debonding"},
                        {"Kriteria A": "Delamination", "Kriteria B": "Nicks/dents pada leading & trailing edge, concave/convex side, inner/outer platform"},
                     ]),
                nt("Bila ada temuan, lakukan damage assessment ref. AMM 72-23-00-210-003-C (CFM56-5B). Bila dalam batas layak servis, catat di ASDCS sheet dan informasikan ke MCC & planning department."),
            ]},
            {"no": 16, "title": "LH / RH Engine — Cowling & Fan Cowl", "icon": "flame", "items": [
                ck("ENG2-04", "GVI", "Engine cowling termasuk access panel & latch — secure."),
                ck("ENG2-05", "GVI", "Thrust reverser, exhaust tail plug, exhaust tail case strut, turbine blade — kondisi."),
                ck("ENG2-06", "GVI", "Perform external zonal inspection engine & pylon fairing."),
                ck("ENG2-07", "GVI", "Check kebocoran fluida di bagian bawah cowling."),
                ck("ENG2-08", "GVI", "Buka engine fan cowl — inspeksi starter untuk kebocoran oli, refill bila perlu."),
                ck("ENG2-09", "DET", "Inspeksi area TGB housing untuk jejak oli menggunakan UV light. Bila ada jejak, lakukan AMM Task 79-00-00-210-003-A."),
            ]},
            {"no": 17, "title": "Placard and Marking — Fan Cowl", "icon": "flame", "items": [
                ck("PLF-01", "GVI", "Check placard & marking Extinguisher 1 & 2 pada area pylon."),
                ck("PLF-02", "GVI", "Check placard & marking hazard area, WARNING/CAUTION, dan access name pada fan cowl."),
            ]},
            {"no": 18, "title": "IDG Oil", "icon": "flame", "items": [
                nt("Berlaku untuk Engine 1 & Engine 2 (MP 2421002102, 2421512010, 2421002000)."),
                ck("IDG-E1", "SVC", "Engine 1 — Check IDG oil level & oil-filter differential pressure indicator; service bila di bawah green band / di atas yellow band atau red button extended."),
                ck("IDG-E2", "SVC", "Engine 2 — prosedur sama dengan Engine 1."),
                wn("Prosedur overflow drain IDG bisa memakan waktu hingga 20 menit. Kegagalan mengikuti waktu overflow dapat menyebabkan level oli IDG tinggi & suhu operasi meningkat, merusak IDG."),
            ]},
            {"no": 19, "title": "Empennage, APU Area and Stabilizers", "icon": "layers", "items": [
                ck("EMP-01", "GVI", "Check rear fuselage & APU area — drain bila ada kebocoran fluida (ref. AMM 28-22-00-790-002)."),
                ck("EMP-02", "GVI", "Check APU inlet & exhaust — kerusakan yang terlihat."),
                ck("EMP-03", "GVI", "Check toilet, water & waste service panel — kondisi/kebocoran; safety plug pada fill/flush line."),
                ck("EMP-04", "GVI", "Visual check dari ground level — vertical fin/rudder, horizontal stabilizer/elevator, static discharge — kerusakan/hilang."),
                ck("EMP-05", "GVI", "Check kelengkapan fastener/screw."),
                ck("EMP-06", "VCK", "Check APU oil level pada sight glass; replenish bila diperlukan (ref. Task 12-13-49-612-001)."),
            ]},
            {"no": 20, "title": "Cabin", "icon": "users", "items": [
                wn("Saat membuka pax door: pastikan cabin door disarmed & cross-checked. Hentikan prosedur bila lampu warning merah menyala — tekanan residual dapat melukai orang dan/atau merusak pesawat."),
                ck("CAB-01", "GVI", "Check tekanan emergency cylinder/accumulator pintu penumpang/kru (MP 5210002101); charge bila tidak sesuai (ref. AMM 52-10-00-614-001)."),
                ck("CAB-02", "GVI", "Cabin carpet & floor covering, galley — kondisi umum & kebersihan."),
                ck("CAB-03", "GVI", "Attendant seat cover & harness — kerusakan/kebersihan."),
                ck("CAB-04", "GVI", "Passenger seat: cover, armrest, tray table, ashtray, seat belt, backrest — kondisi & kebersihan."),
                ck("CAB-05", "GVI", "Interior: sidewall, ceiling panel, stowage bin, partisi, dado panel — kerusakan & kebersihan."),
                ck("CAB-06", "GVI", "Pastikan potable water & toilet waste tank sudah diservis."),
                ck("CAB-07", "GVI", "Emergency equipment — check sesuai Emergency Equipment Checklist (EEL) terlampir."),
                ck("CAB-08", "GVI", "Lavatories — kerusakan/kebersihan; test flush system & water system."),
            ]},
            {"no": 21, "title": "Placard and Marking — Cabin", "icon": "users", "items": [
                ck("PLC-01", "GVI", "Check placard & marking cabin — kondisi umum."),
            ]},
            {"no": 22, "title": "Cockpit", "icon": "id", "items": [
                ck("CKP-01", "GVI", "Pastikan seluruh circuit breaker tertutup."),
                ck("CKP-02", "GVI", "Cockpit — kondisi umum & kebersihan."),
                ck("CKP-03", "GVI", "Windows, windshield, wiper blades; emergency exit handle — secured."),
                ck("CKP-04", "GVI", "Captain/FO/Observer seat & harness — kondisi & security (ref. AMM 25-11-00-200-002; ganti harness bila perlu)."),
                ck("CKP-05", "OPC", "Check & test aircraft communication equipment — lengkap."),
                ck("CKP-06", "GVI", "Seluruh instrument panel & display unit — kebersihan."),
                ck("CKP-07", "GVI", "IDG disconnect switches — normal (guarded/wired)."),
                ck("CKP-08", "GVI", "Check Navigation Data Base (NDB) — tanggal expired."),
                ck("CKP-09", "GVI", "Hydraulic brake accumulator pre-charge pressure."),
                ck("CKP-10", "GVI", "Aircraft status pada ECAM upper/lower display — tindak lanjuti sesuai kebutuhan."),
                ck("CKP-11", "GVI", "Check level fluida hidrolik (dari MCDU) — refill bila perlu, catat di AML (ref. AMM 29-10-00-200-001)."),
                ck("CKP-12", "SPC", "Review PFR print-out dan tindak lanjuti sesuai kebutuhan."),
            ]},
            {"no": 23, "title": "Cockpit — Crew Oxygen", "icon": "id", "items": [
                meas("CKP-OXY", "GVI", "Record tekanan crew oxygen bottle (psi) — ref. FCOM A320/CT LIM-35 Oxygen untuk tekanan minimum dispatch.", unit="psi"),
                nt("Tabel referensi tekanan minimum oksigen berbeda-beda menurut suhu & jumlah kru/observer sesuai MSN pesawat — lihat FCOM LIM-35 halaman 1–4."),
                ck("CKP-13", "GVI", "Check ketersediaan kertas printer, ganti bila perlu."),
                ck("CKP-14", "GVI", "Pastikan seluruh dokumen pesawat lengkap & valid sesuai Form CT-1-23."),
                ck("CKP-15", "GVI", "Emergency equipment — check kondisi, fungsi, validitas sesuai EEL."),
            ]},
            {"no": 24, "title": "Operational Checks", "icon": "radio", "items": [
                ck("OP-01", "OPC", "Operational check loop/squib fire detection engine (ref. AMM 26-12-00-710-001-A)."),
                ck("OP-02", "OPC", "Operational test APU fire & overheat detection system (ref. AMM 26-13-00-710-001-A)."),
                ck("OP-03", "OPC", "Check flight deck lighting termasuk annunciator light."),
                ck("OP-04", "OPC", "Check seluruh exterior light (runway turn-off, taxi, wing illumination, landing, anti-collision, position, strobe, logo) — iluminasi, beam, kerusakan."),
            ]},
            {"no": 25, "title": "CVR / DFDR", "icon": "radio", "items": [
                ck("CVR-01", "OPC", "Operational test CVR — Cockpit Voice Recorder (ref. AMM 23-71-00-710-001)."),
                ck("DFDR-01", "OPC", "Operational check DFDR system menggunakan MCDU (ref. AMM 31-33-00-710-006-A)."),
            ]},
            {"no": 26, "title": "Emergency Lights & AC Emergency Generation", "icon": "radio", "items": [
                ck("EML-01", "OPC", "Operational test emergency lights (MP 3351007101). Tekan TEST EMER LIGHT/SYS switch ≥3 detik; SYS OK menyala ~30 detik, mati ~60 detik."),
                wn("Sebelum tes AC Emergency Generation: pastikan travel range flight control surface bebas hambatan sebelum pressurize/depressurize sistem hidrolik."),
                ck("ACE-01", "OPC", "Operational test AC Emergency Generation System (MP 2424007001/2424007101, ref. AMM 242400-710-001) — pressurize blue hydraulic (electric pump), push EMER GEN TEST P/B, verifikasi ECAM AC page, release & depressurize."),
            ]},
            {"no": 27, "title": "Fuel for Water Contamination", "icon": "droplet", "items": [
                ck("FWC-01", "SVC", "Drain water content dari tangki main & center (MP 1232282811, ref. AMM 123228-281-001) sebelum flight/refuel atau minimum 1 jam setelahnya. Gunakan tool yang benar untuk membuka water drain valve. Drain ±1.0 liter hingga tidak ada air & tidak ada kebocoran bahan bakar."),
            ]},
            {"no": 28, "title": "Final Work", "icon": "check", "items": [
                ck("FIN-01", "GVI", "Check additional requested service (water disinfection, special inspection, TLW, dll)."),
                ck("FIN-02", "GVI", "Check seluruh Pilot Report, inspection finding, open item (HIL) sudah ditindaklanjuti; entri di AML/CML."),
                ck("FIN-03", "GVI", "Pastikan pesawat bebas dari ground equipment."),
                ck("FIN-04", "SPC", "De-energize kelistrikan; tutup & aman-kan seluruh pintu dan access panel."),
            ]},
        ],
    },

    # ------------------------------------------------------------------ #
    "Cabin Standard Check (24H)": {
        "meta": {
            "WO Number": "AUTO-24H-000217", "A/C Type": "ALL", "A/C Reg": "PK-GLV",
            "Station": "CGK", "Skill": "CABIN", "Event / Interval": "24 HOURS",
            "Chapter / Page": "12.02.01", "Manhours": "-",
        },
        "mode": "checklist",
        "sections": [
            {"no": 1, "title": "Open Items Review", "icon": "clipboard", "items": [
                nt("Sebaiknya job card ini dikerjakan setelah cabin interior cleaning selesai."),
                ck("OPN-01", "SPC", "Check Cabin Maintenance Log Book (CML) untuk open item yang masih ada."),
            ]},
            {"no": 2, "title": "Cabin — Floor", "icon": "layers", "items": [
                ck("FLR-01", "GVI", "Carpet di seluruh area kabin — kerusakan/kondisi."),
                ck("FLR-02", "GVI", "Floor covering di entry area — kerusakan/kontaminasi."),
            ]},
            {"no": 3, "title": "Cabin — Galleys", "icon": "layers", "items": [
                ck("GAL-01", "GVI", "Galley — kondisi umum, kerusakan, kontaminasi."),
                ck("GAL-02", "GVI", "Floor covering di galley — kerusakan/kontaminasi."),
            ]},
            {"no": 4, "title": "Cabin — Coatroom", "icon": "layers", "items": [
                ck("COT-01", "GVI", "Coatroom — kerusakan yang terlihat."),
            ]},
            {"no": 5, "title": "Cabin — Seats", "icon": "users", "items": [
                ck("SEA-01", "VCK", "Seat & seat cover — kerusakan/kontaminasi."),
                ck("SEA-02", "VCK", "Seat back posisi vertikal; ashtray & seat belt — presensi/kondisi (ref. AMM 25-21-00-210-001, ganti bila perlu)."),
                ck("SEA-03", "GVI", "F/C seat cover — kesesuaian pemasangan."),
                ck("SEA-04", "OPC", "Attendant seat — fungsi & kondisi (ref. AMM 25-22-00-210-001, ganti seat belt bila perlu)."),
            ]},
            {"no": 6, "title": "Cabin — Interior", "icon": "layers", "items": [
                ck("INT-01", "GVI", "Sidewall & ceiling panel, bin, partisi & curtain — kerusakan/kontaminasi."),
                ck("INT-02", "GVI", "Ceiling panel — instalasi yang benar."),
                ck("INT-03", "GVI", "Dado panel — kondisi umum."),
            ]},
            {"no": 7, "title": "Cabin — Lavatories", "icon": "layers", "items": [
                ck("LAV-01", "VCK", "Lavatories — kerusakan/kontaminasi."),
                ck("LAV-02", "OPC", "Operasikan flushing system lavatory, pastikan flushing berjalan benar."),
            ]},
            {"no": 8, "title": "Final Work", "icon": "check", "items": [
                ck("FNW-01", "GVI", "Bila ditemukan defisiensi tambahan saat cabin standard check, inisiasi tindakan korektif; catat di CML 'Cabin Standard Check Performed'. Temuan yang tidak direktifikasi saat transit dicatat di HIL."),
            ]},
        ],
    },

    # ------------------------------------------------------------------ #
    "Daily Interior Cleaning": {
        "meta": {
            "WO Number": "AUTO-CLN-000984", "A/C Type": "ALL", "A/C Reg": "PK-GLV",
            "Station": "CGK", "Skill": "CABIN", "Event / Interval": "INT CLN",
            "Chapter / Page": "14.02.98", "Manhours": "A320: 13.5 / B737: 9",
        },
        "mode": "checklist",
        "sections": [
            {"no": 1, "title": "Cockpit", "icon": "id", "items": [
                ck("CLN-01", "CLN",
                   "Windows (bersihkan dengan wet leather) · Ashtray & waste box (kosongkan & bersihkan) · "
                   "Seat covers (sikat/vacuum) · Floor (wet cleaning & vacuum carpet).",
                   status_options=CLEAN_STATUS_OPTIONS),
            ]},
            {"no": 2, "title": "Entry Areas", "icon": "door", "items": [
                ck("CLN-02", "CLN",
                   "Sidewall, ceiling panel, pintu & door frame attendant station (bersihkan dengan solusi & lap kering) · "
                   "Attendant seat cover (sikat/vacuum) · Floor (wet cleaning & lap kering).",
                   status_options=CLEAN_STATUS_OPTIONS),
            ]},
            {"no": 3, "title": "Galleys", "icon": "layers", "items": [
                ck("CLN-03", "CLN",
                   "Galley, ceiling, control panel, working place (bersihkan & lap kering) · Waste container (kosongkan, bersihkan, deodorizer) · "
                   "Oven & coffee maker (lap lembab tanpa kimia, poles pintu oven bila perlu) · Grill (bersihkan & lap kering) · "
                   "Sink (bersihkan & lap kering) · Floor bila perlu (wet cleaning) · Mirror (bersihkan & lap kering).",
                   status_options=CLEAN_STATUS_OPTIONS),
            ]},
            {"no": 4, "title": "Cabin", "icon": "layers", "items": [
                ck("CLN-04", "CLN",
                   "Sidewall, dado panel, ceiling panel, stowage bin, window shade, coat stowage, bar & partisi (bersihkan & lap kering) · "
                   "Cabin window inner pane & TV monitor screen (bersihkan & lap kering) · Carpet floor (vacuum) · Window shade (posisi upright).",
                   status_options=CLEAN_STATUS_OPTIONS),
            ]},
            {"no": 5, "title": "Cabin Seats", "icon": "users", "items": [
                ck("CLN-05", "CLN",
                   "Seat pocket (kosongkan & bersihkan) · Seat cover (sikat/vacuum) · Seat fairing & armrest (bersihkan & lap kering) · "
                   "Food table atas-bawah (bersihkan & lap kering) · Ashtray (kosongkan, bersihkan, tutup) · "
                   "Seat backrest (posisi upright) · Seat belt (bersihkan, ada, tersilang).",
                   status_options=CLEAN_STATUS_OPTIONS),
            ]},
            {"no": 6, "title": "Lavatories", "icon": "layers", "items": [
                ck("CLN-06", "CLN",
                   "Sidewall, ceiling panel, pintu & door frame (bersihkan & lap kering) · Wash basin (bersihkan & poles) · "
                   "Mirror (bersihkan & lap kering) · Ashtray (kosongkan, bersihkan, tutup) · Waste container (kosongkan, bersihkan, deodorizer) · "
                   "Lavatory seat assy (bersihkan & lap kering) · Lavatory bowl (bersihkan sesuai permukaan) · Floor (wet cleaning & lap kering).",
                   status_options=CLEAN_STATUS_OPTIONS),
            ]},
            {"no": 7, "title": "Cargo Compartment", "icon": "cone", "items": [
                ck("CLN-07", "CLN",
                   "Forward & aftward cargo compartment (vacuum cleaning, wet cleaning) · Ceiling panel (wet cleaning) · "
                   "Sidewall panel — khusus B737 (wet cleaning) · Cargo net (terpasang).",
                   status_options=CLEAN_STATUS_OPTIONS),
            ]},
            {"no": 8, "title": "Final Work", "icon": "check", "items": [
                ck("CLN-08", "CLN",
                   "Mechanic Supervisor check hasil daily interior cleaning; catat di CML 'Daily Interior Cleaning Performed'.",
                   status_options=CLEAN_STATUS_OPTIONS),
            ]},
        ],
    },

    # ------------------------------------------------------------------ #
    "Emergency Equipment Checklist": {
        "meta": {
            "WO Number": "AUTO-EEL-000552", "A/C Type": "A320", "A/C Reg": "PK-GLV",
            "Station": "CGK", "Skill": "CABIN / AP-EA", "Event / Interval": "Sesuai Effectivity",
            "Chapter / Page": "Attachment CT-2-01", "Manhours": "-",
        },
        "mode": "equipment_log",
        "sections": [
            {"no": 1, "title": "Halaman 1 dari 3 — Evacuation & Rescue", "icon": "shield", "rows": [
                ("Crash Axe", "Check for Availability and Good Condition (ref. AMM 25-65-00)"),
                ("Crew Life Vest", "Check for Validity, Quantity and Sealed at Protective Package (ref. AMM 25-66-00)"),
                ("Portable ELT", "Check for Validity / Date"),
                ("Fixed ELT", "Check for Validity / Date"),
                ("Escape Path with Rope (Cockpit)", "Check for Availability and Condition"),
                ("Escape Slide/Raft (Passenger Wing & Door)", "Check for Validity and Pressure / Green Band (ref. AMM 25-62-00)"),
                ("Overwing Escape Slide Container", "Check escape slide off-wing container condition for crack and delamination (ref. AMM 25-62-42)"),
                ("Exit Path with Escape Slide", "Operational test (ref. AMM 25-63-00)"),
                ("Fire Extinguisher BCF", "Check for Validity and Pressure / Green Band (ref. AMM 26-24-00)"),
                ("Fire Extinguisher Water", "Check for Validity and Pressure / Green Band, Quantity (ref. AMM 26-24-00)"),
                ("First Aid Kit", "Check for Validity, Quantity and Sealed at Protective Package"),
            ]},
            {"no": 2, "title": "Halaman 2 dari 3 — Personal Protection", "icon": "shield", "rows": [
                ("Flashlight", "Check for Functional Charging Cycle, Quantity"),
                ("Heat Resistant Gloves", "Check for Condition, Quantity and Sealed at Protective Package"),
                ("Infant Belt", "Check for good condition, Quantity and Sealed at Protective Package"),
                ("Lavatory Fire Extinguisher", "Check for Validity / Date and Temp. Indicator (ref. AMM 26-25-00)"),
                ("Additional Life Raft (if installed)", "Check for Validity / Date and Pressure / Green Band"),
                ("Megaphone", "Check for Quantity and Operational Test (ref. AMM 25-65-51)"),
                ("Pax Life Vest", "Check for Validity, Quantity and Sealed at Protective Package (ref. AMM 25-66-00)"),
                ("Infant Life Vest", "Check for Validity, Quantity and Sealed at Protective Package (ref. AMM 25-66-00)"),
                ("PBE / Smoke Hood with Oxygen", "Check for Validity, Quantity and Sealed at Protective Package"),
                ("Portable Oxygen Bottle & Mask", "Check for Validity, Quantity and Pressure / Green Band (ref. AMM 35-30-00)"),
                ("Demo Kit — Safety Belt", "Check for Condition and Quantity"),
            ]},
            {"no": 3, "title": "Halaman 3 dari 3 — Demo Kit & Medical", "icon": "shield", "rows": [
                ("Demo Kit — Life Vest", "Check for Condition, Quantity and Sealed at Protective Package"),
                ("Demo Kit — Oxygen Mask", "Check for Condition, Quantity and Sealed at Protective Package"),
                ("Life Vest (spare)", "Check for Condition, Quantity and Sealed at Protective Package"),
                ("Life Line", "Check for Condition and Quantity"),
                ("Survival Kit (if available)", "Check for Condition, Quantity and Sealed at Protective Package"),
                ("Emergency Medical Kit", "Check for Condition and Sealed at Protective Package"),
                ("Extension Belt", "Check for Condition and Quantity"),
                ("Manual Release Tool", "Check for Condition and Quantity"),
            ]},
        ],
    },
}

STEP_LABELS = ["Work Order", "Pemeriksaan", "Otorisasi", "Selesai"]

# ============================================================================
# 4. ICON SYSTEM
# ============================================================================
def icon(name, size=18, color="currentColor", stroke=1.8):
    paths = {
        "plane": '<path d="M2.5 16l19-6.5-2-2-7 2-6-4.5-2 .7 3.8 5.5-4.3 1.5z"/><path d="M8 18.5l2-.6.7 2-3.2 1z"/>',
        "wheel": '<circle cx="12" cy="12" r="7.5"/><circle cx="12" cy="12" r="2"/><path d="M12 4.5v3"/><path d="M12 16.5v3"/><path d="M4.5 12h3"/><path d="M16.5 12h3"/>',
        "flame": '<path d="M12 2.5c1.2 3 4 4 4 8a4 4 0 0 1-8 0c0-1.3.6-2 1.2-2.8.3 1 .9 1.4 1.3 1.1-.4-2.4.7-4.6 1.5-6.3z"/><path d="M9 16.5a3 3 0 0 0 6 0"/>',
        "users": '<path d="M17 21v-1.5a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4V21"/><circle cx="9.5" cy="7.5" r="3.5"/><path d="M22 21v-1.5a4 4 0 0 0-3-3.87"/><path d="M15 3.6a3.5 3.5 0 0 1 0 6.8"/>',
        "bell": '<path d="M6 17v-5a6 6 0 0 1 12 0v5l1.5 2.5h-15z"/><path d="M10 21a2 2 0 0 0 4 0"/>',
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
        "gauge": '<circle cx="12" cy="13" r="8"/><path d="M12 13l4-4"/><path d="M8 6.5l1 1.6"/><path d="M16 6.5l-1 1.6"/>',
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
    "submitted_at": None,
    "tech_snapshot": None,
    "station_final": "CGK",
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def reset_all():
    keys = list(st.session_state.keys())
    for k in keys:
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

        .tech-card { display:flex; align-items:center; gap:14px; background: var(--success-bg); border:1px solid #BEE7D4; border-radius: var(--radius-md); padding:14px 16px; margin-bottom:16px; }
        .tech-avatar { width:42px; height:42px; border-radius:10px; background: linear-gradient(135deg, var(--steel-600), var(--cyan-400)); display:flex; align-items:center; justify-content:center; color:#fff; font-weight:800; font-family:'Montserrat',sans-serif; flex-shrink:0; }
        .tech-name { font-weight:700; font-size:14px; color: var(--ink-900); margin:0; }
        .tech-meta { font-size:11px; color: var(--slate-500); margin:1px 0 0 0; font-family:'JetBrains Mono',monospace; }

        .fail-summary-item { display:flex; gap:10px; padding:10px 0; border-bottom:1px solid var(--slate-100); font-size:12.5px; }
        .fail-summary-item:last-child { border-bottom:none; }

        .badge { display:inline-flex; align-items:center; gap:5px; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:700; }
        .badge-pass { color: var(--success); background: var(--success-bg); }
        .badge-fail { color: var(--danger); background: var(--danger-bg); }
        .badge-na { color: var(--slate-500); background: var(--slate-100); }
        .badge-skill { color: var(--steel-600); background: #EAF3F9; font-family:'JetBrains Mono',monospace; }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# 7. HEADER + STEPPER
# ============================================================================
st.markdown(f"""
    <div class="header-box">
        <p class="header-eyebrow">GMF AeroAsia &middot; Digital Maintenance Release</p>
        <h2 class="header-title">{icon('clipboard', 19, '#FFFFFF')} E-Task Card System</h2>
        <p class="header-sub">Digitalisasi penuh dari Form CT-2-01/A2-04, A2-09, A2-10 &amp; Attachment CT-2-01 — tidak ada halaman atau tanda tangan yang bisa terlewat.</p>
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
        complete = val not in ("⚠️ Belum Dicek", "⚠️ Belum Dikerjakan")
        if val == "❌ FAIL":
            remark = st.text_area("Catatan temuan (wajib diisi)", key=f"remark_{code}",
                                   placeholder="Jelaskan temuan, kondisi, dan tindakan yang diambil...")
            st.session_state.remarks[code] = remark
            if not remark.strip():
                complete = False
        else:
            st.session_state.remarks[code] = ""
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
        val = st.number_input(f"Nilai ({item['unit']})", key=f"meas_{code}", value=None,
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
            with st.expander("Lihat kriteria kerusakan (referensi AMM)"):
                st.table(pd.DataFrame(item["criteria"]))
        nil = st.checkbox("Tidak ada temuan (NIL)", value=True, key=f"nil_{code}")
        if nil:
            st.session_state.responses[code] = "NIL"
            st.markdown("</div>", unsafe_allow_html=True)
            return True
        else:
            txt = st.text_area("Deskripsikan kondisi temuan di bawah ini",
                                key=f"findtext_{code}", placeholder="Jelaskan temuan secara rinci...")
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
    df = pd.DataFrame(section["rows"], columns=["Equipment", "Deskripsi"])
    df["Remark"] = ""
    key = f"eq_{section['no']}"
    edited = st.data_editor(
        df, key=key, hide_index=True, use_container_width=True,
        column_config={
            "Equipment": st.column_config.TextColumn("Equipment", disabled=True, width="medium"),
            "Deskripsi": st.column_config.TextColumn("Deskripsi", disabled=True, width="large"),
            "Remark": st.column_config.TextColumn("Remark (wajib diisi)", required=True, width="medium"),
        },
    )
    st.session_state.responses[key] = edited
    remarks = edited["Remark"].fillna("").astype(str).str.strip()
    return bool((remarks != "").all()) and len(remarks) > 0

# ============================================================================
# STEP 0 — WORK ORDER / PILIH JOB CARD
# ============================================================================
if st.session_state.step == 0:
    st.markdown(f"<div class='sub-header'><span class='sh-icon'>{icon('file', 14)}</span>A. Work Order Details</div>", unsafe_allow_html=True)
    st.markdown('<div class="panel">', unsafe_allow_html=True)

    job_card_type = st.selectbox("Jenis Job Card", options=list(JOB_CARDS.keys()),
                                  index=list(JOB_CARDS.keys()).index(st.session_state.job_card_type))
    card = JOB_CARDS[job_card_type]
    meta = card["meta"]

    cols = st.columns(2)
    meta_items = list(meta.items())
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

    n_sections = len(card["sections"])
    st.info(f"📋 **{job_card_type}** berisi **{n_sections} halaman pemeriksaan**. Setiap halaman wajib diselesaikan sebelum bisa lanjut ke halaman berikutnya.")

    if st.button("Mulai Pemeriksaan  →", use_container_width=True, type="primary"):
        st.session_state.step = 1
        st.rerun()

# ============================================================================
# STEP 1 — PAGINATED CHECKLIST (per section = 1 halaman, tidak bisa di-skip)
# ============================================================================
elif st.session_state.step == 1:
    card = JOB_CARDS[st.session_state.job_card_type]
    sections = card["sections"]
    mode = card.get("mode", "checklist")
    idx = st.session_state.section_idx
    idx = max(0, min(idx, len(sections) - 1))
    st.session_state.section_idx = idx
    section = sections[idx]

    st.progress((idx) / len(sections), text=f"Halaman {idx + 1} dari {len(sections)}")
    st.markdown(f"<div class='sub-header'><span class='sh-icon'>{icon(section.get('icon', 'clipboard'), 14)}</span>{section['no']}. {section['title']}</div>", unsafe_allow_html=True)

    if mode == "equipment_log":
        st.markdown("🔒 Kolom **Remark** wajib diisi untuk setiap peralatan (kondisi / tanggal validitas / N/A).")
        complete = render_equipment_section(section)
        if not complete:
            st.warning("🚨 Masih ada baris equipment yang kolom Remark-nya kosong. Lengkapi dulu sebelum lanjut.")
    else:
        complete = render_checklist_section(section)
        n_missing = sum(
            1 for it in section["items"]
            if it["kind"] == "check" and st.session_state.responses.get(it["code"]) in ("⚠️ Belum Dicek", "⚠️ Belum Dikerjakan")
        )
        if not complete:
            st.warning("🚨 Masih ada item yang belum diisi lengkap (termasuk catatan temuan untuk status FAIL) di halaman ini. Semua wajib diisi sebelum lanjut.")

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("←  Kembali", use_container_width=True, type="secondary"):
            if idx == 0:
                st.session_state.step = 0
            else:
                st.session_state.section_idx = idx - 1
            st.rerun()
    with col_next:
        is_last = idx == len(sections) - 1
        label = "Lanjut ke Otorisasi  →" if is_last else "Halaman Berikutnya  →"
        if st.button(label, use_container_width=True, type="primary", disabled=not complete):
            if is_last:
                st.session_state.step = 2
            else:
                st.session_state.section_idx = idx + 1
            st.rerun()

# ============================================================================
# STEP 2 — AUTHORIZATION & DIGITAL RELEASE
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
            st.markdown(f"<div style='font-weight:700; font-size:12.5px; margin-bottom:6px; color:#C5303A;'>{icon('alert', 13, '#C5303A')} {len(fails) + len(findings)} item memerlukan review sebelum rilis</div>", unsafe_allow_html=True)
            for it in fails:
                note = st.session_state.remarks.get(it["code"], "").strip() or "(tanpa catatan)"
                st.markdown(f"""<div class="fail-summary-item"><span class="badge badge-fail">{it['code']}</span>
                    <div><b>FAIL</b><br><span style="color:#5B6B80;">{note}</span></div></div>""", unsafe_allow_html=True)
            for it in findings:
                note = st.session_state.responses.get(it["code"], "").strip()
                st.markdown(f"""<div class="fail-summary-item"><span class="badge badge-fail">{it['code']}</span>
                    <div><b>Temuan</b><br><span style="color:#5B6B80;">{note}</span></div></div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="panel" style="display:flex; align-items:center; gap:10px;">{icon("check", 18, "#148F5E")} <span style="font-size:13px; font-weight:600;">Seluruh item PASS / N/A / Selesai — tidak ada temuan.</span></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="panel" style="display:flex; align-items:center; gap:10px;">{icon("shield", 18, "#0E5C8C")} <span style="font-size:13px; font-weight:600;">Seluruh {sum(len(s["rows"]) for s in sections)} item Emergency Equipment sudah direkam remark-nya.</span></div>', unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("**24. Maintenance Release** — lengkapi data rilis berikut sebagai pengganti kolom Station/Date/Time/Sign pada form kertas.")
    c1, c2 = st.columns(2)
    with c1:
        station_final = st.text_input("Station", value=st.session_state.station_final, key="station_final_input")
        st.session_state.station_final = station_final
    with c2:
        st.text_input("Date / Time", value=datetime.now().strftime("%d %b %Y | %H:%M WIB"), disabled=True)

    st.markdown("🔒 **Digital sign-off** — masukkan PIN pegawai sebagai pengganti tanda tangan basah. PIN otomatis mengonfirmasi identitas &amp; lisensi teknisi.")
    pin_input = st.text_input("Technician PIN (demo: 1234 atau 5678)", type="password", max_chars=4,
                               placeholder="••••", key="pin_field")
    tech = TECHNICIAN_DB.get(pin_input) if len(pin_input) == 4 else None
    if len(pin_input) == 4 and tech is None:
        st.error("🚨 PIN tidak dikenali dalam sistem. Pastikan PIN pegawai Anda benar.")

    declaration = False
    if tech:
        st.markdown(f"""
            <div class="tech-card">
                <div class="tech-avatar">{tech['name'][:2].upper()}</div>
                <div>
                    <p class="tech-name">{tech['name']}</p>
                    <p class="tech-meta">{tech['license']} &middot; Rating {tech['rating']}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        declaration = st.checkbox(
            "\"Saya menyatakan pesawat/kabin ini telah dirawat & diperiksa sesuai persyaratan regulasi keselamatan penerbangan sipil Indonesia yang berlaku, dan dalam kondisi laik operasi (airworthy).\"",
            key="declaration_check"
        )
    st.markdown('</div>', unsafe_allow_html=True)

    can_submit = tech is not None and declaration

    col_back, col_submit = st.columns(2)
    with col_back:
        if st.button("←  Kembali ke Halaman Terakhir", use_container_width=True, type="secondary"):
            st.session_state.step = 1
            st.session_state.section_idx = len(sections) - 1
            st.rerun()
    with col_submit:
        if st.button("📤  Submit &amp; Release", use_container_width=True, type="primary", disabled=not can_submit):
            with st.spinner("Mengenkripsi data dan mengirim ke server pusat..."):
                time.sleep(1.4)
            st.session_state.submitted_at = datetime.now()
            st.session_state.tech_snapshot = tech
            st.session_state.step = 3
            st.rerun()

# ============================================================================
# STEP 3 — CONFIRMATION
# ============================================================================
elif st.session_state.step == 3:
    card = JOB_CARDS[st.session_state.job_card_type]
    sections = card["sections"]
    mode = card.get("mode", "checklist")
    tech = st.session_state.get("tech_snapshot") or {}

    st.markdown(f"<div class='sub-header'><span class='sh-icon'>{icon('check', 14)}</span>Job Card Released</div>", unsafe_allow_html=True)
    st.success("✅ **JOB CARD BERHASIL DI-SUBMIT & DIRILIS!**")

    if mode == "checklist":
        all_checks = [it for s in sections for it in s["items"] if it["kind"] == "check"]
        pass_count = sum(1 for it in all_checks if st.session_state.responses.get(it["code"]) in ("✅ PASS", "✅ Selesai"))
        fail_count = sum(1 for it in all_checks if st.session_state.responses.get(it["code"]) == "❌ FAIL")
        na_count = sum(1 for it in all_checks if st.session_state.responses.get(it["code"]) == "➖ N/A")
        badges = f"""<span class="badge badge-pass">{pass_count} PASS/Selesai</span>
            <span class="badge badge-fail">{fail_count} FAIL</span>
            <span class="badge badge-na">{na_count} N/A</span>"""
    else:
        total_rows = sum(len(s["rows"]) for s in sections)
        badges = f'<span class="badge badge-pass">{total_rows} Equipment Direkam</span>'

    st.markdown(f"""
        <div class="panel">
            <div style="display:flex; justify-content:space-between; margin-bottom:14px; flex-wrap:wrap; gap:10px;">
                <div><div class="task-code">Jenis Job Card</div><div style="font-weight:700;">{st.session_state.job_card_type}</div></div>
                <div><div class="task-code">Station</div><div style="font-weight:700;">{st.session_state.station_final}</div></div>
                <div><div class="task-code">Waktu Rilis</div><div class="mono" style="font-weight:700;">{st.session_state.submitted_at.strftime('%H:%M:%S WIB')}</div></div>
            </div>
            <div style="display:flex; gap:8px; margin-bottom:14px; flex-wrap:wrap;">{badges}</div>
            <div style="border-top:1px solid #E4E9F0; padding-top:12px; font-size:12.5px; color:#5B6B80;">
                Ditandatangani secara digital oleh <b style="color:#0B1220;">{tech.get('name', '-')}</b> ({tech.get('license', '-')}).
                Status pesawat otomatis terupdate di Dashboard Command Center.
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.balloons()

    if st.button("＋  Buat Job Card Baru", use_container_width=True, type="primary"):
        reset_all()
        st.rerun()
