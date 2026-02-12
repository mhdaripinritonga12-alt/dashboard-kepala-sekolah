import streamlit as st
import pandas as pd
import os
import re   # ✅ TAMBAHAN (UNTUK HAPUS HTML TAG)

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

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
# FUNGSI SIMPAN & LOAD PENGGANTI
# =========================================================
def load_perubahan():
    if os.path.exists(DATA_SAVE):
        try:
            df = pd.read_excel(DATA_SAVE)
            if {"Nama Sekolah", "Calon Pengganti"}.issubset(df.columns):
                return dict(zip(df["Nama Sekolah"], df["Calon Pengganti"]))
        except:
            return {}
    return {}

def save_perubahan(data_dict):
    df = pd.DataFrame([{"Nama Sekolah": k, "Calon Pengganti": v} for k, v in data_dict.items()])
    df.to_excel(DATA_SAVE, index=False)

perubahan_kepsek = load_perubahan()

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
df_guru.rename(columns=rename_map_guru, inplace=True)

# =========================================================
# ✅ TAMBAHAN FIX BARU (ISI NaN JADI STRING KOSONG)
# =========================================================
df_ks = df_ks.fillna("")
df_guru = df_guru.fillna("")
# =========================================================
# ✅ FIX FINAL MERGE CELL EXCEL (RIWAYAT DAPODIK)
# =========================================================
if "Riwayat Dapodik" in df_ks.columns:
    df_ks["Riwayat Dapodik"] = df_ks["Riwayat Dapodik"].replace("", pd.NA)
    df_ks["Riwayat Dapodik"] = df_ks["Riwayat Dapodik"].fillna(method="ffill")
    df_ks["Riwayat Dapodik"] = df_ks["Riwayat Dapodik"].fillna("")


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

    if "plt" in masa or "plt" in jabatan:
        return "Plt"
    if "periode 1" in masa or "periode 1" in ket_akhir:
        return "Aktif Periode Ke 1"
    if "periode 2" in masa or "periode 2" in ket_akhir:
        return "Aktif Periode Ke 2"
    if "lebih dari 2" in masa or ">2" in masa or "lebih dari 2" in ket_akhir or ">2" in ket_akhir:
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

