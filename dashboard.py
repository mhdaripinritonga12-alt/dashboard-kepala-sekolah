import streamlit as st
import pandas as pd
import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

# =========================================================
# 🔒 PAKSA LOGIN SETIAP APLIKASI DIBUKA ULANG
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
    st.session_state.login = False

if "page" not in st.session_state:
    st.session_state.page = "cabdin"

if "selected_cabdin" not in st.session_state:
    st.session_state.selected_cabdin = None

if "selected_sekolah" not in st.session_state:
    st.session_state.selected_sekolah = None

# =========================================================
# 🔐 SISTEM LOGIN & ROLE USER
# =========================================================
USERS = {
    "operator": {"password": "operator123", "role": "Operator"},
    "kabidptk": {"password": "kabid123", "role": "Kabid"},
    "kadis": {"password": "kadis123", "role": "Kadis"},
    "viewer": {"password": "viewer123", "role": "View"},
}

if "role" not in st.session_state:
    st.session_state.role = None

# =========================================================
# LOGIN WAJIB SEBELUM AKSES DASHBOARD
# =========================================================
if not st.session_state.login:
    st.markdown("## 🔐 Login Dashboard Kepala Sekolah")

    col1, col2, col3 = st.columns([2, 3, 2])
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
boleh_edit_role = st.session_state.role in ["Operator", "Kabid"]

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
# 🔢 FUNGSI URUT CABDIN CABANG_DINAS_PENDIDIKAN_WIL 1 - 14
# =========================================================
def urutkan_cabdin(cabdin_list):
    def ambil_angka(text):
        angka = "".join(filter(str.isdigit, str(text)))
        return int(angka) if angka else 999
    return sorted(cabdin_list, key=ambil_angka)

# =========================================================
# LOAD DATA UTAMA (CACHE)
# =========================================================
@st.cache_data(show_spinner="📂 Memuat data Kepala Sekolah & SIMPEG...")
def load_data():
    xls = pd.ExcelFile(DATA_FILE)

    cabdis_sheets = [s for s in xls.sheet_names if "CABANG_DINAS_PENDIDIKAN_WIL" in s.upper()]

    if len(cabdis_sheets) == 0:
        st.error("❌ Sheet CABANG_DINAS_PENDIDIKAN_WIL tidak ditemukan di Excel")
        st.stop()

    df_list = []
    for sh in cabdis_sheets:
        df_temp = pd.read_excel(DATA_FILE, sheet_name=sh)
        df_temp["Cabang Dinas"] = sh.replace("_", " ")
        df_list.append(df_temp)

    df_ks = pd.concat(df_list, ignore_index=True)

    if "GURU_SIMPEG" not in xls.sheet_names:
        st.error("❌ Sheet GURU_SIMPEG tidak ditemukan di Excel")
        st.stop()

    df_guru = pd.read_excel(DATA_FILE, sheet_name="GURU_SIMPEG")

    return df_ks, df_guru

df_ks, df_guru = load_data()

# =========================================================
# 🔧 NORMALISASI NAMA KOLOM
# =========================================================
df_ks.columns = df_ks.columns.astype(str).str.strip()
df_guru.columns = df_guru.columns.astype(str).str.strip()

# =========================================================
# 🔧 NORMALISASI NAMA KOLOM (FIX TOTAL + ANTI ERROR)
# =========================================================
df_ks.columns = df_ks.columns.astype(str).str.strip()
df_guru.columns = df_guru.columns.astype(str).str.strip()

