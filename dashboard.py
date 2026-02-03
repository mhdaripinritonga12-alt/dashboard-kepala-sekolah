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
# SESSION STATE
# =========================================================
if "login" not in st.session_state:
    st.session_state.login = False

if "page" not in st.session_state:
    st.session_state.page = "cabdin"

if "selected_cabdin" not in st.session_state:
    st.session_state.selected_cabdin = None

# =========================================================
# CSS GLOBAL (LOGIN + DASHBOARD)
# =========================================================
st.markdown("""
<style>
/* ================= BACKGROUND ================= */
.stApp {
    background: #d3d3d3; /* biru tua */
    color: black;
}

/* ================= LOGIN ================= */
.login-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 85vh;
}

.login-box {
    width: 250px;
    padding: 28px;
    border-radius: 16px;
    background: linear-gradient(130deg, #1f2fd2, #150fa3);
    box-shadow: 0 12px 28px rgba(0,0,0,0.25);
    text-align: center;
}

.login-title {
    color: white;
    font-weight: 100;
    font-size: 18px;
    margin-top: 10px;
    margin-bottom: 18px;
}

/* ================= CARD SEKOLAH ================= */
.school-card {
    background:#eaf2fb;
    border-left:6px solid #1f77b4;
    border-radius:12px;
    padding:20px;
    margin-bottom:25px;
    font-size:20px;
    color:black;
}

.school-danger {
    background:#fdecea;
    border-left:6px solid #d93025;
}

.school-title {
    font-weight:700;
}

/* ================= BUTTON ================= */
button {
    border-radius:10px !important;
    font-weight:600 !important;
}

.logout-btn button {
    background:#0000ff !important;
    color:white !important;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# LOGIN (GABUNGAN RUMUS 1 + 2)
# =========================================================
if not st.session_state.login:

    st.markdown("<div class='login-wrapper'>", unsafe_allow_html=True)
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)

    st.image(
        "st.image(
    "https://upload.wikimedia.org/wikipedia/commons/8/8e/Logo_Pemerintah_Provinsi_Sumatera_Utara.png",
    width=90 )

    st.markdown("<div class='login-title'>🔐 LOGIN DASHBOARD</div>", unsafe_allow_html=True)

    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login", use_container_width=True):
        if user == "aripin" and pwd == "ritonga":
            st.session_state.login = True
            st.rerun()
        else:
            st.error("❌ Username atau Password salah")

    st.markdown("</div></div>", unsafe_allow_html=True)
    st.stop()

# =========================================================
# LOAD DATA
# =========================================================
@st.cache_data
def load_data():
    df_ks = pd.read_excel("data_kepala_sekolah.xlsx", sheet_name="KEPALA_SEKOLAH")
    df_guru = pd.read_excel("data_kepala_sekolah.xlsx", sheet_name="GURU_SIMPEG")
    return df_ks, df_guru

df_ks, df_guru = load_data()

# =========================================================
# HEADER + LOGOUT
# =========================================================
col1, col2 = st.columns([6,1])

with col1:
    st.markdown(
        "<h2 style='color:black;'>📊 Dashboard Kepala Sekolah</h2>",
        unsafe_allow_html=True
    )

with col2:
    with st.container():
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.login = False
            st.session_state.page = "cabdin"
            st.session_state.selected_cabdin = None
            st.rerun()

st.markdown("<hr>", unsafe_allow_html=True)

# =========================================================
# SIDEBAR FILTER
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
# HALAMAN CABANG DINAS
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
# HALAMAN SEKOLAH
# =========================================================
elif st.session_state.page == "sekolah":

    cabdin = st.session_state.selected_cabdin
    st.subheader(f"🏫 Sekolah — {cabdin}")

    if st.button("⬅ Kembali ke Cabang Dinas"):
        st.session_state.page = "cabdin"
        st.rerun()

    df_cab = apply_filter(df_ks[df_ks["Cabang Dinas"] == cabdin])

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
<p style='text-align:center; color:black; font-size:12px'>
Dashboard Kepala Sekolah • Streamlit
</p>
""", unsafe_allow_html=True)







