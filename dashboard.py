import streamlit as st
import pandas as pd
import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO


# =========================================================
# KONFIGURASI APLIKASI
# =========================================================
st.set_page_config(page_title="Dashboard Kepala Sekolah", layout="wide")

DATA_SAVE = "perubahan_kepsek.xlsx"
DATA_FILE = "data_kepala_sekolah.xlsx"


# =========================================================
# SESSION STATE INIT
# =========================================================
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.login = False
    st.session_state.role = None
    st.session_state.page = "cabdin"
    st.session_state.selected_cabdin = None
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
    df = pd.DataFrame([{"Nama Sekolah": k, "Calon Pengganti": v} for k, v in data_dict.items()])
    df.to_excel(DATA_SAVE, index=False)


perubahan_kepsek = load_perubahan()


# =========================================================
# 🔢 FUNGSI URUT CABDIN
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
    "Nama Kepala Sekolah ": "Nama Kepala Sekolah",

    "Keterangan": "Keterangan Akhir",
    "KETERANGAN": "Keterangan Akhir",
    "KETERANGAN AKHIR": "Keterangan Akhir",
    "Keteranngan Akhir": "Keterangan Akhir",
    "Keterangan Akhir ": "Keterangan Akhir",

    "Cabang Dinas ": "Cabang Dinas",
    "CABANG DINAS": "Cabang Dinas",

    "Ket. Sertifikat BCKS": "Ket Sertifikat BCKS",
    "Ket Sertifikat BCKS ": "Ket Sertifikat BCKS",
    "Ket. Sertifikat": "Ket Sertifikat BCKS",
    "Sertifikat BCKS": "Ket Sertifikat BCKS",

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

df_ks.rename(columns=rename_map_ks, inplace=True)
df_guru.rename(columns=rename_map_guru, inplace=True)

# hapus kolom duplikat
df_ks = df_ks.loc[:, ~df_ks.columns.duplicated()]
df_guru = df_guru.loc[:, ~df_guru.columns.duplicated()]

# paksa kolom wajib
if "Masa Periode Sesuai KSPSTK" not in df_ks.columns:
    df_ks["Masa Periode Sesuai KSPSTK"] = ""

if "Keterangan Akhir" not in df_ks.columns:
    df_ks["Keterangan Akhir"] = ""

if "Nama Kepala Sekolah" not in df_ks.columns:
    df_ks["Nama Kepala Sekolah"] = ""

# normalisasi nama sekolah
df_ks["Nama Sekolah"] = (
    df_ks["Nama Sekolah"]
    .astype(str)
    .str.replace("\xa0", " ", regex=False)
    .str.strip()
)

# guru list
if "NAMA GURU" not in df_guru.columns:
    st.error("❌ Kolom 'NAMA GURU' tidak ditemukan di sheet GURU_SIMPEG")
    st.stop()

guru_list = sorted(df_guru["NAMA GURU"].astype(str).dropna().unique())


# =========================================================
# MAP STATUS
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
# FILTER SIDEBAR
# =========================================================
st.sidebar.header("🔍 Filter & Pencarian")

search_nama = st.sidebar.text_input("Cari Nama Kepala Sekolah")
search_sekolah = st.sidebar.text_input("Cari Nama Sekolah")

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
        df = df[df["Nama Kepala Sekolah"].astype(str).str.contains(search_nama, case=False, na=False)]

    if search_sekolah:
        df = df[df["Nama Sekolah"].astype(str).str.contains(search_sekolah, case=False, na=False)]

    return df


