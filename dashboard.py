import streamlit as st
import pandas as pd
from datetime import datetime

# =====================
# KONFIGURASI HALAMAN
# =====================
st.set_page_config(
    page_title="Dashboard Kepala Sekolah Dinas Pendidikan",
    layout="wide"
)

# =====================
# JUDUL UTAMA (BIRU & BOLD)
# =====================
st.markdown("""
<h1 style='color:#0B5394; font-weight:800;'>
📊 DASHBOARD KEPALA SEKOLAH DINAS PENDIDIKAN
</h1>
<hr>
""", unsafe_allow_html=True)

# =====================
# LOAD DATA
# =====================
data_kasek = pd.read_excel("data_kepala_sekolah.xlsx")
data_simpeg = pd.read_excel("data_guru_simpeg.xlsx")

tahun_sekarang = datetime.now().year

# =====================
# HITUNG TAHUN BERJALAN & STATUS
# =====================
data_kasek["Tahun Pengangkatan"] = pd.to_numeric(
    data_kasek["Tahun Pengangkatan"], errors="coerce"
)

data_kasek["Tahun Berjalan"] = tahun_sekarang - data_kasek["Tahun Pengangkatan"]

def hitung_periode(tahun):
    if tahun <= 4:
        return "Periode 1"
    elif tahun <= 8:
        return "Periode 2"
    else:
        return "Lebih dari 2 Periode"

data_kasek["Status Periode"] = data_kasek["Tahun Berjalan"].apply(hitung_periode)

def keterangan_akhir(row):
    if row["Tahun Berjalan"] > 8:
        return "Harus Diberhentikan"
    return f"Aktif {row['Status Periode']}"

data_kasek["Keterangan Akhir"] = data_kasek.apply(keterangan_akhir, axis=1)

# =====================
# FILTER SIDEBAR
# =====================
st.sidebar.header("🔎 Filter Data")

jenjang_filter = st.sidebar.selectbox(
    "Jenjang",
    ["Semua"] + sorted(data_kasek["Jenjang"].dropna().unique())
)

bcks_filter = st.sidebar.selectbox(
    "Sertifikat BCKS",
    ["Semua"] + sorted(data_kasek["Sertifikat BCKS"].dropna().unique())
)

periode_filter = st.sidebar.selectbox(
    "Status Periode",
    ["Semua"] + sorted(data_kasek["Status Periode"].dropna().unique())
)

df = data_kasek.copy()

if jenjang_filter != "Semua":
    df = df[df["Jenjang"] == jenjang_filter]

if bcks_filter != "Semua":
    df = df[df["Sertifikat BCKS"] == bcks_filter]

if periode_filter != "Semua":
    df = df[df["Status Periode"] == periode_filter]

# =====================
# DATA KEPALA SEKOLAH (RINGKAS)
# =====================
st.subheader("📋 Data Kepala Sekolah (Klik untuk Detail)")

for i, row in df.iterrows():
    with st.expander(f"🏫 {row['Nama Sekolah']} — {row['Nama Kepala Sekolah']}"):
        st.write("**Nama Kepala Sekolah:**", row["Nama Kepala Sekolah"])
        st.write("**NIP:**", row["NIP"])
        st.write("**Jenjang:**", row["Jenjang"])
        st.write("**Sertifikat BCKS:**", row["Sertifikat BCKS"])
        st.write("**Tahun Pengangkatan:**", row["Tahun Pengangkatan"])
        st.write("**Tahun Berjalan:**", row["Tahun Berjalan"])
        st.write("**Status Periode:**", row["Status Periode"])
        st.write("**Keterangan Akhir:**", row["Keterangan Akhir"])

        # =====================
        # CALON PENGGANTI OTOMATIS
        # =====================
        if row["Keterangan Akhir"] == "Harus Diberhentikan":
            st.markdown("### 🔁 Calon Pengganti (SIMPEG)")

            calon = data_simpeg[
                (data_simpeg["JABATAN"].str.lower() == "guru")
            ]

            calon_list = calon["NAMA GURU"].dropna().unique()

            pilihan = st.selectbox(
                "Pilih Calon Pengganti",
                calon_list,
                key=f"calon_{i}"
            )

            st.success(f"✅ Calon pengganti dipilih: **{pilihan}**")

# =====================
# RINGKASAN PENGGANTIAN
# =====================
st.markdown("---")
st.subheader("📌 Penetapan Calon Pengganti")

pengganti = df[df["Keterangan Akhir"] == "Harus Diberhentikan"][
    ["Nama Kepala Sekolah", "Nama Sekolah", "Jenjang", "Keterangan Akhir"]
]

st.dataframe(pengganti, use_container_width=True)
