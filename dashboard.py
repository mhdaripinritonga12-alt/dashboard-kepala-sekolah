import streamlit as st
import pandas as pd

# =====================
# KONFIGURASI HALAMAN
# =====================
st.set_page_config(
    page_title="Dashboard Kepala Sekolah Dinas Pendidikan",
    layout="wide"
)

# =====================
# JUDUL
# =====================
st.markdown("""
<h1 style='color:#0B5394; font-weight:800;'>
📊 DASHBOARD KEPALA SEKOLAH DINAS PENDIDIKAN
</h1>
<hr>
""", unsafe_allow_html=True)

# =====================
# LOAD DATA (FIX)
# =====================
@st.cache_data
def load_data():
    return pd.read_excel(
        "data_kepala_sekolah.xlsx",
        sheet_name="Dashboard_Kepala_Sekolah"
    )

data = load_data()

# =====================
# VALIDASI KOLOM
# =====================
kolom_wajib = [
    "Cabang Dinas",
    "Nama Sekolah",
    "Nama Kepala Sekolah",
    "NIP",
    "Jenjang",
    "Sertifikat BCKS",
    "Tahun Pengangkatan",
    "Jabatan",
    "Keterangan Akhir",
    "Calon Pengganti"
]

for kolom in kolom_wajib:
    if kolom not in data.columns:
        st.error(f"❌ Kolom '{kolom}' tidak ditemukan di Excel")
        st.stop()

# =====================
# SIDEBAR FILTER
# =====================
st.sidebar.header("🔎 Filter Data")

jenjang = st.sidebar.selectbox(
    "Jenjang",
    ["Semua"] + sorted(data["Jenjang"].dropna().unique())
)

bcks = st.sidebar.selectbox(
    "Sertifikat BCKS",
    ["Semua", "Sudah", "Belum"]
)

# =====================
# FILTER DATA
# =====================
df = data.copy()

if jenjang != "Semua":
    df = df[df["Jenjang"] == jenjang]

if bcks != "Semua":
    df = df[df["Sertifikat BCKS"] == bcks]

# =====================
# TAMPILAN PER CABDIN
# =====================
st.subheader("🏢 Data Kepala Sekolah per Cabang Dinas")
st.caption("Klik Cabang Dinas → Sekolah → Detail Kepala Sekolah")

for cabdin in sorted(df["Cabang Dinas"].unique()):
    with st.expander(f"📍 {cabdin}", expanded=False):

        df_cabdin = df[df["Cabang Dinas"] == cabdin]

        for _, row in df_cabdin.iterrows():

            warna = "#ffdddd" if "Harus Diberhentikan" in row["Keterangan Akhir"] else "#f9f9f9"

            with st.expander(
                f"🏫 {row['Nama Sekolah']} — {row['Nama Kepala Sekolah']}",
                expanded=False
            ):
                st.markdown(
                    f"<div style='background:{warna}; padding:15px; border-radius:8px;'>",
                    unsafe_allow_html=True
                )

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
                <b style='color:red;'>{row['Keterangan Akhir']}</b>
                """ , unsafe_allow_html=True)

                # =====================
                # CALON PENGGANTI
                # =====================
                if "Harus Diberhentikan" in row["Keterangan Akhir"]:
                    st.markdown(f"""
                    **👤 Calon Pengganti**  
                    <b>{row['Calon Pengganti']}</b>
                    """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

# =====================
# FOOTER
# =====================
st.markdown("""
<hr>
<p style='text-align:center; font-size:13px; color:gray;'>
Dashboard Kepala Sekolah • Dinas Pendidikan Provinsi • Streamlit
</p>
""", unsafe_allow_html=True)
