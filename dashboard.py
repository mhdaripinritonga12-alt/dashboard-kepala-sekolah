import streamlit as st
import pandas as pd
import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

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
# SESSION STATE DEFAULT
# =========================================================
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.login = False
    st.session_state.role = None
    st.session_state.page = "cabdin"
    st.session_state.selected_cabdin = None
    st.session_state.selected_sekolah = None

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
# LOGIN USER
# =========================================================
USERS = {
    "operator": {"password": "operator123", "role": "Operator"},
    "kabidptk": {"password": "kabid123", "role": "Kabid"},
    "kadis": {"password": "kadis123", "role": "Kadis"},
    "viewer": {"password": "viewer123", "role": "View"},
}

# =========================================================
# FUNGSI LOAD & SAVE PERUBAHAN
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
# BADGE HTML
# =========================================================
def badge(text, bg, color="white"):
    return f"""
    <span style="
        background:{bg};
        color:{color};
        padding:6px 12px;
        border-radius:10px;
        font-weight:700;
        font-size:13px;
        display:inline-block;
        margin-right:6px;
        margin-bottom:6px;
    ">
        {text}
    </span>
    """

# =========================================================
# URUT CABDIN
# =========================================================
def urutkan_cabdin(cabdin_list):
    def ambil_angka(text):
        angka = "".join(filter(str.isdigit, str(text)))
        return int(angka) if angka else 999
    return sorted(cabdin_list, key=ambil_angka)

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
    "Keterangan Akhir ": "Keterangan Akhir",

    "Cabang Dinas ": "Cabang Dinas",
    "CABANG DINAS": "Cabang Dinas",

    "Ket. Sertifikat BCKS": "Ket Sertifikat BCKS",
    "Ket Sertifikat BCKS ": "Ket Sertifikat BCKS",
    "Sertifikat BCKS": "Ket Sertifikat BCKS",

    "Masa Periode Sesuai KSPSTK": "Masa Periode Sesuai KSPSTK",
    "Masa Periode Sesuai KSPSTK ": "Masa Periode Sesuai KSPSTK",
}

rename_map_guru = {
    "NAMA GURU ": "NAMA GURU",
    "Nama Guru": "NAMA GURU",
    "Nama guru": "NAMA GURU",
    "NAMA": "NAMA GURU",

    "NIP ": "NIP",
    "NIP.": "NIP",
    "NIP GURU": "NIP",
}

df_ks.rename(columns=rename_map_ks, inplace=True)
df_guru.rename(columns=rename_map_guru, inplace=True)

# FIX DUPLIKAT KOLOM
df_ks = df_ks.loc[:, ~df_ks.columns.duplicated()]
df_guru = df_guru.loc[:, ~df_guru.columns.duplicated()]

# PAKSA KOLOM WAJIB ADA
for col in ["Nama Sekolah", "Nama Kepala Sekolah", "Cabang Dinas", "Jenjang", "Keterangan Akhir", "Masa Periode Sesuai KSPSTK"]:
    if col not in df_ks.columns:
        df_ks[col] = ""

# NORMALISASI NAMA SEKOLAH
df_ks["Nama Sekolah"] = (
    df_ks["Nama Sekolah"]
    .astype(str)
    .str.replace("\xa0", " ", regex=False)
    .str.strip()
)

# LIST GURU
if "NAMA GURU" not in df_guru.columns:
    st.error("❌ Kolom 'NAMA GURU' tidak ditemukan di sheet GURU_SIMPEG")
    st.stop()

guru_list = sorted(df_guru["NAMA GURU"].astype(str).dropna().unique())

# =========================================================
# MAP STATUS REGULATIF
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

    if "diberhentikan" in ket_akhir or "harus diberhentikan" in ket_akhir:
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
# FILTER SIDEBAR
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

