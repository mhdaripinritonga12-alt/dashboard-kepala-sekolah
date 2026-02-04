import streamlit as st
import pandas as pd
import os
# =========================================================
# 🔒 PAKSA LOGIN SETIAP APLIKASI DIBUKA ULANG
# (ANTI AUTO-LOGIN, TANPA MENGUBAH KODE LAMA)
# =========================================================
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.login = False
    st.session_state.role = None

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
# SESSION STATE
# =========================================================
if "login" not in st.session_state:
    st.session_state.login = True

if "page" not in st.session_state:
    st.session_state.page = "cabdin"

if "selected_cabdin" not in st.session_state:
    st.session_state.selected_cabdin = None
    # =========================================================
# 🔐 SISTEM LOGIN & ROLE USER (WAJIB LOGIN)
# =========================================================

# DAFTAR USER (HARDCODE – AMAN UNTUK INTERNAL DINAS)
USERS = {
    "operator": {
        "password": "operator123",
        "role": "Operator"
    },
    "kabidptk": {
        "password": "kabid123",
        "role": "Kabid"
    },
    "kadis": {
        "password": "kadis123",
        "role": "Kadis"
    }
}

# SESSION ROLE
if "role" not in st.session_state:
    st.session_state.role = None

# LOGIN WAJIB SEBELUM AKSES DASHBOARD
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
                st.success(f"✅ Login berhasil sebagai **{st.session_state.role}**")
                st.rerun()
            else:
                st.error("❌ Username atau Password salah")

    st.stop()
# =========================================================
# 👤 INFO USER LOGIN
# =========================================================
st.caption(f"👤 Login sebagai: **{st.session_state.role}**")

# =========================================================
# 🔐 BATASI AKSES BERDASARKAN ROLE
# =========================================================
boleh_edit = st.session_state.role in ["Operator", "Kabid"]

# =========================================================
# FUNGSI SIMPAN & LOAD PERUBAHAN KEPSEK
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

def save_perubahan(data_dict):
    df = pd.DataFrame(
        [{"Nama Sekolah": k, "Calon Pengganti": v} for k, v in data_dict.items()]
    )
    df.to_excel(DATA_SAVE, index=False)

perubahan_kepsek = load_perubahan()

# =========================================================
# LOAD DATA UTAMA (CACHE)
# =========================================================
@st.cache_data(show_spinner="📂 Memuat data Kepala Sekolah & SIMPEG...")
def load_data():
    df_ks = pd.read_excel(DATA_FILE, sheet_name="KEPALA_SEKOLAH")
    df_guru = pd.read_excel(DATA_FILE, sheet_name="GURU_SIMPEG")
    return df_ks, df_guru

df_ks, df_guru = load_data()
guru_list = sorted(df_guru["NAMA GURU"].astype(str).dropna().unique())

