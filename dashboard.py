import streamlit as st
import pandas as pd
import os
from io import BytesIO

# =========================================================
# KONFIGURASI
# =========================================================
st.set_page_config(
    page_title="Dashboard Kepala Sekolah",
    layout="wide"
)

DATA_SAVE = "perubahan_kepsek.xlsx"
DATA_FILE = "data_kepala_sekolah.xlsx"

# =========================================================
# SESSION STATE
# =========================================================
if "login" not in st.session_state:
    st.session_state.login = True

if "page" not in st.session_state:
    st.session_state.page = "cabdin"

if "selected_cabdin" not in st.session_state:
    st.session_state.selected_cabdin = None

# =========================================================
# LOAD & SAVE PERUBAHAN
# =========================================================
def load_perubahan():
    if os.path.exists(DATA_SAVE):
        df = pd.read_excel(DATA_SAVE)
        if {"Nama Sekolah", "Calon Pengganti"}.issubset(df.columns):
            return dict(zip(df["Nama Sekolah"], df["Calon Pengganti"]))
    return {}

def save_perubahan(data):
    pd.DataFrame(
        [{"Nama Sekolah": k, "Calon Pengganti": v} for k, v in data.items()]
    ).to_excel(DATA_SAVE, index=False)

perubahan_kepsek = load_perubahan()

# =========================================================
# LOAD DATA (CACHE)
# =========================================================
@st.cache_data(show_spinner="Memuat data...")
def load_data():
    df_ks = pd.read_excel(DATA_FILE, sheet_name="KEPALA_SEKOLAH")
    df_guru = pd.read_excel(DATA_FILE, sheet_name="GURU_SIMPEG")
    return df_ks, df_guru

df_ks, df_guru = load_data()
guru_list = sorted(df_guru["NAMA GURU"].astype(str).dropna().unique())

# =========================================================
# CSS TAMPILAN DINAS
# =========================================================
st.markdown("""
<style>
.stApp { background:#eef2f6; }
.card {
    background:white; padding:16px; border-radius:10px;
    border-left:6px solid #0d6efd; margin-bottom:14px;
}
.card-danger { border-left-color:#dc3545; background:#fdecea; }
.card-success { border-left-color:#198754; background:#e6f4ea; }
.title { font-weight:700; font-size:16px; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# LOGIN
# =========================================================
if not st.session_state.login:
    st.markdown("## 🔐 LOGIN DASHBOARD DINAS")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u == "aripin" and p == "@Ritonga":
            st.session_state.login = True
            st.rerun()
        else:
            st.error("❌ Login gagal")
    st.stop()

# =========================================================
# HEADER + REFRESH + LOGOUT
# =========================================================
c1, c2, c3, c4 = st.columns([5,2,2,2])
with c1:
    st.markdown("## 📊 Dashboard Kepala Sekolah")
with c2:
    if st.button("🔄 Refresh SIMPEG"):
        st.cache_data.clear()
        st.success("Data SIMPEG dimuat ulang")
        st.rerun()
with c3:
    if st.button("🔄 Refresh Kepala Sekolah"):
        st.cache_data.clear()
        st.success("Data Kepala Sekolah dimuat ulang")
        st.rerun()
with c4:
    if st.button("🚪 Logout"):
        st.session_state.login = False
        st.rerun()

st.divider()

# =========================================================
# 🔍 PENCARIAN GURU SIMPEG
# =========================================================
with st.expander("🔍 Pencarian Guru (SIMPEG)", expanded=True):
    key = st.text_input("Nama / NIP Guru")
    if key:
        hasil = df_guru[
            df_guru.astype(str)
            .apply(lambda c: c.str.contains(key, case=False, na=False))
            .any(axis=1)
        ]
        if hasil.empty:
            st.error("Guru tidak ditemukan")
        else:
            st.dataframe(hasil, use_container_width=True)

st.divider()

# =========================================================
# FILTER SIDEBAR
# =========================================================
st.sidebar.header("🔎 Filter")
search_nama = st.sidebar.text_input("Nama Kepala Sekolah")
jenjang = st.sidebar.selectbox("Jenjang", ["Semua"] + sorted(df_ks["Jenjang"].dropna().unique()))
ket = st.sidebar.selectbox("Keterangan", ["Semua"] + sorted(df_ks["Keterangan Akhir"].dropna().unique()))

def filter_df(df):
    if jenjang != "Semua":
        df = df[df["Jenjang"] == jenjang]
    if ket != "Semua":
        df = df[df["Keterangan Akhir"] == ket]
    if search_nama:
        df = df[df["Nama Kepala Sekolah"].str.contains(search_nama, case=False, na=False)]
    return df

# =========================================================
# HALAMAN CABANG DINAS + DOWNLOAD REKAP
# =========================================================
if st.session_state.page == "cabdin":
    st.subheader("🏢 Cabang Dinas Wilayah")
    df_view = filter_df(df_ks)

    cols = st.columns(4)
    for i, cabdin in enumerate(sorted(df_view["Cabang Dinas"].unique())):
        df_cd = df_view[df_view["Cabang Dinas"] == cabdin]

        rekap = df_cd["Keterangan Akhir"].value_counts()

        excel = BytesIO()
        with pd.ExcelWriter(excel, engine="xlsxwriter") as writer:
            df_cd.to_excel(writer, index=False)

        with cols[i % 4]:
            st.markdown(f"""
            <div class="card">
            <b>{cabdin}</b><br>
            Periode 1: {rekap.get('Aktif Periode 1',0)}<br>
            Periode 2: {rekap.get('Aktif Periode 2',0)}<br>
            PLT: {rekap.get('PLT',0)}<br>
            Diberhentikan: {rekap.get('Harus Diberhentikan',0)}
            </div>
            """, unsafe_allow_html=True)

            st.download_button(
                "📥 Download Rekap",
                data=excel.getvalue(),
                file_name=f"Rekap_{cabdin}.xlsx"
            )

            if st.button(f"📍 Buka {cabdin}", key=cabdin):
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

    df_cab = filter_df(df_ks[df_ks["Cabang Dinas"] == cabdin])

    for i, r in df_cab.iterrows():
        danger = r["Keterangan Akhir"] in ["Harus Diberhentikan", "Harap Segera Defenitifkan"]
        card = "card-danger" if danger else "card"

        st.markdown(f"""
        <div class="{card}">
        <div class="title">{r['Nama Sekolah']}</div>
        👤 {r['Nama Kepala Sekolah']}<br>
        <b>{r['Keterangan Akhir']}</b>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# FOOTER
# =========================================================
st.divider()
st.caption("Dashboard Kepala Sekolah • MHD. ARIPIN RITONGA, S.Kom")
