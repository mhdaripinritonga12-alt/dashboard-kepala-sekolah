import streamlit as st
import pandas as pd

# ======================
# KONFIGURASI HALAMAN
# ======================
st.set_page_config(
    page_title="Dashboard Kepala Sekolah Dinas Pendidikan",
    layout="wide"
)

# ======================
# JUDUL
# ======================
st.markdown("""
<h1 style='color:#0B5394; font-weight:800;'>
📊 DASHBOARD KEPALA SEKOLAH DINAS PENDIDIKAN
</h1>
<hr>
""", unsafe_allow_html=True)

# ======================
# LOAD DATA
# ======================
@st.cache_data
def load_data():
    return pd.read_excel("data_kepala_sekolah.xlsx")

data = load_data()

# ======================
# VALIDASI KOLOM WAJIB
# ======================
kolom_wajib = [
    "Cabang Dinas",
    "Nama Sekolah",
    "Nama Kepala Sekolah",
    "Jenjang",
    "Sertifikat BCKS",
    "Keterangan Akhir",
    "NIP",
    "Jabatan",
    "Tahun Pengangkatan"
]

for kolom in kolom_wajib:
    if kolom not in data.columns:
        st.error(f"❌ Kolom '{kolom}' tidak ditemukan di Excel")
        st.stop()

# ======================
# SIDEBAR FILTER
# ======================
st.sidebar.header("🔎 Filter Data")

f_jenjang = st.sidebar.selectbox(
    "Jenjang",
    ["Semua"] + sorted(data["Jenjang"].dropna().unique())
)

f_bcks = st.sidebar.selectbox(
    "Sertifikat BCKS",
    ["Semua", "Sudah", "Belum"]
)

f_status = st.sidebar.selectbox(
    "Keterangan Akhir",
    ["Semua"] + sorted(data["Keterangan Akhir"].dropna().unique())
)

# ======================
# FILTER DATA
# ======================
df = data.copy()

if f_jenjang != "Semua":
    df = df[df["Jenjang"] == f_jenjang]

if f_bcks != "Semua":
    df = df[df["Sertifikat BCKS"] == f_bcks]

if f_status != "Semua":
    df = df[df["Keterangan Akhir"] == f_status]

# ======================
# TAMPILAN PER CABANG DINAS
# ======================
st.subheader("🏢 Data Kepala Sekolah per Cabang Dinas")
st.caption("Klik Cabang Dinas → Sekolah → Detail Kepala Sekolah")

for cabdin in sorted(df["Cabang Dinas"].unique()):
    with st.expander(f"📍 {cabdin}", expanded=False):
        df_cd = df[df["Cabang Dinas"] == cabdin]

        for _, r in df_cd.iterrows():
            with st.expander(
                f"🏫 {r['Nama Sekolah']} — {r['Nama Kepala Sekolah']}",
                expanded=False
            ):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"""
**Nama Kepala Sekolah**  
{r['Nama Kepala Sekolah']}

**NIP**  
{r['NIP']}

**Jabatan**  
{r['Jabatan']}
""")

                with col2:
                    st.markdown(f"""
**Jenjang**  
{r['Jenjang']}

**Sertifikat BCKS**  
{r['Sertifikat BCKS']}

**Tahun Pengangkatan**  
{r['Tahun Pengangkatan']}
""")

                st.markdown("---")
                st.markdown(f"""
**📌 Keterangan Akhir**  
<span style='font-size:18px; font-weight:700; color:red;'>
{r['Keterangan Akhir']}
</span>
""", unsafe_allow_html=True)

# ======================
# FOOTER
# ======================
st.markdown("""
<hr>
<p style='text-align:center; font-size:13px; color:gray;'>
Dashboard Kepala Sekolah • Dinas Pendidikan Provinsi • Streamlit
</p>
""", unsafe_allow_html=True)
