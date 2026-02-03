import streamlit as st
import pandas as pd

# ===============================
# KONFIGURASI
# ===============================
st.set_page_config(
    page_title="Dashboard Kepala Sekolah",
    layout="wide"
)

# ===============================
# LOAD DATA (AMAN & STABIL)
# ===============================
@st.cache_data
def load_data():
    ks = pd.read_excel(
        "data_kepala_sekolah.xlsx",
        sheet_name="KEPALA_SEKOLAH"
    )
    guru = pd.read_excel(
        "data_guru_simpeg.xlsx",
        sheet_name="GURU_SIMPEG"
    )
    return ks, guru

df_ks, df_guru = load_data()

# ===============================
# JUDUL
# ===============================
st.markdown("""
<h1 style='color:#0B5394;'>📊 Dashboard Kepala Sekolah Dinas Pendidikan</h1>
<hr>
""", unsafe_allow_html=True)

# ===============================
# SEARCH KEPALA SEKOLAH (GLOBAL)
# ===============================
search = st.text_input("🔍 Cari Nama Kepala Sekolah")

if search:
    df_ks = df_ks[df_ks["Nama Kepala Sekolah"].str.contains(search, case=False, na=False)]

# ===============================
# SIDEBAR FILTER
# ===============================
st.sidebar.header("🔎 Filter")

filter_jenjang = st.sidebar.selectbox(
    "Jenjang",
    ["Semua"] + sorted(df_ks["Jenjang"].unique())
)

filter_status = st.sidebar.selectbox(
    "Keterangan Akhir",
    ["Semua"] + sorted(df_ks["Keterangan Akhir"].unique())
)

if filter_jenjang != "Semua":
    df_ks = df_ks[df_ks["Jenjang"] == filter_jenjang]

if filter_status != "Semua":
    df_ks = df_ks[df_ks["Keterangan Akhir"] == filter_status]

# ===============================
# CARD CABANG DINAS (14 CABDIS)
# ===============================
st.subheader("🏢 Cabang Dinas")

cabdis_list = sorted(df_ks["Cabang Dinas"].unique())

cols = st.columns(4)
for i, cab in enumerate(cabdis_list):
    jumlah = len(df_ks[df_ks["Cabang Dinas"] == cab])
    with cols[i % 4]:
        st.markdown(
            f"""
            <div style="
                background:#F5F8FF;
                border-left:6px solid #0B5394;
                padding:15px;
                border-radius:10px;
                margin-bottom:15px;">
                <h4>📍 {cab}</h4>
                <b>{jumlah} Kepala Sekolah</b>
            </div>
            """,
            unsafe_allow_html=True
        )

# ===============================
# DETAIL PER CABANG DINAS
# ===============================
st.subheader("📂 Data Kepala Sekolah per Cabang Dinas")

for cab in cabdis_list:
    with st.expander(f"📍 {cab}", expanded=False):
        data_cab = df_ks[df_ks["Cabang Dinas"] == cab]

        for _, row in data_cab.iterrows():
            warna = "#FFEEEE" if row["Keterangan Akhir"] == "Harus Diberhentikan" else "#FFFFFF"

            with st.expander(
                f"🏫 {row['Nama Sekolah']} — {row['Nama Kepala Sekolah']}"
            ):
                st.markdown(
                    f"""
                    <div style="background:{warna}; padding:10px; border-radius:8px;">
                    <b>Nama Kepala Sekolah:</b> {row['Nama Kepala Sekolah']}<br>
                    <b>NIP:</b> {row['NIP']}<br>
                    <b>Jenjang:</b> {row['Jenjang']}<br>
                    <b>Status Jabatan:</b> {row['Status Jabatan']}<br>
                    <b>Keterangan Akhir:</b> <b>{row['Keterangan Akhir']}</b>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # ===============================
                # CALON PENGGANTI (JIKA PLT / DIBERHENTIKAN)
                # ===============================
                if row["Keterangan Akhir"] == "Harus Diberhentikan" or row["Status Jabatan"] == "PLT":
                    kandidat = df_guru[
                        (df_guru["Jenjang"] == row["Jenjang"]) &
                        (df_guru["Cabang Dinas"] == row["Cabang Dinas"])
                    ]

                    st.selectbox(
                        "👤 Pilih Calon Pengganti",
                        kandidat["Nama Guru"].tolist()
                    )

# ===============================
# FOOTER
# ===============================
st.markdown("""
<hr>
<p style="text-align:center; color:gray;">
Dashboard Kepala Sekolah • Final Stabil • Streamlit
</p>
""", unsafe_allow_html=True)
