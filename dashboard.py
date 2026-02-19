import streamlit as st
import pandas as pd
import os
import re   # ✅ TAMBAHAN (UNTUK HAPUS HTML TAG)
import streamlit.components.v1 as components
import base64

import gspread
from google.oauth2.service_account import Credentials

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO


# =========================================================
# FUNGSI BACKGROUND (TARUH DI SINI)
# =========================================================
def set_bg(image_name):
    path = os.path.join(os.path.dirname(__file__), image_name)

    if not os.path.exists(path):
        st.warning(f"⚠️ Background tidak ditemukan: {image_name}")
        return

    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()

    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{data}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    """, unsafe_allow_html=True)


# =========================================================
# KONFIGURASI APP
# =========================================================
st.set_page_config(page_title="Dashboard Kepala Sekolah", layout="wide")

DATA_SAVE = "perubahan_kepsek.xlsx"
DATA_FILE = "data_kepala_sekolah.xlsx"

# =========================================================
# SESSION STATE DEFAULT
# =========================================================
if "login" not in st.session_state:
    st.session_state.login = False

if "role" not in st.session_state:
    st.session_state.role = None

if "page" not in st.session_state:
    st.session_state.page = "cabdin"

if "selected_cabdin" not in st.session_state:
    st.session_state.selected_cabdin = None

if "selected_sekolah" not in st.session_state:
    st.session_state.selected_sekolah = None

if "filter_status" not in st.session_state:
    st.session_state.filter_status = None
    
if "username" not in st.session_state:
    st.session_state.username = None

if "sekolah_user" not in st.session_state:
    st.session_state.sekolah_user = None

# =========================================================
# USER LOGIN
# =========================================================
USERS = {
    "operator": {"password": "operator123", "role": "Operator"},
    "kabidptk": {"password": "kabid111", "role": "Kabid"},
    "kadis": {"password": "kadis123", "role": "Kadis"},
    "viewer": {"password": "viewer123", "role": "View"},
}

# =========================================================
# GOOGLE SHEET CONFIG (SIMPAN PERMANEN)
# =========================================================
SHEET_ID = "1LfdTvQAMxc1r97HOmL6zylzn_d_CWrmvC8V5etaMSIA"
SHEET_NAME = "perubahan_kepsek"

# =========================================================
# FUNGSI SIMPAN & LOAD PENGGANTI (PERMANEN GOOGLE SHEET)
# =========================================================

def konek_gsheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)

    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

    return sheet


def load_perubahan():
    try:
        sheet = konek_gsheet()
        data = sheet.get_all_records()

        if not data:
            return {}

        df = pd.DataFrame(data)

        if "Sekolah Tujuan" not in df.columns or "Calon Pengganti" not in df.columns:
            return {}

        df["Sekolah Tujuan"] = df["Sekolah Tujuan"].astype(str).str.strip()
        df["Calon Pengganti"] = df["Calon Pengganti"].astype(str).str.strip()

        return dict(zip(df["Sekolah Tujuan"], df["Calon Pengganti"]))

    except Exception as e:
        st.error("❌ ERROR GOOGLE SHEET (LOAD):")
        st.exception(e)
        return {}

def save_perubahan(data_dict, df_ks, df_guru):
    try:
        sheet = konek_gsheet()

        sheet.clear()
        sheet.append_row(["Sekolah Tujuan", "Kepsek Lama", "Calon Pengganti", "Sekolah Asal"])

        rows = []
        for sekolah_tujuan, calon_pengganti in data_dict.items():

            # Kepsek lama dari df_ks
            data_row = df_ks[df_ks["Nama Sekolah"].astype(str).str.strip() == str(sekolah_tujuan).strip()]
            kepsek_lama = "-"
            if not data_row.empty:
                kepsek_lama = str(data_row.iloc[0].get("Nama Kepala Sekolah", "-"))

            # Sekolah asal calon pengganti dari df_guru (SIMPEG)
            asal = "-"
            data_calon = df_guru[df_guru["NAMA GURU"].astype(str).str.strip() == str(calon_pengganti).strip()]

            if not data_calon.empty:
                calon_row = data_calon.iloc[0]

                # ambil kolom UNOR / UNIT KERJA
                kol_unor = cari_kolom(data_calon, ["UNOR", "UNIT ORGANISASI", "UNIT KERJA", "SATKER", "INSTANSI"])
                if kol_unor:
                    asal = str(calon_row.get(kol_unor, "-")).strip()

            rows.append([sekolah_tujuan, kepsek_lama, calon_pengganti, asal])

        if rows:
            sheet.append_rows(rows)

    except Exception as e:
        st.error(f"❌ Gagal simpan ke Google Sheet: {e}")

# LOAD DATA PERUBAHAN SAAT APLIKASI START
perubahan_kepsek = load_perubahan()

# =========================================================
# DATA RIWAYAT KEPALA SEKOLAH (GOOGLE SHEET PERMANEN)
# =========================================================
SHEET_RIWAYAT = "RIWAYAT_KASEK"

def konek_gsheet_riwayat():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)

    client = gspread.authorize(creds)
    sh = client.open_by_key(SHEET_ID)

    try:
        ws = sh.worksheet(SHEET_RIWAYAT)
    except:
        ws = sh.add_worksheet(title=SHEET_RIWAYAT, rows=2000, cols=20)
        ws.append_row(["Nama Sekolah", "Nama Kepsek", "NIP", "Mulai", "Selesai", "Keterangan", "Input Oleh", "Timestamp"])

    return ws


def load_riwayat():
    try:
        ws = konek_gsheet_riwayat()
        data = ws.get_all_records()

        if not data:
            return pd.DataFrame(columns=["Nama Sekolah", "Nama Kepsek", "NIP", "Mulai", "Selesai", "Keterangan", "Input Oleh", "Timestamp"])

        df = pd.DataFrame(data).fillna("")
        return df

    except Exception as e:
        st.error(f"❌ Gagal load riwayat Google Sheet: {e}")
        return pd.DataFrame()


def simpan_riwayat_baru(nama_sekolah, nama_kepsek, nip, mulai, selesai, ket=""):
    try:
        ws = konek_gsheet_riwayat()

        timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        input_oleh = st.session_state.username if st.session_state.username else "-"

        ws.append_row([nama_sekolah, nama_kepsek, nip, mulai, selesai, ket, input_oleh, timestamp])

    except Exception as e:
        st.error(f"❌ Gagal simpan riwayat ke Google Sheet: {e}")
        return pd.DataFrame()

def simpan_riwayat_baru(nama_sekolah, nama_kepsek, nip, mulai, selesai, ket=""):
    df_riwayat = load_riwayat()

    data_baru = {
        "Nama Sekolah": nama_sekolah,
        "Nama Kepsek": nama_kepsek,
        "NIP": nip,
        "Mulai": mulai,
        "Selesai": selesai,
        "Keterangan": ket
    }

    df_riwayat = pd.concat([df_riwayat, pd.DataFrame([data_baru])], ignore_index=True)

    # simpan kembali ke excel (rewrite file)
    with pd.ExcelWriter(DATA_FILE, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        df_riwayat.to_excel(writer, sheet_name=SHEET_RIWAYAT, index=False)
    from datetime import datetime

def ambil_tahun(text):
    if text is None:
        return None

    text = str(text).strip()
    if text == "" or text.lower() == "nan":
        return None

    try:
        return int(text[-4:])
    except:
        return None


def hitung_masa_jabatan(df_riwayat, nama_kepsek):
    df = df_riwayat[df_riwayat["Nama Kepsek"].astype(str).str.strip().str.lower() == str(nama_kepsek).strip().lower()].copy()

    if df.empty:
        return 0, 0

    tahun_sekarang = datetime.now().year
    total_tahun = 0
    jumlah_periode = 0

    for _, r in df.iterrows():
        mulai = ambil_tahun(r.get("Mulai", ""))
        selesai = ambil_tahun(r.get("Selesai", ""))

        if mulai is None:
            continue

        if selesai is None:
            selesai = tahun_sekarang

        if selesai < mulai:
            continue

        total_tahun += (selesai - mulai) + 1
        jumlah_periode += 1

    return total_tahun, jumlah_periode

# =========================================================
# LOAD DATA UTAMA
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
        df_temp = pd.read_excel(DATA_FILE, sheet_name=sh, header=0, dtype=str)
        df_temp["Cabang Dinas"] = sh.replace("_", " ")
        df_list.append(df_temp)

    df_ks = pd.concat(df_list, ignore_index=True)
    # =========================================================
    # ✅ FIX: HAPUS KOLOM UNNAMED (BIASANYA AKIBAT FORMAT EXCEL)
    # =========================================================
    df_ks = df_ks.loc[:, ~df_ks.columns.astype(str).str.contains("^Unnamed", case=False)]

    if "GURU_SIMPEG" not in xls.sheet_names:
        st.error("❌ Sheet GURU_SIMPEG tidak ditemukan di Excel")
        st.stop()

    df_guru = pd.read_excel(DATA_FILE, sheet_name="GURU_SIMPEG", header=0, dtype=str)
    return df_ks, df_guru

df_ks, df_guru = load_data()

def buat_username_sekolah(nama):
    return str(nama).lower().strip().replace(" ", "")

# =========================================================
# TAMBAH USER SEKOLAH OTOMATIS
# =========================================================
daftar_sekolah = df_ks["Nama Sekolah"].astype(str).str.strip().unique()

for sekolah in daftar_sekolah:
    if sekolah and sekolah != "-" and sekolah.lower() != "nan":
        username = buat_username_sekolah(sekolah)
        USERS[username] = {
            "password": "sekolah123",
            "role": "Sekolah",
            "sekolah": sekolah
        }

# =========================================================
# ✅ DEBUG PLT: CEK APAKAH DATA PLT MASUK KE DF_KS
# =========================================================
cek_plt = df_ks[
    df_ks.astype(str)
    .apply(lambda col: col.str.contains("plt|pelaksana tugas", case=False, na=False))
    .any(axis=1)
]

# =========================================================
# NORMALISASI KOLOM
# =========================================================
df_ks.columns = df_ks.columns.astype(str).str.strip()
df_guru.columns = df_guru.columns.astype(str).str.strip()

# =========================================================
# ✅ TAMBAHAN FIX BARU (BERSIHKAN KOLOM DARI ENTER/TAB)
# =========================================================
df_ks.columns = (
    df_ks.columns.astype(str)
    .str.replace("\n", " ", regex=False)
    .str.replace("\r", " ", regex=False)
    .str.replace("\t", " ", regex=False)
    .str.strip()
)

df_guru.columns = (
    df_guru.columns.astype(str)
    .str.replace("\n", " ", regex=False)
    .str.replace("\r", " ", regex=False)
    .str.replace("\t", " ", regex=False)
    .str.strip()
)

rename_map_ks = {
    "NAMA SEKOLAH": "Nama Sekolah",
    "Nama Sekolah ": "Nama Sekolah",
    "Nama sekolah": "Nama Sekolah",

    "NAMA KASEK": "Nama Kepala Sekolah",
    "Nama Kasek": "Nama Kepala Sekolah",
    "Nama Kepsek": "Nama Kepala Sekolah",

    "Keterangan": "Keterangan Akhir",
    "KETERANGAN": "Keterangan Akhir",
    "KETERANGAN AKHIR": "Keterangan Akhir",

    "Ket. Sertifikat BCKS": "Ket Sertifikat BCKS",
    "Ket Sertifikat BCKS ": "Ket Sertifikat BCKS",
    "Sertifikat BCKS": "Ket Sertifikat BCKS",

    "CABANG DINAS": "Cabang Dinas",

    "Masa Periode Sesuai KSPSTK ": "Masa Periode Sesuai KSPSTK",
    "Masa Periode Sisuai KSPSTK": "Masa Periode Sesuai KSPSTK",

    # =========================================================
    # ✅ TAMBAHAN FIX BARU (RIWAYAT DAPODIK)
    # =========================================================
    "RIWAYAT DAPODIK": "Riwayat Dapodik",
    "Riwayat Dapodik ": "Riwayat Dapodik",
    "Riwayat dapodik": "Riwayat Dapodik",
    "Riwayat_Dapodik": "Riwayat Dapodik",
}

rename_map_guru = {
    "NAMA GURU ": "NAMA GURU",
    "Nama Guru": "NAMA GURU",
    "Nama guru": "NAMA GURU",
    "NAMA": "NAMA GURU",

    "NIP ": "NIP",
    "NIP.": "NIP",
    "NIP Guru": "NIP",
    "NIP GURU": "NIP",
}

df_ks.rename(columns=rename_map_ks, inplace=True)
df_ks.columns = df_ks.columns.astype(str).str.strip()
df_guru.rename(columns=rename_map_guru, inplace=True)

# =========================================================
# ✅ FIX: PAKSA RIWAYAT DAPODIK JADI STRING
# =========================================================
if "Riwayat Dapodik" in df_ks.columns:
    df_ks["Riwayat Dapodik"] = df_ks["Riwayat Dapodik"].astype(str).fillna("").str.strip()


# =========================================================
# ✅ TAMBAHAN FIX BARU (ISI NaN JADI STRING KOSONG)
# =========================================================
df_ks = df_ks.fillna("")
df_guru = df_guru.fillna("")
# =========================================================
# ✅ FIX SUPER FINAL: PAKSA AMBIL KOLOM RIWAYAT DAPODIK MESKI NAMA KOLOM BERBEDA
# =========================================================
kolom_riwayat_asli = None

for c in df_ks.columns:
    nama = str(c).upper().strip()
    if "RIWAYAT" in nama and "DAPODIK" in nama:
        kolom_riwayat_asli = c
        break

# jika ketemu kolom asli, pindahkan isinya ke kolom standar "Riwayat Dapodik"
if kolom_riwayat_asli:
    df_ks["Riwayat Dapodik"] = df_ks[kolom_riwayat_asli]



df_ks = df_ks.loc[:, ~df_ks.columns.duplicated()]
df_guru = df_guru.loc[:, ~df_guru.columns.duplicated()]

# =========================================================
# PAKSA KOLOM WAJIB ADA
# =========================================================
wajib = ["Jenjang", "Cabang Dinas", "Nama Sekolah", "Keterangan Akhir"]
for col in wajib:
    if col not in df_ks.columns:
        df_ks[col] = ""

if "Nama Kepala Sekolah" not in df_ks.columns:
    df_ks["Nama Kepala Sekolah"] = ""

if "Masa Periode Sesuai KSPSTK" not in df_ks.columns:
    df_ks["Masa Periode Sesuai KSPSTK"] = ""

if "Ket Sertifikat BCKS" not in df_ks.columns:
    df_ks["Ket Sertifikat BCKS"] = ""

if "Keterangan Jabatan" not in df_ks.columns:
    df_ks["Keterangan Jabatan"] = ""

# =========================================================
# ✅ TAMBAHAN BARU (PAKSA SEMUA KOLOM EXCEL AGAR SELALU ADA)
# =========================================================
kolom_excel_wajib = [
    "NO",
    "Status",
    "Kabupaten",
    "Tahun Pengangkatan",
    "Tahun Berjalan",
    "Permendikdasmen No 7 Tahun 2025 Maksimal 2 Periode ( 1 Periode 4 Tahun )",
    "Riwayat Dapodik",
    "Calon Pengganti jika Sudah Harus di Berhentikan"
]

for col in kolom_excel_wajib:
    if col not in df_ks.columns:
        df_ks[col] = ""

# =========================================================
# NORMALISASI NAMA SEKOLAH
# =========================================================
df_ks["Nama Sekolah"] = (
    df_ks["Nama Sekolah"]
    .astype(str)
    .str.replace("\xa0", " ", regex=False)
    .str.strip()
)

# =========================================================
# LIST GURU SIMPEG
# =========================================================
if "NAMA GURU" not in df_guru.columns:
    st.error("❌ Kolom 'NAMA GURU' tidak ditemukan di sheet GURU_SIMPEG")
    st.stop()

guru_list = sorted(df_guru["NAMA GURU"].astype(str).dropna().unique())

# =========================================================
# FUNGSI AMBIL DATA SIMPEG
# =========================================================
def ambil_data_simpeg(nama_guru):
    if nama_guru is None:
        return pd.DataFrame()

    nama_guru = str(nama_guru).strip()

    if "NAMA GURU" not in df_guru.columns:
        return pd.DataFrame()

    hasil = df_guru[df_guru["NAMA GURU"].astype(str).str.strip() == nama_guru].copy()
    return hasil

# =========================================================
# DETEKSI KOLOM SIMPEG (UNOR/CABDIS/ALAMAT)
# =========================================================
def cari_kolom(df, kandidat):
    for col in df.columns:
        nama_col = str(col).upper().strip()
        for k in kandidat:
            if k in nama_col:
                return col
    return None

# =========================================================
# ✅ TAMBAHAN FIX FINAL: DETEKSI KOLOM RIWAYAT DAPODIK OTOMATIS
# =========================================================
def cari_kolom_riwayat_dapodik(df):
    for col in df.columns:
        nama_col = str(col).upper().strip()
        if "RIWAYAT" in nama_col and "DAPODIK" in nama_col:
            return col
    return None

# =========================================================
# ✅ TAMBAHAN FIX FORMAT RIWAYAT DAPODIK AGAR RAPI
# =========================================================
def format_riwayat_dapodik(text):
    if text is None:
        return "-"

    text = str(text).strip()

    if text.lower() == "nan" or text == "":
        return "-"

    text = text.replace("---", "\n")
    return text.strip()

# =========================================================
# BERSIHKAN NILAI (FIX HTML TAG)
# =========================================================
import re

def bersihkan(teks):
    if teks is None:
        return "-"

    teks = str(teks)

    teks = re.sub(r"<[^>]*>", "", teks)
    teks = teks.replace("\xa0", " ").strip()

    if teks.strip().lower() == "nan" or teks.strip() == "":
        return "-"

    return teks.strip()

# =========================================================
# TAMBAHAN: DETEKSI CABDIS DARI UNOR (AUTO CABDIS)
# =========================================================
def deteksi_cabdis_dari_unor(unor_text):
    if unor_text is None:
        return "-"

    unor_text = str(unor_text).upper().strip()

    if unor_text == "" or unor_text == "-" or unor_text.lower() == "nan":
        return "-"

    df_tmp = df_ks.copy()
    df_tmp["Nama Sekolah"] = df_tmp["Nama Sekolah"].astype(str).str.upper().str.strip()

    cocok = df_tmp[df_tmp["Nama Sekolah"].apply(lambda x: x in unor_text or unor_text in x)]

    if cocok.empty:
        return "-"

    return str(cocok.iloc[0].get("Cabang Dinas", "-"))

# =========================================================
# URUT CABDIN
# =========================================================
def urutkan_cabdin(cabdin_list):
    def ambil_angka(text):
        angka = "".join(filter(str.isdigit, str(text)))
        return int(angka) if angka else 999
    return sorted(cabdin_list, key=ambil_angka)

# =========================================================
# LOGIKA STATUS UTAMA
# =========================================================
def map_status(row):
    masa = str(row.get("Masa Periode Sesuai KSPSTK", "")).strip().lower()
    ket_akhir = str(row.get("Keterangan Akhir", "")).strip().lower()
    jabatan = str(row.get("Keterangan Jabatan", "")).strip().lower()
    status_excel = str(row.get("Status", "")).strip().lower()

    # ambil juga kolom lain yang mungkin berisi PLT
    ket_bcks = str(row.get("Ket Sertifikat BCKS", "")).strip().lower()
    permendik = str(row.get("Permendikdasmen No 7 Tahun 2025 Maksimal 2 Periode ( 1 Periode 4 Tahun )", "")).strip().lower()

    gabung = f"{masa} {ket_akhir} {jabatan} {status_excel} {ket_bcks} {permendik}"

    # hapus simbol, titik, spasi (biar P.L.T jadi plt)
    cek = re.sub(r"[^a-z0-9]", "", gabung)

    # =========================================================
    # ✅ DETEKSI PLT SUPER FINAL
    # =========================================================
    if "plt" in cek or "pelaksanatugas" in cek or "masihplt" in cek:
        return "Plt"

    # =========================================================
    # DETEKSI PERIODE
    # =========================================================
    if "periode1" in cek:
        return "Aktif Periode Ke 1"

    if "periode2" in cek:
        return "Aktif Periode Ke 2"

    if "lebihdari2" in cek or "lebihdaridua" in cek or "lebih2" in cek:
        return "Lebih dari 2 Periode"

    return "Aktif Periode Ke 1"

# =========================================================
# CSS CARD SEKOLAH SERAGAM
# =========================================================
st.markdown("""
<style>
div[data-testid="stButton"] > button {
    border-radius: 14px !important;
    height: 95px !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    text-align: center !important;
    border: 1px solid #ddd !important;
    box-shadow: 0 3px 8px rgba(0,0,0,0.12) !important;
    width: 100% !important;
    white-space: normal !important;
    padding: 10px !important;
}
</style>
""", unsafe_allow_html=True)

import base64
import os
import streamlit as st
# =========================================================
# BACKGROUND LOGIN / DASHBOARD / CABDIS
# =========================================================
if not st.session_state.login:
    set_bg("login.jpg")
else:
    set_bg("dashboard.jpg")

# =========================================================
# LOGIN PAGE
# =========================================================
st.markdown("""
<style>
.stApp {
    background-color: #1034A6;
}