rename_map_ks = {
    # ==========================
    # NAMA SEKOLAH
    # ==========================
    "NAMA SEKOLAH": "Nama Sekolah",
    "Nama Sekolah ": "Nama Sekolah",
    "Nama sekolah": "Nama Sekolah",

    # ==========================
    # NAMA KEPALA SEKOLAH
    # ==========================
    "NAMA KASEK": "Nama Kepala Sekolah",
    "Nama Kasek": "Nama Kepala Sekolah",
    "Nama Kepsek": "Nama Kepala Sekolah",
    "Nama Kepala Sekolah ": "Nama Kepala Sekolah",

    # ==========================
    # KETERANGAN AKHIR (TYPO EXCEL)
    # ==========================
    "Keterangan": "Keterangan Akhir",
    "KETERANGAN": "Keterangan Akhir",
    "KETERANGAN AKHIR": "Keterangan Akhir",
    "Keteranngan Akhir": "Keterangan Akhir",
    "Keteranngan akhir": "Keterangan Akhir",
    "Keterangan Akhir ": "Keterangan Akhir",

    # ==========================
    # CABANG DINAS
    # ==========================
    "Cabang Dinas ": "Cabang Dinas",
    "CABANG DINAS": "Cabang Dinas",

    # ==========================
    # SERTIFIKAT BCKS
    # ==========================
    "Ket. Sertifikat BCKS": "Ket Sertifikat BCKS",
    "Ket Sertifikat BCKS ": "Ket Sertifikat BCKS",
    "Ket. Sertifikat": "Ket Sertifikat BCKS",
    "Sertifikat BCKS": "Ket Sertifikat BCKS",

    # ==========================
    # MASA PERIODE KSPSTK (TYPO)
    # ==========================
    "Masa Periode Sesuai KSPSTK": "Masa Periode Sesuai KSPSTK",
    "Masa Periode Sesuai KSPSTK ": "Masa Periode Sesuai KSPSTK",
    "Masa Periode Sesuai KSPSTK ": "Masa Periode Sesuai KSPSTK",
}

rename_map_guru = {
    "NAMA GURU ": "NAMA GURU",
    "Nama Guru": "NAMA GURU",
    "Nama guru": "NAMA GURU",
    "NAMA": "NAMA GURU",
    "NAMA ": "NAMA GURU",

    "NIP ": "NIP",
    "NIP.": "NIP",
    "NIP GURU": "NIP",
    "NIP Guru": "NIP",
}

# =========================================================
# ✅ RENAME KOLOM
# =========================================================
df_ks.rename(columns=rename_map_ks, inplace=True)
df_guru.rename(columns=rename_map_guru, inplace=True)

# =========================================================
# ✅ FIX GABUNG KOLOM MASA PERIODE (BIAR WIL 1-14 TERBACA)
# =========================================================
if "Masa Periode Sesuai KSPSTK" not in df_ks.columns:
    df_ks["Masa Periode Sesuai KSPSTK"] = ""

# kalau masih ada kolom typo, gabungkan isinya
if "Masa Periode Sisuai KSPSTK" in df_ks.columns:
    df_ks["Masa Periode Sesuai KSPSTK"] = df_ks["Masa Periode Sesuai KSPSTK"].fillna("")
    df_ks["Masa Periode Sisuai KSPSTK"] = df_ks["Masa Periode Sisuai KSPSTK"].fillna("")

    df_ks["Masa Periode Sesuai KSPSTK"] = df_ks["Masa Periode Sesuai KSPSTK"].astype(str).str.strip()
    df_ks["Masa Periode Sisuai KSPSTK"] = df_ks["Masa Periode Sisuai KSPSTK"].astype(str).str.strip()

    df_ks.loc[
        (df_ks["Masa Periode Sesuai KSPSTK"] == "") | (df_ks["Masa Periode Sesuai KSPSTK"].str.lower() == "nan"),
        "Masa Periode Sesuai KSPSTK"
    ] = df_ks["Masa Periode Sisuai KSPSTK"]

    # hapus kolom typo supaya tidak bikin bingung
    df_ks.drop(columns=["Masa Periode Sisuai KSPSTK"], inplace=True, errors="ignore")

# rapikan nilai akhir
df_ks["Masa Periode Sesuai KSPSTK"] = (
    df_ks["Masa Periode Sesuai KSPSTK"]
    .astype(str)
    .str.replace("\xa0", " ", regex=False)
    .str.strip()
)
# =========================================================
# ✅ STRIP LAGI SETELAH RENAME
# =========================================================
df_ks.columns = df_ks.columns.astype(str).str.strip()
df_guru.columns = df_guru.columns.astype(str).str.strip()

# =========================================================
# ✅ FIX KOLOM DUPLIKAT (INI WAJIB!)
# supaya df_ks["Keterangan Akhir"] tidak jadi DataFrame
# =========================================================
df_ks = df_ks.loc[:, ~df_ks.columns.duplicated()]
df_guru = df_guru.loc[:, ~df_guru.columns.duplicated()]

