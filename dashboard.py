import streamlit as st
import pandas as pd
import os

# =========================================================
# KONFIGURASI APLIKASI
# =========================================================
st.set_page_config(
    page_title="Dashboard Kepala Sekolah",
    layout="wide"
)

DATA_SAVE = "perubahan_kepsek.xlsx"
DATA_FILE = "data_kepala_sekolah.xlsx"

# =========================================================
# SESSION STATE (ANTI AUTO LOGIN)
# =========================================================
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.login = False
    st.session_state.role = None

if "page" not in st.session_state:
    st.session_state.page = "cabdin"

if "selected_cabdin" not in st.session_state:
    st.session_state.selected_cabdin = None

# =========================================================
# 🔐 SISTEM LOGIN & ROLE USER
# =========================================================
USERS = {
    "operator": {"password": "operator123", "role": "Operator"},
    "kabidptk": {"password": "kabid123", "role": "Kabid"},
    "kadis": {"password": "kadis123", "role": "Kadis"}
}

if not st.session_state.login:
    st.markdown("## 🔐 Login Dashboard Kepala Sekolah")
    col1, col2, col3 = st.columns([2,3,2])
    with col2:
        username = st.text_input("👤 Username")
        password = st.text_input("🔑 Password", type="password")
        if st.button("🔓 Login", use_container_width=True):
            if username in USERS and USERS[username]["password"] == password:
                st.session_state.login = True
                st.session_state.role = USERS[username]["role"]
                st.success(f"✅ Login sebagai **{st.session_state.role}**")
                st.rerun()
            else:
                st.error("❌ Username / Password salah")
    st.stop()

boleh_edit = st.session_state.role in ["Operator", "Kabid"]

# =========================================================
# LOAD & SAVE PERUBAHAN KEPSEK
# =========================================================
def load_perubahan():
    if os.path.exists(DATA_SAVE):
        try:
            df = pd.read_excel(DATA_SAVE)
            if {"Nama Sekolah", "Calon Pengganti"}.issubset(df.columns):
                return dict(zip(df["Nama Sekolah"], df["Calon Pengganti"]))
        except:
            pass
    return {}

def save_perubahan(data):
    pd.DataFrame(
        [{"Nama Sekolah": k, "Calon Pengganti": v} for k, v in data.items()]
    ).to_excel(DATA_SAVE, index=False)

perubahan_kepsek = load_perubahan()