# =========================================================
# CSS (TAMPILAN DINAS)
# =========================================================
st.markdown("""
<style>
/* ===== CABANG DINAS CARD BESAR ===== */
.cabdin-card {
    background: white;
    border-radius: 16px;
    padding: 26px 18px;
    margin-bottom: 20px;
    text-align: center;
    font-size: 20px;
    font-weight: 700;
    border-left: 10px solid #1f77b4;
    box-shadow: 0 4px 10px rgba(0,0,0,0.12);
    cursor: pointer;
    transition: 0.2s;
}

.cabdin-card:hover {
    background: #eef4ff;
    transform: scale(1.02);
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# HEADER + REFRESH + LOGOUT
# =========================================================
col1, col2, col3, col4 = st.columns([5,2,2,2])

with col1:
    st.markdown("## 📊 Dashboard Kepala Sekolah")

with col2:
    if st.button("🔄 Refresh Data SIMPEG", use_container_width=True):
        st.cache_data.clear()
        st.success("✅ Data SIMPEG dimuat ulang")
        st.rerun()

with col3:
    if st.button("🔄 Refresh Data Kepsek", use_container_width=True):
        st.cache_data.clear()
        st.success("✅ Data Kepala Sekolah dimuat ulang")
        st.rerun()

with col4:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.login = False
        st.session_state.page = "cabdin"
        st.session_state.selected_cabdin = None
        st.rerun()

st.divider()
# RESET ROLE SAAT LOGOUT
if not st.session_state.login:
    st.session_state.role = None

# =========================================================
# 🔍 PENCARIAN GURU SIMPEG
# =========================================================
with st.expander("🔍 Pencarian Guru (SIMPEG)", expanded=False):
    keyword = st.text_input(
        "Ketik Nama Guru atau NIP",
        placeholder="contoh: Mhd Aripin Ritonga/ 1994"
    )

    if keyword:
        hasil = df_guru[
            df_guru.astype(str)
            .apply(lambda col: col.str.contains(keyword, case=False, na=False))
            .any(axis=1)
        ]

        if hasil.empty:
            st.error("❌ Guru tidak ditemukan di data SIMPEG")
        else:
            st.success(f"✅ Ditemukan {len(hasil)} data guru")
            st.dataframe(hasil, use_container_width=True)

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
        df = df[df["Nama Kepala Sekolah"].str.contains(search_nama, case=False, na=False)]
    return df
def urutkan_cabdin(cabdin_list):
    def ambil_angka(text):
        angka = "".join(filter(str.isdigit, str(text)))
        return int(angka) if angka else 999  # aman jika tidak ada angka
    return sorted(cabdin_list, key=ambil_angka)


# =========================================================
# HALAMAN CABANG DINAS
# =========================================================
elif st.session_state.page == "sekolah":

    cabdin = st.session_state.selected_cabdin
    st.subheader(f"🏫 Sekolah — {cabdin}")

    if st.button("⬅ Kembali"):
        st.session_state.page = "cabdin"
        st.rerun()

    # ===============================
    # 🔴 WAJIB ADA: DEFINISI df_cab
    # ===============================
    df_cab = apply_filter(
        df_ks[df_ks["Cabang Dinas"] == cabdin]
    )

    # ===============================
    # GRID 5 KOLOM
    # ===============================
    cols = st.columns(5)

    for i, row in df_cab.reset_index(drop=True).iterrows():

        with cols[i % 5]:

            # ===============================
            # DATA DASAR (WAJIB SEBELUM DIPAKAI)
            # ===============================
            nama_sekolah = row["Nama Sekolah"]
            nama_kepsek  = row["Nama Kepala Sekolah"]
            status       = row["Keterangan Akhir"]

            sudah = nama_sekolah in perubahan_kepsek

            # ===============================
            # CARD RINGKAS
            # ===============================
            st.markdown(f"""
            <div class="school-card">
                <b>🏫 {nama_sekolah}</b>
            </div>
            """, unsafe_allow_html=True)

            # ===============================
            # DETAIL & PENANGANAN
            # ===============================
            with st.expander("🔍 Lihat Detail & Penanganan"):

                st.markdown(f"""
                👤 **Kepala Sekolah Saat Ini:** {nama_kepsek}  
                📌 **Status:** {status}
                """)

                if sudah:
                    st.success(f"✅ Calon Pengganti: {perubahan_kepsek[nama_sekolah]}")

                # ===============================
                # ATURAN FINAL
                # ===============================
                boleh_ganti_baru = status != "Aktif Periode 1"
                boleh_batalkan   = sudah

                widget_id = nama_sekolah.replace(" ", "_")

                # ===============================
                # PILIH CALON BARU
                # ===============================
                if boleh_ganti_baru:

                    default_idx = (
                        guru_list.index(perubahan_kepsek[nama_sekolah])
                        if sudah and perubahan_kepsek[nama_sekolah] in guru_list
                        else 0
                    )

                    calon = st.selectbox(
                        "👤 Pilih Calon Pengganti (SIMPEG)",
                        guru_list,
                        index=default_idx,
                        key=f"calon_{widget_id}"
                    )

                    if st.button(
                        "💾 Simpan",
                        key=f"save_{widget_id}",
                        use_container_width=True
                    ):
                        perubahan_kepsek[nama_sekolah] = calon
                        save_perubahan(perubahan_kepsek)
                        st.success("✅ Pengganti disimpan")
                        st.rerun()
                else:
                    st.warning("⛔ Tidak dapat memilih calon baru karena masih Aktif Periode 1")

                # ===============================
                # ✏️ KEMBALIKAN / BERSIHKAN
                # ===============================
                if boleh_batalkan:
                    if st.button(
                        "✏️ Kembalikan ke Kepala Sekolah Lama",
                        key=f"undo_{widget_id}",
                        use_container_width=True
                    ):
                        perubahan_kepsek.pop(nama_sekolah, None)
                        save_perubahan(perubahan_kepsek)
                        st.success("🔄 Calon pengganti dibersihkan")
                        st.rerun()

# =========================================================
# 📊 REKAP & ANALISIS PIMPINAN (TAMBAHAN RESMI DINAS)
# =========================================================
st.divider()
st.markdown("## 📑 Rekap & Analisis Kepala Sekolah (Pimpinan)")

# ---------------------------------------------------------
# NORMALISASI STATUS SESUAI REGULASI
# ---------------------------------------------------------
def map_status(status):
    if "Periode 1" in status:
        return "Aktif Periode 1"
    if "Periode 2" in status:
        return "Aktif Periode 2"
    if "Definitif" in status or "PLT" in status:
        return "PLT / Harap Definitif"
    if "Diberhentikan" in status:
        return "Harus Diberhentikan"
    return "Lainnya"

df_rekap = df_ks.copy()
df_rekap["Status Regulatif"] = df_rekap["Keterangan Akhir"].astype(str).apply(map_status)

# ---------------------------------------------------------
# 📊 REKAP PER CABANG DINAS
# ---------------------------------------------------------
rekap_cabdin = (
    df_rekap
    .groupby(["Cabang Dinas", "Status Regulatif"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)

st.subheader("📌 Rekap Kepala Sekolah per Cabang Dinas")
st.dataframe(rekap_cabdin, use_container_width=True)

# ---------------------------------------------------------
# 📥 DOWNLOAD EXCEL REKAP
# ---------------------------------------------------------
excel_file = "rekap_kepala_sekolah_per_cabdin.xlsx"
rekap_cabdin.to_excel(excel_file, index=False)

with open(excel_file, "rb") as f:
    st.download_button(
        label="📥 Download Rekap Kepala Sekolah (Excel)",
        data=f,
        file_name=excel_file,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ---------------------------------------------------------
# 📈 GRAFIK STATUS KEPALA SEKOLAH
# ---------------------------------------------------------
st.subheader("📊 Grafik Status Kepala Sekolah")

grafik_data = (
    df_rekap["Status Regulatif"]
    .value_counts()
    .reindex([
        "Aktif Periode 1",
        "Aktif Periode 2",
        "PLT / Harap Definitif",
        "Harus Diberhentikan"
    ], fill_value=0)
)

st.bar_chart(grafik_data)

# ---------------------------------------------------------
# ⚖️ DASAR HUKUM (PERMENDIKDASMEN)
# ---------------------------------------------------------
st.divider()
st.markdown("## ⚖️ Dasar Hukum Penugasan Kepala Sekolah")

st.info("""
**Permendikdasmen Nomor 7 Tahun 2025**

**Pokok Ketentuan:**
1. Kepala Sekolah diberikan tugas maksimal **2 (dua) periode**
2. Satu periode = **4 (empat) tahun**
3. Kepala Sekolah yang telah menjabat **2 periode wajib diberhentikan sesuai pada pasal 31**
4. Kepala Sekolah yang telah menajabat **1 Periode bisa di perpanjang apabila memiliki Sertifikat BCKS sesuai pada Pasal 32**
5. Sekolah tanpa Kepala Sekolah definitif **wajib segera diisi (PLT/Definitif)**
6. Penugasan Kepala Sekolah merupakan **tugas tambahan ASN**
""")

st.success("📌 Seluruh status dan rekomendasi pada dashboard ini telah diselaraskan dengan Permendikdasmen No. 7 Tahun 2025")

# =========================================================
# FOOTER
# =========================================================
st.divider()
st.caption("Dashboard Kepala Sekolah • MHD. ARIPIN RITONGA, S.Kom")




























































