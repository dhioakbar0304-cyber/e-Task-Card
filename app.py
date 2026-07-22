import streamlit as st
from datetime import datetime
import time

# ============================================================================
# 1. KONFIGURASI HALAMAN (centered, seperti layar iPad yang dipegang teknisi)
# ============================================================================
st.set_page_config(
    page_title="GMF - e-Task Card",
    page_icon="🛠️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# 2. "DATABASE" SIMULASI — di produksi ini idealnya ditarik dari AMOS/Core MRO
# ============================================================================
WORK_ORDER = {
    "wo_number": "WO-2026-071842",
    "ac_reg": "PK-GIA (B777-300ER)",
    "station": "CGK - Apron T3",
}

# PIN memetakan ke identitas teknisi — meniru scan badge pegawai, bukan isian
# nama bebas, supaya tanda tangan digital terikat pada identitas yang tervalidasi.
TECHNICIAN_DB = {
    "1234": {"name": "Ahmad Fadli", "license": "AMEL A-2201", "rating": "B777/B737"},
    "5678": {"name": "Budi Santoso", "license": "AMEL A-1187", "rating": "A320/B737"},
}

TASK_LIBRARY = {
    "Daily Check": [
        {"code": "EXT-01", "category": "Exterior", "icon": "plane",
         "desc": "Cek kondisi radome dan pitot tubes dari kerusakan/sumbatan."},
        {"code": "LG-01", "category": "Landing Gear", "icon": "wheel",
         "desc": "Periksa tekanan ban dan indikator keausan rem (brake wear pin)."},
        {"code": "ENG-01", "category": "Engine", "icon": "flame",
         "desc": "Cek level oli mesin dan pastikan tidak ada kebocoran di cowling."},
        {"code": "CAB-01", "category": "Cabin", "icon": "users",
         "desc": "Periksa seluruh pintu darurat bersih dari halangan."},
        {"code": "CAB-02", "category": "Cabin Sign", "icon": "bell",
         "desc": "Uji coba lampu 'Fasten Seatbelt' dan PA System berfungsi normal."},
    ],
    "Weekly Check": [
        {"code": "AF-01", "category": "Airframe", "icon": "layers",
         "desc": "Periksa kondisi struktur fuselage dan sambungan panel dari retak/korosi."},
        {"code": "LG-02", "category": "Landing Gear", "icon": "wheel",
         "desc": "Lakukan pengukuran tekanan nitrogen pada shock strut."},
        {"code": "ENG-02", "category": "Engine", "icon": "flame",
         "desc": "Lakukan borescope check ringan pada fan blade bila diperlukan."},
        {"code": "HYD-01", "category": "Hydraulic", "icon": "droplet",
         "desc": "Periksa level fluida hidrolik sistem primer dan cadangan."},
        {"code": "AVI-01", "category": "Avionics", "icon": "radio",
         "desc": "Uji fungsi sistem navigasi dan komunikasi cockpit."},
    ],
    "Before Departure": [
        {"code": "BD-01", "category": "Walkaround", "icon": "plane",
         "desc": "Pastikan tidak ada kebocoran fluida terlihat di bawah pesawat."},
        {"code": "BD-02", "category": "Doors", "icon": "door",
         "desc": "Pastikan seluruh pintu tertutup dan terkunci sempurna."},
        {"code": "BD-03", "category": "Ground Equipment", "icon": "cone",
         "desc": "Pastikan seluruh ground equipment sudah dilepas dari pesawat."},
        {"code": "BD-04", "category": "Cabin", "icon": "users",
         "desc": "Pastikan kabin bersih dan siap untuk boarding penumpang."},
        {"code": "BD-05", "category": "Documents", "icon": "file",
         "desc": "Pastikan Aircraft Flight Log lengkap dan sudah ditandatangani."},
    ],
}

STATUS_OPTIONS = ["⚠️ Belum Dicek", "✅ PASS", "❌ FAIL", "➖ N/A"]

# ============================================================================
# 3. ICON SYSTEM — monoline SVG kecil, konsisten dengan Manpower Dashboard
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
        "arrow-right": '<path d="M4 12h16"/><path d="M14 6l6 6-6 6"/>',
        "arrow-left": '<path d="M20 12H4"/><path d="M10 18l-6-6 6-6"/>',
        "clipboard": '<rect x="6" y="4" width="12" height="17" rx="2"/><rect x="9" y="2" width="6" height="3.5" rx="1"/><path d="M9 11h6"/><path d="M9 15h6"/>',
    }
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-4px;">{paths.get(name, "")}</svg>'

