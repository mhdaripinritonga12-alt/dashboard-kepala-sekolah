import streamlit as st
import pandas as pd

# =====================
# KONFIGURASI HALAMAN
# =====================
st.set_page_config(
    page_title="Dashboard Kepala Sekolah",
    layout="wide"
)

# =====================
# LOAD DATA (AMAN)
# =====================
@st.cache_data
def load_data():
    df_ks = pd.read_excel(
        "data_kepala_sekolah.xlsx",
        sheet_name="KEPALA_SEKOLAH"
    )

    df_guru = pd.read_excel(
        "data_guru_simpeg.xlsx",
        sheet_name="Sheet1"
    )

    return df_ks, df_guru


df_ks, df_guru = load_data()

# =====================
# VALIDASI KOLOM WAJIB
# =====================
kolom_ks = [
    "Cabang Dinas",
    "Nama Sekolah",
    "Nama Kepala Sekolah",
    "Keterangan Akhir",
    "Jenjang"
]

for k in kolom_ks:
    if k not in df_ks.columns:
        st.error(f"❌ Kolom '{k}' tidak ditemukan di data_kepala_sekolah.xlsx")
        st.stop()

kolom_guru = ["NAMA GURU", "NIK", "UNOR", "JABATAN"]
for k in kolom_guru:
    if k not in df_guru.columns:
        st.error(f"❌ Kolom '{k}' tidak ditemukan di data_guru_simpeg.xlsx")
        st.stop()

# =====================
# SIDEBAR FILTER
# =====================
st.sidebar.header("🔎 Filter")

jenjang = st.sidebar.selectbox(
    "Jenjang",
    ["Semua"] + sorted(df_ks["Jenjang"].dropna().unique())
)

if jenjang != "Semua":
    df_ks = df_ks[df_ks["Jenjang"] == jenjang]

# =====================
# HEADER
# =====================
st.markdown("""
<h2 style='color:#0B5394;'>📊 DASHBOARD KEPALA SEKOLAH</h2>
<hr>
""", unsafe_allow_html=True)

# =====================
# CSS CARD SEKOLAH
# =====================
st.markdown("""
<style>
.sekolah-box {
    background:#E8F1FF;
    padding:14px;
    border-radius:10px;
    margin-bottom:12px;
    border-left:6px solid #0B5394;
}
.berhenti {
    background:#FDECEA;
    border-left:6px solid #D93025;
}
.small {
    font-size:14px;
}
</style>
""", unsafe_allow_html=True)

# =====================
# TAMPILAN CABANG DINAS
# =====================
st.subheader("🏢 Cabang Dinas Pendidikan")

cabdin_list = sorted(df_ks["Cabang Dinas"].unique())

for cabdin in cabdin_list:
    with st.expander(f"📍 {cabdin}", expanded=False):

        data_cabdin = df_ks[df_ks["Cabang Dinas"] == cabdin]

        for i, row in data_cabdin.iterrows():
            status = row["Keterangan Akhir"]
            css = "sekolah-box berhenti" if status == "Harus Diberhentikan" else "sekolah-box"

            st.markdown(f"""
            <div class="{css}">
                <b>🏫 {row['Nama Sekolah']}</b><br>
                👤 {row['Nama Kepala Sekolah']}<br>
                <span style="color:red;"><b>{status}</b></span>
            </div>
            """, unsafe_allow_html=True)

            # =====================
            # DETAIL
            # =====================
            with st.expander("🔍 Lihat Detail"):
                st.markdown(f"""
                <div class="small">
                <b>Jenjang:</b> {row['Jenjang']}<br>
                </div>
                """, unsafe_allow_html=True)

                # =====================
                # JIKA HARUS DIGANTI
                # =====================
                if status == "Harus Diberhentikan":
                    st.markdown("### 👥 Pilih Calon Pengganti (SIMPEG)")

                    calon = st.selectbox(
                        "Nama Guru",
                        sorted(df_guru["NAMA GURU"].unique()),
                        key=f"ganti_{i}"
                    )

                    data_calon = df_guru[df_guru["NAMA GURU"] == calon].iloc[0]

                    st.success(f"""
                    ✅ **Calon Pengganti Dipilih**
                    - Nama: {data_calon['NAMA GURU']}
                    - NIK: {data_calon['NIK']}
                    - UNOR: {data_calon['UNOR']}
                    - Jabatan: {data_calon['JABATAN']}
                    """)

# =====================
# FOOTER
# =====================
st.markdown("""
<hr>
<p style='text-align:center; font-size:12px; color:gray;'>
Dashboard Kepala Sekolah • Dinas Pendidikan • Streamlit
</p>
""", unsafe_allow_html=True)
