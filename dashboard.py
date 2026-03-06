import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime

# =====================================================
# KONFIGURASI APLIKASI
# =====================================================

st.set_page_config(
    page_title="SMART-KS Nasional",
    layout="wide",
    page_icon="🎓"
)

DATA_FILE = "data_kepala_sekolah.xlsx"

# =====================================================
# SESSION DEFAULT
# =====================================================

if "login" not in st.session_state:
    st.session_state.login = False

if "role" not in st.session_state:
    st.session_state.role = None

if "page" not in st.session_state:
    st.session_state.page = "dashboard"

# =====================================================
# USER LOGIN
# =====================================================

USERS = {
    "operator": {"password": "operator123", "role": "Operator"},
    "kabid": {"password": "kabid123", "role": "Kabid"},
    "kadis": {"password": "kadis123", "role": "Kadis"},
    "viewer": {"password": "viewer123", "role": "Viewer"},
}

# =====================================================
# LOAD DATA EXCEL
# =====================================================

@st.cache_data
def load_data():

    if not os.path.exists(DATA_FILE):
        st.error("File Excel tidak ditemukan")
        st.stop()

    xls = pd.ExcelFile(DATA_FILE)

    cabdis_sheets = [
        s for s in xls.sheet_names
        if "CABANG_DINAS" in s.upper()
    ]

    df_list = []

    for sh in cabdis_sheets:

        df_temp = pd.read_excel(
            DATA_FILE,
            sheet_name=sh,
            dtype=str
        )

        df_temp["Cabang Dinas"] = sh
        df_list.append(df_temp)

    df = pd.concat(df_list)

    df = df.fillna("")

    return df

df = load_data()

# =====================================================
# NORMALISASI KOLOM
# =====================================================

rename_map = {
    "NAMA SEKOLAH": "Nama Sekolah",
    "NAMA KASEK": "Nama Kepala Sekolah",
    "CABANG DINAS": "Cabang Dinas",
}

df.rename(columns=rename_map, inplace=True)

if "Nama Sekolah" not in df.columns:
    df["Nama Sekolah"] = ""

if "Nama Kepala Sekolah" not in df.columns:
    df["Nama Kepala Sekolah"] = ""

# =====================================================
# LOGIKA STATUS REGULATIF
# =====================================================

def map_status(row):

    text = " ".join([
        str(row.get("Masa Periode Sesuai KSPSTK","")),
        str(row.get("Keterangan Akhir","")),
        str(row.get("Status","")),
        str(row.get("Keterangan Jabatan",""))
    ]).lower()

    text = re.sub(r"[^a-z0-9]","",text)

    if "plt" in text:
        return "Plt"

    if "periode1" in text:
        return "Aktif Periode 1"

    if "periode2" in text:
        return "Aktif Periode 2"

    if "lebih2" in text:
        return "Lebih dari 2 Periode"

    return "Aktif Periode 1"

df["Status Regulatif"] = df.apply(map_status, axis=1)

# =====================================================
# LOGIN PAGE
# =====================================================

if not st.session_state.login:

    st.title("SMART-KS Nasional")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        if username in USERS and USERS[username]["password"] == password:

            st.session_state.login = True
            st.session_state.role = USERS[username]["role"]
            st.rerun()

        else:

            st.error("Username atau password salah")

    st.stop()

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.title("SMART-KS")

if st.sidebar.button("Dashboard"):
    st.session_state.page = "dashboard"

if st.sidebar.button("Data Kepsek"):
    st.session_state.page = "data"

if st.sidebar.button("Rekap"):
    st.session_state.page = "rekap"

if st.sidebar.button("Logout"):

    st.session_state.login = False
    st.rerun()

# =====================================================
# DASHBOARD NASIONAL
# =====================================================

def page_dashboard():

    st.title("Dashboard Nasional Kepala Sekolah")

    col1,col2,col3,col4 = st.columns(4)

    p1 = (df["Status Regulatif"]=="Aktif Periode 1").sum()
    p2 = (df["Status Regulatif"]=="Aktif Periode 2").sum()
    p3 = (df["Status Regulatif"]=="Lebih dari 2 Periode").sum()
    plt = (df["Status Regulatif"]=="Plt").sum()

    col1.metric("Periode 1",p1)
    col2.metric("Periode 2",p2)
    col3.metric(">2 Periode",p3)
    col4.metric("PLT",plt)

    st.divider()

    st.subheader("Distribusi Status")

    st.bar_chart(
        df["Status Regulatif"].value_counts()
    )

# =====================================================
# DATA KEPSEK
# =====================================================

def page_data():

    st.title("Data Kepala Sekolah")

    search = st.text_input("Cari Nama Sekolah")

    df_view = df.copy()

    if search:

        df_view = df_view[
            df_view["Nama Sekolah"].str.contains(search,case=False)
        ]

    st.dataframe(
        df_view,
        use_container_width=True
    )

# =====================================================
# REKAP PROVINSI
# =====================================================

def page_rekap():

    st.title("Rekap Nasional")

    rekap = df.groupby(
        ["Cabang Dinas","Status Regulatif"]
    ).size().reset_index(name="Jumlah")

    st.dataframe(rekap,use_container_width=True)

# =====================================================
# ROUTER HALAMAN
# =====================================================

if st.session_state.page == "dashboard":
    page_dashboard()

elif st.session_state.page == "data":
    page_data()

elif st.session_state.page == "rekap":
    page_rekap()

# =====================================================
# FOOTER
# =====================================================

st.divider()

st.caption(
"SMART-KS Nasional • Sistem Monitoring Kepala Sekolah"
)
