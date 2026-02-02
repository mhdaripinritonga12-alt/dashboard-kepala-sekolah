import streamlit as st
import pandas as pd
from datetime import datetime

# =========================================
# KONFIGURASI HALAMAN
# =========================================
st.set_page_config(
    page_title="Dashboard Kepala Sekolah – Disdik Sumut",
    layout="wide"
)

# =========================================
# HEADER
# =========================================
st.markdown("""
<div style="background-color:#0d47a1;padding:18px;border-radius:10px">
<h2 style="color:white;text-align:center;font-weight:bold">
DASHBOARD KEPALA SEKOLAH<br>
DINAS PENDIDIKAN PROVINSI SUMATERA UTARA
</h2>
</div>
""", unsafe_allow_html=True)

# =========================================
# HAK AKSES SEDERHANA (ONLINE READY)
# =========================================
st.sidebar.header("🔐 Akses Pengguna")

role = st.sidebar.selectbox(
    "Peran Pengguna",
    ["Viewer", "Admin", "Pimpinan"]
)

# =========================================
# LOAD DATA (AMAN ONLINE)
# =========================================
@st.cache_data
def load_data():
    data = pd.read_excel("data_kepala_sekolah.xlsx")
    guru = pd.read_excel("data_guru_simpeg.xlsx")
    return data, guru

data, guru = load_data()

list_guru = sorted(
    guru["NAMA GURU"].dropna().unique().tolist()
)

# =========================================
# LOGIKA PERIODE
# =========================================
tahun_sekarang = datetime.now().year

data["Tahun Pengangkatan"] = pd.to_numeric(
    data["Tahun Pengangkatan"], errors="coerce"
)

data["Tahun Berjalan"] = tahun_sekarang - data["Tahun Pengangkatan"]

def hitung_periode(t):
    if t <= 4:
        return "Periode 1"
    elif t <= 8:
        return "Periode 2"
    else:
        return "Lebih dari 2 Periode"

data["Status Periode"] = data["Tahun Berjalan"].apply(hitung_periode)

def keterangan_akhir(row):
    if row["Tahun Berjalan"] > 8:
        return "Harus Diberhentikan"
    return f"Aktif {row['Status Periode']}"

data["Keterangan Akhir"] = data.apply(keterangan_akhir, axis=1)

if "Calon Pengganti" not in data.columns:
    data["Calon Pengganti"] = ""

if "Tanggal Penetapan" not in data.columns:
    data["Tanggal Penetapan"] = ""

# =========================================
# FILTER
# =========================================
st.subheader("🔍 Filter Data")

c1, c2, c3 = st.columns(3)

with c1:
    f_jenjang = st.selectbox(
        "Jenjang",
        ["Semua"] + sorted(data["Jenjang"].dropna().unique())
    )

with c2:
    f_periode = st.selectbox(
        "Status Periode",
        ["Semua"] + sorted(data["Status Periode"].dropna().unique())
    )

with c3:
    f_bcks = st.selectbox(
        "Sertifikat BCKS",
        ["Semua"] + sorted(data["Sertifikat BCKS"].dropna().unique())
    )

filtered = data.copy()

if f_jenjang != "Semua":
    filtered = filtered[filtered["Jenjang"] == f_jenjang]

if f_periode != "Semua":
    filtered = filtered[filtered["Status Periode"] == f_periode]

if f_bcks != "Semua":
    filtered = filtered[filtered["Sertifikat BCKS"] == f_bcks]

# =========================================
# MASTER – DAFTAR SEKOLAH
# =========================================
st.subheader("🏫 Daftar Sekolah")

ringkas = filtered[["Nama Sekolah", "Jenjang"]]

pilih = st.dataframe(
    ringkas,
    use_container_width=True,
    selection_mode="single-row",
    on_select="rerun",
    key="pilih_sekolah"
)

# =========================================
# DETAIL
# =========================================
rows = st.session_state["pilih_sekolah"].get("selection", {}).get("rows", [])

if rows:
    idx = rows[0]
    detail = filtered.iloc[idx]

    st.markdown("---")
    st.subheader("📋 Detail Kepala Sekolah")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Nama Kepala Sekolah**:", detail["Nama Kepala Sekolah"])
        st.write("**Nama Sekolah**:", detail["Nama Sekolah"])
        st.write("**Jenjang**:", detail["Jenjang"])
        st.write("**Sertifikat BCKS**:", detail["Sertifikat BCKS"])

    with col2:
        st.write("**Tahun Pengangkatan**:", detail["Tahun Pengangkatan"])
        st.write("**Tahun Berjalan**:", detail["Tahun Berjalan"])
        st.write("**Status Periode**:", detail["Status Periode"])
        st.write("**Keterangan Akhir**:", detail["Keterangan Akhir"])

    # =====================================
    # PENETAPAN CALON PENGGANTI
    # =====================================
    st.markdown("### 👤 Penetapan Calon Pengganti")

    if detail["Keterangan Akhir"] == "Harus Diberhentikan":
        if role in ["Admin", "Pimpinan"]:
            calon = st.selectbox(
                "Pilih Calon Pengganti (Guru PNS SIMPEG)",
                [""] + list_guru
            )

            if calon:
                data.loc[detail.name, "Calon Pengganti"] = calon
                data.loc[detail.name, "Tanggal Penetapan"] = datetime.now().strftime("%d-%m-%Y")
                st.success("Calon pengganti berhasil ditetapkan")
        else:
            st.warning("Hanya Admin/Pimpinan yang dapat menetapkan")
    else:
        st.info("Belum memenuhi syarat penggantian")

# =========================================
# DATA PENGGANTI RESMI
# =========================================
st.markdown("---")
st.subheader("📌 Data Pengganti Resmi")

pengganti = data[
    (data["Keterangan Akhir"] == "Harus Diberhentikan") &
    (data["Calon Pengganti"] != "")
][[
    "Nama Kepala Sekolah",
    "Nama Sekolah",
    "Jenjang",
    "Calon Pengganti",
    "Tanggal Penetapan"
]]

st.dataframe(pengganti, use_container_width=True)