# =========================================================
# LOGIN PAGE
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
# PENCARIAN SIMPEG
# =========================================================
with st.expander("🔍 Pencarian Guru (SIMPEG)", expanded=False):
    keyword = st.text_input("Ketik Nama Guru atau NIP", placeholder="contoh: Mhd Aripin Ritonga / 1994")

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
    ket_bcks = str(ket_bcks).lower()

    tampil31 = False
    tampil32 = False

    if status in ["Aktif Periode Ke 2", "Lebih dari 2 Periode", "Plt"]:
        tampil31 = True

    if status == "Aktif Periode Ke 1":
        tampil32 = True

    if status == "Lebih dari 2 Periode" and ("belum" in ket_bcks or ket_bcks.strip() == "" or ket_bcks.strip() == "nan"):
        tampil31 = True
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
    col1, col2, col3, col4, col5 = st.columns([5, 2, 2, 2, 2])

    with col1:
        st.markdown("## 📊 Dashboard Kepala Sekolah")

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

    st.markdown("## 📌 Rekap Status Kepala Sekolah (Provinsi)")

    colx1, colx2, colx3, colx4, colx5 = st.columns(5)
    colx1.metric("Aktif Periode Ke 1", jumlah_p1)
    colx2.metric("Aktif Periode Ke 2", jumlah_p2)
    colx3.metric("Lebih 2 Periode", jumlah_lebih2)
    colx4.metric("Kasek Plt", jumlah_plt)
    colx5.metric("Bisa Diberhentikan", total_bisa_diberhentikan)

    st.divider()

    st.subheader("🏢 Cabang Dinas Pendidikan Wilayah")

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
        st.subheader(f"🏫 Daftar Sekolah — {st.session_state.selected_cabdin}")

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

    st.markdown("### 📌 Rekap Status Kepala Sekolah Cabang Dinas Ini")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Aktif Periode Ke 1", jumlah_p1)
    col2.metric("Aktif Periode Ke 2", jumlah_p2)
    col3.metric("Lebih 2 Periode", jumlah_lebih2)
    col4.metric("Plt", jumlah_plt)
    col5.metric("Bisa Diberhentikan", total_bisa)

    st.divider()

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
# FIELD WARNA
# =========================================================
def tampil_colored_field(label, value, bg="#f1f1f1", text_color="black"):
    st.markdown(f"""
    <div style="padding:10px; border-radius:10px; background:{bg}; margin-bottom:8px;">
        <b>{label}:</b>
        <span style="color:{text_color}; font-weight:700;"> {value}</span>
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

    # =========================================================
    # ✅ TAMBAHAN BARU: TAMPILKAN KOLOM PERMENDIKDASMEN + RIWAYAT DAPODIK
    # =========================================================
    st.divider()
    st.markdown("## 📌 Data Tambahan Sesuai Tabel Excel")

    tampil_colored_field(
        "Permendikdasmen No 7 Tahun 2025 Maksimal 2 Periode",
        row.get("Permendikdasmen No 7 Tahun 2025 Maksimal 2 Periode ( 1 Periode 4 Tahun )", "-"),
        bg="#e2e3ff"
    )

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

    pengganti_excel = row.get("Calon Pengganti jika Sudah Harus di Berhentikan", "-")
    pengganti = perubahan_kepsek.get(nama, "")

    st.markdown("## 👤 Calon Pengganti Kepala Sekolah")

    if pengganti:
        tampil_colored_field("Calon Pengganti (Yang Dipilih Operator)", pengganti, bg="#d1e7dd")
    else:
        tampil_colored_field("Calon Pengganti", pengganti_excel, bg="#fff3cd")

    st.divider()

    tampil_pasal_permendikdasmen(status_regulatif, ket_bcks)

    st.divider()

    is_view_only = st.session_state.role in ["Kadis", "View"]

    if is_view_only:
        st.info("ℹ️ Anda login sebagai **View Only**. Tidak dapat mengubah data.")
        return

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
            kol_cabdis = cari_kolom(data_calon, ["CABANG DINAS", "CABDIS", "WILAYAH", "KCD"])
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
            nama_guru = bersihkan(calon_row.get(kol_nama, "-")) if kol_nama else "-"

            html_card = f"""
            <div style="
                background: white;
                border-radius: 18px;
                padding: 18px;
                border-left: 8px solid #0d6efd;
                box-shadow: 0 3px 10px rgba(0,0,0,0.12);
                margin-top: 10px;
                margin-bottom: 10px;
            ">
                <h3 style="margin:0;">👤 {nama_guru}</h3>
                <hr>

                <p style="margin:6px 0;"><b>NIP:</b> {nip}</p>
                <p style="margin:6px 0;"><b>NIK:</b> {nik}</p>
                <p style="margin:6px 0;"><b>No HP:</b> {nohp}</p>
                <p style="margin:6px 0;"><b>Jabatan:</b> {jabatan}</p>
                <p style="margin:6px 0;"><b>Jenis Pegawai:</b> {jenis_pegawai}</p>

                <hr>
                <p style="margin:6px 0;"><b>UNOR / Unit Kerja:</b> {unor}</p>
                <p style="margin:6px 0;"><b>Cabang Dinas:</b> {cabdis}</p>
                <p style="margin:6px 0;"><b>Alamat:</b> {alamat}</p>
            </div>
            """

            st.markdown(html_card, unsafe_allow_html=True)

    colbtn1, colbtn2 = st.columns(2)

    with colbtn1:
        if st.button("💾 Simpan Pengganti", key="btn_simpan_pengganti", use_container_width=True):
            if calon == "-- Pilih Calon Pengganti --":
                st.warning("⚠️ Pilih calon pengganti terlebih dahulu.")
            else:
                perubahan_kepsek[nama] = calon
                save_perubahan(perubahan_kepsek)
                st.success(f"✅ Diganti dengan: {calon}")
                st.rerun()

    with colbtn2:
        if st.button("↩️ Kembalikan ke Kepala Sekolah Awal", key="btn_reset_pengganti", use_container_width=True):
            if nama in perubahan_kepsek:
                del perubahan_kepsek[nama]
                save_perubahan(perubahan_kepsek)

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
# ROUTING UTAMA
# =========================================================
if st.session_state.page == "cabdin":
    page_cabdin()

elif st.session_state.page == "sekolah":
    page_sekolah()

elif st.session_state.page == "detail":
    page_detail()

elif st.session_state.page == "rekap":
    page_rekap()

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
st.caption("Dashboard Kepala Sekolah • MHD. ARIPIN RITONGA, S.Kom")