.block-container {
    padding-top: 30px !important;
}

/* wrapper logo + judul biar center sempurna */
.login-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    margin-top: 10px;
    margin-bottom: 15px;
}

.login-wrapper img {
    width: 200px;
    margin-bottom: -15px; /* jarak logo ke tulisan rapat */
}

.login-title {
    text-align: center;
    font-size: 42px;
    font-weight: 800;
    margin: 0px;
    padding: 0px;
    color: #E0FFFF;
}
</style>
""", unsafe_allow_html=True)

if not st.session_state.login:

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================
    # LOGO + JUDUL (RATA TENGAH FIX)
    # ==========================
    logo_path = os.path.join(os.path.dirname(__file__), "logo.png")

    if os.path.exists(logo_path):
        import base64
        with open(logo_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
    
    st.markdown(f"""
    <div class="login-wrapper">
        <img src="data:image/png;base64,{data}">
        <div class="login-title" style="margin-bottom:2px; font-size:28px;">
            Sistem Monitoring dan Analisis Riwayat Tugas
        </div>
        <div class="login-title" style="margin-top:0px; font-size:28px;">
            Kepala Sekolah
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================
# FORM LOGIN (WAJIB DIATUR BEGINI)
# ==========================
if not st.session_state.login:

    col1, col2, col3 = st.columns([2, 3, 2])

    with col2:
        st.markdown("""
        <style>
        /* Label Username & Password jadi putih */
        div[data-testid="stTextInput"] label {
            color: white !important;
            font-weight: 700 !important;
            font-size: 16px !important;
        }
        </style>
        """, unsafe_allow_html=True)

        username = st.text_input("👤 Username")
        password = st.text_input("🔑 Password", type="password")

        if st.button("🔓 Login", use_container_width=True):

            if username in USERS and USERS[username]["password"] == password:
                st.session_state.login = True
                st.session_state.role = USERS[username]["role"]
                st.session_state.username = username

                # jika login sekolah
                if USERS[username]["role"] == "Sekolah":
                    st.session_state.sekolah_user = USERS[username]["sekolah"]
                    st.session_state.selected_sekolah = USERS[username]["sekolah"]

                    # sekolah langsung ke update
                    st.session_state.page = "update"
                else:
                    st.session_state.sekolah_user = None
                    st.session_state.page = "cabdin"

                st.success(f"✅ Login berhasil sebagai **{st.session_state.role}**")
                st.rerun()

            else:
                st.error("❌ Username atau Password salah")

    st.stop()