# =========================================================
# INFO USER LOGIN
# =========================================================
st.caption(f"👤 Login sebagai: **{st.session_state.role}**")
is_view_only = st.session_state.role in ["Kadis", "View"]

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
        if st.button("🔄 Refresh Data SIMPEG", key="refresh_simpeg", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Data SIMPEG diperbarui")
            st.rerun()

    with col3:
        if st.button("🔄 Refresh Data Kepsek", key="refresh_kepsek", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Data Kepala Sekolah diperbarui")
            st.rerun()

    with col4:
        if st.button("📌 Rekap", key="btn_rekap", use_container_width=True):
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
    # REKAP PIMPINAN
    # =========================================================
    st.divider()
    st.markdown("## 📑 Rekap & Analisis Kepala Sekolah (Pimpinan)")

    df_rekap = df_ks.copy()
    df_rekap["Status Regulatif"] = df_rekap.apply(map_status, axis=1)

    rekap_cabdin = (
        df_rekap.groupby(["Cabang Dinas", "Status Regulatif"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    st.dataframe(rekap_cabdin, use_container_width=True)

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

    st.subheader("📊 Grafik Status Kepala Sekolah")
    st.bar_chart(grafik_data)

    # =========================================================
    # DASAR HUKUM (2023)
    # =========================================================
    st.divider()
    st.markdown("## ⚖️ Dasar Hukum Penugasan Kepala Sekolah")

    st.info("""
    **Permendikdasmen Nomor 7 Tahun 2025**

    **Pokok Ketentuan:**
    1. Kepala Sekolah diberikan tugas maksimal **2 (dua) periode**
    2. Satu periode = **4 (empat) tahun**
    3. Kepala Sekolah yang telah menjabat **lebih dari 2 periode wajib diberhentikan**
    4. Kepala Sekolah periode 2 bisa diperpanjang jika memenuhi persyaratan (BCKS)
    5. Sekolah tanpa Kepala Sekolah definitif wajib segera diisi (PLT/Definitif)
    6. Penugasan Kepala Sekolah merupakan tugas tambahan ASN
    """)

    st.success("📌 Dashboard telah menyesuaikan status sesuai Permendikdasmen No 7 Tahun 2023")

# =========================================================
# HALAMAN SEKOLAH
# =========================================================
def page_sekolah():
    if st.session_state.selected_cabdin is None:
        st.warning("⚠️ Cabang Dinas belum dipilih.")
        st.session_state.page = "cabdin"
        st.rerun()

    col_a, col_b, col_c = st.columns([1.5, 1.5, 6])

    with col_a:
        if st.button("⬅️ Back", key="btn_back_sekolah", use_container_width=True):
            st.session_state.page = "cabdin"
            st.session_state.selected_cabdin = None
            st.session_state.selected_sekolah = None
            st.rerun()

    with col_b:
        if st.button("🏠 Home", key="btn_home_sekolah", use_container_width=True):
            st.session_state.page = "cabdin"
            st.session_state.selected_cabdin = None
            st.session_state.selected_sekolah = None
            st.rerun()

    with col_c:
        st.subheader(f"🏫 Sekolah — {st.session_state.selected_cabdin}")

    df_cab = df_ks[df_ks["Cabang Dinas"] == st.session_state.selected_cabdin].copy()
    df_cab = apply_filter(df_cab)

    if df_cab.empty:
        st.warning("⚠️ Tidak ada data sekolah pada Cabang Dinas ini.")
        st.stop()

    # =========================================================
    # REKAP STATUS CABDIN INI (SESUAI FOTO 1)
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
    colx1.metric("Periode 1", int(rekap_status_cab["Aktif Periode 1"]))
    colx2.metric("Periode 2", int(rekap_status_cab["Aktif Periode 2"]))
    colx3.metric("> 2 Periode", int(rekap_status_cab["Lebih dari 2 Periode"]))
    colx4.metric("PLT", int(rekap_status_cab["Plt"]))
    colx5.metric("Harus Berhenti", int(rekap_status_cab["Harus Diberhentikan"]))
    colx6.metric("Lainnya", int(rekap_status_cab["Lainnya"]))

    st.divider()

    # =========================================================
    # LIST SEKOLAH (GRID 4 KOLOM)
    # =========================================================
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
            if st.button(f"{warna} {nama_sekolah}", key=f"btn_sekolah_{idx}", use_container_width=True):
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

    col_a, col_b, col_c = st.columns([1.5, 1.5, 6])

    with col_a:
        if st.button("⬅️ Sekolah", key="btn_back_detail", use_container_width=True):
            st.session_state.page = "sekolah"
            st.session_state.selected_sekolah = None
            st.rerun()

    with col_b:
        if st.button("🏠 Home", key="btn_home_detail", use_container_width=True):
            st.session_state.page = "cabdin"
            st.session_state.selected_cabdin = None
            st.session_state.selected_sekolah = None
            st.rerun()

    with col_c:
        st.subheader(f"📄 Detail Sekolah: {st.session_state.selected_sekolah}")

    # NORMALISASI
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

    status_reg = map_status(row)
    masa = str(row.get("Masa Periode Sesuai KSPSTK", "")).lower()
    ket_akhir = str(row.get("Keterangan Akhir", "")).lower()
    bcks = str(row.get("Ket Sertifikat BCKS", "")).lower()

    # =========================================================
    # BADGE STATUS
    # =========================================================
    if status_reg == "Aktif Periode 1":
        st.markdown(badge("Aktif Periode 1", "#2196f3"), unsafe_allow_html=True)
    elif status_reg == "Aktif Periode 2":
        st.markdown(badge("Aktif Periode 2", "#fbc02d", "black"), unsafe_allow_html=True)
    elif status_reg == "Lebih dari 2 Periode":
        st.markdown(badge("Lebih dari 2 Periode", "#d32f2f"), unsafe_allow_html=True)
    elif status_reg == "Plt":
        st.markdown(badge("PLT", "#2e7d32"), unsafe_allow_html=True)
    elif status_reg == "Harus Diberhentikan":
        st.markdown(badge("Harus Diberhentikan", "#b71c1c"), unsafe_allow_html=True)
    else:
        st.markdown(badge("Lainnya", "#616161"), unsafe_allow_html=True)

    if "plt" in masa or "plt" in ket_akhir:
        st.markdown(badge("PLT", "#2e7d32"), unsafe_allow_html=True)
    else:
        st.markdown(badge("Definitif", "#1565c0"), unsafe_allow_html=True)

    if "sudah" in bcks or "ada" in bcks or "memiliki" in bcks:
        st.markdown(badge("Sudah BCKS", "#4caf50"), unsafe_allow_html=True)
    elif "belum" in bcks or "tidak" in bcks or bcks.strip() == "" or bcks == "nan":
        st.markdown(badge("Belum BCKS", "#ff9800", "black"), unsafe_allow_html=True)
    else:
        st.markdown(badge("Status BCKS Tidak Jelas", "#9e9e9e"), unsafe_allow_html=True)

    st.divider()

    # =========================================================
    # DATA DETAIL 2 KOLOM
    # =========================================================
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

    # =========================================================
    # SIMPAN PENGGANTI
    # =========================================================
    calon_tersimpan = perubahan_kepsek.get(nama)

    if is_view_only:
        st.info("ℹ️ Anda login sebagai **View Only**. Tidak dapat mengubah data.")
    else:
        calon = st.selectbox(
            "👤 Pilih Calon Pengganti (SIMPEG)",
            guru_list,
            key=f"calon_{nama}"
        )

        if st.button("💾 Simpan Pengganti", key="btn_simpan_pengganti", use_container_width=True):
            perubahan_kepsek[nama] = calon
            save_perubahan(perubahan_kepsek)
            st.success(f"✅ Diganti dengan: {calon}")
            st.rerun()

    # =========================================================
    # KEMBALIKAN KE KEPSEK LAMA (WAJIB ADA)
    # =========================================================
    if calon_tersimpan:
        st.info(f"👤 Pengganti Saat Ini: **{calon_tersimpan}**")

        if not is_view_only:
            if st.button("✏️ Kembalikan ke Kepala Sekolah Lama", key="btn_kembalikan", use_container_width=True):
                perubahan_kepsek.pop(nama, None)
                save_perubahan(perubahan_kepsek)
                st.success("🔄 Berhasil dikembalikan ke Kepala Sekolah Lama")
                st.rerun()

# =========================================================
# HALAMAN REKAP
# =========================================================
def page_rekap():
    col_a, col_b = st.columns([2, 10])

    with col_a:
        if st.button("🏠 Home", key="btn_home_rekap", use_container_width=True):
            st.session_state.page = "cabdin"
            st.session_state.selected_cabdin = None
            st.session_state.selected_sekolah = None
            st.rerun()

    with col_b:
        st.markdown("## 📌 Rekap Kepala Sekolah Bisa di Berhentikan")

    st.divider()

    df_rekap = df_ks.copy()
    df_rekap["Status Regulatif"] = df_rekap.apply(map_status, axis=1)

    df_bisa = df_rekap[
        df_rekap["Status Regulatif"].isin(["Aktif Periode 2", "Lebih dari 2 Periode", "Harus Diberhentikan"])
    ].copy()

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

    st.divider()
    st.markdown("### 📄 Pilih Sekolah untuk lihat detail")

    sekolah_opsi = df_bisa["Nama Sekolah"].unique().tolist()
    pilih_sekolah = st.selectbox("Pilih Sekolah", sekolah_opsi, key="rekap_pilih_sekolah")

    if st.button("📌 Lihat Detail Sekolah", key="btn_lihat_detail_rekap", use_container_width=True):
        st.session_state.selected_sekolah = pilih_sekolah
        st.session_state.page = "detail"
        st.rerun()

# =========================================================
# ROUTING HALAMAN
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
