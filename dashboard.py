import streamlit as st
import pandas as pd
import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

# =========================================================
# KONFIGURASI APLIKASI
# =========================================================
st.set_page_config(page_title="Dashboard Kepala Sekolah", layout="wide")

DATA_SAVE = "perubahan_kepsek.xlsx"
DATA_FILE = "data_kepala_sekolah.xlsx"

# =========================================================
# SESSION STATE INIT
# =========================================================
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.login = False
    st.session_state.role = None
    st.session_state.page = "cabdin"
    st.session_state.selected_cabdin = None
    st.session_state.selected_sekolah = None

# =========================================================
# 🔐 LOGIN USER
# =========================================================
USERS = {
    "operator": {"password": "operator123", "role": "Operator"},
    "kabidptk": {"password": "kabid123", "role": "Kabid"},
    "kadis": {"password": "kadis123", "role": "Kadis"},
    "viewer": {"password": "viewer123", "role": "View"},
}

# =========================================================
# LOGIN SCREEN
# =========================================================
if not st.session_state.login:
    st.markdown("## 🔐 Login Dashboard Kepala Sekolah")

    col1, col2, col3 = st.columns([2, 3, 2])
    with col2:
        username = st.text_input("👤 Username")
        password = st.text_input("🔑 Password", type="password")

        if st.button("🔓 Login", use_container_width=True):
            if username in USERS and USERS[username]["password"] == password:
                st.session_state.login = True
                st.session_state.role = USERS[username]["role"]
                st.success(f"✅ Login berhasil sebagai **{st.session_state.role}**")
                st.rerun()
            else:
                st.error("❌ Username atau Password salah")

    st.stop()

st.caption(f"👤 Login sebagai: **{st.session_state.role}**")
boleh_edit_role = st.session_state.role in ["Operator", "Kabid"]

# =========================================================
# LOAD & SAVE PERUBAHAN
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
    df = pd.DataFrame([{"Nama Sekolah": k, "Calon Pengganti": v} for k, v in data_dict.items()])
    df.to_excel(DATA_SAVE, index=False)

perubahan_kepsek = load_perubahan()

# =========================================================
# URUT CABDIN
# =========================================================
def urutkan_cabdin(cabdin_list):
    def ambil_angka(text):
        angka = "".join(filter(str.isdigit, str(text)))
        return int(angka) if angka else 999
    return sorted(cabdin_list, key=ambil_angka)

# =========================================================
# LOAD DATA (CACHE)
# =========================================================
@st.cache_data(show_spinner="📂 Memuat data Kepala Sekolah & SIMPEG...")
def load_data():
    xls = pd.ExcelFile(DATA_FILE)

    cabdis_sheets = [s for s in xls.sheet_names if "CABANG_DINAS_PENDIDIKAN_WIL" in s.upper()]
    if len(cabdis_sheets) == 0:
        st.error("❌ Sheet CABANG_DINAS_PENDIDIKAN_WIL tidak ditemukan di Excel")
        st.stop()

    df_list = []
    for sh in cabdis_sheets:
        df_temp = pd.read_excel(DATA_FILE, sheet_name=sh)
        df_temp["Cabang Dinas"] = sh.replace("_", " ")
        df_list.append(df_temp)

    df_ks = pd.concat(df_list, ignore_index=True)

    if "GURU_SIMPEG" not in xls.sheet_names:
        st.error("❌ Sheet GURU_SIMPEG tidak ditemukan di Excel")
        st.stop()

    df_guru = pd.read_excel(DATA_FILE, sheet_name="GURU_SIMPEG")

    return df_ks, df_guru

df_ks, df_guru = load_data()

# =========================================================
# NORMALISASI KOLOM
# =========================================================
df_ks.columns = df_ks.columns.astype(str).str.strip()
df_guru.columns = df_guru.columns.astype(str).str.strip()

rename_map_ks = {
    "NAMA SEKOLAH": "Nama Sekolah",
    "Nama Sekolah ": "Nama Sekolah",
    "Nama sekolah": "Nama Sekolah",

    "NAMA KASEK": "Nama Kepala Sekolah",
    "Nama Kasek": "Nama Kepala Sekolah",
    "Nama Kepsek": "Nama Kepala Sekolah",

    "Keterangan": "Keterangan Akhir",
    "KETERANGAN": "Keterangan Akhir",
    "KETERANGAN AKHIR": "Keterangan Akhir",
    "Keteranngan Akhir": "Keterangan Akhir",
    "Keterangan Akhir ": "Keterangan Akhir",

    "Ket. Sertifikat BCKS": "Ket Sertifikat BCKS",
    "Ket Sertifikat BCKS ": "Ket Sertifikat BCKS",
    "Sertifikat BCKS": "Ket Sertifikat BCKS",

    "Masa Periode Sisuai KSPSTK": "Masa Periode Sesuai KSPSTK",
    "Masa Periode Sesuai KSPSTK ": "Masa Periode Sesuai KSPSTK",
}

rename_map_guru = {
    "NAMA GURU ": "NAMA GURU",
    "Nama Guru": "NAMA GURU",
    "NAMA": "NAMA GURU",
    "NIP ": "NIP",
    "NIP.": "NIP",
}