# ==========================
# JIKA SUDAH LOGIN
# ==========================
st.caption(f"👤 Login sebagai: **{st.session_state.role}**")

# =========================================================
# SIDEBAR FILTER
# =========================================================
st.sidebar.header("🔍 Filter & Pencarian")

search_nama = st.sidebar.text_input("Cari Nama Kepala Sekolah")
search_sekolah = st.sidebar.text_input("Cari Nama Sekolah")

jenjang_filter = st.sidebar.selectbox("Jenjang", ["Semua"] + sorted(df_ks["Jenjang"].dropna().unique()))
ket_filter = st.sidebar.selectbox("Keterangan Akhir", ["Semua"] + sorted(df_ks["Keterangan Akhir"].dropna().unique()))


# =========================================================
# APPLY FILTER
# =========================================================
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
# FUNGSI WARNA OTOMATIS
# =========================================================
def get_warna_jabatan(value):
    v = str(value).lower()
    if "plt" in v:
        return "#d1e7dd"
    return "#dbeeff"

def get_warna_bcks(value):
    v = str(value).lower()
    if "belum" in v or v.strip() == "" or v.strip() == "nan":
        return "#f8d7da"
    if "sudah" in v or "ada" in v:
        return "#d1e7dd"
    return "#dbeeff"

