import streamlit as st
import pandas as pd
import os

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
# ߔ SISTEM LOGIN & ROLE USER (WAJIB LOGIN)
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
    st.markdown("## ߔ Login Dashboard Kepala Sekolah")

    col1, col2, col3 = st.columns([2,3,2])
    with col2:
        username = st.text_input("ߑ Username")
        password = st.text_input("ߔ Password", type="password")

        if st.button("ߔ Login", use_container_width=True):
            if username in USERS and USERS[username]["password"] == password:
                st.session_state.login = True
                st.session_state.role = USERS[username]["role"]
                st.success(f"✅ Login berhasil sebagai **{st.session_state.role}**")
                st.rerun()
            else:
                st.error("❌ Username atau Password salah")

    st.stop()

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
@st.cache_data(show_spinner="ߓ Memuat data Kepala Sekolah & SIMPEG...")
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
.stApp { background:#d3d3d3; color:black; }
.school-card {
    background:white;
    border-left:6px solid #1f77b4;
    border-radius:10px;
    padding:16px;
    margin-bottom:14px;
}
.school-danger {
    background:#fdecea;
    border-left:6px solid #d93025;
}
.school-saved {
    background:#e6f4ea;
    border-left:6px solid #1e8e3e;
}
.school-title { font-weight:700; font-size:16px; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER + REFRESH + LOGOUT
# =========================================================
col1, col2, col3, col4 = st.columns([5,2,2,2])

with col1:
    st.markdown("## ߓ Dashboard Kepala Sekolah")

with col2:
    if st.button("ߔ Refresh Data SIMPEG", use_container_width=True):
        st.cache_data.clear()
        st.success("✅ Data SIMPEG dimuat ulang")
        st.rerun()

with col3:
    if st.button("ߔ Refresh Data Kepsek", use_container_width=True):
        st.cache_data.clear()
        st.success("✅ Data Kepala Sekolah dimuat ulang")
        st.rerun()

with col4:
    if st.button("ߚ Logout", use_container_width=True):
        st.session_state.login = False
        st.session_state.page = "cabdin"
        st.session_state.selected_cabdin = None
        st.rerun()

st.divider()
# RESET ROLE SAAT LOGOUT
if not st.session_state.login:
    st.session_state.role = None

# =========================================================
# ߔ PENCARIAN GURU SIMPEG
# =========================================================
with st.expander("ߔ Pencarian Guru (SIMPEG)", expanded=False):
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
st.sidebar.header("ߔ Filter & Pencarian")
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

# =========================================================
# HALAMAN CABANG DINAS
# =========================================================
if st.session_state.page == "cabdin":
    st.subheader("ߏ Cabang Dinas Wilayah")
    df_view = apply_filter(df_ks)

    cols = st.columns(4)
    for i, cabdin in enumerate(sorted(df_view["Cabang Dinas"].unique())):
        with cols[i % 4]:
            if st.button(f"ߓ {cabdin}", use_container_width=True):
                st.session_state.selected_cabdin = cabdin
                st.session_state.page = "sekolah"
                st.rerun()

# =========================================================
# HALAMAN SEKOLAH (DETAIL + PENGGANTI)
# =========================================================
elif st.session_state.page == "sekolah":

    cabdin = st.session_state.selected_cabdin
    st.subheader(f"ߏ Sekolah — {cabdin}")

    if st.button("⬅ Kembali"):
        st.session_state.page = "cabdin"
        st.rerun()

    df_cab = apply_filter(df_ks[df_ks["Cabang Dinas"] == cabdin])

    for idx, row in df_cab.iterrows():

        nama_sekolah = row["Nama Sekolah"]
        status = row["Keterangan Akhir"]
        danger = status in ["Harus Diberhentikan", "Harap Segera Defenitifkan"]
        sudah = nama_sekolah in perubahan_kepsek

        card = "school-saved" if sudah else "school-danger" if danger else "school-card"

        st.markdown(f"""
        <div class="{card}">
            <div class="school-title">ߏ {nama_sekolah}</div>
            ߑ {row['Nama Kepala Sekolah']}<br>
            <b>{status}</b>
            {f"<br>✅ Pengganti: <b>{perubahan_kepsek[nama_sekolah]}</b>" if sudah else ""}
        </div>
        """, unsafe_allow_html=True)

        # ߔ BAGIAN YANG SEBELUMNYA HILANG
        with st.expander("ߔ Detail & Penanganan Kepala Sekolah"):
            st.write(f"**NIP:** {row['NIP']}")
            st.write(f"**Jenjang:** {row['Jenjang']}")
            st.write(f"**Tahun Pengangkatan:** {row['Tahun Pengangkatan']}")

            if danger or sudah:
                default_idx = (
                    guru_list.index(perubahan_kepsek[nama_sekolah])
                    if sudah and perubahan_kepsek[nama_sekolah] in guru_list
                    else 0
                )

                calon = st.selectbox(
                    "ߑ Pilih Calon Pengganti (SIMPEG)",
                    guru_list,
                    index=default_idx,
                    key=f"calon_{idx}"
                )

                col_a, col_b = st.columns(2)

                with col_a:
                    if st.button("ߒ SIMPAN PENGGANTI", key=f"save_{idx}", use_container_width=True):
                        perubahan_kepsek[nama_sekolah] = calon
                        save_perubahan(perubahan_kepsek)
                        st.success("✅ Calon pengganti berhasil disimpan")
                        st.rerun()

                if sudah:
                    with col_b:
                        if st.button("✏️ Ubah Kembali", key=f"edit_{idx}", use_container_width=True):
                            del perubahan_kepsek[nama_sekolah]
                            save_perubahan(perubahan_kepsek)
                            st.warning("✏️ Mode edit dibuka kembali")
                            st.rerun()
# =========================================================
# ߓ REKAP & ANALISIS PIMPINAN (TAMBAHAN RESMI DINAS)
# =========================================================
st.divider()
st.markdown("## ߓ Rekap & Analisis Kepala Sekolah (Pimpinan)")

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
# ߓ REKAP PER CABANG DINAS
# ---------------------------------------------------------
rekap_cabdin = (
    df_rekap
    .groupby(["Cabang Dinas", "Status Regulatif"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)

st.subheader("ߓ Rekap Kepala Sekolah per Cabang Dinas")
st.dataframe(rekap_cabdin, use_container_width=True)

# ---------------------------------------------------------
# ߓ DOWNLOAD EXCEL REKAP
# ---------------------------------------------------------
excel_file = "rekap_kepala_sekolah_per_cabdin.xlsx"
rekap_cabdin.to_excel(excel_file, index=False)

with open(excel_file, "rb") as f:
    st.download_button(
        label="ߓ Download Rekap Kepala Sekolah (Excel)",
        data=f,
        file_name=excel_file,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ---------------------------------------------------------
# ߓ GRAFIK STATUS KEPALA SEKOLAH
# ---------------------------------------------------------
st.subheader("ߓ Grafik Status Kepala Sekolah")

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

st.success("ߓ Seluruh status dan rekomendasi pada dashboard ini telah diselaraskan dengan Permendikdasmen No. 7 Tahun 2025")

# =========================================================
# FOOTER
# =========================================================
st.divider()
st.caption("Dashboard Kepala Sekolah • MHD. ARIPIN RITONGA, S.Kom")
