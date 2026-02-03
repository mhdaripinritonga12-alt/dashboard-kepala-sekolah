import streamlit as st
import pandas as pd

# ======================
# KONFIGURASI HALAMAN
# ======================
st.set_page_config(
    page_title="Dashboard Kepala Sekolah",
    layout="wide"
)

# ======================
# LOAD DATA
# ======================
@st.cache_data
def load_data():
    ks = pd.read_excel("data_kepala_sekolah.xlsx", sheet_name="KEPALA_SEKOLAH")
    guru = pd.read_excel("data_guru_simpeg.xlsx", sheet_name="GURU")
    return ks, guru

df_ks, df_guru = load_data()

# ======================
# VALIDASI KOLOM
# ======================
kolom_wajib = [
    "Cabang Dinas", "Nama Sekolah", "Nama Kepala Sekolah",
    "NIP", "Jenjang", "Status Jabatan", "Keterangan Akhir"
]

for k in kolom_wajib:
    if k not in df_ks.columns:
        st.error(f"❌ Kolom '{k}' tidak ditemukan di data_kepala_sekolah.xlsx")
        st.stop()

# ======================
# HEADER
# ======================
st.markdown("""
<h1 style='color:#0B5394;'>📊 DASHBOARD KEPALA SEKOLAH</h1>
<hr>
""", unsafe_allow_html=True)

# ======================
# SEARCH KEPALA SEKOLAH
# ======================
search = st.text_input("🔍 Cari Nama Kepala Sekolah")

if search:
    df_ks = df_ks[
        df_ks["Nama Kepala Sekolah"]
        .str.contains(search, case=False, na=False)
    ]

# ======================
# SIDEBAR FILTER
# ======================
st.sidebar.header("🔎 Filter")

filter_jenjang = st.sidebar.selectbox(
    "Jenjang",
    ["Semua"] + sorted(df_ks["Jenjang"].dropna().unique())
)

filter_status = st.sidebar.selectbox(
    "Keterangan Akhir",
    ["Semua"] + sorted(df_ks["Keterangan Akhir"].dropna().unique())
)

if filter_jenjang != "Semua":
    df_ks = df_ks[df_ks["Jenjang"] == filter_jenjang]

if filter_status != "Semua":
    df_ks = df_ks[df_ks["Keterangan Akhir"] == filter_status]

# ======================
# CARD CABANG DINAS
# ======================
st.subheader("🏢 Cabang Dinas")

cabdis_list = sorted(df_ks["Cabang Dinas"].unique())

cols = st.columns(4)

for i, cabdis in enumerate(cabdis_list):
    jumlah = len(df_ks[df_ks["Cabang Dinas"] == cabdis])
    with cols[i % 4]:
        st.markdown(f"""
        <div style="
            border-left:6px solid #0B5394;
            padding:16px;
            border-radius:10px;
            background:#F5F8FC;
            margin-bottom:12px;">
            <b>📍 {cabdis}</b><br>
            {jumlah} Kepala Sekolah
        </div>
        """, unsafe_allow_html=True)

# ======================
# DETAIL PER CABANG DINAS
# ======================
st.subheader("📂 Data Kepala Sekolah per Cabang Dinas")

for cabdis in cabdis_list:
    with st.expander(f"📍 {cabdis}", expanded=False):
        df_cab = df_ks[df_ks["Cabang Dinas"] == cabdis]

        for _, row in df_cab.iterrows():
            warna = "#FFE5E5" if row["Keterangan Akhir"] == "Harus Diberhentikan" else "#F9F9F9"

            with st.expander(
                f"🏫 {row['Nama Sekolah']} — {row['Nama Kepala Sekolah']}"
            ):
                st.markdown(f"""
                <div style="background:{warna}; padding:12px; border-radius:8px;">
                <b>Nama Kepala Sekolah:</b> {row['Nama Kepala Sekolah']}<br>
                <b>NIP:</b> {row['NIP']}<br>
                <b>Jenjang:</b> {row['Jenjang']}<br>
                <b>Status Jabatan:</b> {row['Status Jabatan']}<br>
                <b>Keterangan Akhir:</b> <b>{row['Keterangan Akhir']}</b>
                </div>
                """, unsafe_allow_html=True)

                # ======================
                # CALON PENGGANTI
                # ======================
                if row["Keterangan Akhir"] == "Harus Diberhentikan" or row["Status Jabatan"] == "PLT":
                    st.markdown("### 🔄 Calon Pengganti")

                    kandidat = df_guru[
                        (df_guru["Jenjang"] == row["Jenjang"]) &
                        (df_guru["Cabang Dinas"] == cabdis)
                    ]

                    if kandidat.empty:
                        st.warning("Tidak ada data guru SIMPEG sesuai jenjang & cabang dinas")
                    else:
                        pilih = st.selectbox(
                            "Pilih Guru Pengganti",
                            kandidat["Nama Guru"].tolist(),
                            key=f"{row['NIP']}"
                        )
                        st.success(f"✅ Dipilih: {pilih}")
