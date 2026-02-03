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
        "data_kepala_sekolah.xlsx",
        sheet_name="GURU_SIMPEG"
    )
    return ks, guru

df_ks, df_guru = load_data()

# ======================
# VALIDASI KOLOM
# ======================
wajib_ks = [
    "Cabang Dinas", "Nama Sekolah", "Nama Kepala Sekolah",
    "NIP", "Jabatan", "Jenjang",
    "Sertifikat BCKS", "Tahun Pengangkatan", "Keterangan Akhir"
]

for col in wajib_ks:
    if col not in df_ks.columns:
        st.error(f"❌ Kolom '{col}' tidak ada di sheet KEPALA_SEKOLAH")
        st.stop()

if "NAMA GURU" not in df_guru.columns:
    st.error("❌ Kolom 'NAMA GURU' tidak ada di sheet GURU_SIMPEG")
    st.stop()

# ======================
# SESSION STATE NAVIGASI
# ======================
if "page" not in st.session_state:
    st.session_state.page = "cabdin"

if "selected_cabdin" not in st.session_state:
    st.session_state.selected_cabdin = None

if "selected_school" not in st.session_state:
    st.session_state.selected_school = None

# ======================
# HEADER
# ======================
st.markdown("""
<h1 style='color:#0B5394;font-weight:800'>
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
    ["Semua"] + sorted(df_ks["Jenjang"].dropna().unique())
)

df_filter = df_ks.copy()
if jenjang != "Semua":
    df_filter = df_filter[df_filter["Jenjang"] == jenjang]

# ======================
# HALAMAN 1 : CABANG DINAS
# ======================
if st.session_state.page == "cabdin":

    st.subheader("🏢 Cabang Dinas Wilayah")
    cols = st.columns(4)

    cabdin_list = sorted(df_filter["Cabang Dinas"].unique())

    for i, cabdin in enumerate(cabdin_list):
        with cols[i % 4]:
            jumlah = len(df_filter[df_filter["Cabang Dinas"] == cabdin])
            if st.button(f"📍 {cabdin}\n\n{jumlah} Sekolah", use_container_width=True):
                st.session_state.selected_cabdin = cabdin
                st.session_state.page = "sekolah"
                st.rerun()

# ======================
# HALAMAN 2 : SEKOLAH
# ======================
elif st.session_state.page == "sekolah":

    cabdin = st.session_state.selected_cabdin
    st.subheader(f"🏫 Sekolah di {cabdin}")

    if st.button("⬅ Kembali ke Cabang Dinas"):
        st.session_state.page = "cabdin"
        st.rerun()

    df_cab = df_filter[df_filter["Cabang Dinas"] == cabdin]

    for _, row in df_cab.iterrows():

        warna = "#fdecea" if row["Keterangan Akhir"] == "Harus Diberhentikan" else "#f4f6f9"
        border = "#d93025" if row["Keterangan Akhir"] == "Harus Diberhentikan" else "#1f77b4"

        st.markdown(
            f"""
            <div style="
                background:{warna};
                border-left:6px solid {border};
                padding:14px;
                border-radius:10px;
                margin-bottom:12px">
            <b>🏫 {row['Nama Sekolah']}</b><br>
            👤 {row['Nama Kepala Sekolah']}<br>
            <b style="color:red">{row['Keterangan Akhir']}</b>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.expander("🔍 Lihat Detail"):
            st.write(f"**NIP:** {row['NIP']}")
            st.write(f"**Jabatan:** {row['Jabatan']}")
            st.write(f"**Jenjang:** {row['Jenjang']}")
            st.write(f"**BCKS:** {row['Sertifikat BCKS']}")
            st.write(f"**Tahun Pengangkatan:** {row['Tahun Pengangkatan']}")

            # ======================
            # CALON PENGGANTI
            # ======================
            if row["Keterangan Akhir"] in ["Harus Diberhentikan", "PLT"]:
                calon = st.selectbox(
                    "👤 Pilih Calon Pengganti",
                    sorted(df_guru["NAMA GURU"].unique()),
                    key=f"calon_{row['NIP']}"
                )
                st.success(f"Calon pengganti dipilih: **{calon}**")

# ======================
# FOOTER
# ======================
st.markdown("""
<hr>
<p style="text-align:center;color:gray;font-size:13px">
Dashboard Kepala Sekolah • Dinas Pendidikan Provinsi
</p>
""", un
