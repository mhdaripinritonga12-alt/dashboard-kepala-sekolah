import streamlit as st
import pandas as pd

# =============================
# KONFIGURASI HALAMAN
# =============================
st.set_page_config(
    page_title="Dashboard Kepala Sekolah Dinas Pendidikan",
    layout="wide"
)

# =============================
# LOAD DATA
# =============================
@st.cache_data
def load_data():
    ks = pd.read_excel("data_kepala_sekolah.xlsx")
    guru = pd.read_excel("data_guru_simpeg.xlsx")
    return ks, guru

df_ks, df_guru = load_data()

# =============================
# VALIDASI KOLOM WAJIB
# =============================
kolom_wajib = [
    "Cabang Dinas", "Nama Sekolah", "Nama Kepala Sekolah",
    "NIP", "Jenjang", "Jabatan", "Sertifikat BCKS",
    "Tahun Pengangkatan", "Status Periode", "Keterangan Akhir"
]

for col in kolom_wajib:
    if col not in df_ks.columns:
        st.error(f"❌ Kolom '{col}' tidak ditemukan di data_kepala_sekolah.xlsx")
        st.stop()

# =============================
# JUDUL
# =============================
st.markdown("""
<h1 style='color:#0B5394; font-weight:900;'>
📊 DASHBOARD KEPALA SEKOLAH DINAS PENDIDIKAN
</h1>
<hr>
""", unsafe_allow_html=True)

# =============================
# SIDEBAR FILTER
# =============================
st.sidebar.header("🔎 Filter Data")

filter_jenjang = st.sidebar.selectbox(
    "Jenjang",
    ["Semua"] + sorted(df_ks["Jenjang"].dropna().unique())
)

filter_status = st.sidebar.selectbox(
    "Keterangan Akhir",
    ["Semua"] + sorted(df_ks["Keterangan Akhir"].dropna().unique())
)

df = df_ks.copy()

if filter_jenjang != "Semua":
    df = df[df["Jenjang"] == filter_jenjang]

if filter_status != "Semua":
    df = df[df["Keterangan Akhir"] == filter_status]

# =============================
# CABANG DINAS (CARD STYLE)
# =============================
st.subheader("🏢 Cabang Dinas")

cabdis_list = sorted(df["Cabang Dinas"].unique())

cols = st.columns(4)

for i, cabdis in enumerate(cabdis_list):
    with cols[i % 4]:
        total = len(df[df["Cabang Dinas"] == cabdis])
        st.markdown(f"""
        <div style="
            background:#F2F6FC;
            border-radius:12px;
            padding:15px;
            border-left:6px solid #0B5394;
            margin-bottom:15px;
        ">
        <h4>📍 {cabdis}</h4>
        <p><b>{total}</b> Kepala Sekolah</p>
        </div>
        """, unsafe_allow_html=True)

# =============================
# DETAIL PER CABDIN
# =============================
st.subheader("📂 Data Kepala Sekolah per Cabang Dinas")

for cabdis in cabdis_list:
    with st.expander(f"📍 {cabdis}", expanded=False):

        df_cab = df[df["Cabang Dinas"] == cabdis]

        for _, row in df_cab.iterrows():

            warna = "#FFD6D6" if row["Keterangan Akhir"] in [
                "Harus Diberhentikan", "PLT"
            ] else "#E8F5E9"

            with st.expander(
                f"🏫 {row['Nama Sekolah']} — {row['Nama Kepala Sekolah']}"
            ):
                st.markdown(f"""
                <div style="
                    background:{warna};
                    padding:15px;
                    border-radius:10px;
                ">
                <b>Kepala Sekolah:</b> {row['Nama Kepala Sekolah']}<br>
                <b>NIP:</b> {row['NIP']}<br>
                <b>Jenjang:</b> {row['Jenjang']}<br>
                <b>Jabatan:</b> {row['Jabatan']}<br>
                <b>Status:</b> {row['Keterangan Akhir']}
                </div>
                """, unsafe_allow_html=True)

                # =============================
                # CALON PENGGANTI
                # =============================
                if row["Keterangan Akhir"] in ["Harus Diberhentikan", "PLT"]:
                    st.markdown("### 👨‍🏫 Calon Pengganti (SIMPEG)")

                    kandidat = df_guru[
                        (df_guru["Jenjang"] == row["Jenjang"])
                    ]

                    if kandidat.empty:
                        st.warning("Tidak ada calon pengganti sesuai jenjang.")
                    else:
                        st.dataframe(
                            kandidat[[
                                "Nama Guru", "NIP",
                                "Unit Kerja", "Jabatan"
                            ]],
                            use_container_width=True
                        )

# =============================
# FOOTER
# =============================
st.markdown("""
<hr>
<p style='text-align:center; font-size:13px; color:gray;'>
Dashboard Kepala Sekolah • Dinas Pendidikan Provinsi • Streamlit Cloud
</p>
""", unsafe_allow_html=True)
