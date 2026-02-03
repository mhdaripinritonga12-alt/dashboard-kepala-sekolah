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
# LOAD DATA
# ======================
@st.cache_data
def load_data():
    df_ks = pd.read_excel("data_kepala_sekolah.xlsx")
    df_guru = pd.read_excel("data_guru_simpeg.xlsx")
    return df_ks, df_guru

df, df_guru = load_data()

# ======================
# VALIDASI KOLOM
# ======================
kolom_ks = [
    "Cabang Dinas", "Nama Sekolah", "Nama Kepala Sekolah",
    "NIP", "Jabatan", "Jenjang",
    "Sertifikat BCKS", "Tahun Pengangkatan", "Keterangan Akhir"
]

kolom_guru = ["Nama Guru", "NIP", "Jenjang", "Cabang Dinas"]

for c in kolom_ks:
    if c not in df.columns:
        st.error(f"❌ Kolom '{c}' tidak ditemukan di data_kepala_sekolah.xlsx")
        st.stop()

for c in kolom_guru:
    if c not in df_guru.columns:
        st.error(f"❌ Kolom '{c}' tidak ditemukan di data_guru_simpeg.xlsx")
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
# SEARCH GLOBAL (NAMA KEPSEK)
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
# CSS
# ======================
st.markdown("""
<style>
.card {
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 14px;
    background-color: #f4f6f9;
    border-left: 6px solid #1f77b4;
}
.card-danger {
    background-color: #fdecea;
    border-left: 6px solid #d93025;
}
</style>
""", unsafe_allow_html=True)

# ======================
# TAMPILAN CABANG DINAS
# ======================
st.subheader("🏢 Cabang Dinas Wilayah")

for cabdin in sorted(df["Cabang Dinas"].unique()):
    with st.expander(f"📍 {cabdin}", expanded=False):

        df_cab = df[df["Cabang Dinas"] == cabdin]

        for i, row in df_cab.iterrows():

            danger = row["Keterangan Akhir"] in ["PLT", "Harus Diberhentikan"]
            card_class = "card-danger" if danger else "card"

            st.markdown(f"""
            <div class="{card_class}">
                <b>🏫 {row['Nama Sekolah']}</b><br>
                👤 {row['Nama Kepala Sekolah']}<br>
                <span style="color:red;font-weight:700;">
                    {row['Keterangan Akhir']}
                </span>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("🔍 Lihat Detail", expanded=False):
                st.write(f"**NIP:** {row['NIP']}")
                st.write(f"**Jabatan:** {row['Jabatan']}")
                st.write(f"**Jenjang:** {row['Jenjang']}")
                st.write(f"**BCKS:** {row['Sertifikat BCKS']}")
                st.write(f"**Tahun Pengangkatan:** {row['Tahun Pengangkatan']}")

                # ======================
                # CALON PENGGANTI
                # ======================
                if row["Keterangan Akhir"] in ["PLT", "Harus Diberhentikan"]:
                    kandidat = df_guru[
                        (df_guru["Jenjang"] == row["Jenjang"]) &
                        (df_guru["Cabang Dinas"] == cabdin)
                    ]

                    if len(kandidat) > 0:
                        pilih = st.selectbox(
                            "👥 Pilih Calon Pengganti",
                            kandidat["Nama Guru"].unique(),
                            key=f"ganti_{i}"
                        )
                        st.success(f"Calon pengganti dipilih: **{pilih}**")
                    else:
                        st.warning("Tidak ada kandidat dari data SIMPEG")

# ======================
# FOOTER
# ======================
st.markdown("""
<hr>
<p style='text-align:center; color:gray; font-size:13px;'>
Dashboard Kepala Sekolah • Dinas Pendidikan Provinsi • Streamlit
</p>
""", unsafe_allow_html=True)
