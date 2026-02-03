import streamlit as st
import pandas as pd

# =========================================================
# KONFIGURASI
# =========================================================
st.set_page_config(
    page_title="Dashboard Kepala Sekolah",
    layout="wide"
)

# =========================================================
# LOGIN SEDERHANA
# =========================================================
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Login Dashboard")

    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == "aripin" and pwd == "ritonga":
            st.session_state.login = True
            st.rerun()
        else:
            st.error("❌ Username / Password salah")
    st.stop()

# =========================================================
# LOAD DATA (PASTI BENAR SESUAI DEBUG ANDA)
# =========================================================
@st.cache_data
def load_data():
    df_ks = pd.read_excel(
        "data_kepala_sekolah.xlsx",
        sheet_name="KEPALA_SEKOLAH"
    )
    df_guru = pd.read_excel(
        "data_kepala_sekolah.xlsx",
        sheet_name="GURU_SIMPEG"
    )
    return df_ks, df_guru

df_ks, df_guru = load_data()

# =========================================================
# SESSION STATE
# =========================================================
if "page" not in st.session_state:
    st.session_state.page = "cabdin"

if "selected_cabdin" not in st.session_state:
    st.session_state.selected_cabdin = None

# =========================================================
# HEADER
# =========================================================
st.markdown("""
<h2 style='color:#0B5394;'>📊 Dashboard Kepala Sekolah</h2>
<hr>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR FILTER & SEARCH
# =========================================================
st.sidebar.header("🔍 Filter & Pencarian")

search_nama = st.sidebar.text_input("Cari Nama Kepala Sekolah")

jenjang_filter = st.sidebar.selectbox(
    "Jenjang",
    ["Semua"] + sorted(df_ks["Jenjang"].dropna().unique())
)

ket_filter = st.sidebar.selectbox(
    "Keterangan Akhir",
    ["Semua"] + sorted(df_ks["Keterangan Akhir"].dropna().unique())
)

# =========================================================
# CSS CARD
# =========================================================
st.markdown("""
<style>
.school-card {
    background:#eaf2fb;
    border-left:6px solid #1f77b4;
    border-radius:10px;
    padding:12px;
    margin-bottom:10px;
    font-size:14px;
}
.school-danger {
    background:#fdecea;
    border-left:6px solid #d93025;
}
.school-title {
    font-weight:700;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# FUNGSI FILTER GLOBAL
# =========================================================
def apply_filter(df):
    if jenjang_filter != "Semua":
        df = df[df["Jenjang"] == jenjang_filter]

    if ket_filter != "Semua":
        df = df[df["Keterangan Akhir"] == ket_filter]

    if search_nama:
        df = df[df["Nama Kepala Sekolah"]
                .str.contains(search_nama, case=False, na=False)]

    return df

# =========================================================
# HALAMAN 1 — CABANG DINAS
# =========================================================
if st.session_state.page == "cabdin":

    st.subheader("🏢 Cabang Dinas Wilayah")

    df_view = apply_filter(df_ks)
    cabdin_list = sorted(df_view["Cabang Dinas"].unique())

    cols = st.columns(4)
    for i, cabdin in enumerate(cabdin_list):
        with cols[i % 4]:
            if st.button(f"📍 {cabdin}", use_container_width=True):
                st.session_state.selected_cabdin = cabdin
                st.session_state.page = "sekolah"
                st.rerun()

# =========================================================
# HALAMAN 2 — SEKOLAH DALAM CABDIN
# =========================================================
elif st.session_state.page == "sekolah":

    cabdin = st.session_state.selected_cabdin
    st.subheader(f"🏫 Sekolah — {cabdin}")

    if st.button("⬅ Kembali ke Cabang Dinas"):
        st.session_state.page = "cabdin"
        st.rerun()

    df_cab = df_ks[df_ks["Cabang Dinas"] == cabdin]
    df_cab = apply_filter(df_cab)

    for idx, row in df_cab.iterrows():

        status = row["Keterangan Akhir"]
        danger = status in ["PLT", "Harus Diberhentikan"]

        card_class = "school-card school-danger" if danger else "school-card"

        st.markdown(f"""
        <div class="{card_class}">
            <div class="school-title">🏫 {row['Nama Sekolah']}</div>
            👤 {row['Nama Kepala Sekolah']}<br>
            <b style="color:red">{status}</b>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🔍 Detail Kepala Sekolah"):
            st.write(f"**NIP:** {row['NIP']}")
            st.write(f"**Jabatan:** {row['Jabatan']}")
            st.write(f"**Jenjang:** {row['Jenjang']}")
            st.write(f"**Tahun Pengangkatan:** {row['Tahun Pengangkatan']}")

            # =================================================
            # GANTI KEPSEK DARI SIMPEG
            # =================================================
            if danger:
                calon = st.selectbox(
                    "👤 Pilih Calon Pengganti (SIMPEG)",
                    sorted(df_guru["NAMA GURU"].dropna().unique()),
                    key=f"calon_{idx}"
                )
                st.success(f"✅ Calon dipilih: {calon}")

# =========================================================
# FOOTER
# =========================================================
st.markdown("""
<hr>
<p style='text-align:center; color:gray; font-size:12px'>
Dashboard Kepala Sekolah • Streamlit
</p>
""", unsafe_allow_html=True)
