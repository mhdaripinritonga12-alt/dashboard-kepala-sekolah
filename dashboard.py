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
# LOAD DATA (AMAN)
# ======================
@st.cache_data
def load_data():
    ks = pd.read_excel("data_kepala_sekolah.xlsx")
    guru = pd.read_excel("data_guru_simpeg.xlsx")
    return ks, guru

df, df_guru = load_data()

# ======================
# VALIDASI KOLOM WAJIB
# ======================
wajib_ks = [
    "Cabang Dinas","Nama Sekolah","Nama Kepala Sekolah",
    "NIP","Jenjang","Jabatan","Sertifikat BCKS",
    "Tahun Pengangkatan","Keterangan Akhir"
]

wajib_guru = ["Nama Guru","NIP","Jenjang","Cabang Dinas"]

for c in wajib_ks:
    if c not in df.columns:
        st.error(f"❌ Kolom '{c}' tidak ditemukan di data_kepala_sekolah.xlsx")
        st.stop()

for c in wajib_guru:
    if c not in df_guru.columns:
        st.error(f"❌ Kolom '{c}' tidak ditemukan di data_guru_simpeg.xlsx")
        st.stop()

# ======================
# HEADER
# ======================
st.markdown("""
<h1 style='color:#0B5394;font-weight:800'>
📊 DASHBOARD KEPALA SEKOLAH DINAS PENDIDIKAN
</h1><hr>
""", unsafe_allow_html=True)

# ======================
# SIDEBAR FILTER + SEARCH
# ======================
st.sidebar.header("🔍 Filter & Pencarian")

search = st.sidebar.text_input("Cari Nama Kepala Sekolah")

jenjang = st.sidebar.selectbox(
    "Jenjang",
    ["Semua"] + sorted(df["Jenjang"].dropna().unique())
)

if search:
    df = df[df["Nama Kepala Sekolah"].str.contains(search, case=False, na=False)]

if jenjang != "Semua":
    df = df[df["Jenjang"] == jenjang]

# ======================
# CSS
# ======================
st.markdown("""
<style>
.card {
    padding:16px;
    border-radius:12px;
    background:#f4f6f9;
    border-left:6px solid #1f77b4;
    margin-bottom:14px;
}
.danger {
    background:#fdecea;
    border-left:6px solid #d93025;
}
</style>
""", unsafe_allow_html=True)

# ======================
# CABANG DINAS
# ======================
st.subheader("🏢 Cabang Dinas Wilayah")
cabdin_list = sorted(df["Cabang Dinas"].unique())

cols = st.columns(4)

for i, cabdin in enumerate(cabdin_list):
    with cols[i % 4]:
        with st.expander(f"📍 {cabdin}", expanded=False):

            df_cab = df[df["Cabang Dinas"] == cabdin]

            for idx, row in df_cab.iterrows():

                bahaya = row["Keterangan Akhir"] in ["PLT","Harus Diberhentikan"]
                css = "danger" if bahaya else "card"

                st.markdown(f"""
                <div class="{css}">
                    <b>🏫 {row['Nama Sekolah']}</b><br>
                    👤 {row['Nama Kepala Sekolah']}<br>
                    <span style="color:red;font-weight:700">
                        {row['Keterangan Akhir']}
                    </span>
                </div>
                """, unsafe_allow_html=True)

                with st.expander("🔎 Detail & Penggantian"):
                    st.write(f"**NIP:** {row['NIP']}")
                    st.write(f"**Jabatan:** {row['Jabatan']}")
                    st.write(f"**Jenjang:** {row['Jenjang']}")
                    st.write(f"**BCKS:** {row['Sertifikat BCKS']}")
                    st.write(f"**Tahun:** {row['Tahun Pengangkatan']}")

                    # ======================
                    # CALON PENGGANTI
                    # ======================
                    if bahaya:
                        kandidat = df_guru[
                            (df_guru["Jenjang"] == row["Jenjang"]) &
                            (df_guru["Cabang Dinas"] == cabdin)
                        ]

                        if not kandidat.empty:
                            pilih = st.selectbox(
                                "👥 Pilih Calon Pengganti",
                                kandidat["Nama Guru"].tolist(),
                                key=f"ganti_{idx}"
                            )
                            st.success(f"✅ Calon Pengganti: {pilih}")
                        else:
                            st.warning("⚠️ Tidak ada kandidat dari SIMPEG")

# ======================
# FOOTER
# ======================
st.markdown("""
<hr>
<p style='text-align:center;color:gray;font-size:13px'>
Dashboard Kepala Sekolah • Dinas Pendidikan Provinsi • Streamlit
</p>
""", unsafe_allow_html=True)
