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
# SIDEBAR FILTER
# ======================
st.sidebar.header("🔎 Filter Data")

filter_jenjang = st.sidebar.selectbox(
    "Jenjang",
    ["Semua"] + sorted(data["Jenjang"].dropna().unique().tolist())
)

filter_bcks = st.sidebar.selectbox(
    "Sertifikat BCKS",
    ["Semua", "Sudah", "Belum"]
)

filter_status = st.sidebar.selectbox(
    "Keterangan Akhir",
    ["Semua"] + sorted(data["Keterangan Akhir"].dropna().unique().tolist())
)

# ======================
# TERAPKAN FILTER
# ======================
df = data.copy()

if filter_jenjang != "Semua":
    df = df[df["Jenjang"] == filter_jenjang]

if filter_bcks != "Semua":
    df = df[df["Sertifikat BCKS"] == filter_bcks]

if filter_status != "Semua":
    df = df[df["Keterangan Akhir"] == filter_status]

# ======================
# TAMPILAN PER CABDIN
# ======================
st.subheader("🏢 Data Kepala Sekolah per Cabang Dinas")
st.caption("Klik Cabang Dinas → Sekolah → Detail Kepala Sekolah")

for cabdin in sorted(df["Cabang Dinas"].unique()):
    with st.expander(f"📍 {cabdin}", expanded=False):
        df_cabdin = df[df["Cabang Dinas"] == cabdin]

        for _, row in df_cabdin.iterrows():
            with st.expander(
                f"🏫 {row['Nama Sekolah']} — {row['Nama Kepala Sekolah']}",
                expanded=False
            ):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"""
                    **Nama Kepala Sekolah**  
                    {row['Nama Kepala Sekolah']}

                    **NIP**  
                    {row['NIP']}

                    **Jabatan**  
                    {row['Jabatan']}
                    """)

                with col2:
                    st.markdown(f"""
                    **Jenjang**  
                    {row['Jenjang']}

                    **Sertifikat BCKS**  
                    {row['Sertifikat BCKS']}

                    **Tahun Pengangkatan**  
                    {row['Tahun Pengangkatan']}
                    """)

                st.markdown("---")
                st.markdown(f"""
                **📌 Keterangan Akhir**  
                <span style='font-size:18px; font-weight:700; color:red;'>
                {row['Keterangan Akhir']}
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
