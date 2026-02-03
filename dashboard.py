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
# LOAD DATA (AMAN)
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

    # Normalisasi nama kolom (ANTI ERROR)
    ks.columns = ks.columns.str.strip().str.upper()
    guru.columns = guru.columns.str.strip().str.upper()

    return ks, guru


df_ks, df_guru = load_data()

# ======================
# VALIDASI KOLOM WAJIB
# ======================
wajib_ks = [
    "CABANG DINAS", "NAMA SEKOLAH", "NAMA KEPALA SEKOLAH",
    "NIP", "JENJANG", "JABATAN",
    "TAHUN PENGANGKATAN", "KETERANGAN AKHIR"
]

for col in wajib_ks:
    if col not in df_ks.columns:
        st.error(f"❌ Kolom '{col}' tidak ditemukan di KEPALA_SEKOLAH")
        st.stop()

for col in ["NAMA GURU", "UNOR"]:
    if col not in df_guru.columns:
        st.error(f"❌ Kolom '{col}' tidak ditemukan di GURU_SIMPEG")
        st.stop()

# ======================
# SIDEBAR FILTER
# ======================
st.sidebar.header("🔍 Filter")

jenjang = st.sidebar.selectbox(
    "Jenjang",
    ["Semua"] + sorted(df_ks["JENJANG"].dropna().unique())
)

if jenjang != "Semua":
    df_ks = df_ks[df_ks["JENJANG"] == jenjang]

# ======================
# HEADER
# ======================
st.markdown("""
<h2 style='color:#0B5394;'>📊 Dashboard Kepala Sekolah</h2>
<hr>
""", unsafe_allow_html=True)

# ======================
# CSS KOTAK SEKOLAH
# ======================
st.markdown("""
<style>
.school-box {
    background:#e8f1ff;
    border-left:6px solid #0B5394;
    padding:14px;
    border-radius:10px;
    margin-bottom:12px;
}
.school-danger {
    background:#fdecea;
    border-left:6px solid #d93025;
}
.small {
    font-size:13px;
}
</style>
""", unsafe_allow_html=True)

# ======================
# NAVIGASI CABANG DINAS
# ======================
if "cabdin" not in st.session_state:
    st.session_state.cabdin = None

st.subheader("🏢 Cabang Dinas")

cols = st.columns(4)
for i, cab in enumerate(sorted(df_ks["CABANG DINAS"].unique())):
    with cols[i % 4]:
        if st.button(f"📍 {cab}", use_container_width=True):
            st.session_state.cabdin = cab

# ======================
# TAMPILKAN SEKOLAH
# ======================
if st.session_state.cabdin:
    st.markdown(f"### 📍 {st.session_state.cabdin}")

    df_cab = df_ks[df_ks["CABANG DINAS"] == st.session_state.cabdin]

    for _, row in df_cab.iterrows():
        danger = row["KETERANGAN AKHIR"].upper() == "HARUS DIBERHENTIKAN"
        box = "school-box school-danger" if danger else "school-box"

        st.markdown(f"""
        <div class="{box}">
            <b>🏫 {row['NAMA SEKOLAH']}</b><br>
            👤 {row['NAMA KEPALA SEKOLAH']}<br>
            <span class="small"><b>Status:</b> {row['KETERANGAN AKHIR']}</span>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🔍 Detail"):
            st.write(f"**NIP:** {row['NIP']}")
            st.write(f"**Jabatan:** {row['JABATAN']}")
            st.write(f"**Jenjang:** {row['JENJANG']}")
            st.write(f"**Tahun Pengangkatan:** {row['TAHUN PENGANGKATAN']}")

            # ======================
            # CALON PENGGANTI
            # ======================
            if danger:
                st.markdown("### 👤 Pilih Calon Pengganti")

                calon = df_guru[
                    df_guru["UNOR"].str.contains(row["NAMA SEKOLAH"], case=False, na=False)
                ]

                if calon.empty:
                    st.warning("Tidak ada guru SIMPEG yang sesuai")
                else:
                    pilih = st.selectbox(
                        "Calon dari SIMPEG",
                        calon["NAMA GURU"].unique(),
                        key=row["NIP"]
                    )

                    st.success(f"Calon dipilih: {pilih}")

# ======================
# FOOTER
# ======================
st.markdown("""
<hr>
<p style='text-align:center;color:gray;font-size:12px;'>
Dashboard Kepala Sekolah • Streamlit
</p>
""", unsafe_allow_html=True)