# =========================================================
# CSS CARD SEKOLAH
# =========================================================
st.markdown("""
<style>
div[data-testid="stButton"] > button {
    border-radius: 14px !important;
    height: 110px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
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
# 🔍 PENCARIAN GURU SIMPEG
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
# HALAMAN SEKOLAH
# =========================================================
def page_sekolah():

    if st.session_state.selected_cabdin is None:
        st.warning("⚠️ Cabang Dinas belum dipilih.")
        st.session_state.page = "cabdin"
        st.rerun()

    col_a, col_b = st.columns([1, 6])

    with col_a:
        if st.button("⬅️ Kembali", key="btn_back_sekolah", use_container_width=True):
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

    # ===============================
    # REKAP STATUS CABDIN
    # ===============================
    st.markdown("## 📌 Rekap Status Kepala Sekolah Cabang Dinas Ini")

    df_cab_rekap = df_cab.copy()
    df_cab_rekap["Status Regulatif"] = df_cab_rekap.apply(map_status, axis=1)

    rekap_status = (
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

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Periode 1", int(rekap_status["Aktif Periode 1"]))
    col2.metric("Periode 2", int(rekap_status["Aktif Periode 2"]))
    col3.metric(">2 Periode", int(rekap_status["Lebih dari 2 Periode"]))
    col4.metric("Plt", int(rekap_status["Plt"]))

    total_bisa = int(rekap_status["Aktif Periode 2"]) + int(rekap_status["Lebih dari 2 Periode"])
    col5.metric("Bisa Diberhentikan", total_bisa)

    col6.metric("Lainnya", int(rekap_status["Lainnya"]))

    st.divider()

    # ===============================
    # GRID SEKOLAH
    # ===============================
    cols = st.columns(4)
    idx = 0

    for _, row in df_cab.iterrows():
        nama_sekolah = str(row.get("Nama Sekolah", "-")).strip()

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
            if st.button(f"{warna} {nama_sekolah}", key=f"sekolah_{idx}", use_container_width=True):
                st.session_state.selected_sekolah = nama_sekolah
                st.session_state.page = "detail"
                st.rerun()

        idx += 1


# =========================================================
# HALAMAN DETAIL SEKOLAH
# =========================================================
def page_detail():

    if st.session_state.selected_sekolah is None:
        st.warning("⚠️ Sekolah belum dipilih.")
        st.session_state.page = "sekolah"
        st.rerun()

    col_a, col_b = st.columns([1, 6])

    with col_a:
        if st.button("⬅️ Kembali", key="btn_back_detail", use_container_width=True):
            st.session_state.page = "sekolah"
            st.session_state.selected_sekolah = None
            st.rerun()

    with col_b:
        st.subheader(f"📄 Detail Sekolah: {st.session_state.selected_sekolah}")

    nama = (
        str(st.session_state.selected_sekolah)
        .replace("\xa0", " ")
        .strip()
    )

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
    st.markdown("### 📝 Data Lengkap (Sesuai Excel)")

    data_items = list(row.items())

    pengganti = perubahan_kepsek.get(nama, "-")
    data_items.append(("Calon Pengganti jika Sudah Harus di Berhentikan", pengganti))

    left_items = data_items[0::2]
    right_items = data_items[1::2]

    col_left, col_right = st.columns(2)

    with col_left:
        for col, val in left_items:
            st.markdown(f"**{col}:** {val}")

    with col_right:
        for col, val in right_items:
            st.markdown(f"**{col}:** {val}")

    st.divider()

    # ===============================
    # SIMPAN PENGGANTI
    # ===============================
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

    if calon_tersimpan:
        st.info(f"👤 Pengganti Saat Ini: **{calon_tersimpan}**")

        if not is_view_only:
            if st.button("✏️ Kembalikan ke Kepala Sekolah Lama", key="btn_kembalikan", use_container_width=True):
                perubahan_kepsek.pop(nama, None)
                save_perubahan(perubahan_kepsek)
                st.success("🔄 Berhasil dikembalikan")
                st.rerun()


# =========================================================
# HALAMAN REKAP
# =========================================================
def page_rekap():

    col_back, col_title = st.columns([1, 10])

    with col_back:
        if st.button("⬅️", key="btn_back_rekap", use_container_width=True):
            st.session_state.page = "cabdin"
            st.rerun()

    with col_title:
        st.markdown("## 📌 Rekap Kepala Sekolah Bisa di Berhentikan")

    st.divider()

    df_rekap = df_ks.copy()
    df_rekap["Status Regulatif"] = df_rekap.apply(map_status, axis=1)

    df_bisa = df_rekap[df_rekap["Status Regulatif"].isin(["Aktif Periode 2", "Lebih dari 2 Periode"])].copy()

    if df_bisa.empty:
        st.warning("⚠️ Tidak ada data Kepala Sekolah Bisa di Berhentikan.")
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
    pilih_sekolah = st.selectbox("📄 Pilih Sekolah untuk lihat detail", sekolah_opsi, key="rekap_pilih_sekolah")

    if st.button("📌 Lihat Detail Sekolah", key="btn_detail_rekap", use_container_width=True):
        st.session_state.selected_sekolah = pilih_sekolah
        st.session_state.page = "detail"
        st.rerun()


# =========================================================
# HALAMAN CABDIN
# =========================================================
def page_cabdin():

    col1, col2, col3, col4, col5 = st.columns([5, 2, 2, 2, 2])

    with col1:
        st.markdown("## 📊 Dashboard Kepala Sekolah")

    with col2:
        if st.button("🔄 Refresh Data SIMPEG", key="btn_refresh_simpeg", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Data SIMPEG diperbarui")
            st.rerun()

    with col3:
        if st.button("🔄 Refresh Data Kepsek", key="btn_refresh_kepsek", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Data Kepala Sekolah diperbarui")
            st.rerun()

    with col4:
        if st.button("📌 Rekap", key="btn_ke_rekap", use_container_width=True):
            st.session_state.page = "rekap"
            st.rerun()

    with col5:
        if st.button("🚪 Logout", key="btn_logout", use_container_width=True):
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


# =========================================================
# LOGIN PAGE
# =========================================================
if not st.session_state.login:
    st.markdown("## 🔐 Login Dashboard Kepala Sekolah")

    col1, col2, col3 = st.columns([2, 3, 2])
    with col2:
        username = st.text_input("👤 Username")
        password = st.text_input("🔑 Password", type="password")

        if st.button("🔓 Login", key="btn_login", use_container_width=True):
            if username in USERS and USERS[username]["password"] == password:
                st.session_state.login = True
                st.session_state.role = USERS[username]["role"]
                st.success(f"✅ Login berhasil sebagai **{st.session_state.role}**")
                st.rerun()
            else:
                st.error("❌ Username atau Password salah")

    st.stop()


# =========================================================
# INFO LOGIN
# =========================================================
st.caption(f"👤 Login sebagai: **{st.session_state.role}**")
st.divider()


# =========================================================
# ROUTING FINAL
# =========================================================
if st.session_state.page == "cabdin":
    page_cabdin()

elif st.session_state.page == "sekolah":
    page_sekolah()

elif st.session_state.page == "detail":
    page_detail()

elif st.session_state.page == "rekap":
    page_rekap()

else:
    st.session_state.page = "cabdin"
    st.rerun()


# =========================================================
# FOOTER
# =========================================================
st.divider()
st.caption("Dashboard Kepala Sekolah • MHD. ARIPIN RITONGA, S.Kom")
