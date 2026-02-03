import streamlit as st
import pandas as pd

# ======================
# KONFIGURASI HALAMAN
# ======================
st.set_page_config(
    page_title="Dashboard Kepala Sekolah",
    layout="wide"
)

# ======================
# LOAD DATA AMAN
# ======================
@st.cache_data
def load_data():
    df_ks = pd.read_excel("data_kepala_sekolah.xlsx")
    df_guru = pd.read_excel("data_guru_simpeg.xlsx")
    return df_ks, df_guru

df, df_guru = load_data()

# ======================
# VALIDASI KOLOM WAJIB
# ======================
kolom_wajib_ks = [
    "Cabang Dinas",
    "Nama Sekolah",
    "Nama Kepala Sekolah",
    "Keterangan Akhir",
    "Jenjang"
]

for col in kolom_wajib_ks:
    if col not in df.columns:
        st.error(f"❌ Kolom '{col}' tidak ditemukan di data_kepala_sekolah.xlsx")
        st.stop()

# ======================
# CEK KOLOM GURU (AMAN)
# ======================
# 👉 GANTI "Nama" JIKA DI EXCEL ANDA BEDA
NAMA_GURU_COL = "Nama"

if NAMA_GURU_COL not in df_guru.columns:
    st.error(
        f"❌ Kolom '{NAMA_GURU_COL}' tidak ditemukan di data_guru_simpeg.xlsx\n\n"
        "➡️ Buka Excel SIMPEG\n"
        "➡️ Lihat nama kolom yang berisi NAMA GURU\n"
        "➡️ Ganti variabel NAMA_GURU_COL di dashboard.py"
    )
    st.stop()

# ======================
# HEADER
# ======================
st.markdown("""
<h1 style='color:#0B5394; font-weight:800;'>
📊 DASHBOARD KEPALA SEKOLAH DINAS PENDIDIKAN
</h1>
<hr>
""", unsafe_allow_html=True)

# ======================
# SEARCH KEPALA SEKOLAH
# ======================
search = st.text_input("🔍 Cari Nama Kepala Sekolah")

if search:
    df = df[df["Nama Kepala Sekolah"].str.contains(search, case=False, na=False)]

# ======================
# SIDEBAR FILTER
# ======================
st.sidebar.header("🔎 Filter")

jenjang = st.sidebar.selectbox(
    "Jenjang",
    ["Semua"] + sorted(df["Jenjang"].dropna().unique())
)

if jenjang != "Semua":
    df = df[df["Jenjang"] == jenjang]

# ======================
# STYLE CARD
# ======================
st.markdown("""
<style>
.card {
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
    background-color: #f4f6f9;
    border-left: 6px solid #1f77b4;
}
.danger {
    background-color: #fdecea;
    border-left: 6px solid #d93025;
}
</style>
""", unsafe_allow_html=True)

# ======================
# TAMPILAN PER CABDIN
# ======================
st.subheader("🏢 Cabang Dinas Wilayah")

cabdin_list = sorted(df["Cabang Dinas"].unique())
cols = st.columns(4)

for i, cabdin in enumerate(cabdin_list):
    with cols[i % 4]:
        with st.expander(f"📍 {cabdin}", expanded=False):

            df_cab = df[df["Cabang Dinas"] == cabdin]

            for _, row in df_cab.iterrows():
                is_danger = row["Keterangan Akhir"] in ["PLT", "Harus Diberhentikan"]
                card_class = "danger" if is_danger else "card"

                st.markdown(
                    f"""
                    <div class="{card_class}">
                        <b>🏫 {row['Nama Sekolah']}</b><br>
                        👤 {row['Nama Kepala Sekolah']}<br>
                        <span style="color:red; font-weight:700;">
                        {row['Keterangan Akhir']}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                with st.expander("🔍 Detail & Pengganti"):
                    st.write(f"**Jenjang:** {row.get('Jenjang','-')}")
                    st.write(f"**NIP:** {row.get('NIP','-')}")
                    st.write(f"**Jabatan:** {row.get('Jabatan','-')}")
                    st.write(f"**Tahun Pengangkatan:** {row.get('Tahun Pengangkatan','-')}")

                    if is_danger:
                        calon = df_guru[
                            df_guru["Jenjang"] == row["Jenjang"]
                        ][NAMA_GURU_COL].dropna().unique()

                        st.selectbox(
                            "👥 Pilih Calon Pengganti",
                            calon,
                            key=f"ganti_{cabdin}_{row['Nama Sekolah']}"
                        )

# ======================
# FOOTER
# ======================
st.markdown("""
<hr>
<p style='text-align:center; color:gray; font-size:13px;'>
Dashboard Kepala Sekolah • Dinas Pendidikan Provinsi • Streamlit
</p>
""", unsafe_allow_html=True)