# =========================================================
# LOAD DATA (CACHE)
# =========================================================
@st.cache_data(show_spinner="📂 Memuat data Kepala Sekolah & SIMPEG...")
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
.stApp { background:#eef2f7; color:#000; }
.school-card { background:white; border-left:6px solid #1f77b4;
border-radius:10px; padding:16px; margin-bottom:14px; }
.school-danger { background:#fdecea; border-left:6px solid #d93025; }
.school-saved { background:#e6f4ea; border-left:6px solid #1e8e3e; }
.school-title { font-weight:700; font-size:16px; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER + REFRESH + LOGOUT
# =========================================================
col1, col2, col3, col4 = st.columns([5,2,2,2])

with col1:
    st.markdown("## 📊 Dashboard Kepala Sekolah")

with col2:
    if st.button("🔄 Refresh SIMPEG", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with col3:
    if st.button("🔄 Refresh Kepsek", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with col4:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.login = False
        st.session_state.role = None
        st.rerun()

st.divider()

# =========================================================
# 🔍 PENCARIAN GURU SIMPEG
# =========================================================
with st.expander("🔍 Pencarian Guru (SIMPEG)", expanded=False):
    key = st.text_input("Nama / NIP Guru")
    if key:
        hasil = df_guru[df_guru.astype(str)
                         .apply(lambda x: x.str.contains(key, case=False, na=False))
                         .any(axis=1)]
        st.dataframe(hasil if not hasil.empty else pd.DataFrame(),
                     use_container_width=True)

# =========================================================
# SIDEBAR FILTER
# =========================================================
st.sidebar.header("🔍 Filter")
search_nama = st.sidebar.text_input("Nama Kepala Sekolah")
jenjang = st.sidebar.selectbox("Jenjang", ["Semua"] + sorted(df_ks["Jenjang"].dropna().unique()))
ket = st.sidebar.selectbox("Keterangan", ["Semua"] + sorted(df_ks["Keterangan Akhir"].dropna().unique()))

def apply_filter(df):
    if jenjang != "Semua": df = df[df["Jenjang"] == jenjang]
    if ket != "Semua": df = df[df["Keterangan Akhir"] == ket]
    if search_nama:
        df = df[df["Nama Kepala Sekolah"].str.contains(search_nama, case=False, na=False)]
    return df

# =========================================================
# CABANG DINAS
# =========================================================
if st.session_state.page == "cabdin":
    st.subheader("🏢 Cabang Dinas")
    for cab in sorted(df_ks["Cabang Dinas"].unique()):
        if st.button(f"📍 {cab}", use_container_width=True):
            st.session_state.selected_cabdin = cab
            st.session_state.page = "sekolah"
            st.rerun()

# =========================================================
# SEKOLAH
# =========================================================
elif st.session_state.page == "sekolah":
    cab = st.session_state.selected_cabdin
    st.subheader(f"🏫 Sekolah — {cab}")

    if st.button("⬅ Kembali"):
        st.session_state.page = "cabdin"
        st.rerun()

    df_cab = apply_filter(df_ks[df_ks["Cabang Dinas"] == cab])

    for i, r in df_cab.iterrows():
        nama = r["Nama Sekolah"]
        status = r["Keterangan Akhir"]
        danger = status in ["Harus Diberhentikan", "Harap Segera Defenitifkan"]
        sudah = nama in perubahan_kepsek

        card = "school-saved" if sudah else "school-danger" if danger else "school-card"

        st.markdown(f"""
        <div class="{card}">
        <div class="school-title">🏫 {nama}</div>
        👤 {r['Nama Kepala Sekolah']}<br><b>{status}</b>
        {f"<br>✅ Pengganti: <b>{perubahan_kepsek[nama]}</b>" if sudah else ""}
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🔍 Detail & Penanganan"):
            st.write(f"NIP: {r['NIP']}")
            st.write(f"Jenjang: {r['Jenjang']}")
            st.write(f"Tahun Pengangkatan: {r['Tahun Pengangkatan']}")

            if (danger or sudah) and boleh_edit:
                calon = st.selectbox("Calon Pengganti", guru_list, key=f"c{i}")
                if st.button("💾 Simpan", key=f"s{i}"):
                    perubahan_kepsek[nama] = calon
                    save_perubahan(perubahan_kepsek)
                    st.rerun()

# =========================================================
# 📊 REKAP & REGULASI
# =========================================================
st.divider()
st.markdown("## 📑 Rekap Kepala Sekolah")

def map_status(s):
    if "Periode 1" in s: return "Periode 1"
    if "Periode 2" in s: return "Periode 2"
    if "PLT" in s: return "PLT"
    if "Diberhentikan" in s: return "Harus Diberhentikan"
    return "Lainnya"

df_ks["Status Regulatif"] = df_ks["Keterangan Akhir"].astype(str).apply(map_status)

rekap = df_ks.groupby(["Cabang Dinas", "Status Regulatif"]).size().unstack(fill_value=0)
st.dataframe(rekap, use_container_width=True)

rekap.to_excel("rekap_kepsek.xlsx")
with open("rekap_kepsek.xlsx","rb") as f:
    st.download_button("📥 Download Rekap Excel", f, "rekap_kepsek.xlsx")

st.bar_chart(df_ks["Status Regulatif"].value_counts())

st.info("""
⚖️ **Permendikdasmen No. 7 Tahun 2025**
- Maksimal 2 periode
- Wajib BCKS untuk perpanjangan
- Lebih 2 periode → diberhentikan
""")

st.caption("Dashboard Kepala Sekolah • MHD. ARIPIN RITONGA, S.Kom")
