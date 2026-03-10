import streamlit as st
import pandas as pd
import os
import re   # ✅ TAMBAHAN (UNTUK HAPUS HTML TAG)
import streamlit.components.v1 as components
import base64

def get_base64_image(image_path):
    with open(image_path, "rb") as img:
        return base64.b64encode(img.read()).decode()

import gspread
from google.oauth2.service_account import Credentials

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

# =========================================================
# FUNGSI VIDEO BACKGROUND LOGIN
# =========================================================

def set_video_bg(video_file):

    video_path = os.path.join(os.path.dirname(__file__), video_file)

    if not os.path.exists(video_path):
        st.error("❌ Video login_.mp4 tidak ditemukan di folder aplikasi")
        return

    video_bytes = open(video_path, "rb").read()
    video_base64 = base64.b64encode(video_bytes).decode()

    st.markdown(f"""
    <style>

    /* HILANGKAN BACKGROUND STREAMLIT */
    .stApp {{
        background: transparent !important;
    }}

    .main {{
        background: transparent !important;
    }}

    header {{
        background: transparent !important;
    }}

    /* VIDEO BACKGROUND */
    #loginVideo {{
        position: fixed;
        right: 0;
        bottom: 0;
        min-width: 100vw;
        min-height: 100vh;
        object-fit: cover;
        z-index: -999;
    }}

    </style>

    <video autoplay muted loop id="loginVideo">
        <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
    </video>
    """, unsafe_allow_html=True)
# =========================================================
# FUNGSI BACKGROUND GAMBAR
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
        background-size: 100% 100%;
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
if "filter_dashboard" not in st.session_state:
    st.session_state.filter_dashboard = None
    
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

if "filter_cabdin" not in st.session_state:
    st.session_state.filter_cabdin = None
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
# SHEET AUDIT SMART-KS 2026
# =========================================================
SHEET_AUDIT = "AUDIT_LOG_SMART_KS"

# =========================================================
# SHEET AUDIT TRAIL SMART-KS 2026
# =========================================================
SHEET_AUDIT = "AUDIT_LOG_SMART_KS"

# =========================================================
# FUNGSI SIMPAN & LOAD PENGGANTI (PERMANEN GOOGLE SHEET)
# =========================================================

@st.cache_resource
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


@st.cache_data(ttl=60)
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
load_perubahan.clear()
# =========================================================
# FUNGSI SIMPAN AUDIT LOG (MENUNGGU PERSETUJUAN KADIS)
# =========================================================
def save_audit_log(sekolah, kepsek_lama, pengganti, alasan, role, username):

    try:
        sheet = konek_gsheet()
        spreadsheet = sheet.spreadsheet

        try:
            audit_sheet = spreadsheet.worksheet(SHEET_AUDIT)
        except:
            audit_sheet = spreadsheet.add_worksheet(title=SHEET_AUDIT, rows="1000", cols="10")
            audit_sheet.append_row([
                "Tanggal",
                "Sekolah",
                "Kepsek Lama",
                "Pengganti",
                "Alasan",
                "Role Pengusul",
                "User",
                "Status Approval",
                "Approved By"
            ])

        from datetime import datetime
        tanggal = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        audit_sheet.append_row([
            tanggal,
            sekolah,
            kepsek_lama,
            pengganti,
            alasan,
            role,
            username,
            "Menunggu Persetujuan Kadis",
            "-"
        ])

    except Exception as e:
        st.error(f"Gagal menyimpan audit: {e}")
# =========================================================
# UPDATE STATUS APPROVAL (KHUSUS KADIS)
# =========================================================
def update_status_approval(row_index, status):

    sheet = konek_gsheet()
    spreadsheet = sheet.spreadsheet
    audit_sheet = spreadsheet.worksheet(SHEET_AUDIT)

    audit_sheet.update(f"H{row_index}", status)
    audit_sheet.update(f"I{row_index}", "Kadis")
# =========================================================
# FUNGSI SIMPAN AUDIT TRAIL SMART-KS 2026
# =========================================================
def save_audit_log(sekolah, kepsek_lama, pengganti, alasan, role, username):

    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)

        spreadsheet = client.open_by_key(SHEET_ID)

        try:
            sheet = spreadsheet.worksheet(SHEET_AUDIT)
        except:
            sheet = spreadsheet.add_worksheet(title=SHEET_AUDIT, rows="1000", cols="10")
            sheet.append_row([
                "Tanggal",
                "Sekolah",
                "Kepsek Lama",
                "Pengganti",
                "Alasan",
                "Role",
                "User"
            ])

        from datetime import datetime
        tanggal = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        sheet.append_row([
            tanggal,
            sekolah,
            kepsek_lama,
            pengganti,
            alasan,
            role,
            username
        ])

    except Exception as e:
        st.error(f"❌ Gagal menyimpan Audit Log: {e}")
        
# =========================================================
# DATA RIWAYAT KEPALA SEKOLAH (UPDATE SEKOLAH)
# =========================================================
SHEET_RIWAYAT = "RIWAYAT_KASEK"

