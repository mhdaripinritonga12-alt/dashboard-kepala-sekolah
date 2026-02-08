import streamlit as st
import pandas as pd
import os

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

# =========================================================
# USER LOGIN
# =========================================================
USERS = {
    "operator": {"password": "operator123", "role": "Operator"},
    "kabidptk": {"password": "kabid123", "role": "Kabid"},
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

# hapus kolom duplikat
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
# URUT CABDIN
# =========================================================
def urutkan_cabdin(cabdin_list):
    def ambil_angka(text):
        angka = "".join(filter(str.isdigit, str(text)))
        return int(angka) if angka else 999
    return sorted(cabdin_list, key=ambil_angka)

# =========================================================
# LOGIKA STATUS
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

    if "diberhentikan" in ket_akhir:
        return "Harus Diberhentikan"

    return "Lainnya"

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
        if st.button("📌 Rekap", use_container_width=True):
            st.session_state.page = "rekap"
            st.rerun()

    with col5:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.login = False
            st.session_state.role = None
            st.session_state.page = "cabdin"
            st.session_state.selected_cabdin = None
            st.session_state.selected_sekolah = None
            st.rerun()

    st.divider()
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

    st.divider()
    st.markdown("## ⚖️ Permendikdasmen No 7 Tahun 2025")

    st.markdown("""
    <div style="background:#0d6efd; padding:14px; border-radius:14px; color:white; font-size:16px; font-weight:800;">
        Permendikdasmen Nomor 7 Tahun 2025 (Maksimal 2 Periode / 1 Periode 4 Tahun)
    </div>
    """, unsafe_allow_html=True)

    st.info("""
    **Pokok Ketentuan:**
    1. Kepala Sekolah diberikan tugas maksimal **2 (dua) periode**
    2. Satu periode = **4 (empat) tahun**
    3. Kepala Sekolah yang telah menjabat **Lebih dari 2 periode wajib diberhentikan**
    4. Kepala Sekolah periode 1 dapat diperpanjang jika memiliki Sertifikat BCKS (Pasal 32)
    5. Sekolah tanpa Kepala Sekolah definitif wajib segera diisi (Plt/Definitif)
    """)

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

    cols = st.columns(4)
    idx = 0

    for _, row in df_cab.iterrows():
        nama_sekolah = str(row.get("Nama Sekolah", "-"))

        masa = str(row.get("Masa Periode Sesuai KSPSTK", "")).lower()
        ket_akhir = str(row.get("Keterangan Akhir", "")).lower()

        if "periode 1" in masa:
            warna = "🟦"
        elif "periode 2" in masa:
            warna = "🟨"
        elif "lebih dari 2" in masa or ">2" in masa or "diberhentikan" in ket_akhir:
            warna = "🟥"
        elif "plt" in masa:
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
# FUNGSI WARNA TEXT FIELD DI DETAIL
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
    st.markdown("## 📝 Data Lengkap (Sumber Dapodikdasmen dan SIM KSPSTK)")

    # =========================================================
    # WARNA FIELD SESUAI PERMINTAAN
    # =========================================================
    ket_akhir = str(row.get("Keterangan Akhir", "-")).lower()
    jabatan = str(row.get("Keterangan Jabatan", "-")).lower()
    bcks = str(row.get("Ket Sertifikat BCKS", "-")).lower()

    # 1) Keterangan Akhir
    bg_ket = "#dbeeff"  # biru muda
    if "periode 2" in ket_akhir:
        bg_ket = "#fff3cd"  # kuning
    if "lebih dari 2" in ket_akhir or ">2" in ket_akhir:
        bg_ket = "#f8d7da"  # merah muda

    # 2) Keterangan Jabatan
    bg_jabatan = "#dbeeff"  # definitif biru muda
    if "plt" in jabatan:
        bg_jabatan = "#d1e7dd"  # hijau

    # 3) Ket Sertifikat BCKS
    bg_bcks = "#dbeeff"  # sudah biru muda
    if "belum" in bcks or "tidak" in bcks:
        bg_bcks = "#d1e7dd"  # hijau muda

    # =========================================================
    # DATA DUA KOLOM
    # =========================================================
    col_left, col_right = st.columns(2)

    with col_left:
        tampil_colored_field("NO", row.get("NO", "-"))
        tampil_colored_field("Nama Kepala Sekolah", row.get("Nama Kepala Sekolah", "-"))
        tampil_colored_field("Status", row.get("Status", "-"))
        tampil_colored_field("Cabang Dinas", row.get("Cabang Dinas", "-"))
        tampil_colored_field("Ket Sertifikat BCKS", row.get("Ket Sertifikat BCKS", "-"), bg=bg_bcks)
        tampil_colored_field("Tahun Berjalan", row.get("Tahun Berjalan", "-"))

        tampil_colored_field("Permendikdasmen No 7 Tahun 2025 Maksimal 2 Periode (1 Periode 4 Tahun)",
                             row.get("Permendikdasmen No 7 Tahun 2025 Maksimal 2 Periode (1 Periode 4 Tahun)", "-"))

        tampil_colored_field("Keterangan Akhir", row.get("Keterangan Akhir", "-"), bg=bg_ket)

    with col_right:
        tampil_colored_field("Nama Sekolah", row.get("Nama Sekolah", "-"))
        tampil_colored_field("Jenjang", row.get("Jenjang", "-"))
        tampil_colored_field("Kabupaten", row.get("Kabupaten", "-"))
        tampil_colored_field("Keterangan Jabatan", row.get("Keterangan Jabatan", "-"), bg=bg_jabatan)
        tampil_colored_field("Tahun Pengangkatan", row.get("Tahun Pengangkatan", "-"))
        tampil_colored_field("Masa Periode Sesuai KSPSTK", row.get("Masa Periode Sesuai KSPSTK", "-"))
        tampil_colored_field("Riwayat Dapodik", row.get("Riwayat Dapodik", "-"))

        pengganti = perubahan_kepsek.get(nama, "-")
        tampil_colored_field("Calon Pengganti jika Sudah Harus di Berhentikan", pengganti)

    st.divider()

    # =========================================================
    # SIMPAN PENGGANTI
    # =========================================================
    is_view_only = st.session_state.role in ["Kadis", "View"]
    calon_tersimpan = perubahan_kepsek.get(nama)

    if is_view_only:
        st.info("ℹ️ Anda login sebagai **View Only**. Tidak dapat mengubah data.")
    else:
        calon = st.selectbox("👤 Pilih Calon Pengganti (SIMPEG)", guru_list, key=f"calon_{nama}")

        if st.button("💾 Simpan Pengganti", key="btn_simpan_pengganti", use_container_width=True):
            perubahan_kepsek[nama] = calon
            save_perubahan(perubahan_kepsek)
            st.success(f"✅ Diganti dengan: {calon}")
            st.rerun()

    # =========================================================
    # KEMBALIKAN KEPSEK LAMA
    # =========================================================
    if calon_tersimpan:
        st.info(f"👤 Pengganti Saat Ini: **{calon_tersimpan}**")

        if not is_view_only:
            if st.button("✏️ Kembalikan ke Kepala Sekolah Lama", key="btn_kembali_lama", use_container_width=True):
                perubahan_kepsek.pop(nama, None)
                save_perubahan(perubahan_kepsek)
                st.success("🔄 Berhasil dikembalikan")
                st.rerun()

# =========================================================
# HALAMAN REKAP
# =========================================================
def page_rekap():
    col_a, col_b, col_c = st.columns([1, 6, 1])

    with col_a:
        if st.button("🏠", key="home_rekap"):
            st.session_state.page = "cabdin"
            st.rerun()

    with col_b:
        st.markdown("## 📌 Rekap Kepala Sekolah Bisa Diberhentikan")

    with col_c:
        if st.button("⬅️", key="back_rekap"):
            st.session_state.page = "cabdin"
            st.rerun()

    st.divider()

    df_rekap = df_ks.copy()
    df_rekap["Status Regulatif"] = df_rekap.apply(map_status, axis=1)

    df_bisa = df_rekap[df_rekap["Status Regulatif"].isin(["Aktif Periode 2", "Lebih dari 2 Periode"])].copy()

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

    sekolah_opsi = df_bisa["Nama Sekolah"].unique().tolist()
    pilih = st.selectbox("📄 Pilih Sekolah untuk lihat detail", sekolah_opsi, key="rekap_pilih")

    if st.button("📌 Lihat Detail Sekolah", key="rekap_btn_detail", use_container_width=True):
        st.session_state.selected_sekolah = pilih
        st.session_state.page = "detail"
        st.rerun()

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
st.caption("Dashboard Kepala Sekolah • MHD. ARIPIN RITONGA, S.Kom")

