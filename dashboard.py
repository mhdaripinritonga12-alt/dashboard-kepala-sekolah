import streamlit as st
import pandas as pd
import os

# =========================================================
# KONFIGURASI
# =========================================================
st.set_page_config(page_title="Dashboard Kepala Sekolah", layout="wide")

DATA_SAVE = "perubahan_kepsek.xlsx"
TAHUN_EVALUASI = 2026

# =========================================================
# SESSION STATE (LOGIN TAHAN RELOAD)
# =========================================================
if "login" not in st.session_state:
    st.session_state.login = True  # ⬅️ TIDAK MINTA LOGIN SAAT RELOAD

if "page" not in st.session_state:
    st.session_state.page = "cabdin"

if "selected_cabdin" not in st.session_state:
    st.session_state.selected_cabdin = None

# =========================================================
# LOAD & SAVE PERMANEN (ANTI ERROR)
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
# CSS
# =========================================================
st.markdown("""
<style>
.stApp { background:#d3d3d3; color:black; }
.school-card { background:white; border-left:6px solid #1f77b4;
    border-radius:10px; padding:16px; margin-bottom:14px; }
.school-danger { background:#fdecea; border-left:6px solid #d93025; }
.school-saved { background:#e6f4ea; border-left:6px solid #1e8e3e; }
.school-title { font-weight:700; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# LOAD DATA
# =========================================================
@st.cache_data
def load_data():
    df_ks = pd.read_excel("data_kepala_sekolah.xlsx", sheet_name="KEPALA_SEKOLAH")
    df_guru = pd.read_excel("data_kepala_sekolah.xlsx", sheet_name="GURU_SIMPEG")
    return df_ks, df_guru

df_ks, df_guru = load_data()
guru_list = sorted(df_guru["NAMA GURU"].dropna().unique())

# =========================================================
# HEADER
# =========================================================
col1, col2 = st.columns([6,1])
with col1:
    st.markdown("## 📊 Dashboard Kepala Sekolah")
with col2:
    if st.button("🚪 Logout"):
        st.session_state.login = False
        st.rerun()

st.divider()

# =========================================================
# FILTER
# =========================================================
st.sidebar.header("🔍 Filter")
search_nama = st.sidebar.text_input("Cari Nama Kepsek")
jenjang_filter = st.sidebar.selectbox("Jenjang", ["Semua"] + sorted(df_ks["Jenjang"].dropna().unique()))
ket_filter = st.sidebar.selectbox("Keterangan Akhir", ["Semua"] + sorted(df_ks["Keterangan Akhir"].dropna().unique()))

def apply_filter(df):
    if jenjang_filter != "Semua":
        df = df[df["Jenjang"] == jenjang_filter]
    if ket_filter != "Semua":
        df = df[df["Keterangan Akhir"] == ket_filter]
    if search_nama:
        df = df[df["Nama Kepala Sekolah"].str.contains(search_nama, case=False, na=False)]
    return df

# =========================================================
# HALAMAN CABDIN
# =========================================================
if st.session_state.page == "cabdin":
    st.subheader("🏢 Cabang Dinas Wilayah")
    cols = st.columns(4)
    for i, cabdin in enumerate(sorted(df_ks["Cabang Dinas"].unique())):
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
        sudah = nama_sekolah in perubahan_kepsek

        card = "school-saved" if sudah else "school-danger" if status == "Harus Diberhentikan" else "school-card"

        st.markdown(f"""
        <div class="{card}">
            <div class="school-title">🏫 {nama_sekolah}</div>
            👤 {row['Nama Kepala Sekolah']}<br>
            <b>{status}</b>
        </div>
        """, unsafe_allow_html=True)

        # ================= NIP → KETERANGAN HUKUM =================
        with st.expander(f"📌 NIP: {row['NIP']} (Klik untuk keterangan hukum)"):

            alasan = []

            masa_tugas = TAHUN_EVALUASI - row["Tahun Pengangkatan"]
            punya_bcks = str(row["Sertifikat BCKS"]).upper() == "YA"

            if row["Status Jabatan"] == "PLT":
                alasan.append("🔸 PLT: Masih berstatus Pelaksana Tugas, belum definitif.")

            if masa_tugas > 8:
                alasan.append("❌ Pasal 31: Telah melewati batas periode penugasan Kepala Sekolah.")

            if not punya_bcks:
                alasan.append("❌ Pasal 32: Belum memiliki Sertifikat Pelatihan BCKS.")

            if not alasan:
                st.success("✅ Aman tanpa masalah (sesuai Permendikdasmen No. 7 Tahun 2025)")
            else:
                for a in alasan:
                    st.error(a)

            st.caption("Dasar hukum: Permendikdasmen Nomor 7 Tahun 2025")

        # ================= PENGGANTI (TIDAK DIUBAH) =================
        if status == "Harus Diberhentikan" or sudah:

            default_idx = guru_list.index(perubahan_kepsek[nama_sekolah]) if sudah else 0
            calon = st.selectbox("👤 Calon Pengganti", guru_list, index=default_idx, key=f"calon_{idx}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 SAVE", key=f"save_{idx}"):
                    perubahan_kepsek[nama_sekolah] = calon
                    save_perubahan(perubahan_kepsek)
                    st.success("✅ Tersimpan permanen")
                    st.rerun()

            if sudah:
                with col2:
                    if st.button("✏️ Ubah Kembali", key=f"edit_{idx}"):
                        del perubahan_kepsek[nama_sekolah]
                        save_perubahan(perubahan_kepsek)
                        st.warning("Mode edit aktif")
                        st.rerun()

# =========================================================
# FOOTER
# =========================================================
st.divider()
st.caption("Dashboard Kepala Sekolah • MHD. ARIPIN RITONGA, S.Kom")
