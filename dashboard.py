import streamlit as st
import pandas as pd

# ======================
# KONFIGURASI
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
    ks = pd.read_excel(
        "data_kepala_sekolah.xlsx",
        sheet_name="KEPALA_SEKOLAH"
    )
    guru = pd.read_excel(
        "data_kepala_sekolah.xlsx",
        sheet_name="GURU_SIMPEG"
    )
    return ks, guru

df_ks, df_guru = load_data()

# ======================
# VALIDASI KOLOM
# ======================
kolom_ks_wajib = [
    "Cabang Dinas", "Nama Sekolah", "Nama Kepala Sekolah",
    "NIP", "Jenjang", "Jabatan",
    "Sertifikat BCKS", "Tahun Pengangkatan", "Keterangan Akhir"
]

for col in kolom_ks_wajib:
    if col not in df_ks.columns:
        st.error(f"❌ Kolom '{col}' tidak ditemukan di sheet KEPALA_SEKOLAH")
        st.stop()

if "NAMA GURU" not in df_guru.columns:
    st.error("❌ Kolom 'NAMA GURU' tidak ditemukan di sheet GURU_SIMPEG")
    st.stop()

# ======================
# HEADER
# ======================
st.markdown("""
<h1 style='color:#0B5394; font-weight:800;'>
📊 DASHBOARD KEPALA SEKOLAH DINAS PENDIDIKAN
</h1>
<hr>
""", unsafe_allow_html=True)

# ======================
# FILTER SIDEBAR
# ======================
st.sidebar.header("🔎 Filter")

jenjang = st.sidebar.selectbox(
    "Jenjang",
    ["Semua"] + sorted(df_ks["Jenjang"].dropna().unique())
)

if jenjang != "Semua":
    df_ks = df_ks[df_ks["Jenjang"] == jenjang]

# ======================
# CSS
# ======================
st.markdown("""
<style>
.card {
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 14px;
    background-color: #f4f6f9;
    border-left: 6px solid #1f77b4;
}
.card-danger {
    background-color: #fdecea;
    border-left: 6px solid #d93025;
}
</style>
""", unsafe_allow_html=True)

# ======================
# CABANG DINAS
# ======================
st.subheader("🏢 Cabang Dinas Wilayah")
st.caption("Klik Cabang Dinas → Sekolah → Detail Kepala Sekolah")

cabdin_list = sorted(df_ks["Cabang Dinas"].unique())
cols = st.columns(4)

for i, cabdin in enumerate(cabdin_list):
    with cols[i % 4]:
        with st.expander(f"📍 {cabdin}", expanded=False):

            df_cab = df_ks[df_ks["Cabang Dinas"] == cabdin]

            for idx, row in df_cab.iterrows():

                status = row["Keterangan Akhir"]
                danger = status in ["PLT", "Harus Diberhentikan"]
                card_class = "card-danger" if danger else "card"

                st.markdown(f"""
                <div class="{card_class}">
                    <b>🏫 {row['Nama Sekolah']}</b><br>
                    👤 {row['Nama Kepala Sekolah']}<br>
                    <span style="color:red; font-weight:700;">
                        {status}
                    </span>
                </div>
                """, unsafe_allow_html=True)

                with st.expander("🔍 Lihat Detail"):
                    st.write(f"**NIP:** {row['NIP']}")
                    st.write(f"**Jabatan:** {row['Jabatan']}")
                    st.write(f"**Jenjang:** {row['Jenjang']}")
                    st.write(f"**Sertifikat BCKS:** {row['Sertifikat BCKS']}")
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
                        st.success(f"Calon pengganti dipilih: **{calon}**")

# ======================
# FOOTER
# ======================
st.markdown("""
<hr>
<p style='text-align:center; color:gray; font-size:13px;'>
Dashboard Kepala Sekolah • Dinas Pendidikan Provinsi • Streamlit
</p>
""", unsafe_allow_html=True)