# =========================================================
# ✅ PAKSA KOLOM WAJIB ADA (BIAR TIDAK ERROR)
# =========================================================
if "Keterangan Akhir" not in df_ks.columns:
    df_ks["Keterangan Akhir"] = ""

if "Masa Periode Sesuai KSPSTK" not in df_ks.columns:
    df_ks["Masa Periode Sesuai KSPSTK"] = ""

if "Nama Kepala Sekolah" not in df_ks.columns:
    df_ks["Nama Kepala Sekolah"] = ""

# =========================================================
# 🔍 CEK KOLOM WAJIB
# =========================================================
kolom_wajib = ["Jenjang", "Cabang Dinas", "Keterangan Akhir", "Nama Sekolah"]

for k in kolom_wajib:
    if k not in df_ks.columns:
        st.error(f"❌ Kolom wajib '{k}' tidak ditemukan di Excel. Kolom tersedia: {list(df_ks.columns)}")
        st.stop()

if "Nama Kepala Sekolah" not in df_ks.columns:
    df_ks["Nama Kepala Sekolah"] = "-"

# WAJIB ADA UNTUK REKAP (KOLOM MERAH DI EXCEL)
if "Masa Periode Sesuai KSPSTK" not in df_ks.columns:
    df_ks["Masa Periode Sesuai KSPSTK"] = ""

# =========================================================
# LIST GURU SIMPEG
# =========================================================
if "NAMA GURU" not in df_guru.columns:
    st.error("❌ Kolom 'NAMA GURU' tidak ditemukan di sheet GURU_SIMPEG")
    st.stop()

guru_list = sorted(df_guru["NAMA GURU"].astype(str).dropna().unique())

# =========================================================
# ✅ MAP STATUS (PAKAI KOLOM MASA PERIODE SESUAI KSPSTK)
# =========================================================
def map_status(row):
    masa = str(row.get("Masa Periode Sesuai KSPSTK", "")).strip().lower()
    ket_akhir = str(row.get("Keterangan Akhir", "")).strip().lower()

    if "periode 1" in masa:
        return "Aktif Periode 1"
    if "periode 2" in masa:
        return "Aktif Periode 2"
    if "lebih dari 2" in masa or ">2" in masa:
        return "Lebih dari 2 Periode"
    if "plt" in masa:
        return "Plt"

    # ✅ jika masa kosong, cek dari Keterangan Akhir
    if "Harus diberhentikan" in ket_akhir:
        return "Harus Diberhentikan"
    if "Diberhentikan" in ket_akhir:
        return "Harus Diberhentikan"

    if "periode 1" in ket_akhir:
        return "Aktif Periode 1"
    if "periode 2" in ket_akhir:
        return "Aktif Periode 2"
    if "lebih dari 2" in ket_akhir or ">2" in ket_akhir:
        return "Lebih dari 2 Periode"
    if "plt" in ket_akhir:
        return "Plt"

    return "Lainnya"

# =========================================================
# ✅ LOGIKA BOLEH DIGANTI (Sesuai Permintaan)
# =========================================================
def cek_boleh_diganti(row):
    masa = str(row.get("Masa Periode Sesuai KSPSTK", "")).lower()
    ket_akhir = str(row.get("Keterangan Akhir", "")).lower()
    sertifikat = str(row.get("Ket Sertifikat BCKS", row.get("Sertifikat BCKS", ""))).lower()

    # ❌ periode 1 tidak boleh
    if "periode 1" in masa:
        return False

    # ✅ periode 2 boleh
    if "periode 2" in masa:
        return True

    # ✅ lebih dari 2 periode boleh
    if "lebih dari 2" in masa or ">2" in masa:
        return True

    # ✅ Plt boleh diganti
    if "plt" in masa or "plt" in ket_akhir:
        return True

    # ✅ Harus Diberhentikan boleh diganti
    if "Harus Hiberhentikan" in ket_akhir or "Hiberhentikan" in ket_akhir:
        return True

    # ✅ Tidak memiliki sertifikat BCKS boleh diganti
    if "belum" in sertifikat or "tidak" in sertifikat:
        return True

    # default boleh
    return True

