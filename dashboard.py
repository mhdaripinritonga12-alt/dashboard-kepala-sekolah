import streamlit as st
import pandas as pd
import os

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

# =========================================================
# 🔐 SISTEM LOGIN & ROLE USER
# =========================================================
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
    },
    "viewer": {
        "password": "viewer123",
        "role": "View"
    }
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

    # ambil semua sheet cabdis
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

    # load simpeg
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

rename_map_ks = {
    "NAMA SEKOLAH": "Nama Sekolah",
    "Nama Kasek": "Nama Kepala Sekolah",
    "NAMA KASEK": "Nama Kepala Sekolah",
    "Nama Kepsek": "Nama Kepala Sekolah",
    "Keterangan": "Keterangan Akhir",
    "KETERANGAN": "Keterangan Akhir",
    "KETERANGAN AKHIR": "Keterangan Akhir",
}

df_ks.rename(columns=rename_map_ks, inplace=True)

rename_map_guru = {
    "NAMA GURU ": "NAMA GURU",
    "NAMA": "NAMA GURU",
    "NIP ": "NIP",
}

df_guru.rename(columns=rename_map_guru, inplace=True)

df_ks.columns = df_ks.columns.astype(str).str.strip()
df_guru.columns = df_guru.columns.astype(str).str.strip()

# =========================================================
# 🔍 CEK KOLOM WAJIB
# =========================================================
kolom_wajib = ["Jenjang", "Cabang Dinas", "Keterangan Akhir", "Nama Sekolah"]

for k in kolom_wajib:
    if k not in df_ks.columns:
        st.error(f"❌ Kolom wajib '{k}' tidak ditemukan di Excel. Kolom tersedia: {list(df_ks.columns)}")
        st.stop()

# jika kolom nama kepsek tidak ada, fallback ke NAMA KASEK
if "Nama Kepala Sekolah" not in df_ks.columns:
    if "NAMA KASEK" in df_ks.columns:
        df_ks["Nama Kepala Sekolah"] = df_ks["NAMA KASEK"]
    else:
        df_ks["Nama Kepala Sekolah"] = "-"

# =========================================================
# LIST GURU SIMPEG
# =========================================================
if "NAMA GURU" not in df_guru.columns:
    st.error("❌ Kolom 'NAMA GURU' tidak ditemukan di sheet GURU_SIMPEG")
    st.stop()

guru_list = sorted(df_guru["NAMA GURU"].astype(str).dropna().unique())

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
# NORMALISASI STATUS SESUAI REGULASI
# =========================================================
def map_status(status):
    status = str(status).lower()

    if "periode 1" in status:
        return "Aktif Periode 1"
    if "periode 2" in status:
        return "Aktif Periode 2"
    if "lebih dari 2" in status or ">2" in status:
        return "Lebih dari 2 Periode"
    if "plt" in status:
        return "PLT"
    if "diberhentikan" in status or "harus diberhentikan" in status:
        return "Harus Diberhentikan"

    return "Lainnya"

