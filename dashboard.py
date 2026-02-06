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
def badge(text, warna_bg, warna_text="white"):
    return f"""
    <span style="
        padding:6px 12px;
        border-radius:10px;
        font-weight:600;
        color:{warna_text};
        background:{warna_bg};
        font-size:13px;
        display:inline-block;
    ">
        {text}
    </span>
    """



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
# HEADER + REFRESH + LOGOUT (HANYA HALAMAN CABDIN)
# =========================================================
elif st.session_state.page == "rekap":

    # ==========================
    # HEADER + TOMBOL BACK (LOGO SAJA)
    # ==========================
    col_back, col_title = st.columns([1, 10])

    with col_back:
        if st.button("⬅️", use_container_width=True):
            st.session_state.page = "cabdin"
            st.rerun()

    with col_title:
        st.markdown("## 📌 Rekap Kepala Sekolah Bisa di Berhentikan")

    st.divider()

    # ==========================
    # FILTER DATA YANG BISA DI BERHENTIKAN
    # ==========================
    df_rekap = df_ks.copy()
    df_rekap["Status Regulatif"] = df_rekap.apply(map_status, axis=1)

    df_bisa = df_rekap[df_rekap["Status Regulatif"].str.lower().str.contains("bisa")]

    if df_bisa.empty:
        st.warning("Tidak ada data Kepala Sekolah yang Bisa di Berhentikan.")
        st.stop()

    # ==========================
    # TAMBAHKAN PENGGANTI DARI FILE PERUBAHAN
    # ==========================
    def ambil_pengganti(nama_sekolah):
        return perubahan_kepsek.get(nama_sekolah, "-")

    df_bisa["Calon Pengganti"] = df_bisa["Nama Sekolah"].apply(ambil_pengganti)

    # ==========================
    # TAMPILKAN TABEL REKAP
    # ==========================
    tampil = df_bisa[[
        "Cabang Dinas",
        "Nama Sekolah",
        "Nama Kepala Sekolah",
        "Keterangan Jabatan",
        "Ket Sertifikat BCKS",
        "Calon Pengganti"
    ]].copy()

    st.dataframe(tampil, use_container_width=True, hide_index=True)

    st.divider()

    st.info("Klik nama sekolah di menu Detail untuk mengubah calon pengganti.")


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
Kembalikan ke Kepala Sekolah Lama
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
































