# =========================================================
# FUNGSI PASAL PERMENDIKDASMEN OTOMATIS
# =========================================================
def tampil_pasal_permendikdasmen(status, ket_bcks):
    ket_bcks = str(ket_bcks).strip().lower()

    tampil31 = False
    tampil32 = False

    # ================================
    # PASAL 31: aturan periode jabatan
    # ================================
    if status in ["Aktif Periode Ke 2", "Lebih dari 2 Periode", "Plt"]:
        tampil31 = True

    # ================================
    # PASAL 32: aturan sertifikat BCKS
    # tampilkan jika BCKS belum ada
    # ================================
    if ("belum" in ket_bcks) or (ket_bcks == "") or (ket_bcks == "nan") or (ket_bcks == "-"):
        tampil32 = True

    st.markdown("## ⚖️ Permendikdasmen No 7 Tahun 2025")

    if tampil31:
        st.error("""
        **📌 PASAL 31 (Penugasan Kepala Sekolah)**
        - Kepala Sekolah dapat ditugaskan maksimal **2 periode**
        - 1 periode = **4 tahun**
        - Jika sudah menjabat **lebih dari 2 periode**, maka wajib dilakukan pergantian
        """)

    if tampil32:
        st.warning("""
        **📌 PASAL 32 (Sertifikat BCKS)**
        - Kepala Sekolah wajib memiliki Sertifikat BCKS
        - Jika belum memiliki BCKS maka menjadi catatan evaluasi dalam perpanjangan jabatan
        """)
