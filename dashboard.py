import streamlit as st
import pandas as pd
import os

# =========================================================
# KONFIGURASI
# =========================================================
st.set_page_config(page_title="Dashboard Kepala Sekolah", layout="wide")
DATA_SAVE = "perubahan_kepsek.xlsx"
TAHUN_ACUAN = 2026

# =========================================================
# SESSION STATE
# =========================================================
if "login" not in st.session_state:
    st.session_state.login = True

if "page" not in st.session_state:
    st.session_state.page = "cabdin"

if "selected_cabdin" not in st.session_state:
    st.session_state.selected_cabdin = None

# =========================================================
# SIMPAN & LOAD PERUBAHAN
# =========================================================
def load_perubahan():
    if os.path.exists(DATA_SAVE):
        try:
            df = pd.read_excel(DATA_SAVE)
            if {"Nama Sekolah", "Calon Pengganti"}.issubset(df.columns):
                return dict(zip(df["Nama Sekolah"], df["Calon Pengganti"]))
        except:
            pass
    return {}

def save_perubahan(data_dict):
    pd.DataFrame(
        [{"Nama Sekolah": k, "Calon Pengganti": v} for k, v in data_dict.items()]
    ).to_excel(DATA_SAVE, index=False)

perubahan_kepsek = load_perubahan()

# =========================================================
# FUNGSI KETERANGAN PERMENDIKDASMEN
# =========================================================
def keterangan_hukum(row):
    jabatan = str(row["Jabatan"]).lower()
    tahun = int(row["Tahun Pengangkatan"])
    bcks = str(row["Sertifikat BCKS"]).strip().lower()

    lama = TAHUN_ACUAN - tahun
    punya_bcks = bcks in ["ya", "ada", "sudah"]

    hasil = []

    if "plt" in jabatan:
        hasil.append("🔹 Kepala Sekolah masih berstatus Pelaksana Tugas (Plt) dan belum ditetapkan sebagai Kepala Sekolah definitif.")

    if lama <= 4:
        if punya_bcks:
            hasil.append("✅ Aman tanpa masalah.")
        else:
            hasil.append("❌ Pasal 32: Belum memiliki Sertifikat Pelatihan BCKS.")

    elif lama <= 8:
        if punya_bcks:
            hasil.append("✅ Aman tanpa masalah.")
        else:
            hasil.append("❌ Pasal 32: Belum memiliki Sertifikat Pelatihan BCKS.")

    else:
        hasil.append("❌ Pasal 31: Telah melewati batas periode penugasan Kepala Sekolah.")
        if not punya_bcks:
            hasil.append("❌ Pasal 32: Belum memiliki Sertifikat Pelatihan BCKS.")

    return hasil

# =========================================================
# CSS
# =========================================================
st.markdown("""
<style>
.stApp { background:#d3d3d3; color:black; }
.school-card {
    background:white;
    border-left:6px solid #1f77b4;
    border-radius:10px;
    padding:16px;
    margin-bottom:14px;
}
.school-danger { background:#fdecea; border-left:6px solid #d93025; }
.school-saved { background:#e6f4ea; border-left:6px solid #1e8e3e; }
.school-title { font-weight:700; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# LOGIN
# =========================================================
if not st.session_state.login:
    st.markdown("## 🔐 LOGIN DASHBOARD")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if user == "aripin" and pwd == "ritonga":
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Username / Password salah")
    st.stop()

# =========================================================
# LOAD DATA
# =========================================================
@st.cache_data
def load_data():
    return (
        pd.read_excel("data_kepala_sekolah.xlsx", sheet_name="KEPALA_SEKOLAH"),
        pd.read_excel("data_kepala_sekolah.xlsx", sheet_name="GURU_SIMPEG")
    )

df_ks, df_guru = load_data()
guru_list = sorted(df_guru["NAMA GURU"].dropna().unique())

# =========================================================
# HEADER
# =========================================================
col1, col2 = st.columns([6,1])
with col1:
    st.markdown("## 📊 Dashboard Kepala Sekolah")
with col2:
    if st.button("🚪 Logout"):
        st.session_state.login = False
        st.session_state.page = "cabdin"
        st.rerun()

st.divider()

# =========================================================
# HALAMAN SEKOLAH
# =========================================================
if st.session_state.page == "cabdin":
    for cabdin in sorted(df_ks["Cabang Dinas"].unique()):
        if st.button(f"📍 {cabdin}", use_container_width=True):
            st.session_state.selected_cabdin = cabdin
            st.session_state.page = "sekolah"
            st.rerun()

elif st.session_state.page == "sekolah":
    df_cab = df_ks[df_ks["Cabang Dinas"] == st.session_state.selected_cabdin]

    for idx, row in df_cab.iterrows():
        nama = row["Nama Sekolah"]
        sudah = nama in perubahan_kepsek
        card = "school-saved" if sudah else "school-card"

        st.markdown(f"""
        <div class="{card}">
            <div class="school-title">🏫 {nama}</div>
            👤 {row['Nama Kepala Sekolah']}<br>
            <b>{row['Keterangan Akhir']}</b>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"📌 NIP: {row['NIP']} (Klik untuk keterangan hukum)"):
            for h in keterangan_hukum(row):
                st.write("•", h)

st.caption("Dashboard Kepala Sekolah • Permendikdasmen No. 7 Tahun 2025")