def load_riwayat():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame()

    try:
        xls = pd.ExcelFile(DATA_FILE)
        if SHEET_RIWAYAT not in xls.sheet_names:
            return pd.DataFrame(columns=[
                "Nama Sekolah", "Nama Kepsek", "NIP", "Mulai", "Selesai", "Keterangan"
            ])

        df = pd.read_excel(DATA_FILE, sheet_name=SHEET_RIWAYAT, dtype=str)
        df = df.fillna("")
        return df

    except Exception as e:
        st.error(f"❌ Gagal membaca sheet {SHEET_RIWAYAT}: {e}")
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
# =========================================================
# LOAD RIWAYAT DAPODIK
# =========================================================
try:
    df_riwayat_dapodik = pd.read_excel(DATA_FILE, sheet_name="Riwayat_Dapodik", dtype=str)
    df_riwayat_dapodik = df_riwayat_dapodik.fillna("")
except:
    df_riwayat_dapodik = pd.DataFrame()

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

    nama_guru = str(nama_guru).strip().upper()

    if "NAMA GURU" not in df_guru.columns:
        return pd.DataFrame()

    df_tmp = df_guru.copy()

    df_tmp["NAMA_FIX"] = (
        df_tmp["NAMA GURU"]
        .astype(str)
        .str.replace("\xa0", " ", regex=False)
        .str.strip()
        .str.upper()
    )

    # cari jika nama ada di dalam string
    hasil = df_tmp[df_tmp["NAMA_FIX"].str.contains(nama_guru, na=False)]

    # jika tidak ketemu, coba balik kata
    if hasil.empty:

        kata = nama_guru.split()

        if len(kata) >= 2:

            balik = kata[-1] + " " + kata[0]

            hasil = df_tmp[df_tmp["NAMA_FIX"].str.contains(balik, na=False)]

    return hasil
# =========================================================
# FOTO SIMPEG (AUTO GENERATE DARI NIP)
# =========================================================
def ambil_foto_simpeg(nip):
    if nip is None:
        return None

    nip = str(nip).strip()

    if nip == "" or nip == "-" or nip.lower() == "nan":
        return None

    # jika SIMPEG punya endpoint foto
    url = f"https://simpeg.sumutprov.go.id/foto/{nip}.jpg"
    return url
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
# VIDEO LOGIN BACKGROUND
# =========================================================

if not st.session_state.login:

    set_video_bg("login_.mp4")

else:

    pass