# ============================================================================
# 4. SESSION STATE
# ============================================================================
_defaults = {
    "step": 0,
    "check_type": "Daily Check",
    "responses": {},
    "remarks": {},
    "pin_input": "",
    "declaration": False,
    "submitted_at": None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def reset_all():
    for k, v in _defaults.items():
        st.session_state[k] = v

# ============================================================================
# 5. DESIGN SYSTEM
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
        .block-container { padding-top: 2.2rem !important; padding-bottom: 3rem !important; max-width: 720px; }

        /* ---- Header ---- */
        .header-box {
            background: linear-gradient(135deg, var(--navy-950) 0%, var(--navy-900) 60%, var(--steel-700) 150%);
            color: white; padding: 26px 28px; border-radius: var(--radius-lg);
            margin-bottom: 22px; box-shadow: var(--shadow-md); position: relative; overflow: hidden;
        }
        .header-box::before {
            content:""; position:absolute; inset:0;
            background-image: linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px),
                               linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px);
            background-size: 26px 26px; pointer-events:none;
        }
        .header-eyebrow { color: var(--cyan-400); font-family:'JetBrains Mono',monospace; font-size:10.5px; letter-spacing:2px; text-transform:uppercase; font-weight:600; margin:0 0 6px 0; position:relative; }
        .header-title { margin:0; font-weight:900; font-size:22px; letter-spacing:0.3px; font-family:'Montserrat',sans-serif; position:relative; }
        .header-sub { margin:6px 0 0 0; font-size:12.5px; color:#A9BCCF; position:relative; }
        .header-wo { margin-top:14px; padding-top:14px; border-top:1px solid rgba(255,255,255,0.12); display:flex; justify-content:space-between; font-size:11px; color:#8FB4CE; font-family:'JetBrains Mono',monospace; position:relative; }

        /* ---- Stepper ---- */
        .stepper { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:26px; padding:0 4px; }
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

        /* ---- Section headers & cards ---- */
        .sub-header {
            color: var(--ink-900); font-weight:700; font-size:13px; letter-spacing:0.6px; text-transform:uppercase;
            margin-top:6px; margin-bottom:16px; display:flex; align-items:center; gap:9px; font-family:'Montserrat',sans-serif;
        }
        .sub-header .sh-icon { width:26px; height:26px; border-radius:8px; background:var(--slate-100); color:var(--steel-600); display:flex; align-items:center; justify-content:center; }

        .panel { background:#fff; border:1px solid var(--slate-200); border-radius: var(--radius-lg); padding:20px 22px; box-shadow: var(--shadow-md); margin-bottom:18px; }

        .task-card { background:#fff; border:1px solid var(--slate-200); border-radius: var(--radius-md); padding:16px 18px; margin-bottom:14px; box-shadow: var(--shadow-sm); }
        .task-top { display:flex; align-items:flex-start; gap:12px; margin-bottom:12px; }
        .task-icon { width:34px; height:34px; border-radius:9px; background:var(--slate-100); color:var(--steel-600); display:flex; align-items:center; justify-content:center; flex-shrink:0; }
        .task-code { font-family:'JetBrains Mono',monospace; font-size:10.5px; color:var(--slate-400); font-weight:600; letter-spacing:0.4px; }
        .task-category { font-size:10.5px; font-weight:700; color:var(--steel-600); text-transform:uppercase; letter-spacing:0.6px; margin-bottom:2px; }
        .task-desc { font-size:13.5px; color:var(--ink-900); line-height:1.45; margin:0; }

        /* Segmented radio look, more touch-friendly like an iPad control */
        div[role="radiogroup"] { gap:6px !important; }
        div[role="radiogroup"] label {
            border:1.5px solid var(--slate-200) !important; border-radius:9px !important; padding:8px 12px !important;
            background:#fff !important; transition: all 0.12s ease;
        }
        div[role="radiogroup"] label:hover { border-color: var(--steel-400) !important; }

        /* ---- Buttons ---- */
        div.stButton > button {
            font-weight:700 !important; border-radius:11px !important; padding:14px !important; border:none !important;
            font-size:14.5px !important; letter-spacing:0.2px; transition: all 0.15s ease;
        }
        div.stButton > button[kind="primary"] { background: linear-gradient(135deg, var(--steel-600), var(--steel-700)) !important; color:#fff !important; box-shadow:0 6px 18px rgba(14,92,140,0.25); }
        div.stButton > button[kind="primary"]:hover:not(:disabled) { transform: translateY(-1px); box-shadow:0 8px 22px rgba(14,92,140,0.32); }
        div.stButton > button[kind="secondary"] { background:#fff !important; color: var(--ink-900) !important; border:1.5px solid var(--slate-200) !important; }
        div.stButton > button:disabled { opacity:0.45 !important; box-shadow:none !important; }

        /* ---- Badges / identity card ---- */
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
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# 6. HEADER
# ============================================================================
st.markdown(f"""
    <div class="header-box">
        <p class="header-eyebrow">GMF AeroAsia &middot; Digital Maintenance Release</p>
        <h2 class="header-title">{icon('clipboard', 20, '#FFFFFF')} E-Task Card System</h2>
        <p class="header-sub">Checklist wajib diselesaikan berurutan — tidak ada halaman atau tanda tangan yang bisa terlewat.</p>
        <div class="header-wo">
            <span>WO &nbsp;{WORK_ORDER['wo_number']}</span>
            <span>{WORK_ORDER['ac_reg']}</span>
            <span>{WORK_ORDER['station']}</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# ============================================================================
# 7. STEPPER
# ============================================================================
STEP_LABELS = ["Work Order", "Checklist", "Otorisasi", "Selesai"]

def render_stepper(current):
    items = ""
    for i, label in enumerate(STEP_LABELS):
        state = "done" if i < current else ("active" if i == current else "")
        circle_content = icon("check", 13, "#FFFFFF") if i < current else str(i + 1)
        items += f'<div class="step-item {state}"><div class="step-circle">{circle_content}</div><div class="step-label">{label}</div></div>'
    st.markdown(f'<div class="stepper">{items}</div>', unsafe_allow_html=True)

render_stepper(st.session_state.step)

# ============================================================================
# STEP 0 — WORK ORDER DETAILS
# ============================================================================
if st.session_state.step == 0:
    st.markdown(f"<div class='sub-header'><span class='sh-icon'>{icon('file', 14)}</span>A. Work Order Details</div>", unsafe_allow_html=True)
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("A/C Registration", value=WORK_ORDER["ac_reg"], disabled=True)
        st.text_input("Station Hub", value=WORK_ORDER["station"], disabled=True)
    with c2:
        check_type = st.selectbox("Jenis Pemeriksaan", options=list(TASK_LIBRARY.keys()),
                                   index=list(TASK_LIBRARY.keys()).index(st.session_state.check_type))
        st.text_input("Timestamp Dibuka", value=datetime.now().strftime("%d %b %Y | %H:%M WIB"), disabled=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if check_type != st.session_state.check_type:
        st.session_state.check_type = check_type
        st.session_state.responses = {}
        st.session_state.remarks = {}

    n_items = len(TASK_LIBRARY[check_type])
    st.info(f"📋 Jenis pemeriksaan **{check_type}** berisi **{n_items} item** yang wajib diperiksa satu per satu di halaman berikutnya.")

    if st.button("Mulai Pemeriksaan  →", use_container_width=True, type="primary"):
        st.session_state.step = 1
        st.rerun()

# ============================================================================
# STEP 1 — INSPECTION CHECKLIST (tidak bisa lanjut kalau ada yang kosong)
# ============================================================================
elif st.session_state.step == 1:
    tasks = TASK_LIBRARY[st.session_state.check_type]
    st.markdown(f"<div class='sub-header'><span class='sh-icon'>{icon('clipboard', 14)}</span>B. Inspection Checklist — {st.session_state.check_type}</div>", unsafe_allow_html=True)

    answered_count = sum(1 for t in tasks if st.session_state.responses.get(t["code"], "⚠️ Belum Dicek") != "⚠️ Belum Dicek")
    st.progress(answered_count / len(tasks), text=f"{answered_count} / {len(tasks)} item terisi")

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("⚠️ **MANDATORY** — seluruh item wajib diperiksa. Item berstatus **FAIL** wajib disertai catatan temuan sebelum bisa lanjut.")
    st.markdown('</div>', unsafe_allow_html=True)

    all_answered = True
    fail_missing_remark = False

    for t in tasks:
        code = t["code"]
        st.markdown(f"""
            <div class="task-card">
                <div class="task-top">
                    <div class="task-icon">{icon(t['icon'], 17)}</div>
                    <div>
                        <div class="task-category">{t['category']} &nbsp;·&nbsp; <span class="mono" style="color:#8D9BAF;">{code}</span></div>
                        <p class="task-desc">{t['desc']}</p>
                    </div>
                </div>
        """, unsafe_allow_html=True)

        val = st.radio(f"Status {code}", options=STATUS_OPTIONS, horizontal=True,
                        key=f"radio_{code}", label_visibility="collapsed")
        st.session_state.responses[code] = val

        if val == "⚠️ Belum Dicek":
            all_answered = False
        if val == "❌ FAIL":
            remark = st.text_area("Catatan temuan (wajib diisi)", key=f"remark_{code}",
                                   placeholder="Jelaskan temuan, kondisi, dan tindakan yang diambil...")
            st.session_state.remarks[code] = remark
            if not remark.strip():
                fail_missing_remark = True
        else:
            st.session_state.remarks[code] = ""

        st.markdown("</div>", unsafe_allow_html=True)

    can_proceed = all_answered and not fail_missing_remark

    if not all_answered:
        st.warning(f"🚨 Masih ada **{len(tasks) - answered_count} item** berstatus 'Belum Dicek'. Semua item wajib diisi sebelum lanjut ke otorisasi.")
    elif fail_missing_remark:
        st.warning("🚨 Ada item berstatus **FAIL** yang belum diberi catatan temuan. Lengkapi dulu sebelum lanjut.")

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("←  Kembali", use_container_width=True, type="secondary"):
            st.session_state.step = 0
            st.rerun()
    with col_next:
        if st.button("Lanjut ke Otorisasi  →", use_container_width=True, type="primary", disabled=not can_proceed):
            st.session_state.step = 2
            st.rerun()

# ============================================================================
# STEP 2 — AUTHORIZATION & DIGITAL RELEASE
# ============================================================================
elif st.session_state.step == 2:
    tasks = TASK_LIBRARY[st.session_state.check_type]
    fails = [t for t in tasks if st.session_state.responses.get(t["code"]) == "❌ FAIL"]

    st.markdown(f"<div class='sub-header'><span class='sh-icon'>{icon('lock', 14)}</span>C. Authorization &amp; Release</div>", unsafe_allow_html=True)

    if fails:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(f"<div style='font-weight:700; font-size:12.5px; margin-bottom:6px; color:#C5303A;'>{icon('alert', 13, '#C5303A')} {len(fails)} item ditemukan FAIL — wajib direview sebelum rilis</div>", unsafe_allow_html=True)
        for t in fails:
            note = st.session_state.remarks.get(t["code"], "").strip() or "(tanpa catatan)"
            st.markdown(f"""
                <div class="fail-summary-item">
                    <span class="badge badge-fail">{t['code']}</span>
                    <div><b>{t['category']}</b><br><span style="color:#5B6B80;">{note}</span></div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="panel" style="display:flex; align-items:center; gap:10px;">{icon("check", 18, "#148F5E")} <span style="font-size:13px; font-weight:600;">Seluruh {len(tasks)} item PASS / N/A — tidak ada temuan.</span></div>', unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("🔒 **Digital sign-off** — masukkan PIN pegawai Anda sebagai pengganti tanda tangan basah. PIN akan otomatis mengonfirmasi identitas &amp; lisensi teknisi.")

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
            "Saya menyatakan seluruh item pada job card ini telah diperiksa sesuai prosedur dan data yang saya masukkan adalah benar.",
            key="declaration_check"
        )
    st.markdown('</div>', unsafe_allow_html=True)

    can_submit = tech is not None and declaration

    col_back, col_submit = st.columns(2)
    with col_back:
        if st.button("←  Kembali ke Checklist", use_container_width=True, type="secondary"):
            st.session_state.step = 1
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
    st.markdown(f"<div class='sub-header'><span class='sh-icon'>{icon('check', 14)}</span>Job Card Released</div>", unsafe_allow_html=True)
    st.success("✅ **JOB CARD BERHASIL DI-SUBMIT & DIRILIS!**")

    tasks = TASK_LIBRARY[st.session_state.check_type]
    pass_count = sum(1 for t in tasks if st.session_state.responses.get(t["code"]) == "✅ PASS")
    fail_count = sum(1 for t in tasks if st.session_state.responses.get(t["code"]) == "❌ FAIL")
    na_count = sum(1 for t in tasks if st.session_state.responses.get(t["code"]) == "➖ N/A")
    tech = st.session_state.get("tech_snapshot") or {}

    st.markdown(f"""
        <div class="panel">
            <div style="display:flex; justify-content:space-between; margin-bottom:14px;">
                <div><div class="task-category">Work Order</div><div style="font-weight:700;">{WORK_ORDER['wo_number']}</div></div>
                <div><div class="task-category">Jenis Check</div><div style="font-weight:700;">{st.session_state.check_type}</div></div>
                <div><div class="task-category">Waktu Rilis</div><div class="mono" style="font-weight:700;">{st.session_state.submitted_at.strftime('%H:%M:%S WIB')}</div></div>
            </div>
            <div style="display:flex; gap:8px; margin-bottom:14px;">
                <span class="badge badge-pass">{pass_count} PASS</span>
                <span class="badge badge-fail">{fail_count} FAIL</span>
                <span class="badge badge-na">{na_count} N/A</span>
            </div>
            <div style="border-top:1px solid #E4E9F0; padding-top:12px; font-size:12.5px; color:#5B6B80;">
                Ditandatangani secara digital oleh <b style="color:#0B1220;">{tech.get('name','-')}</b> ({tech.get('license','-')}).
                Status pesawat otomatis terupdate di Dashboard Command Center.
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.balloons()

    if st.button("＋  Buat Job Card Baru", use_container_width=True, type="primary"):
        reset_all()
        st.rerun()