# =========================================================
# LOGIKA BOLEH DIGANTI (PERIODE 1 TIDAK BOLEH)
# =========================================================
def cek_boleh_diganti(row):
    ket = str(row.get("Keterangan Akhir", "")).lower()
    sertifikat = str(row.get("Sertifikat BCKS", row.get("Ket. Sertifikat BCKS", ""))).lower()

    # ❌ periode 1 tidak boleh
    if "periode 1" in ket or "aktif periode 1" in ket:
        return False

    # selain periode 1 boleh
    if "periode 2" in ket:
        return True
    if "lebih dari 2" in ket:
        return True
    if "plt" in ket:
        return True
    if "harus diberhentikan" in ket or "diberhentikan" in ket:
        return True

    # belum sertifikat bcks boleh diganti
    if "belum" in sertifikat:
        return True

    return True

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
# HALAMAN SEKOLAH
# =========================================================
elif st.session_state.page == "sekolah":

    col_a, col_b = st.columns([1, 5])

    with col_a:
        if st.button("⬅️ Kembali", use_container_width=True):
            st.session_state.page = "cabdin"
            st.session_state.selected_cabdin = None
            st.rerun()

    with col_b:
        st.subheader(f"🏫 Sekolah — {st.session_state.selected_cabdin}")

    df_cab = df_ks[df_ks["Cabang Dinas"] == st.session_state.selected_cabdin].copy()
    df_cab = apply_filter(df_cab)

    if df_cab.empty:
        st.warning("⚠️ Tidak ada data sekolah pada Cabang Dinas ini.")
        st.stop()

    # =========================================================
    # 📌 REKAP STATUS CABANG DINAS INI
    # =========================================================
    st.markdown("### 📌 Rekap Status Kepala Sekolah Cabang Dinas Ini")

    df_cab_rekap = df_cab.copy()
    df_cab_rekap["Status Regulatif"] = df_cab_rekap["Keterangan Akhir"].astype(str).apply(map_status)

    rekap_status_cab = (
        df_cab_rekap["Status Regulatif"]
        .value_counts()
        .reindex([
            "Aktif Periode 1",
            "Aktif Periode 2",
            "Lebih dari 2 Periode",
            "PLT",
            "Harus Diberhentikan",
            "Lainnya"
        ], fill_value=0)
    )

    colx1, colx2, colx3, colx4, colx5, colx6 = st.columns(6)
    colx1.metric("Periode 1", int(rekap_status_cab["Aktif Periode 1"]))
    colx2.metric("Periode 2", int(rekap_status_cab["Aktif Periode 2"]))
    colx3.metric(">2 Periode", int(rekap_status_cab["Lebih dari 2 Periode"]))
    colx4.metric("PLT", int(rekap_status_cab["PLT"]))
    colx5.metric("Harus Berhenti", int(rekap_status_cab["Harus Diberhentikan"]))
    colx6.metric("Lainnya", int(rekap_status_cab["Lainnya"]))

    st.divider()

    # =========================================================
    # GRID SEKOLAH
    # =========================================================
    cols = st.columns(5)
    idx = 0

    for _, row in df_cab.iterrows():

        nama_sekolah = row.get("Nama Sekolah", "-")
        nama_kepsek = row.get("Nama Kepala Sekolah", row.get("NAMA KASEK", "-"))
        status = str(row.get("Keterangan Akhir", ""))
        status_lower = status.lower()

        # warna card
        if "periode 1" in status_lower:
            card_class = "card-periode-1"
        elif "periode 2" in status_lower:
            card_class = "card-periode-2"
        elif "plt" in status_lower:
            card_class = "card-plt"
        elif "diberhentikan" in status_lower:
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

            # =========================================================
            # DETAIL SEKOLAH (1 SEKOLAH 1 LEMBAR DETAIL SEPERTI SURAT)
            # =========================================================
            with st.expander("📄 Detail Lengkap (Seperti Surat)"):

                st.markdown("### 📌 Data Lengkap Kepala Sekolah")

                for col in df_cab.columns:
                    st.write(f"**{col}:** {row.get(col, '-')}")
                
                st.divider()

                # =========================================================
                # LOGIKA EDIT
                # =========================================================
                boleh_diganti_status = cek_boleh_diganti(row)
                is_view_only = st.session_state.role in ["Kadis", "View"]

                calon_tersimpan = perubahan_kepsek.get(nama_sekolah)

                if is_view_only:
                    st.info("ℹ️ Anda login sebagai **View Only**. Tidak dapat mengubah data.")
                else:
                    if not boleh_diganti_status:
                        st.warning("⛔ Tidak dapat diganti karena status **Periode 1**.")
                    else:
                        calon = st.selectbox(
                            "👤 Pilih Calon Pengganti (SIMPEG)",
                            guru_list,
                            key=f"calon_{nama_sekolah}"
                        )

                        if st.button(
                            "💾 Simpan Pengganti",
                            key=f"simpan_{nama_sekolah}",
                            use_container_width=True
                        ):
                            perubahan_kepsek[nama_sekolah] = calon
                            save_perubahan(perubahan_kepsek)
                            st.success(f"✅ Diganti dengan: {calon}")
                            st.rerun()

                # tampilkan pengganti tersimpan
                if calon_tersimpan:
                    st.info(f"👤 Pengganti Saat Ini: **{calon_tersimpan}**")

                    # undo hanya jika bukan view only
                    if not is_view_only:
                        if st.button(
                            "✏️ Kembalikan ke Kepala Sekolah Lama",
                            key=f"undo_{nama_sekolah}",
                            use_container_width=True
                        ):
                            perubahan_kepsek.pop(nama_sekolah, None)
                            save_perubahan(perubahan_kepsek)
                            st.success("🔄 Berhasil dikembalikan")
                            st.rerun()

        idx += 1

# =========================================================
# 📊 REKAP & ANALISIS PIMPINAN
# =========================================================
st.divider()
st.markdown("## 📑 Rekap & Analisis Kepala Sekolah (Pimpinan)")

df_rekap = df_ks.copy()
df_rekap["Status Regulatif"] = df_rekap["Keterangan Akhir"].astype(str).apply(map_status)

rekap_cabdin = (
    df_rekap
    .groupby(["Cabang Dinas", "Status Regulatif"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)

# urut cabdin 1-14
rekap_cabdin["__urut__"] = rekap_cabdin["Cabang Dinas"].apply(
    lambda x: int("".join(filter(str.isdigit, str(x)))) if "".join(filter(str.isdigit, str(x))) else 999
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
        "PLT",
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
3. Kepala Sekolah yang telah menjabat **2 periode wajib diberhentikan sesuai pada pasal 31**
4. Kepala Sekolah yang telah menjabat **1 Periode bisa diperpanjang apabila memiliki Sertifikat BCKS sesuai pada Pasal 32**
5. Sekolah tanpa Kepala Sekolah definitif **wajib segera diisi (PLT/Definitif)**
6. Penugasan Kepala Sekolah merupakan **tugas tambahan ASN**
""")

st.success("📌 Status dan rekomendasi pada dashboard ini telah diselaraskan dengan Permendikdasmen No. 7 Tahun 2025")

# =========================================================
# FOOTER
# =========================================================
st.divider()
st.caption("Dashboard Kepala Sekolah • MHD. ARIPIN RITONGA, S.Kom")