# =========================================================
# LOGIN PAGE
# =========================================================
st.markdown("""
<style>
.stApp {
    background-color: transparent;
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
    # FORM LOGIN
    # ==========================
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
                st.success(f"✅ Login berhasil sebagai **{st.session_state.role}**")
                st.rerun()
            else:
                st.error("❌ Username atau Password salah")

    st.stop()

st.caption(f"👤 Login sebagai: **{st.session_state.role}**")


# =========================================================
# SIDEBAR FILTER
# =========================================================
st.sidebar.header("🔍 Filter & Pencarian")

search_nama = st.sidebar.text_input("Cari Nama Kepala Sekolah")
search_sekolah = st.sidebar.text_input("Cari Nama Sekolah")

# ==========================
# FIX JENJANG
# ==========================
opsi_jenjang = ["Semua", "SMA", "SMK", "SLB"]

# jika mau tetap ambil dari data tapi dipaksa bersih:
data_jenjang = sorted(df_ks["Jenjang"].astype(str).str.strip().unique())
opsi_final_jenjang = ["Semua"] + [j for j in opsi_jenjang if j in data_jenjang or j in opsi_jenjang]

jenjang_filter = st.sidebar.selectbox("Jenjang", opsi_final_jenjang)

# ==========================
# FIX KETERANGAN AKHIR
# ==========================
opsi_ket = [
    "Semua",
    "Aktif Periode Ke 1",
    "Aktif Periode Ke 2",
    "Lebih dari 2 Periode",
    "Plt"
]

ket_filter = st.sidebar.selectbox("Keterangan Akhir", opsi_ket)
# =========================================================
# APPLY FILTER
# =========================================================
def apply_filter(df):

    if jenjang_filter != "Semua":
        df = df[df["Jenjang"] == jenjang_filter]

    if ket_filter != "Semua":
        df["Status Regulatif"] = df.apply(map_status, axis=1)
        df = df[df["Status Regulatif"] == ket_filter]

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
# HALAMAN CABDIN (DASHBOARD UTAMA)
# =========================================================
def page_cabdin():

    st.markdown("""
    <style>
    div[data-testid="column"] {
        display:flex;
        flex-direction:column;
        justify-content:center;
    }
    </style>
    """, unsafe_allow_html=True)

    col1,col2,col3,col4,col5,col6 = st.columns([2,2,2,2,2,2])

    with col1:
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")

        if os.path.exists(logo_path):
            st.image(logo_path,width=120)
        else:
            st.markdown("## 📊 SMART.KS")

    with col2:
        if st.button("🔄 Refresh SIMPEG",use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Data SIMPEG diperbarui")
            st.rerun()

    with col3:
        if st.button("🔄 Refresh Kepsek",use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Data Kepala Sekolah diperbarui")
            st.rerun()

    with col4:
        if st.button("📌 Rekapitulasi",use_container_width=True):
            st.session_state.page="rekap"
            st.rerun()

    with col5:
        if st.button("🚪 Logout",use_container_width=True):
            st.session_state.login=False
            st.session_state.role=None
            st.session_state.page="cabdin"
            st.session_state.selected_cabdin=None
            st.session_state.selected_sekolah=None
            st.session_state.filter_status=None
            st.rerun()

    st.divider()

    # =====================================================
    # HITUNG STATUS
    # =====================================================
    df_rekap = df_ks.copy()
    df_rekap["Status Regulatif"] = df_rekap.apply(map_status, axis=1)

    jumlah_p1 = int((df_rekap["Status Regulatif"] == "Aktif Periode Ke 1").sum())
    jumlah_p2 = int((df_rekap["Status Regulatif"] == "Aktif Periode Ke 2").sum())
    jumlah_lebih2 = int((df_rekap["Status Regulatif"] == "Lebih dari 2 Periode").sum())
    jumlah_plt = int((df_rekap["Status Regulatif"] == "Plt").sum())

    total_bisa_diberhentikan = jumlah_p2 + jumlah_lebih2 + jumlah_plt

    st.markdown("""
    <style>
    
    .rekap-title{
    text-align:center;
    font-size:30px;
    font-weight:800;
    margin-bottom:20px;
    color:#1f2d3d;
    }
    
    .rekap-wrapper{
    display:flex;
    justify-content:center;
    gap:18px;
    flex-wrap:wrap;
    margin-bottom:30px;
    }
    
    .rekap-card{
    width:120px;
    height:40px;
    background:white;
    border-radius:10px;
    box-shadow:0 2px 8px rgba(0,0,0,0.15);
    display:flex;
    flex-direction:column;
    justify-content:center;
    align-items:center;
    cursor:pointer;
    transition:0.2s;
    }
    
    .rekap-card:hover{
    transform:scale(1.05);
    box-shadow:0 4px 14px rgba(0,0,0,0.25);
    }
    
    .rekap-label{
    font-size:11px;
    font-weight:700;
    color:#555;
    margin-bottom:2px;
    }
    
    .rekap-number{
    font-size:18px;
    font-weight:900;
    color:#1b4332;
    }
    
    </style>
    """, unsafe_allow_html=True)
    
    
    st.markdown('<div class="rekap-title">📌 REKAP DATA DINAS PENDIDIKAN</div>', unsafe_allow_html=True)
    
    col1,col2,col3,col4,col5 = st.columns(5)
    
    with col1:
        if st.button("Aktif Periode 1\n"+str(jumlah_p1),use_container_width=True):
            st.session_state.filter_status="Aktif Periode Ke 1"
            st.session_state.page="list_status"
            st.rerun()
    
    with col2:
        if st.button("Aktif Periode 2\n"+str(jumlah_p2),use_container_width=True):
            st.session_state.filter_status="Aktif Periode Ke 2"
            st.session_state.page="list_status"
            st.rerun()
    
    with col3:
        if st.button(">2 Periode\n"+str(jumlah_lebih2),use_container_width=True):
            st.session_state.filter_status="Lebih dari 2 Periode"
            st.session_state.page="list_status"
            st.rerun()
    
    with col4:
        if st.button("PLT\n"+str(jumlah_plt),use_container_width=True):
            st.session_state.filter_status="Plt"
            st.session_state.page="list_status"
            st.rerun()
    
    with col5:
        if st.button("Bisa Diberhentikan\n"+str(total_bisa_diberhentikan),use_container_width=True):
            st.session_state.filter_status="Bisa Diberhentikan"
            st.session_state.page="list_status"
            st.rerun()
    st.divider()
    # =====================================================
    # DAFTAR CABANG DINAS
    # =====================================================
    st.subheader("🏢 DAFTAR CABANG DINAS PENDIDIKAN")

    df_view = apply_filter(df_ks)

    cabdin_list = urutkan_cabdin(
        df_view["Cabang Dinas"].dropna().unique()
    )

    cols = st.columns(4)

    for i,cabdin in enumerate(cabdin_list):

        with cols[i%4]:

            if st.button(f"📍 {cabdin}",key=f"cabdin_{cabdin}".replace(" ","_"),use_container_width=True):

                st.session_state.selected_cabdin=cabdin
                st.session_state.page="sekolah"
                st.rerun()
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

    # =============================
    # WARNA KOLOM STATUS
    # =============================
    def warna_status(val):

        if "Periode Ke 1" in val:
            return "background-color:#dbeeff"

        if "Periode Ke 2" in val:
            return "background-color:#fff3cd"

        if "Lebih dari 2" in val:
            return "background-color:#f8d7da"

        if "Plt" in val:
            return "background-color:#d1e7dd"

        return ""

# =========================================================
# TAMPILKAN DAFTAR KEPALA SEKOLAH SESUAI DASHBOARD
# =========================================================

if st.session_state.filter_dashboard:

    st.divider()

    status = st.session_state.filter_dashboard

    df_tmp = df_ks.copy()
    df_tmp["Status Regulatif"] = df_tmp.apply(map_status, axis=1)

    if status == "Bisa Diberhentikan":

        df_tmp = df_tmp[df_tmp["Status Regulatif"].isin([
            "Aktif Periode Ke 2",
            "Lebih dari 2 Periode",
            "Plt"
        ])]

    else:
        df_tmp = df_tmp[df_tmp["Status Regulatif"] == status]

    if df_tmp.empty:
        st.warning("Tidak ada data.")
    else:

        tampil = df_tmp[[
            "Nama Kepala Sekolah",
            "Nama Sekolah",
            "Cabang Dinas",
            "Status Regulatif"
        ]].copy()

        tampil.insert(0, "No", range(1, len(tampil) + 1))

# =========================================================
# HALAMAN LIST STATUS DARI DASHBOARD / CABDIN
# =========================================================
def page_list_status():

    status = st.session_state.filter_status
    cabdin = st.session_state.filter_cabdin

    col1, col2 = st.columns([6,1])

    with col1:

        if cabdin:
            st.markdown(f"## 📋 Daftar Kepala Sekolah - {status} ({cabdin})")
        else:
            st.markdown(f"## 📋 Daftar Kepala Sekolah - {status}")

    with col2:
        if st.button("⬅️ Kembali", use_container_width=True):

            if cabdin:
                st.session_state.page = "sekolah"
            else:
                st.session_state.page = "cabdin"

            st.session_state.filter_status = None
            st.session_state.filter_cabdin = None
            st.rerun()

    st.divider()

    # =====================================================
    # PREPARE DATA
    # =====================================================
    df_tmp = df_ks.copy()
    df_tmp["Status Regulatif"] = df_tmp.apply(map_status, axis=1)

    # =====================================================
    # FILTER CABANG DINAS
    # =====================================================
    if cabdin:
        df_tmp = df_tmp[df_tmp["Cabang Dinas"] == cabdin]

    # =====================================================
    # FILTER STATUS
    # =====================================================
    if status == "Bisa Diberhentikan":

        df_tmp = df_tmp[df_tmp["Status Regulatif"].isin([
            "Aktif Periode Ke 2",
            "Lebih dari 2 Periode",
            "Plt"
        ])]

    else:

        df_tmp = df_tmp[df_tmp["Status Regulatif"] == status]

    # =====================================================
    # TABEL TAMPIL
    # =====================================================
    tampil = df_tmp[[
        "Nama Kepala Sekolah",
        "Nama Sekolah",
        "Cabang Dinas",
        "Status Regulatif"
    ]].copy()

    tampil.insert(0, "No", range(1, len(tampil)+1))

    st.dataframe(
        tampil,
        use_container_width=True,
        hide_index=True
    )

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
    with col1:
        st.markdown("<center>Aktif Periode Ke 1</center>", unsafe_allow_html=True)
        if st.button(str(jumlah_p1), key="cab_p1", use_container_width=True):
            st.session_state.filter_status = "Aktif Periode Ke 1"
            st.session_state.filter_cabdin = st.session_state.selected_cabdin
            st.session_state.page = "list_status"
            st.rerun()
    
    with col2:
        st.markdown("<center>Aktif Periode Ke 2</center>", unsafe_allow_html=True)
        if st.button(str(jumlah_p2), key="cab_p2", use_container_width=True):
            st.session_state.filter_status = "Aktif Periode Ke 2"
            st.session_state.filter_cabdin = st.session_state.selected_cabdin
            st.session_state.page = "list_status"
            st.rerun()
    
    with col3:
        st.markdown("<center>Lebih 2 Periode</center>", unsafe_allow_html=True)
        if st.button(str(jumlah_lebih2), key="cab_p3", use_container_width=True):
            st.session_state.filter_status = "Lebih dari 2 Periode"
            st.session_state.filter_cabdin = st.session_state.selected_cabdin
            st.session_state.page = "list_status"
            st.rerun()
    
    with col4:
        st.markdown("<center>Kasek Plt</center>", unsafe_allow_html=True)
        if st.button(str(jumlah_plt), key="cab_p4", use_container_width=True):
            st.session_state.filter_status = "Plt"
            st.session_state.filter_cabdin = st.session_state.selected_cabdin
            st.session_state.page = "list_status"
            st.rerun()
    
    with col5:
        st.markdown("<center>Bisa Diberhentikan</center>", unsafe_allow_html=True)
        if st.button(str(total_bisa), key="cab_p5", use_container_width=True):
            st.session_state.filter_status = "Bisa Diberhentikan"
            st.session_state.filter_cabdin = st.session_state.selected_cabdin
            st.session_state.page = "list_status"
            st.rerun()
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
    # ======================================
    # DEFAULT VARIABEL TMT
    # ======================================
    tmt_pertama = None
    tahun_pengangkatan = "-"
    tahun_berjalan = "-"
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
    # PILIH BARIS TERBAIK (RIWAYAT DAPODIK TIDAK KOSONG)
    # =========================================================
    
    row = row_detail.iloc[0]
    
    if "Riwayat Dapodik" in row_detail.columns:
    
        kandidat = row_detail[
            row_detail["Riwayat Dapodik"].astype(str).str.strip() != ""
        ]
    
        kandidat = kandidat[
            kandidat["Riwayat Dapodik"].astype(str).str.lower().str.strip() != "nan"
        ]
    
        if not kandidat.empty:
            row = kandidat.iloc[0]
    
    
    # =========================================================
    # DATA KEPALA SEKOLAH (DATABASE + SIMPEG)
    # =========================================================
    
        
    from datetime import datetime
    
    nama_kepsek = row.get("Nama Kepala Sekolah", "-")
    nama_sekolah = row.get("Nama Sekolah", "-")
    jenjang = row.get("Jenjang", "-")
    
    # =========================================================
    # HITUNG TMT PERTAMA (HANYA KEPALA SEKOLAH, BUKAN PLT)
    # =========================================================
    
    from datetime import datetime
    
    tahun_pengangkatan = "-"
    tahun_berjalan = "-"
    tmt_pertama = None
    
    try:
    
        if not df_riwayat_dapodik.empty:
    
            data_riwayat = df_riwayat_dapodik[
                df_riwayat_dapodik["Nama Kepala Sekolah"]
                .astype(str)
                .str.upper()
                .str.strip()
                ==
                str(nama_kepsek).upper().strip()
            ]
    
            # ===============================
            # FILTER HANYA JABATAN KEPALA SEKOLAH
            # ===============================
    
            data_riwayat = data_riwayat[
                data_riwayat["Jabatan"]
                .astype(str)
                .str.contains("Kepala Sekolah", case=False, na=False)
            ]
    
            # buang PLT
            data_riwayat = data_riwayat[
                ~data_riwayat["Jabatan"]
                .astype(str)
                .str.contains("PLT", case=False, na=False)
            ]
    
            if not data_riwayat.empty:
    
                tmt_series = pd.to_datetime(
                    data_riwayat["TMT"],
                    errors="coerce"
                )
    
                if not tmt_series.dropna().empty:
    
                    tmt_pertama = tmt_series.min()
    
                    today = datetime.today()
    
                    selisih = today - tmt_pertama
    
                    tahun = selisih.days // 365
                    bulan = (selisih.days % 365) // 30
                    hari = (selisih.days % 365) % 30
    
                    tahun_pengangkatan = tmt_pertama.strftime("%d-%m-%Y")
    
                    tahun_berjalan = f"{tahun} Tahun {bulan} Bulan {hari} Hari"
    
    except:
        pass
    
    # =========================================================
    # DATA TAMBAHAN
    # =========================================================
    
    periode = row.get("Masa Periode Sesuai KSPSTK", "-")
    status = row.get("Status", "-")
    cabdis = row.get("Cabang Dinas", "-")
    kabupaten = row.get("Kabupaten", "-")
    ket_jabatan = row.get("Keterangan Jabatan", "-")
    ket_bcks = row.get("Ket Sertifikat BCKS", "-")
    
    # ================================
    # AMBIL DATA SIMPEG
    # ================================
    data_kepsek = ambil_data_simpeg(nama_kepsek)
    
    nip = "-"
    nik = "-"
    nohp = "-"
    jabatan = "-"
    jenis_pegawai = "-"
    unor = "-"
    alamat = "-"
    
    if data_kepsek is not None and not data_kepsek.empty:
    
        kepsek_row = data_kepsek.iloc[0]
    
        # DETEKSI KOLOM OTOMATIS
        kol_nip = cari_kolom(data_kepsek, ["NIP"])
        kol_nik = cari_kolom(data_kepsek, ["NIK"])
        kol_hp = cari_kolom(data_kepsek, ["HP","TELP","HANDPHONE","NO HP","NO. HP"])
        kol_jabatan = cari_kolom(data_kepsek, ["JABATAN"])
        kol_jenis = cari_kolom(data_kepsek, ["JENIS PEGAWAI","STATUS PEGAWAI","KEDUDUKAN"])
        kol_unor = cari_kolom(data_kepsek, ["UNOR","UNIT","INSTANSI","SATKER"])
        kol_alamat = cari_kolom(data_kepsek, ["ALAMAT","DOMISILI","TEMPAT TINGGAL"])
        
        nip = bersihkan(kepsek_row.get(kol_nip, "-")) if kol_nip else "-"
        nik = bersihkan(kepsek_row.get(kol_nik, "-")) if kol_nik else "-"
        nohp = bersihkan(kepsek_row.get(kol_hp, "-")) if kol_hp else "-"
        jabatan = bersihkan(kepsek_row.get(kol_jabatan, "-")) if kol_jabatan else "-"
        jenis_pegawai = bersihkan(kepsek_row.get(kol_jenis, "-")) if kol_jenis else "-"
        unor = row.get("Nama Sekolah", "-")
        alamat = bersihkan(kepsek_row.get(kol_alamat, "-")) if kol_alamat else "-"
    
    
    # =========================================================
    # CARD TAMPILAN KEPALA SEKOLAH
    # =========================================================
    bg_card = get_base64_image("background_card.jpg")
    html_kepsek = f"""
    <div style="
    background-image:url('data:image/jpg;base64,{bg_card}');
    background-size: 100% 100%;
    background-repeat:no-repeat;
    background-position:center;
    border-radius:18px;
    padding:25px;
    display:flex;
    gap:30px;
    align-items:flex-start;
    flex-wrap:wrap;
    ">
    
    <div style="
    padding:20px;
    border-radius:14px;
    width:100%;
    display:flex;
    gap:30px;
    flex-wrap:wrap;
    ">
    
    <div style="
    width:100%;
    text-align:center;
    font-size:36px;
    font-weight:900;
    margin-bottom:20px;
    color:#1b4332;
    letter-spacing:1px;
    text-shadow:1px 1px 2px rgba(0,0,0,0.2);
    ">
    👨‍🏫 {nama_kepsek}
    </div>  
    
    <div style="display:grid;grid-template-columns:200px auto;gap:6px;font-size:15px">
    
    <div><b>Nama Sekolah</b></div><div>: {nama_sekolah}</div>
    <div><b>Jenjang</b></div><div>: {jenjang}</div>
    <div><b>Cabang Dinas</b></div><div>: {cabdis}</div>
    <div><b>Kabupaten</b></div><div>: {kabupaten}</div>
    <div><b>Status</b></div><div>: {status}</div>
    
    </div>
    
    <hr style="margin:12px 0">
    
    <div style="display:grid;grid-template-columns:200px auto;gap:6px;font-size:15px">
    
    <div><b>Tahun Pengangkatan</b></div><div>: {tahun_pengangkatan}</div>
    <div><b>Tahun Berjalan</b></div><div>: {tahun_berjalan}</div>
    <div><b>Masa Periode</b></div><div>: {periode}</div>
    <div><b>Keterangan Jabatan</b></div><div>: {ket_jabatan}</div>
    <div><b>Sertifikat BCKS</b></div><div>: {ket_bcks}</div>
    
    </div>
    
    <hr style="margin:12px 0">
    
    <div style="display:grid;grid-template-columns:200px auto;gap:6px;font-size:15px">
    
    <div><b>NIP</b></div><div>: {nip}</div>
    <div><b>NIK</b></div><div>: {nik}</div>
    <div><b>No HP</b></div><div>: {nohp}</div>
    <div><b>Jabatan SIMPEG</b></div><div>: {jabatan}</div>
    <div><b>Jenis Pegawai</b></div><div>: {jenis_pegawai}</div>
    <div><b>Unit Kerja</b></div><div>: {unor}</div>
    
    <div><b>Alamat</b></div>
    <div style="word-wrap:break-word;white-space:normal">
    : {alamat}
    </div>
    
    </div>
    
    </div>
    
    </div>
    
    </div>
    """
    
    components.html(html_kepsek, height=600)
    # =========================================================
    # RIWAYAT DAPODIK (TABEL DARI SHEET RIWAYAT_DAPODIK)
    # =========================================================
    
    st.divider()
    st.markdown("## 📚 Riwayat Dapodik")

    try:
    
        if not df_riwayat_dapodik.empty:
    
            nama_kepsek = str(row.get("Nama Kepala Sekolah", "")).strip().upper()
    
            data_riwayat = df_riwayat_dapodik[
                df_riwayat_dapodik["Nama Kepala Sekolah"]
                .astype(str)
                .str.strip()
                .str.upper()
                == nama_kepsek
            ]
    
            if not data_riwayat.empty:
    
                kolom = [
                "Jabatan",
                "Satuan Pendidikan",
                "Jumlah Jam",
                "Nomor SK",
                "TMT",
                "TST"
            ]
    
                kolom = [k for k in kolom if k in data_riwayat.columns]
    
                df_tampil = data_riwayat[kolom].copy()
                # ======================================
                # TMT PERTAMA KEPALA SEKOLAH
                # ======================================
                
                from datetime import datetime
                
                tmt_pertama = None
                tahun_pengangkatan = "-"
                tahun_berjalan = "-"
                
                if "TMT" in df_tampil.columns:
                
                    # ubah ke datetime
                    tmt_series = pd.to_datetime(df_tampil["TMT"], errors="coerce")
                
                    # ambil tanggal paling awal
                    tmt_pertama = tmt_series.min()
                
                    if pd.notna(tmt_pertama):
                
                        today = datetime.today()
                
                        selisih = today - tmt_pertama
                
                        tahun = selisih.days // 365
                        bulan = (selisih.days % 365) // 30
                        hari = (selisih.days % 365) % 30
                
                        tahun_pengangkatan = tmt_pertama.strftime("%d-%m-%Y")
                
                        tahun_berjalan = f"{tahun} Tahun {bulan} Bulan {hari} Hari"
                # ======================================================
                # AMBIL TMT PERTAMA (AWAL MENJABAT KEPALA SEKOLAH)
                # ======================================================
                tmt_pertama = None
                
                if "TMT" in df_tampil.columns:
                
                    df_tmt = pd.to_datetime(df_tampil["TMT"], errors="coerce")
                
                    if not df_tmt.dropna().empty:
                        tmt_pertama = df_tmt.min()
                    
                from datetime import datetime

                if tmt_pertama is not None:
                
                    today = datetime.today()
                
                    selisih = today - tmt_pertama
                
                    tahun = selisih.days // 365
                    bulan = (selisih.days % 365) // 30
                
                    tahun_pengangkatan = tmt_pertama.strftime("%d-%m-%Y")
                    tahun_berjalan = f"{tahun} Tahun {bulan} Bulan"
    
                # ==============================
                # FORMAT TANGGAL
                # ==============================
    
                if "TMT" in df_tampil.columns:
                    df_tampil["TMT"] = pd.to_datetime(
                        df_tampil["TMT"], errors="coerce"
                    ).dt.strftime("%d-%m-%Y")
    
                if "TST" in df_tampil.columns:
                    df_tampil["TST"] = pd.to_datetime(
                        df_tampil["TST"], errors="coerce"
                    ).dt.strftime("%d-%m-%Y")
    
                    df_tampil["TST"] = df_tampil["TST"].replace("NaT", "Sekarang")
    
                df_tampil.insert(0, "No", range(1, len(df_tampil) + 1))
    
                st.dataframe(df_tampil, use_container_width=True, hide_index=True)
    
            else:
                st.info("Riwayat dapodik belum tersedia")
    
        else:
            st.warning("Sheet Riwayat_Dapodik tidak ditemukan")
    
    except Exception as e:
    
        st.warning("Riwayat dapodik tidak dapat ditampilkan")

    # =========================================================
    # STATUS REGULATIF
    # =========================================================
    
    try:
        status_regulatif = map_status(row)
    except:
        status_regulatif = "-"
    
    
    # =========================================================
    # CALON PENGGANTI (ANTI ERROR)
    # =========================================================
    
    pengganti = perubahan_kepsek.get(nama, "")
    pengganti_excel = row.get("Calon Pengganti", "")
    
    try:
        pengganti = st.session_state.get("calon_pengganti", "")
    except:
        pass
    
    try:
        pengganti_excel = row.get("Calon Pengganti", "")
    except:
        pass
    
    
    if pengganti:
    
        tampil_colored_field(
            "Calon Pengganti (Yang Dipilih Operator)",
            pengganti,
            bg="#d1e7dd"
        )
    
    else:
    
        # =========================================================
        # TAMPILKAN CALON PENGGANTI YANG TERSIMPAN
        # =========================================================
        
        calon_tersimpan = perubahan_kepsek.get(nama, "")
        
        if calon_tersimpan:
        
            tampil_colored_field(
                "Calon Pengganti",
                calon_tersimpan,
                bg="#d1e7dd"
            )
        
        else:
        
            tampil_colored_field(
                "Calon Pengganti",
                "-",
                bg="#fff3cd"
            )
    
    st.divider()
    # =========================================================
    # ROLE VIEW ONLY
    # =========================================================
    
    role_user = st.session_state.get("role", "")
    
    is_view_only = role_user in ["Kadis", "View"]
    
    if is_view_only:
        st.info("ℹ️ Anda login sebagai **View Only**. Tidak dapat mengubah data.")
    # ============================================
    # 🔒 KUNCI PERIODE 1 DENGAN PENGECUALIAN KHUSUS
    # ============================================

    if status_regulatif == "Aktif Periode Ke 1":
    
        st.markdown("""
        <div style="
            background:#d1e7dd;
            border-left:6px solid #198754;
            padding:18px;
            border-radius:14px;
            font-weight:800;
            color:black;
            font-size:15px;
            box-shadow:0 3px 10px rgba(0,0,0,0.12);
            margin-top:15px;
            margin-bottom:15px;
        ">
            🔒 Kepala Sekolah masih dalam <b>Periode Ke-1</b><br>
            Secara regulatif tidak diperkenankan melakukan penggantian.
        </div>
        """, unsafe_allow_html=True)
    
        st.markdown("### ⚖️ Pengecualian Khusus (Jika Ada)")
    
        alasan_khusus = st.selectbox(
            "Pilih Alasan Pemberhentian",
            [
                "-- Tidak Ada Pengecualian --",
                "Meninggal Dunia",
                "Perkara Hukum",
                "Hukuman Disiplin Berat",
                "Mengundurkan Diri",
                "Mutasi / Promosi Jabatan"
            ],
            key=f"alasan_khusus_{nama}"
        )
    
        # Jika tidak ada pengecualian → stop
        if alasan_khusus == "-- Tidak Ada Pengecualian --":
            st.stop()
    
        # Jika ada pengecualian → tampilkan peringatan keras
        st.error(f"""
        ⚠️ Pengecualian dipilih: **{alasan_khusus}**  
        Sistem mengizinkan proses penggantian karena alasan khusus.
        """)
    
   
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
    
        if data_calon is not None and not data_calon.empty:
    
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
    
        else:
            st.warning("Data calon pengganti tidak ditemukan di SIMPEG.")
        # =========================================================
        # FOTO SIMPEG
        # =========================================================
        foto_url = ambil_foto_simpeg(nip)
        
        if foto_url:
            foto_html = f'<img src="{foto_url}" width="120" style="border-radius:10px;">'
        else:
            foto_html = ""
        if calon != "-- Pilih Calon Pengganti --":

            html_card = f"""
            <div style="
                background:white;
                border-radius:16px;
                padding:20px;
                box-shadow:0 3px 12px rgba(0,0,0,0.15);
                display:flex;
                gap:20px;
            ">
        
            <div>
            <img src="https://cdn-icons-png.flaticon.com/512/149/149071.png" width="110">
            </div>
        
            <div>
        
            <div style="font-size:20px;font-weight:800;margin-bottom:10px;">
            👤 {nama_guru}
            </div>
        
            <div><b>NIP :</b> {nip}</div>
            <div><b>NIK :</b> {nik}</div>
            <div><b>No HP :</b> {nohp}</div>
            <div><b>Jabatan :</b> {jabatan}</div>
            <div><b>Jenis Pegawai :</b> {jenis_pegawai}</div>
        
            <hr>
        
            <div><b>Unit Kerja :</b> {unor}</div>
            <div><b>Cabang Dinas :</b> {cabdis}</div>
            <div><b>Alamat :</b> {alamat}</div>
        
            </div>
        
            </div>
            """
        
            components.html(html_card, height=320)
    # ============================================
    # TOMBOL SIMPAN & RESET PENGGANTI
    # ============================================
    
    colbtn1, colbtn2 = st.columns(2)
    
    # SIMPAN PENGGANTI
    with colbtn1:
    
        if st.button("💾 Simpan Pengganti", use_container_width=True):

            if calon == "-- Pilih Calon Pengganti --":
                st.error("⚠️ Pilih calon pengganti terlebih dahulu")
        
            else:
        
                perubahan_kepsek[nama] = calon
        
                save_perubahan(perubahan_kepsek, df_ks, df_guru)
        
                st.success("✅ Pengganti berhasil disimpan")
        
                st.rerun()
    
    
    # RESET KE KEPSEK LAMA
    with colbtn2:
    
        if st.button("↩️ Kembalikan ke Kepsek Lama", use_container_width=True):

            if nama in perubahan_kepsek:
        
                del perubahan_kepsek[nama]
        
                save_perubahan(perubahan_kepsek, df_ks, df_guru)
        
                st.success("✅ Data pengganti dihapus")
        
                st.rerun()
        
            else:
                st.warning("Belum ada pengganti tersimpan")

# ============================================
# KOLOM TOMBOL SIMPAN & RESET (DINAMIS)
# ============================================

calon_tersimpan = perubahan_kepsek.get(nama, None)

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
# HALAMAN UPDATE RIWAYAT KEPSEK (UPDATE data KASEK)
# =========================================================
def page_update():
    st.markdown("## 📝 Update Riwayat Kepala Sekolah")

    if st.session_state.selected_sekolah is None:
        st.warning("⚠️ Pilih sekolah dulu dari menu sekolah.")
        st.stop()

    nama_sekolah = st.session_state.selected_sekolah

    st.info(f"🏫 Sekolah: **{nama_sekolah}**")

    nama_kepsek = st.text_input("Nama Kepala Sekolah")
    nip = st.text_input("NIP Kepala Sekolah")
    mulai = st.text_input("Mulai Menjabat (contoh: 2019 atau 01-01-2019)")
    selesai = st.text_input("Selesai Menjabat (kosongkan jika masih menjabat)")
    ket = st.text_area("Keterangan (opsional)")

    if st.button("💾 Simpan Riwayat", use_container_width=True):
        if nama_kepsek.strip() == "" or mulai.strip() == "":
            st.error("❌ Nama Kepsek dan Mulai Menjabat wajib diisi!")
        else:
            simpan_riwayat_baru(
                nama_sekolah=nama_sekolah,
                nama_kepsek=nama_kepsek,
                nip=nip,
                mulai=mulai,
                selesai=selesai,
                ket=ket
            )
            st.success("✅ Riwayat jabatan berhasil disimpan ke Database!")
            st.rerun()

    st.divider()
    st.markdown("### 📌 Riwayat Jabatan Tersimpan")

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

elif st.session_state.page == "list_status":
    set_bg("dashboard.jpg")
    page_list_status()

elif st.session_state.page == "sekolah":
    set_bg("dashboard.jpg")
    page_sekolah()

elif st.session_state.page == "detail":
    set_bg("dashboard.jpg")
    page_detail()

elif st.session_state.page == "rekap":
    set_bg("dashboard.jpg")
    page_rekap()

elif st.session_state.page == "update":
    set_bg("dashboard.jpg")
    page_update()

# =========================================================
# FOOTER HANYA DI DASHBOARD UTAMA
# =========================================================
if st.session_state.page == "cabdin":

    st.divider()

    st.markdown("## ⚖️ Dasar Hukum Penugasan Kepala Sekolah")

    components.html("""
    <div style="font-family: Arial, sans-serif;">

        <div style="
            background:#ffffff;
            padding:22px;
            border-radius:16px;
            border-left:6px solid #198754;
            box-shadow:0 3px 10px rgba(0,0,0,0.12);
            margin-bottom:20px;
        ">
            <div style="font-size:17px; font-weight:800; color:#198754; margin-bottom:10px;">
                📌 Ringkasan Pokok Ketentuan Permendikdasmen No. 7 Tahun 2025
            </div>

            <ol style="color:#333; font-size:14px; line-height:1.8; padding-left:18px;">
                <li>Kepala Sekolah ditugaskan maksimal <b>2 (dua) periode</b>.</li>
                <li><b>1 (satu) periode = 4 (empat) tahun</b>.</li>
                <li>Kepala Sekolah yang telah menjabat <b>lebih dari 2 periode wajib diberhentikan</b>.</li>
                <li>Kepala Sekolah Periode 1 dapat diperpanjang menjadi Periode 2 apabila memenuhi syarat termasuk <b>BCKS</b>.</li>
                <li>Kepala Sekolah wajib dievaluasi secara berkala.</li>
                <li>Jika terjadi kekosongan jabatan, dapat ditunjuk <b>Plt</b>.</li>
                <li>Penugasan Kepala Sekolah merupakan tugas tambahan ASN.</li>
            </ol>
        </div>

        <div style="
            background:#ffffff;
            padding:18px;
            border-radius:14px;
            border-left:6px solid #ffc107;
            box-shadow:0 3px 10px rgba(0,0,0,0.12);
            font-size:14px;
            color:#333;
            font-weight:600;
        ">
            ✅ Dashboard ini disusun berdasarkan pemetaan status regulatif sesuai Permendikdasmen No. 7 Tahun 2025.
        </div>

    </div>
    """, height=420)

    st.divider()

    st.markdown("""
    <div style="text-align:center; font-weight:800; font-size:16px;">
    © 2026 SMART-KS • Sistem Monitoring dan Analisis Riwayat Tugas - Kepala Sekolah
    </div>
    """, unsafe_allow_html=True)
