# =========================================================
# HALAMAN CABDIN
# =========================================================
def page_cabdin():
    st.markdown("""
    <style>
    /* samakan posisi vertikal semua isi kolom */
    div[data-testid="column"] {
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])

    with col1:
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")

        if os.path.exists(logo_path):
            st.image(logo_path, width=120)
        else:
            st.markdown("## 📊 SMART.KS")

    with col2:
        if st.button("🔄 Refresh SIMPEG", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Data SIMPEG diperbarui")
            st.rerun()

    with col3:
        if st.button("🔄 Refresh Kepsek", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Data Kepala Sekolah diperbarui")
            st.rerun()

    with col4:
        if st.button("📌 Rekapitulasi", use_container_width=True):
            st.session_state.page = "rekap"
            st.rerun()

    with col5:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.login = False
            st.session_state.role = None
            st.session_state.page = "cabdin"
            st.session_state.selected_cabdin = None
            st.session_state.selected_sekolah = None
            st.session_state.filter_status = None
            st.rerun()

    st.divider()

    df_rekap = df_ks.copy()
    df_rekap["Status Regulatif"] = df_rekap.apply(map_status, axis=1)

    jumlah_p1 = int((df_rekap["Status Regulatif"] == "Aktif Periode Ke 1").sum())
    jumlah_p2 = int((df_rekap["Status Regulatif"] == "Aktif Periode Ke 2").sum())
    jumlah_lebih2 = int((df_rekap["Status Regulatif"] == "Lebih dari 2 Periode").sum())
    jumlah_plt = int((df_rekap["Status Regulatif"] == "Plt").sum())

    total_bisa_diberhentikan = jumlah_p2 + jumlah_lebih2 + jumlah_plt

    st.markdown("## 📌 REKAP DATA DINAS PENDIDIKAN")

    colx1, colx2, colx3, colx4, colx5 = st.columns(5)
    colx1.metric("Aktif Periode Ke 1", jumlah_p1)
    colx2.metric("Aktif Periode Ke 2", jumlah_p2)
    colx3.metric("Lebih 2 Periode", jumlah_lebih2)
    colx4.metric("Kasek Plt", jumlah_plt)
    colx5.metric("Bisa Diberhentikan", total_bisa_diberhentikan)

    st.divider()

    # =========================================================
    # 🔍 PENCARIAN GURU SIMPEG (HANYA DI DASHBOARD UTAMA)
    # =========================================================
    st.markdown("## 🔍 Pencarian Guru (SIMPEG)")

    keyword = st.text_input(
        "Ketik Nama Guru atau NIP",
        placeholder="contoh: Mhd Aripin Ritonga / 19940816082025041003",
        key="simpeg_search_dashboard"
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

    st.subheader("🏢 DAFTAR CABANG DINAS PENDIDIKAN")

    df_view = apply_filter(df_ks)
    cabdin_list = urutkan_cabdin(df_view["Cabang Dinas"].dropna().unique())

    cols = st.columns(4)
    for i, cabdin in enumerate(cabdin_list):
        with cols[i % 4]:
            if st.button(f"📍 {cabdin}", key=f"cabdin_{i}", use_container_width=True):
                st.session_state.selected_cabdin = cabdin
                st.session_state.page = "sekolah"
                st.rerun()

    st.divider()


# =========================================================
# HALAMAN SEKOLAH
# =========================================================
def page_sekolah():
    if st.session_state.selected_cabdin is None:
        st.session_state.page = "cabdin"
        st.rerun()

    col_a, col_b, col_c = st.columns([1, 6, 1])

    with col_a:
        if st.button("🏠", key="home_sekolah"):
            st.session_state.page = "cabdin"
            st.session_state.selected_cabdin = None
            st.session_state.selected_sekolah = None
            st.rerun()

    with col_b:
        st.subheader(f"🏫 {st.session_state.selected_cabdin}")

    with col_c:
        if st.button("⬅️", key="back_sekolah"):
            st.session_state.page = "cabdin"
            st.session_state.selected_cabdin = None
            st.session_state.selected_sekolah = None
            st.rerun()

    df_cab = df_ks[df_ks["Cabang Dinas"] == st.session_state.selected_cabdin].copy()
    df_cab = apply_filter(df_cab)

    if df_cab.empty:
        st.warning("⚠️ Tidak ada data sekolah pada Cabang Dinas ini.")
        st.stop()

    df_cab["Status Regulatif"] = df_cab.apply(map_status, axis=1)

    jumlah_p1 = int((df_cab["Status Regulatif"] == "Aktif Periode Ke 1").sum())
    jumlah_p2 = int((df_cab["Status Regulatif"] == "Aktif Periode Ke 2").sum())
    jumlah_lebih2 = int((df_cab["Status Regulatif"] == "Lebih dari 2 Periode").sum())
    jumlah_plt = int((df_cab["Status Regulatif"] == "Plt").sum())
    total_bisa = jumlah_p2 + jumlah_lebih2 + jumlah_plt

    st.markdown("### 📌 Rekap pada Cabang Dinas")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Aktif Periode Ke 1", jumlah_p1)
    col2.metric("Aktif Periode Ke 2", jumlah_p2)
    col3.metric("Lebih 2 Periode", jumlah_lebih2)
    col4.metric("Plt", jumlah_plt)
    col5.metric("Bisa Diberhentikan", total_bisa)

    st.divider()

   # =========================================================
# HALAMAN SEKOLAH
# =========================================================
def page_sekolah():
    if st.session_state.selected_cabdin is None:
        st.session_state.page = "cabdin"
        st.rerun()

    col_a, col_b, col_c = st.columns([1, 6, 1])

    with col_a:
        if st.button("🏠", key="home_sekolah"):
            st.session_state.page = "cabdin"
            st.session_state.selected_cabdin = None
            st.session_state.selected_sekolah = None
            st.rerun()

    with col_b:
        st.subheader(f"🏫 {st.session_state.selected_cabdin}")

    with col_c:
        if st.button("⬅️", key="back_sekolah"):
            st.session_state.page = "cabdin"
            st.session_state.selected_cabdin = None
            st.session_state.selected_sekolah = None
            st.rerun()

    df_cab = df_ks[df_ks["Cabang Dinas"] == st.session_state.selected_cabdin].copy()
    df_cab = apply_filter(df_cab)

    if df_cab.empty:
        st.warning("⚠️ Tidak ada data sekolah pada Cabang Dinas ini.")
        st.stop()

    df_cab["Status Regulatif"] = df_cab.apply(map_status, axis=1)

    jumlah_p1 = int((df_cab["Status Regulatif"] == "Aktif Periode Ke 1").sum())
    jumlah_p2 = int((df_cab["Status Regulatif"] == "Aktif Periode Ke 2").sum())
    jumlah_lebih2 = int((df_cab["Status Regulatif"] == "Lebih dari 2 Periode").sum())
    jumlah_plt = int((df_cab["Status Regulatif"] == "Plt").sum())
    total_bisa = jumlah_p2 + jumlah_lebih2 + jumlah_plt

    st.markdown("### 📌 Rekap Pada Cabang Dinas")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Aktif Periode Ke 1", jumlah_p1)
    col2.metric("Aktif Periode Ke 2", jumlah_p2)
    col3.metric("Lebih 2 Periode", jumlah_lebih2)
    col4.metric("Plt", jumlah_plt)
    col5.metric("Bisa Diberhentikan", total_bisa)

    st.divider()

    # =========================================================
    # LIST SEKOLAH (CARD BUTTON)
    # =========================================================
    cols = st.columns(4)
    idx = 0

    for _, row in df_cab.iterrows():
        nama_sekolah = str(row.get("Nama Sekolah", "-"))
        status = map_status(row)

        if status == "Aktif Periode Ke 1":
            warna = "🟦"
        elif status == "Aktif Periode Ke 2":
            warna = "🟨"
        elif status == "Lebih dari 2 Periode":
            warna = "🟥"
        elif status == "Plt":
            warna = "🟩"
        else:
            warna = "⬜"

        with cols[idx % 4]:
            if st.button(f"{warna} {nama_sekolah}", key=f"btn_sekolah_{idx}", use_container_width=True):
                st.session_state.selected_sekolah = nama_sekolah
                st.session_state.page = "detail"
                st.rerun()

        idx += 1

    # =========================================================
    # ✅ REKAP CABANG DINAS (TABEL SEKOLAH BISA DIBERHENTIKAN)
    # =========================================================
    st.divider()
    st.markdown(f"## 📌 Rekap Kepala Sekolah Bisa Diberhentikan — {st.session_state.selected_cabdin}")

    df_cab_rekap = df_cab.copy()
    df_cab_rekap["Status Regulatif"] = df_cab_rekap.apply(map_status, axis=1)

    df_bisa = df_cab_rekap[df_cab_rekap["Status Regulatif"].isin([
        "Aktif Periode Ke 2",
        "Lebih dari 2 Periode",
        "Plt"
    ])].copy()

    if df_bisa.empty:
        st.warning("⚠️ Tidak ada Kepala Sekolah yang bisa diberhentikan pada Cabang Dinas ini.")
    else:
        df_bisa["Calon Pengganti"] = df_bisa["Nama Sekolah"].map(perubahan_kepsek).fillna("-")

        tampil = df_bisa[[
            "Nama Sekolah",
            "Nama Kepala Sekolah",
            "Status Regulatif",
            "Ket Sertifikat BCKS",
            "Calon Pengganti"
        ]].copy()

        st.dataframe(tampil, use_container_width=True, hide_index=True)

    st.divider()

# =========================================================
# FIELD WARNA
# =========================================================
def tampil_colored_field(label, value, bg="#f1f1f1", text_color="black"):
    st.markdown(f"""
    <div style="padding:10px; border-radius:10px; background:{bg}; margin-bottom:8px;">
        <b>{label}:</b>
        <div style="color:{text_color}; font-weight:700;">{value}</div>
    </div>
    """, unsafe_allow_html=True)
# =========================================================
# HALAMAN DETAIL SEKOLAH
# =========================================================
def page_detail():
    if st.session_state.selected_sekolah is None:
        st.session_state.page = "sekolah"
        st.rerun()

    col_a, col_b, col_c = st.columns([1, 6, 1])

    with col_a:
        if st.button("🏠", key="home_detail"):
            st.session_state.page = "cabdin"
            st.session_state.selected_cabdin = None
            st.session_state.selected_sekolah = None
            st.rerun()

    with col_b:
        st.subheader(f"📄 Detail Sekolah: {st.session_state.selected_sekolah}")

    with col_c:
        if st.button("⬅️", key="back_detail"):
            st.session_state.page = "sekolah"
            st.session_state.selected_sekolah = None
            st.rerun()

    nama = str(st.session_state.selected_sekolah).replace("\xa0", " ").strip()

    row_detail = df_ks[
        df_ks["Nama Sekolah"]
        .astype(str)
        .str.replace("\xa0", " ", regex=False)
        .str.strip()
        == nama
    ]

    if row_detail.empty:
        st.error("❌ Data sekolah tidak ditemukan.")
        st.stop()

    row = row_detail.iloc[0]

    # =========================================================
    # ✅ FIX FINAL: PILIH BARIS TERBAIK (RIWAYAT DAPODIK TIDAK KOSONG)
    # =========================================================
    if "Riwayat Dapodik" in row_detail.columns:
        kandidat = row_detail[row_detail["Riwayat Dapodik"].astype(str).str.strip() != ""]
        kandidat = kandidat[kandidat["Riwayat Dapodik"].astype(str).str.lower().str.strip() != "nan"]

        if not kandidat.empty:
            row = kandidat.iloc[0]

    st.divider()
    st.markdown("## 📝 Data Lengkap (Database)")

    status_regulatif = map_status(row)

    bg_status = "#dbeeff"
    if status_regulatif == "Aktif Periode Ke 2":
        bg_status = "#fff3cd"
    if status_regulatif == "Lebih dari 2 Periode":
        bg_status = "#f8d7da"
    if status_regulatif == "Plt":
        bg_status = "#d1e7dd"

    ket_jabatan = row.get("Keterangan Jabatan", "-")
    ket_bcks = row.get("Ket Sertifikat BCKS", "-")

    bg_jabatan = get_warna_jabatan(ket_jabatan)
    bg_bcks = get_warna_bcks(ket_bcks)

    col_left, col_right = st.columns(2)

    with col_left:
        tampil_colored_field("NO", row.get("NO", "-"))
        tampil_colored_field("Nama Kepala Sekolah", row.get("Nama Kepala Sekolah", "-"))
        tampil_colored_field("Cabang Dinas", row.get("Cabang Dinas", "-"))
        tampil_colored_field("Kabupaten", row.get("Kabupaten", "-"))
        tampil_colored_field("Status", row.get("Status", "-"))
        tampil_colored_field("Ket Sertifikat BCKS", ket_bcks, bg=bg_bcks)
        tampil_colored_field("Keterangan Akhir", row.get("Keterangan Akhir", "-"))
        tampil_colored_field("Status Regulatif", status_regulatif, bg=bg_status)

    with col_right:
        tampil_colored_field("Nama Sekolah", row.get("Nama Sekolah", "-"))
        tampil_colored_field("Jenjang", row.get("Jenjang", "-"))
        tampil_colored_field("Tahun Pengangkatan", row.get("Tahun Pengangkatan", "-"))
        tampil_colored_field("Tahun Berjalan", row.get("Tahun Berjalan", "-"))
        tampil_colored_field("Masa Periode Sesuai KSPSTK", row.get("Masa Periode Sesuai KSPSTK", "-"))
        tampil_colored_field("Keterangan Jabatan", ket_jabatan, bg=bg_jabatan)

    st.divider()

    # =========================================================
    # ✅ REKAP MASA JABATAN KEPSEK
    # =========================================================
    st.markdown("## 📌 Rekap Masa Jabatan Kepala Sekolah")

    df_riwayat = load_riwayat()
    nama_kepsek_asli = row.get("Nama Kepala Sekolah", "-")

    total_tahun, jumlah_periode = hitung_masa_jabatan(df_riwayat, nama_kepsek_asli)

    st.success(f"🕒 Total Masa Jabatan: **{total_tahun} Tahun**")
    st.info(f"📍 Jumlah Periode Menjabat: **{jumlah_periode} Kali**")

    st.divider()

    # =========================================================
    # ✅ FIX FINAL: RIWAYAT DAPODIK PASTI TAMPIL
    # =========================================================
    kol_riwayat = cari_kolom_riwayat_dapodik(df_ks)

    if kol_riwayat:
        riwayat_dapodik = bersihkan(row.get(kol_riwayat, "-"))
    else:
        riwayat_dapodik = bersihkan(row.get("Riwayat Dapodik", "-"))

    riwayat_dapodik = format_riwayat_dapodik(riwayat_dapodik)

    tampil_colored_field(
        "Riwayat Dapodik",
        riwayat_dapodik.replace("\n", "<br>"),
        bg="#f1f1f1"
    )

    # =========================================================
    # CALON PENGGANTI
    # =========================================================
    pengganti_excel = row.get("Calon Pengganti jika Sudah Harus di Berhentikan", "-")
    pengganti = perubahan_kepsek.get(nama, "")

    st.markdown("## 👤 Calon Pengganti Kepala Sekolah")

    if pengganti:
        tampil_colored_field(
            "Calon Pengganti (Yang Dipilih Operator)",
            pengganti,
            bg="#d1e7dd"
        )
    else:
        tampil_colored_field(
            "Calon Pengganti",
            pengganti_excel,
            bg="#fff3cd"
        )

    st.divider()

    tampil_pasal_permendikdasmen(status_regulatif, ket_bcks)

    st.divider()

    # =========================================================
    # CEK ROLE VIEW ONLY
    # =========================================================
    is_view_only = st.session_state.role in ["Kadis", "View"]

    if is_view_only:
        st.info("ℹ️ Anda login sebagai **View Only**. Tidak dapat mengubah data.")
        return

    # =========================================================
    # TOMBOL MENUJU UPDATE RIWAYAT
    # =========================================================
    if st.button("📝 Update Riwayat Kepala Sekolah", use_container_width=True):
        st.session_state.page = "update"
        st.rerun()


    # ============================================
    # SELECTBOX CALON PENGGANTI
    # ============================================
    key_select = f"calon_{nama}"

    calon = st.selectbox(
        "👤 Pilih Calon Pengganti (SIMPEG)",
        ["-- Pilih Calon Pengganti --"] + guru_list,
        key=key_select
    )

    # ============================================
    # TAMPILKAN DATA SIMPEG CALON
    # ============================================
    if calon != "-- Pilih Calon Pengganti --":
        st.markdown("### 📌 Data SIMPEG Calon Pengganti")
    
        data_calon = ambil_data_simpeg(calon)
    
        if data_calon.empty:
            st.warning("⚠️ Data calon pengganti tidak ditemukan di SIMPEG.")
        else:
            calon_row = data_calon.iloc[0]
            calon_row = calon_row.apply(lambda x: bersihkan(x))
    
            kol_unor = cari_kolom(data_calon, ["UNOR", "UNIT ORGANISASI", "UNIT KERJA", "SATKER", "INSTANSI"])
            kol_cabdis = cari_kolom(data_calon, [
                "CABANG DINAS", "CABDIS", "WILAYAH", "KCD",
                "CABDIN", "CABDINAS", "CABANG_DINAS", "CABANGDINAS",
                "KANTOR CABANG", "CABANG"
            ])
            kol_alamat = cari_kolom(data_calon, ["ALAMAT", "JALAN", "DOMISILI", "TEMPAT TINGGAL", "ALAMAT RUMAH"])
    
            unor = bersihkan(calon_row.get(kol_unor, "-")) if kol_unor else "-"
            cabdis = bersihkan(calon_row.get(kol_cabdis, "-")) if kol_cabdis else "-"
            alamat = bersihkan(calon_row.get(kol_alamat, "-")) if kol_alamat else "-"
    
            if cabdis == "-" or cabdis.strip() == "":
                cabdis = deteksi_cabdis_dari_unor(unor)
    
            kol_nip = cari_kolom(data_calon, ["NIP"])
            kol_nik = cari_kolom(data_calon, ["NIK"])
            kol_nohp = cari_kolom(data_calon, ["NO HP", "NO. HP", "HP", "HANDPHONE", "TELP", "TELEPON"])
            kol_jabatan = cari_kolom(data_calon, ["JABATAN", "JABATAN TERAKHIR", "JABATAN FUNGSIONAL"])
            kol_jenis = cari_kolom(data_calon, ["JENIS PEGAWAI", "STATUS PEGAWAI", "KEDUDUKAN"])
            kol_nama = cari_kolom(data_calon, ["NAMA GURU", "NAMA"])
    
            nip = bersihkan(calon_row.get(kol_nip, "-")) if kol_nip else "-"
            nik = bersihkan(calon_row.get(kol_nik, "-")) if kol_nik else "-"
            nohp = bersihkan(calon_row.get(kol_nohp, "-")) if kol_nohp else "-"
            jabatan = bersihkan(calon_row.get(kol_jabatan, "-")) if kol_jabatan else "-"
            jenis_pegawai = bersihkan(calon_row.get(kol_jenis, "-")) if kol_jenis else "-"
    
            if kol_nama:
                nama_guru = bersihkan(calon_row.get(kol_nama, "-"))
            else:
                nama_guru = str(calon)
    
            html_card = f"""
    <div style="
        background: white;
        border-radius: 16px;
        padding: 16px;
        border-left: 8px solid #0d6efd;
        box-shadow: 0 3px 10px rgba(0,0,0,0.12);
        margin-top: 10px;
        margin-bottom: 10px;
        line-height: 1.6;
        word-wrap: break-word;
        overflow-wrap: break-word;
    ">
        <div style="font-size:18px; font-weight:800; margin-bottom:10px;">
            👤 {nama_guru}
        </div>
    
        <div style="margin-bottom:8px;"><b>NIP:</b> {nip}</div>
        <div style="margin-bottom:8px;"><b>NIK:</b> {nik}</div>
        <div style="margin-bottom:8px;"><b>No HP:</b> {nohp}</div>
        <div style="margin-bottom:8px;"><b>Jabatan:</b> {jabatan}</div>
        <div style="margin-bottom:8px;"><b>Jenis Pegawai:</b> {jenis_pegawai}</div>
    
        <hr style="margin:12px 0;">
    
        <div style="margin-bottom:8px;"><b>UNOR / Unit Kerja:</b> {unor}</div>
        <div style="margin-bottom:8px;"><b>Cabang Dinas:</b> {cabdis}</div>
        <div style="margin-bottom:8px;"><b>Alamat:</b> {alamat}</div>
    </div>
    """
    
            components.html(html_card, height=450, scrolling=True)  
    colbtn1, colbtn2 = st.columns(2)

    with colbtn1:
        if st.button("💾 Simpan Pengganti", key="btn_simpan_pengganti", use_container_width=True):
            if calon == "-- Pilih Calon Pengganti --":
                st.warning("⚠️ Pilih calon pengganti terlebih dahulu.")
            else:
                perubahan_kepsek[nama] = calon
                save_perubahan(perubahan_kepsek, df_ks, df_guru)
                st.success(f"✅ Diganti dengan: {calon}")
                st.rerun()

    with colbtn2:
        if st.button("↩️ Kembalikan ke Kepala Sekolah Awal", key="btn_reset_pengganti", use_container_width=True):
            if nama in perubahan_kepsek:
                del perubahan_kepsek[nama]
                save_perubahan(perubahan_kepsek, df_ks, df_guru)

            if key_select in st.session_state:
                del st.session_state[key_select]

            st.success("✅ Calon pengganti dikembalikan ke kondisi awal")
            st.rerun()

# =========================================================
# HALAMAN REKAP PROVINSI
# =========================================================
def page_rekap():
    col1, col2 = st.columns([6, 1])

    with col1:
        st.markdown("## 📌 Rekap Kepala Sekolah Bisa Diberhentikan")

    with col2:
        if st.button("⬅️ Kembali", use_container_width=True):
            st.session_state.page = "cabdin"
            st.rerun()

    st.divider()

    df_rekap = df_ks.copy()
    df_rekap["Status Regulatif"] = df_rekap.apply(map_status, axis=1)

    df_bisa = df_rekap[df_rekap["Status Regulatif"].isin(["Aktif Periode Ke 2", "Lebih dari 2 Periode", "Plt"])].copy()

    if df_bisa.empty:
        st.warning("⚠️ Tidak ada data Kepala Sekolah Bisa Diberhentikan.")
        st.stop()

    df_bisa["Calon Pengganti"] = df_bisa["Nama Sekolah"].map(perubahan_kepsek).fillna("-")

    tampil = df_bisa[[
        "Cabang Dinas",
        "Nama Sekolah",
        "Nama Kepala Sekolah",
        "Status Regulatif",
        "Ket Sertifikat BCKS",
        "Calon Pengganti"
    ]].copy()

    st.dataframe(tampil, use_container_width=True, hide_index=True)
# =========================================================
# HALAMAN UPDATE RIWAYAT KEPSEK (INPUT BANYAK SEKALIGUS)
# =========================================================
def page_update():

    # ===========================
    # AMBIL NAMA SEKOLAH LOGIN
    # ===========================
    if st.session_state.role == "Sekolah":
        nama_sekolah = st.session

    # ===========================
    # HEADER + TOMBOL KEMBALI
    # ===========================
    colA, colB = st.columns([1, 6])

    with colA:
        if st.button("⬅️ Kembali", use_container_width=True):

            # jika sekolah login, kunci sekolahnya
            if st.session_state.role == "Sekolah":
                st.session_state.selected_sekolah = st.session_state.sekolah_user

            st.session_state.page = "detail"
            st.rerun()

    with colB:
        st.markdown("## 📝 Update Riwayat Kepala Sekolah")

    st.divider()

    # ===========================
    # VALIDASI SEKOLAH
    # ===========================
    if st.session_state.selected_sekolah is None:
        st.warning("⚠️ Pilih sekolah dulu dari menu sekolah.")
        st.stop()

    nama_sekolah = st.session_state.selected_sekolah
    st.info(f"🏫 Sekolah: **{nama_sekolah}**")

    # ===========================
    # SESSION UNTUK LIST RIWAYAT INPUT
    # ===========================
    if "riwayat_inputs" not in st.session_state:
        st.session_state.riwayat_inputs = [
            {"nama_kepsek": "", "nip": "", "mulai": "", "selesai": "", "ket": ""}
        ]

    # ===========================
    # TOMBOL TAMBAH RIWAYAT
    # ===========================
    col_add, col_reset = st.columns([2, 2])

    with col_add:
        if st.button("➕ Tambah Riwayat Baru", use_container_width=True):
            st.session_state.riwayat_inputs.append(
                {"nama_kepsek": "", "nip": "", "mulai": "", "selesai": "", "ket": ""}
            )
            st.rerun()

    with col_reset:
        if st.button("🗑️ Reset Form", use_container_width=True):
            st.session_state.riwayat_inputs = [
                {"nama_kepsek": "", "nip": "", "mulai": "", "selesai": "", "ket": ""}
            ]
            st.rerun()

    st.divider()

    # ===========================
    # FORM INPUT MULTI RIWAYAT
    # ===========================
    for i, item in enumerate(st.session_state.riwayat_inputs):
        st.markdown(f"### 📌 Riwayat Ke-{i+1}")

        col1, col2 = st.columns(2)

        with col1:
            item["nama_kepsek"] = st.text_input(
                f"Nama Kepala Sekolah (Riwayat {i+1})",
                value=item["nama_kepsek"],
                key=f"nama_{i}"
            )

            item["mulai"] = st.text_input(
                f"Mulai Menjabat (Riwayat {i+1})",
                value=item["mulai"],
                placeholder="contoh: 2012 atau 01-01-2012",
                key=f"mulai_{i}"
            )

            item["ket"] = st.text_area(
                f"Keterangan (Riwayat {i+1})",
                value=item["ket"],
                key=f"ket_{i}"
            )

        with col2:
            item["nip"] = st.text_input(
                f"NIP Kepala Sekolah (Riwayat {i+1})",
                value=item["nip"],
                key=f"nip_{i}"
            )

            item["selesai"] = st.text_input(
                f"Selesai Menjabat (Riwayat {i+1})",
                value=item["selesai"],
                placeholder="kosongkan jika masih menjabat",
                key=f"selesai_{i}"
            )

        # tombol hapus riwayat tertentu
        if len(st.session_state.riwayat_inputs) > 1:
            if st.button(f"❌ Hapus Riwayat Ke-{i+1}", key=f"hapus_{i}"):
                st.session_state.riwayat_inputs.pop(i)
                st.rerun()

        st.divider()

    # ===========================
# SIMPAN SEMUA RIWAYAT SEKALIGUS
# ===========================
if st.button("💾 Simpan Semua Riwayat", key="btn_simpan_semua_riwayat", use_container_width=True):

    sukses = 0
    gagal = 0

    for item in st.session_state.riwayat_inputs:
        nama_kepsek = item["nama_kepsek"].strip()
        nip = item["nip"].strip()
        mulai = item["mulai"].strip()
        selesai = item["selesai"].strip()
        ket = item["ket"].strip()

        if nama_kepsek == "" or mulai == "":
            gagal += 1
            continue

        simpan_riwayat_baru(
            nama_sekolah=nama_sekolah,
            nama_kepsek=nama_kepsek,
            nip=nip,
            mulai=mulai,
            selesai=selesai,
            ket=ket
        )
        sukses += 1

    st.success(f"✅ Berhasil simpan {sukses} riwayat.")
    if gagal > 0:
        st.warning(f"⚠️ {gagal} riwayat tidak disimpan karena Nama Kepsek / Mulai kosong.")

    # reset form setelah simpan
    st.session_state.riwayat_inputs = [
        {"nama_kepsek": "", "nip": "", "mulai": "", "selesai": "", "ket": ""}
    ]
    st.rerun()

st.divider()

# ===========================
# TAMPILKAN RIWAYAT YANG SUDAH TERSIMPAN
# ===========================
st.markdown("## 📌 Riwayat Jabatan Tersimpan")

df_riwayat = load_riwayat()
df_view = df_riwayat[df_riwayat["Nama Sekolah"].astype(str).str.strip() == nama_sekolah].copy()

if df_view.empty:
    st.warning("⚠️ Belum ada riwayat jabatan.")
else:
    st.dataframe(df_view, use_container_width=True)

# =========================================================
# ROUTING UTAMA
# =========================================================
if st.session_state.page == "cabdin":
    set_bg("cabdis.jpg")
    page_cabdin()

elif st.session_state.page == "sekolah":
    set_bg("dashboard.jpg")
    page_sekolah()

elif st.session_state.page == "detail":

    # ✅ JIKA ROLE SEKOLAH, JANGAN TAMPILKAN DETAIL
    if st.session_state.role == "Sekolah":
        st.session_state.page = "update"
        st.rerun()

    set_bg("dashboard.jpg")
    page_detail()

elif st.session_state.page == "rekap":
    set_bg("dashboard.jpg")
    page_rekap()

elif st.session_state.page == "update":
    set_bg("dashboard.jpg")
    page_update()


# =========================================================
# FOOTER
# =========================================================
st.divider()
st.markdown("## ⚖️ Dasar Hukum Penugasan Kepala Sekolah")

st.markdown("""
<div style="
    background: linear-gradient(90deg, #0d6efd, #198754);
    padding: 18px;
    border-radius: 16px;
    color: white;
    font-size: 18px;
    font-weight: 800;
    box-shadow: 0 3px 10px rgba(0,0,0,0.15);
">
📌 Permendikdasmen Nomor 7 Tahun 2025  
<br>
<span style="font-size:14px; font-weight:500;">
Penugasan Kepala Sekolah Maksimal 2 Periode (1 Periode = 4 Tahun)
</span>
</div>
""", unsafe_allow_html=True)

st.info("""
### 📌 Ringkasan Pokok Ketentuan Permendikdasmen No. 7 Tahun 2025

1. Kepala Sekolah ditugaskan maksimal **2 (dua) periode**.  
2. **1 (satu) periode = 4 (empat) tahun**.  
3. Kepala Sekolah yang telah menjabat **lebih dari 2 periode wajib diberhentikan dari penugasan**.  
4. Kepala Sekolah **Periode 1** dapat diperpanjang menjadi Periode 2 apabila memenuhi syarat, termasuk sertifikat kompetensi (misalnya **BCKS**).  
5. Kepala Sekolah wajib dievaluasi kinerjanya secara berkala sebagai dasar perpanjangan atau pemberhentian.  
6. Jika terjadi kekosongan jabatan Kepala Sekolah, dapat ditunjuk **Pelaksana Tugas (Plt)** sampai Kepala Sekolah definitif ditetapkan.  
7. Penugasan Kepala Sekolah merupakan **tugas tambahan ASN** dan harus sesuai aturan manajemen ASN.  
""")

st.success("✅ Dashboard ini disusun berdasarkan pemetaan status regulatif sesuai Permendikdasmen No. 7 Tahun 2025.")

st.divider()
st.markdown("""
<div style="text-align:center; font-weight:800; font-size:16px;">
© 2026 SMART-KS • Sistem Monitoring dan Analisis Riwayat Tugas - Kepala Sekolah
</div>
""", unsafe_allow_html=True)

















