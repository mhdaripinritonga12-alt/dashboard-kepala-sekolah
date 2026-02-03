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

# ======================
# VALIDASI KOLOM
# ======================
kolom_ks_wajib = [
    "Cabang Dinas",
    "Nama Sekolah",
    "Nama Kepala Sekolah",
    "NIP",
    "Jenjang",
    "Jabatan",
    "Tahun Pengangkatan",
    "Keterangan Akhir"
]

for col in kolom_ks_wajib:
    if col not in df_ks.columns:
        st.error(f"❌ Kolom '{col}' tidak ditemukan di data_kepala_sekolah.xlsx")
        st.stop()

if "NAMA GURU" not in df_guru.columns:
    st.error("❌ Kolom 'NAMA GURU' tidak ditemukan di data_guru_simpeg.xlsx")
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
# SIDEBAR FILTER
# ======================
st.sidebar.header("🔎 Filter")

jenjang_filter = st.sidebar.selectbox(
    "Jenjang",
    ["Semua"] + sorted(df_ks["Jenjang"].dropna().unique())
)

df_view = df_ks.copy()
if jenjang_filter != "Semua":
    df_view = df_view[df_view["Jenjang"] == jenjang_filter]

# ======================
# CSS CARD
# ======================
st.markdown("""
<style>
.card {
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 14px;
    background-color: #e8f1ff;
    border-left: 6px solid #0b5394;
}
.card-danger {
    background-color: #fdecea;
    border-left: 6px solid #d93025;
}
.school-title {
    font-size: 16px;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# ======================
# CABANG DINAS
# ======================
st.subheader("🏢 Cabang Dinas Wilayah")
st.caption("Klik Cabang Dinas → Sekolah → Detail Kepala Sekolah")

for cabdin in sorted(df_view["Cabang Dinas"].unique()):
    with st.expander(f"📍 {cabdin}", expanded=False):

        df_cab = df_view[df_view["Cabang Dinas"] == cabdin]

        for idx, row in df_cab.iterrows():

            is_danger = row["Keterangan Akhir"] == "Harus Diberhentikan"
            card_class = "card-danger" if is_danger else "card"

            st.markdown(f"""
            <div class="{card_class}">
                <div class="school-title">🏫 {row['Nama Sekolah']}</div>
                👤 <b>{row['Nama Kepala Sekolah']}</b><br>
                <span style="color:red; font-weight:700;">
                    {row['Keterangan Akhir']}
                </span>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("🔍 Lihat Detail"):
                st.write(f"**NIP:** {row['NIP']}")
                st.write(f"**Jabatan:** {row['Jabatan']}")
                st.write(f"**Jenjang:** {row['Jenjang']}")
                st.write(f"**Tahun Pengangkatan:** {row['Tahun Pengangkatan']}")

                # ======================
                # CALON PENGGANTI
                # ======================
                if is_danger:
                    st.markdown("### 👤 Pilih Calon Pengganti")

                    calon_list = sorted(df_guru["NAMA GURU"].dropna().unique())

                    calon = st.selectbox(
                        "Calon Pengganti (Data Guru SIMPEG)",
                        ["-- Pilih --"] + calon_list,
                        key=f"calon_{idx}"
                    )

                    if calon != "-- Pilih --":
                        st.success(f"✅ Calon pengganti dipilih: **{calon}**")

# ======================
# FOOTER
# ======================
st.markdown("""
<hr>
<p style='text-align:center; color:gray; font-size:13px;'>
Dashboard Kepala Sekolah • Dinas Pendidikan Provinsi • Streamlit
</p>
""", unsafe_allow_html=True)
