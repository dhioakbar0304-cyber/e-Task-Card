import streamlit as st
from datetime import datetime
import time

# 1. KONFIGURASI HALAMAN (Centered biar kayak layar iPad/Tablet)
st.set_page_config(
    page_title="GMF - e-Task Card",
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# 🎨 CSS KUSTOM BUAT TAMPILAN CLEAN MRO
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
        html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
        .header-box { background-color: #041226; color: white; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px; }
        .sub-header { color: #005C97; font-weight: 800; font-size: 18px; margin-top: 20px; border-bottom: 2px solid #E2E8F0; padding-bottom: 5px; margin-bottom: 15px;}
        div.stButton > button { background-color: #10B981 !important; color: white !important; font-weight: 800 !important; border-radius: 8px !important; padding: 15px !important; border: none; }
        div.stButton > button:hover { background-color: #059669 !important; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4); }
    </style>
""", unsafe_allow_html=True)

# 🏢 HEADER IPAD APP
st.markdown("""
    <div class="header-box">
        <h2 style="margin:0; font-weight: 900; letter-spacing: 2px;">📱 E-TASK CARD SYSTEM</h2>
        <p style="margin:0; font-size: 14px; color: #00C9FF;">Digital Maintenance Release</p>
    </div>
""", unsafe_allow_html=True)

# ✈️ INFORMASI JOB CARD (Otomatis terisi dari sistem AMOS/Core MRO)
st.markdown("<div class='sub-header'>A. WORK ORDER DETAILS</div>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.text_input("A/C Registration", value="PK-GIA (B777-300ER)", disabled=True)
    st.text_input("Station Hub", value="CGK - Apron T3", disabled=True)
with c2:
    st.text_input("Task Type", value="Daily Check & Cabin Standard", disabled=True)
    st.text_input("Timestamp", value=datetime.now().strftime("%d %b %Y | %H:%M WIB"), disabled=True)

# 📋 CHECKLIST SECTION
st.markdown("<div class='sub-header'>B. INSPECTION CHECKLIST</div>", unsafe_allow_html=True)
st.info("⚠️ **MANDATORY:** Seluruh item wajib diperiksa dan diisi statusnya. Pilih 'N/A' jika tidak relevan.")

# Simulasi data task card
tasks = [
    "1. EXTERIOR: Cek kondisi radome dan pitot tubes dari kerusakan/sumbatan.",
    "2. LANDING GEAR: Periksa tekanan ban dan indikator keausan rem (brake wear pin).",
    "3. ENGINE: Cek level oli mesin dan pastikan tidak ada kebocoran di cowling.",
    "4. CABIN: Periksa seluruh pintu darurat bersih dari halangan.",
    "5. CABIN SIGN: Uji coba lampu 'Fasten Seatbelt' dan PA System berfungsi normal."
]

# Simpan jawaban di dictionary
responses = {}
for i, task in enumerate(tasks):
    st.markdown(f"**{task}**")
    # Pilihan default kita kasih string kosong atau peringatan biar teknisi WAJIB milih
    responses[task] = st.radio(
        f"Status {i}", 
        options=["⚠️ Belum Dicek", "✅ PASS", "❌ FAIL", "➖ N/A"], 
        horizontal=True, 
        key=f"task_{i}",
        label_visibility="collapsed"
    )
    st.markdown("<hr style='margin: 10px 0; border-top: 1px dashed #E2E8F0;'>", unsafe_allow_html=True)

# ✍️ SIGNATURE & RELEASE SECTION
st.markdown("<div class='sub-header'>C. AUTHORIZATION & RELEASE</div>", unsafe_allow_html=True)
st.warning("🔒 Masukkan 4-Digit PIN Personal Anda sebagai pengganti tanda tangan basah.")

pin_input = st.text_input("Technician PIN (Contoh input: 1234)", type="password", max_chars=4, placeholder="••••")

st.markdown("<br>", unsafe_allow_html=True)

# 🚨 LOGIC SUBMISSION (ANTI-BOLONG)
if st.button("📤 SUBMIT & RELEASE JOB CARD", use_container_width=True):
    # 1. Cek apakah masih ada yang belum diisi
    if "⚠️ Belum Dicek" in responses.values():
        st.error("🚨 **SUBMISSION FAILED:** Masih ada checklist yang belum Anda isi! Silakan cek kembali list di atas.")
    
    # 2. Cek kebenaran PIN (Simulasi database PIN)
    elif pin_input != "1234":
        st.error("🚨 **SUBMISSION FAILED:** PIN Otorisasi tidak valid/kosong!")
    
    # 3. Kalau semua lolos, submit sukses
    else:
        with st.spinner('Mengenkripsi data dan mengirim ke server pusat...'):
            time.sleep(1.5) # Efek loading biar realistis
            st.success("✅ **JOB CARD BERHASIL DI-SUBMIT!**")
            st.info(f"Data tersimpan di sistem pada {datetime.now().strftime('%H:%M:%S WIB')}. Status pesawat otomatis terupdate di Dashboard Command Center.")
            st.balloons()
