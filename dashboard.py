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

if "perubahan_kepsek" not in st.session_state:
    st.session_state.perubahan_kepsek = {}

# =========================================================
# CSS GLOBAL (AMAN)
# =========================================================
st.markdown("""
<style>
.stApp {
    background-color: #d3d3d3;
    color: black;
}

/* Card sekolah */
.school-card {
    background: white;
    border-left: 6px solid #1f77b4;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 14px;
}
.school-danger {
    background: #fdecea;
    border-left: 6px solid #d93025;
}
.school-saved {
    background: #e6f4ea;
    border-left: 6px solid #1e8e3e;
}
.school-title {
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# LOGIN (STABIL)
# =========================================================
if not st.session_state.login:

    st.markdown("## 🔐 LOGIN DASHBOARD")

    col1, col2, col3 = st.columns([2,3,2])
    with col2:
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")

        if st.button("Login", use_container_width=True):
            if user == "aripin" and pwd == "ritonga":
                st.session_state.login = True
                st.rerun()
            else:
                st.error("❌ Username atau Password salah")

    st.stop()

# =========================================================
# LOAD DATA
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
# HEADER + LOGOUT
# =========================================================
col1, col2 = st.columns([6,1])
with col1:
    st.markdown("## 📊 Dashboard Kepala Sekolah")
with col2:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.login = False
        st.session_state.page = "cabdin"
        st.session_state.selected_cabdin = None
        st.session_state.perubahan_kepsek = {}
        st.rerun()

st.divider()

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

    if st.button("⬅ Kembali"):
        st.session_state.page = "cabdin"
        st.rerun()

    df_cab = apply_filter(df_ks[df_ks["Cabang Dinas"] == cabdin])

    for idx, row in df_cab.iterrows():

        nama_sekolah = row["Nama Sekolah"]
        status = row["Keterangan Akhir"]

        danger = status in ["Harap Segera Defenitifkan", "Harus Diberhentikan"]
        sudah_disave = nama_sekolah in st.session_state.perubahan_kepsek

        if sudah_disave:
            card_class = "school-card school-saved"
        elif danger:
            card_class = "school-card school-danger"
        else:
            card_class = "school-card"

        st.markdown(f"""
        <div class="{card_class}">
            <div class="school-title">🏫 {nama_sekolah}</div>
            👤 {row['Nama Kepala Sekolah']}<br>
            <b>{status}</b>
            {f"<br>✅ Pengganti: <b>{st.session_state.perubahan_kepsek[nama_sekolah]}</b>" if sudah_disave else ""}
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🔍 Detail Kepala Sekolah"):
            st.write(f"**NIP:** {row['NIP']}")
            st.write(f"**Jabatan:** {row['Jabatan']}")
            st.write(f"**Jenjang:** {row['Jenjang']}")
            st.write(f"**Tahun Pengangkatan:** {row['Tahun Pengangkatan']}")

            if danger or sudah_disave:

                daftar_guru = sorted(df_guru["NAMA GURU"].dropna().unique())

                default_index = (
                    daftar_guru.index(
                        st.session_state.perubahan_kepsek[nama_sekolah]
                    ) if sudah_disave else 0
                )

                calon = st.selectbox(
                    "👤 Pilih / Ubah Calon Pengganti (SIMPEG)",
                    daftar_guru,
                    index=default_index,
                    key=f"calon_{idx}"
                )

                col_save, col_edit = st.columns(2)

                with col_save:
                    if st.button("💾 SAVE", key=f"save_{idx}", use_container_width=True):
                        st.session_state.perubahan_kepsek[nama_sekolah] = calon
                        st.success("✅ Perubahan disimpan")
                        st.rerun()

                if sudah_disave:
                    with col_edit:
                        if st.button("✏️ Ubah Kembali", key=f"edit_{idx}", use_container_width=True):
                            del st.session_state.perubahan_kepsek[nama_sekolah]
                            st.warning("✏️ Mode edit diaktifkan")
                            st.rerun()

# =========================================================
# FOOTER
# =========================================================
st.divider()
st.caption("Dashboard Kepala Sekolah • MHD. ARIPIN RITONGA, S.Kom")