df_ks.rename(columns=rename_map_ks, inplace=True)
df_guru.rename(columns=rename_map_guru, inplace=True)

df_ks = df_ks.loc[:, ~df_ks.columns.duplicated()]
df_guru = df_guru.loc[:, ~df_guru.columns.duplicated()]

# WAJIB ADA
if "Nama Sekolah" not in df_ks.columns:
    df_ks["Nama Sekolah"] = ""
if "Nama Kepala Sekolah" not in df_ks.columns:
    df_ks["Nama Kepala Sekolah"] = ""
if "Keterangan Akhir" not in df_ks.columns:
    df_ks["Keterangan Akhir"] = ""
if "Masa Periode Sesuai KSPSTK" not in df_ks.columns:
    df_ks["Masa Periode Sesuai KSPSTK"] = ""
if "Ket Sertifikat BCKS" not in df_ks.columns:
    df_ks["Ket Sertifikat BCKS"] = ""

df_ks["Nama Sekolah"] = (
    df_ks["Nama Sekolah"]
    .astype(str)
    .str.replace("\xa0", " ", regex=False)
    .str.strip()
)

# LIST GURU
guru_list = sorted(df_guru["NAMA GURU"].astype(str).dropna().unique()) if "NAMA GURU" in df_guru.columns else []

# =========================================================
# STATUS LOGIKA
# =========================================================
def map_status(row):
    masa = str(row.get("Masa Periode Sesuai KSPSTK", "")).strip().lower()
    ket_akhir = str(row.get("Keterangan Akhir", "")).strip().lower()

    if "periode 1" in masa:
        return "Aktif Periode 1"
    if "periode 2" in masa:
        return "Aktif Periode 2"
    if "lebih dari 2" in masa or ">2" in masa:
        return "Lebih dari 2 Periode"
    if "plt" in masa:
        return "Plt"

    if "periode 1" in ket_akhir:
        return "Aktif Periode 1"
    if "periode 2" in ket_akhir:
        return "Aktif Periode 2"
    if "lebih dari 2" in ket_akhir or ">2" in ket_akhir:
        return "Lebih dari 2 Periode"
    if "plt" in ket_akhir:
        return "Plt"

    return "Lainnya"

# =========================================================
# FILTER SIDEBAR
# =========================================================
st.sidebar.header("🔍 Filter & Pencarian")
search_nama = st.sidebar.text_input("Cari Nama Kepala Sekolah")
search_sekolah = st.sidebar.text_input("Cari Nama Sekolah")

jenjang_filter = st.sidebar.selectbox("Jenjang", ["Semua"] + sorted(df_ks["Jenjang"].dropna().unique()))
ket_filter = st.sidebar.selectbox("Keterangan Akhir", ["Semua"] + sorted(df_ks["Keterangan Akhir"].dropna().unique()))

def apply_filter(df):
    if jenjang_filter != "Semua":
        df = df[df["Jenjang"] == jenjang_filter]

    if ket_filter != "Semua":
        df = df[df["Keterangan Akhir"] == ket_filter]

    if search_nama:
        df = df[df["Nama Kepala Sekolah"].astype(str).str.contains(search_nama, case=False, na=False)]

    if search_sekolah:
        df = df[df["Nama Sekolah"].astype(str).str.contains(search_sekolah, case=False, na=False)]

    return df

# =========================================================
# CSS CARD SEKOLAH
# =========================================================
st.markdown("""
<style>
div[data-testid="stButton"] > button {
    border-radius: 14px !important;
    height: 110px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    text-align: center !important;
    border: 1px solid #ddd !important;
    box-shadow: 0 3px 8px rgba(0,0,0,0.12) !important;
    width: 100% !important;
    white-space: normal !important;
    padding: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# BADGE WARNA DI DETAIL
# =========================================================
def badge(text, bg, color="white"):
    return f"""
    <span style="
        display:inline-block;
        padding:8px 18px;
        border-radius:14px;
        font-weight:700;
        background:{bg};
        color:{color};
        font-size:14px;
        margin:4px 0px;
    ">{text}</span>
    """

# =========================================================
# HALAMAN DETAIL SEKOLAH
# =========================================================
def page_detail():

    if st.session_state.selected_sekolah is None:
        st.warning("⚠️ Sekolah belum dipilih.")
        st.session_state.page = "sekolah"
        st.rerun()

    colA, colB, colC = st.columns([1, 1, 8])

    with colA:
        if st.button("🏠", key="btn_home_detail", use_container_width=True):
            st.session_state.page = "cabdin"
            st.session_state.selected_cabdin = None
            st.session_state.selected_sekolah = None
            st.rerun()

    with colB:
        if st.button("⬅️", key="btn_back_detail", use_container_width=True):
            st.session_state.page = "sekolah"
            st.session_state.selected_sekolah = None
            st.rerun()

    with colC:
        st.subheader(f"📄 Detail Sekolah: {st.session_state.selected_sekolah}")

    nama = str(st.session_state.selected_sekolah).replace("\xa0", " ").strip()

    row_detail = df_ks[
        df_ks["Nama Sekolah"].astype(str).str.replace("\xa_
