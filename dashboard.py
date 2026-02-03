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
    df_ks = pd.read_excel("data_kepala_sekolah.xlsx")
    df_guru = pd.read_excel("data_guru_simpeg.xlsx")
    return df_ks, df_guru

df, df_guru = load_data()

# ======================
# VALIDASI KOLOM
# ======================
ks_cols = [
    "Cabang Dinas", "Nama Sekolah", "Nama Kepala Sekolah",
    "NIP", "Jabatan", "Jenjang",
    "BCKS", "Tahun Pengangkatan", "Keterangan Akhir"
]

guru_cols = ["NAMA GURU"]

for c in ks_cols:
    if c not in df.columns:
        st.error(f"❌ Kolom '{c}' tidak ditemukan di data_kepala_sekolah.xlsx")
        st.stop()

for c in guru_cols:
    if c not in df_guru.columns:
        st.error(f"❌ Kolom '{c}' tidak ditemukan di data_guru_simpeg.xlsx")
        st.stop()

# ======================
# HEADER
# ======================
st.markdown("""
<h1 style="color:#0B5394; font-weight:800;">
📊 DASHBOARD KEPALA SEKOLAH DINAS PENDIDIKAN
</h1>
<hr>
""", unsafe_allow_html=True)

# ======================
# SIDEBAR FILTER
# ======================
st.sidebar.header("🔎 Filter")

jenjang = st.sidebar.selectbox(
    "Jenjang",
    ["Semua"] + sorted(df["Jenjang"].dropna().unique())
)

if jenjang != "Semua":
    df = df[df["Jenjang"] == jenjang]

# ======================
# CSS CARD
# ======================
st.markdown("""
<style>
.school-card {
    background-color:#E8F1FF;
    border-left:6px solid #0B5394;
    border-radius:10px;
    padding:14px;
    margin-bottom:14px;
}
.school-danger {
    background-color:#FDECEA;
    border-left:6px solid #D93025;
}
.small-text { font-size:13px; }
</style>
""", unsafe_allow_html=True)

# ======================
# CABANG DINAS
# ======================
st.subheader("🏢 Cabang Dinas Wilayah")

cabdin_list = sorted(df["Cabang Dinas"].unique())

for cabdin in cabdin_list:
    with st.expander(f"📍 {cabdin}", expanded=False):

        df_cab = df[df["Cabang Dinas"] == cabdin]

        for idx, row in df_cab.iterrows():
            danger = row["Keterangan Akhir"] in ["Harus Diberhentikan", "PLT"]
            card_class = "school-danger" if danger else "school-card"

            st.markdown(f"""
            <div class="{card_class}">
                <b>🏫 {row['Nama Sekolah']}</b><br>
                👤 {row['Nama Kepala Sekolah']}<br>
                <span style="color:red; font-weight:700;">
                    {row['Keterangan Akhir']}
                </span>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("🔍 Lihat Detail"):
                st.write(f"**NIP:** {row['NIP']}")
                st.write(f"**Jabatan:** {row['Jabatan']}")
                st.write(f"**Jenjang:** {row['Jenjang']}")
                st.write(f"**BCKS:** {row['BCKS']}")
                st.write(f"**Tahun Pengangkatan:** {row['Tahun Pengangkatan']}")

                # ======================
                # CALON PENGGANTI
                # ======================
                if danger:
                    calon = st.selectbox(
                        "👤 Pilih Calon Pengganti",
                        sorted(df_guru["NAMA GURU"].dropna().unique()),
                        key=f"calon_{idx}"
                    )

                    st.success(f"✅ Calon pengganti dipilih: **{calon}**")

# ======================
# FOOTER
# ======================
st.markdown("""
<hr>
<p style="text-align:center; color:gray; font-size:13px;">
Dashboard Kepala Sekolah • Dinas Pendidikan Provinsi • Streamlit
</p>
""", unsafe_allow_html=True)