# =========================================================
# FUNGSI BUAT PDF SURAT KETERANGAN
# =========================================================
def buat_pdf_surat(row):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "SURAT KETERANGAN DATA KEPALA SEKOLAH")
    y -= 25

    c.setFont("Helvetica", 11)
    c.drawString(50, y, "DINAS PENDIDIKAN PROVINSI SUMATERA UTARA")
    y -= 35

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "DATA LENGKAP:")
    y -= 20

    c.setFont("Helvetica", 10)

    for col in row.index:
        nilai = str(row[col])
        teks = f"{col}: {nilai}"

        while len(teks) > 95:
            c.drawString(50, y, teks[:95])
            teks = teks[95:]
            y -= 15

        c.drawString(50, y, teks)
        y -= 15

        if y < 100:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)

    y -= 30
    c.setFont("Helvetica", 10)
    c.drawString(50, y, "Dokumen ini dibuat otomatis melalui Dashboard Kepala Sekolah.")
    y -= 40

    c.setFont("Helvetica", 10)
    c.drawString(50, y, "Medan, ____________________")
    y -= 50
    c.drawString(50, y, "Mengetahui,")
    y -= 60
    c.drawString(50, y, "(__________________________)")

    c.save()
    buffer.seek(0)
    return buffer

# =========================================================
# CSS (TAMPILAN DINAS)
# =========================================================
st.markdown("""
<style>
.school-card {
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 16px;
    height: 120px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    font-weight: 600;
    font-size: 14px;
    box-shadow: 0 3px 8px rgba(0,0,0,0.12);
}

.card-periode-1 {
    background: #e3f2fd !important;
    border-left: 6px solid #2196f3;
}

.card-periode-2 {
    background: #fff8e1 !important;
    border-left: 6px solid #fbc02d;
}

.card-berhenti {
    background: #fdecea !important;
    border-left: 6px solid #d32f2f;
}

.card-plt {
    background: #e8f5e9 !important;
    border-left: 6px solid #2e7d32;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER + REFRESH + LOGOUT
# =========================================================
col1, col2, col3, col4 = st.columns([5, 2, 2, 2])

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
        st.session_state.selected_sekolah = None
        st.session_state.role = None
        st.rerun()

st.divider()

# =========================================================
# 🔍 PENCARIAN GURU SIMPEG
# =========================================================
with st.expander("🔍 Pencarian Guru (SIMPEG)", expanded=False):
    keyword = st.text_input(
        "Ketik Nama Guru atau NIP",
        placeholder="contoh: Mhd Aripin Ritonga / 1994"
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

search_sekolah = st.sidebar.text_input("Cari Nama Sekolah")

def apply_filter(df):
    if jenjang_filter != "Semua":
        df = df[df["Jenjang"] == jenjang_filter]

    if ket_filter != "Semua":
        df = df[df["Keterangan Akhir"] == ket_filter]

    if search_nama:
        df = df[df["Nama Kepala Sekolah"].astype(str).str.contains(search_nama, case=False, na=False)]

    if search_sekolah:
        df = df[df["Nama Sekolah"].astype(str).str.contains(search_sekolah, case=False, na=False)]

    return df

# =========================================================
# HALAMAN CABANG DINAS
# =========================================================
if st.session_state.page == "cabdin":

    st.subheader("🏢 Cabang Dinas Wilayah")

    df_view = apply_filter(df_ks)

    cabdin_list = urutkan_cabdin(df_view["Cabang Dinas"].dropna().unique())
    cols = st.columns(4)

    for i, cabdin in enumerate(cabdin_list):
        with cols[i % 4]:
            if st.button(f"📍 {cabdin}", key=f"cabdin_{i}", use_container_width=True):
                st.session_state.selected_cabdin = cabdin
                st.session_state.page = "sekolah"
                st.rerun()

# =========================================================
# HALAMAN SEKOLAH (LIST)
# =========================================================
elif st.session_state.page == "sekolah":

    col_a, col_b = st.columns([1, 5])

    with col_a:
        if st.button("⬅️ Kembali", use_container_width=True):
            st.session_state.page = "cabdin"
            st.session_state.selected_cabdin = None
            st.session_state.selected_sekolah = None
            st.rerun()

    with col_b:
        st.subheader(f"🏫 Sekolah — {st.session_state.selected_cabdin}")

    df_cab = df_ks[df_ks["Cabang Dinas"] == st.session_state.selected_cabdin].copy()
    df_cab = apply_filter(df_cab)

    if df_cab.empty:
        st.warning("⚠️ Tidak ada data sekolah pada Cabang Dinas ini.")
        st.stop()

    # =========================================================
    # 📌 REKAP STATUS CABANG DINAS INI (TERKONEKSI MASA PERIODE)
    # =========================================================
    st.markdown("### 📌 Rekap Status Kepala Sekolah Cabang Dinas Ini")

    df_cab_rekap = df_cab.copy()
    df_cab_rekap["Status Regulatif"] = df_cab_rekap.apply(map_status, axis=1)

    rekap_status_cab = (
        df_cab_rekap["Status Regulatif"]
        .value_counts()
        .reindex([
            "Aktif Periode 1",
            "Aktif Periode 2",
            "Lebih dari 2 Periode",
            "Plt",
            "Harus Diberhentikan",
            "Lainnya"
        ], fill_value=0)
    )

    colx1, colx2, colx3, colx4, colx5, colx6 = st.columns(6)
    colx1.metric("dalam Periode 1", int(rekap_status_cab["Aktif Periode 1"]))
    colx2.metric("dalam Periode 2", int(rekap_status_cab["Aktif Periode 2"]))
    colx3.metric("Lebih 2 Periode", int(rekap_status_cab["Lebih dari 2 Periode"]))
    colx4.metric("Kasek Plt", int(rekap_status_cab["Plt"]))
    total_bisa_diberhentikan = int(rekap_status_cab["Aktif Periode 2"]) + int(rekap_status_cab["Lebih dari 2 Periode"])
if colx5.button("📌 Lihat Detail Bisa Diberhentikan", use_container_width=True):
    st.session_state.page = "bisa_diberhentikan"
    st.rerun()
    colx6.metric("Lainnya", int(rekap_status_cab["Lainnya"]))

    st.divider()

    # =========================================================
    # GRID SEKOLAH (KLIK SEKOLAH -> HALAMAN DETAIL)
    # =========================================================
    cols = st.columns(5)
    idx = 0

    for _, row in df_cab.iterrows():

        nama_sekolah = row.get("Nama Sekolah", "-")

        masa = str(row.get("Masa Periode Sesuai KSPSTK", "")).lower()
        ket_akhir = str(row.get("Keterangan Akhir", "")).lower()

        if "periode 1" in masa:
            card_class = "card-periode-1"
        elif "periode 2" in masa:
            card_class = "card-periode-2"
        elif "lebih dari 2" in masa or ">2" in masa:
            card_class = "card-berhenti"
        elif "plt" in masa:
            card_class = "card-plt"
        elif "Diberhentikan" in ket_akhir:
            card_class = "card-berhenti"
        else:
            card_class = "card-plt"

        with cols[idx % 5]:

            st.markdown(
                f"""
                <div class="school-card {card_class}">
                    🏫 {nama_sekolah}
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button("📄 Buka Detail", key=f"detail_{idx}", use_container_width=True):
                st.session_state.selected_sekolah = nama_sekolah
                st.session_state.page = "detail"
                st.rerun()

        idx += 1

# =========================================================
# HALAMAN BISA DIBERHENTIKAN (GLOBAL SEMUA CABDIN)
# =========================================================
if st.session_state.page == "bisa_diberhentikan":

    col_a, col_b = st.columns([1, 6])

    with col_a:
        if st.button("⬅️ Kembali", use_container_width=True):
            st.session_state.page = "cabdin"
            st.rerun()

    with col_b:
        st.subheader("📌 Daftar Sekolah Bisa Diberhentikan (Periode 2 + Lebih dari 2 Periode)")

    df_bisa = df_ks.copy()
    df_bisa["Status Regulatif"] = df_bisa.apply(map_status, axis=1)

    df_bisa = df_bisa[df_bisa["Status Regulatif"].isin(["Aktif Periode 2", "Lebih dari 2 Periode"])]

    df_bisa = apply_filter(df_bisa)

    if df_bisa.empty:
        st.warning("⚠️ Tidak ada sekolah yang termasuk kategori Bisa Diberhentikan.")
        st.stop()

    st.success(f"✅ Total Sekolah Bisa Diberhentikan: {len(df_bisa)}")

    is_view_only = st.session_state.role in ["Kadis", "View"]

    for idx, row in df_bisa.iterrows():
        nama_sekolah = row.get("Nama Sekolah", "-")
        cabdin = row.get("Cabang Dinas", "-")
        status_reg = row.get("Status Regulatif", "-")
        kepsek_lama = row.get("Nama Kepala Sekolah", "-")

        st.markdown(f"### 🏫 {nama_sekolah}")
        st.write(f"📍 **Cabang Dinas:** {cabdin}")
        st.write(f"📌 **Status:** {status_reg}")
        st.write(f"👤 **Kepala Sekolah Lama:** {kepsek_lama}")

        calon_tersimpan = perubahan_kepsek.get(nama_sekolah)

        if calon_tersimpan:
            st.info(f"👤 Pengganti Saat Ini: **{calon_tersimpan}**")

        if is_view_only:
            st.warning("🔒 View Only — Tidak bisa mengganti pengganti.")
        else:
            calon = st.selectbox(
                f"👤 Pilih Calon Pengganti SIMPEG ({nama_sekolah})",
                guru_list,
                key=f"calon_global_{nama_sekolah}"
            )

            col1, col2 = st.columns([2, 2])

            with col1:
                if st.button("💾 Simpan Pengganti", key=f"simpan_{nama_sekolah}", use_container_width=True):
                    perubahan_kepsek[nama_sekolah] = calon
                    save_perubahan(perubahan_kepsek)
                    st.success(f"✅ {nama_sekolah} diganti dengan: {calon}")
                    st.rerun()

            with col2:
                if calon_tersimpan:
                    if st.button("✏️ Kembalikan Kepsek Lama", key=f"reset_{nama_sekolah}", use_container_width=True):
                        perubahan_kepsek.pop(nama_sekolah, None)
                        save_perubahan(perubahan_kepsek)
                        st.success(f"🔄 {nama_sekolah} dikembalikan ke Kepsek Lama")
                        st.rerun()

        st.divider()

    if st.session_state.selected_sekolah is None:
        st.warning("⚠️ Sekolah belum dipilih.")
        st.session_state.page = "sekolah"
        st.rerun()

    col_a, col_b = st.columns([1, 6])
    with col_a:
        if st.button("⬅️ Kembali", use_container_width=True):
            st.session_state.page = "sekolah"
            st.session_state.selected_sekolah = None
            st.rerun()

    with col_b:
        st.subheader(f"📄 Detail Sekolah: {st.session_state.selected_sekolah}")

    row_detail = df_ks[df_ks["Nama Sekolah"] == st.session_state.selected_sekolah]

    if row_detail.empty:
        st.error("❌ Data sekolah tidak ditemukan.")
        st.stop()

    row = row_detail.iloc[0]

    # =========================================================
    # TAMPILKAN DETAIL (1 SEKOLAH 1 LEMBAR)
    # =========================================================
    st.markdown("### 📝 Data Lengkap (Sesuai Excel)")
    for col in row.index:
        st.write(f"**{col}:** {row[col]}")

    st.divider()

    # =========================================================
    # DOWNLOAD PDF
    # =========================================================
    pdf_buffer = buat_pdf_surat(row)
    st.download_button(
        label="📄 Download Surat Keterangan (PDF)",
        data=pdf_buffer,
        file_name=f"Surat_Keterangan_{st.session_state.selected_sekolah}.pdf",
        mime="application/pdf"
    )

    st.divider()

    # =========================================================
    # LOGIKA EDIT (PERIODE 1 TIDAK BOLEH)
    # =========================================================
    status_boleh = cek_boleh_diganti(row)
    is_view_only = st.session_state.role in ["Kadis", "View"]

    calon_tersimpan = perubahan_kepsek.get(st.session_state.selected_sekolah)

    if is_view_only:
        st.info("ℹ️ Anda login sebagai **View Only**. Tidak dapat mengubah data.")
    else:
        if not status_boleh:
            st.warning("⛔ Tidak dapat diganti karena status **Periode 1**.")
        else:
            calon = st.selectbox(
                "👤 Pilih Calon Pengganti (SIMPEG)",
                guru_list,
                key=f"calon_{st.session_state.selected_sekolah}"
            )

            if st.button("💾 Simpan Pengganti", use_container_width=True):
                perubahan_kepsek[st.session_state.selected_sekolah] = calon
                save_perubahan(perubahan_kepsek)
                st.success(f"✅ Diganti dengan: {calon}")
                st.rerun()

    if calon_tersimpan:
        st.info(f"👤 Pengganti Saat Ini: **{calon_tersimpan}**")

        if not is_view_only:
            if st.button("✏️ Kembalikan ke Kepala Sekolah Lama", use_container_width=True):
                perubahan_kepsek.pop(st.session_state.selected_sekolah, None)
                save_perubahan(perubahan_kepsek)
                st.success("🔄 Berhasil dikembalikan")
                st.rerun()

# =========================================================
# 📊 REKAP & ANALISIS PIMPINAN (HANYA DI HALAMAN DEPAN)
# =========================================================
if st.session_state.page == "cabdin":

    st.divider()
    st.markdown("## 📑 Rekap & Analisis Kepala Sekolah (Pimpinan)")

    df_rekap = df_ks.copy()
    df_rekap["Status Regulatif"] = df_rekap.apply(map_status, axis=1)

    rekap_cabdin = (
        df_rekap
        .groupby(["Cabang Dinas", "Status Regulatif"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    rekap_cabdin["__urut__"] = rekap_cabdin["Cabang Dinas"].apply(
        lambda x: int("".join(filter(str.isdigit, str(x))))
        if "".join(filter(str.isdigit, str(x))) else 999
    )

    rekap_cabdin = rekap_cabdin.sort_values("__urut__").drop(columns="__urut__")

    st.dataframe(rekap_cabdin, use_container_width=True)

    # =========================================================
    # DOWNLOAD EXCEL REKAP
    # =========================================================
    excel_file = "rekap_kepala_sekolah_per_cabdin.xlsx"
    rekap_cabdin.to_excel(excel_file, index=False)

    with open(excel_file, "rb") as f:
        st.download_button(
            label="📥 Download Rekap Kepala Sekolah (Excel)",
            data=f,
            file_name=excel_file,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # =========================================================
    # GRAFIK STATUS
    # =========================================================
    st.subheader("📊 Grafik Status Kepala Sekolah")

    grafik_data = (
        df_rekap["Status Regulatif"]
        .value_counts()
        .reindex([
            "Aktif Periode 1",
            "Aktif Periode 2",
            "Lebih dari 2 Periode",
            "Plt",
            "Harus Diberhentikan",
            "Lainnya"
        ], fill_value=0)
    )

    st.bar_chart(grafik_data)

    # =========================================================
    # DASAR HUKUM
    # =========================================================
    st.divider()
    st.markdown("## ⚖️ Dasar Hukum Penugasan Kepala Sekolah")

    st.info("""
    **Permendikdasmen Nomor 7 Tahun 2025**

    **Pokok Ketentuan:**
    1. Kepala Sekolah diberikan tugas maksimal **2 (dua) periode**
    2. Satu periode = **4 (empat) tahun**
    3. Kepala Sekolah yang telah menjabat **Lebih 2 periode wajib diberhentikan sesuai pasal 31**
    4. Kepala Sekolah yang telah menjabat **1 periode bisa diperpanjang jika memiliki Sertifikat BCKS (Pasal 32)**
    5. Sekolah tanpa Kepala Sekolah definitif **wajib segera diisi (Plt/Definitif)**
    6. Penugasan Kepala Sekolah merupakan **tugas tambahan ASN**
    """)

    st.success("📌 Status dan rekomendasi dashboard telah diselaraskan dengan Permendikdasmen No. 7 Tahun 2025")
# =========================================================
# FOOTER
# =========================================================
st.divider()
st.caption("Dashboard Kepala Sekolah • MHD. ARIPIN RITONGA, S.Kom")




























