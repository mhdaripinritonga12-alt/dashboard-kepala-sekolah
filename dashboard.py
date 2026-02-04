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

/* WARNA STATUS */
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
if st.session_state.page == "cabdin":

    st.subheader("🏢 Cabang Dinas Wilayah")
    df_view = apply_filter(df_ks)

    cabdin_list = urutkan_cabdin(df_view["Cabang Dinas"].unique())
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

    st.subheader(f"🏫 Sekolah — {st.session_state.selected_cabdin}")

    # ===============================
    # FILTER DATA CABANG DINAS
    # ===============================
    df_cab = df_ks[df_ks["Cabang Dinas"] == st.session_state.selected_cabdin]

    if df_cab.empty:
        st.warning("⚠️ Tidak ada data sekolah pada Cabang Dinas ini.")
        st.stop()

    # ===============================
    # GRID 5 KOLOM
    # ===============================
    cols = st.columns(5)
    col_idx = 0

    # ===============================
    # LOOP SEKOLAH
    # ===============================
    for _, row in df_cab.iterrows():

        nama_sekolah = row.get("Nama Sekolah", "-")
        nama_kepsek = row.get("Nama Kepala Sekolah", "-")
        status = str(row.get("Keterangan Akhir", ""))
        status_lower = status.lower()

        # ===============================
        # LOGIKA STATUS (AMAN)
        # ===============================
        is_periode_1 = "periode 1" in status_lower
        is_periode_2 = "periode 2" in status_lower
        is_plt = "plt" in status_lower
        is_berhenti = "diberhentikan" in status_lower

        # BOLEH DIGANTI?
        boleh_edit = not is_periode_1

        # ===============================
        # WARNA CARD
        # ===============================
        if is_periode_1:
            card_class = "card-periode-1"
        elif is_periode_2:
            card_class = "card-periode-2"
        elif is_berhenti:
            card_class = "card-berhenti"
        elif is_plt:
            card_class = "card-plt"
        else:
            card_class = ""

        # ===============================
        # TAMPILKAN CARD SEKOLAH
        # ===============================
        with cols[col_idx % 5]:
            st.markdown(
                f"""
                <div class="school-card {card_class}">
                    🏫 {nama_sekolah}
                </div>
                """,
                unsafe_allow_html=True
            )

            # ===============================
            # DETAIL & PENANGANAN
            # ===============================
           with st.expander("🔍 Lihat Detail & Penanganan"):

    st.write(f"👤 **Kepala Sekolah:** {nama_kepsek}")
    st.write(f"📌 **Status:** {status}")

    calon_tersimpan = perubahan_kepsek.get(nama_sekolah)

    # ⛔ PERIODE 1 → TIDAK BOLEH
    if not boleh_edit:
        st.warning("⛔ Tidak dapat diganti karena masih Aktif Periode 1")

    # ✅ SEMUA SELAIN PERIODE 1 → BOLEH
    else:
        calon = st.selectbox(
            "👤 Pilih Calon Pengganti (SIMPEG)",
            daftar_guru_simpeg,
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

    # 🔄 BISA DIKEMBALIKAN (SELAMA BUKAN PERIODE 1)
    if calon_tersimpan and boleh_edit:
        st.info(f"🔁 Pengganti Saat Ini: {calon_tersimpan}")

        if st.button(
            "✏️ Kembalikan ke Kepala Sekolah Lama",
            key=f"undo_{nama_sekolah}",
            use_container_width=True
        ):
            perubahan_kepsek.pop(nama_sekolah, None)
            save_perubahan(perubahan_kepsek)
            st.success("🔄 Berhasil dikembalikan")
            st.rerun()
                # ===============================
                # BATALKAN PENGGANTI
                # ===============================
                if calon_tersimpan:
                    st.info(f"🔁 Pengganti Saat Ini: {calon_tersimpan}")

                    if st.button(
                        "✏️ Kembalikan ke Kepala Sekolah Lama",
                        key=f"undo_{nama_sekolah}",
                        use_container_width=True
                    ):
                        perubahan_kepsek.pop(nama_sekolah, None)
                        save_perubahan(perubahan_kepsek)
                        st.success("🔄 Pengganti dibatalkan")
                        st.rerun()

        col_idx += 1

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




















































































