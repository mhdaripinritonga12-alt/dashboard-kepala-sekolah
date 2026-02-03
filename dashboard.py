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
    return pd.read_excel("data_kepala_sekolah.xlsx")

df = load_data()

# VALIDASI KOLOM
required_cols = ["Cabang Dinas", "Nama Sekolah", "Nama Kepala Sekolah", "Keterangan Akhir"]
for col in required_cols:
    if col not in df.columns:
        st.error(f"❌ Kolom '{col}' tidak ditemukan di Excel")
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
# SIDEBAR FILTER
# ======================
st.sidebar.header("🔎 Filter Data")

jenjang = st.sidebar.selectbox(
    "Jenjang",
    ["Semua"] + sorted(df["Jenjang"].dropna().unique())
)

if jenjang != "Semua":
    df = df[df["Jenjang"] == jenjang]

# ======================
# CSS CARD
# ======================
st.markdown("""
<style>
.card {
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
    background-color: #f4f6f9;
    border-left: 6px solid #1f77b4;
}
.card-danger {
    background-color: #fdecea;
    border-left: 6px solid #d93025;
}
.card h4 {
    margin: 0;
}
</style>
""", unsafe_allow_html=True)

# ======================
# TAMPILAN CABANG DINAS (CARD)
# ======================
st.subheader("🏢 Cabang Dinas Wilayah")
st.caption("Klik Cabang Dinas → Sekolah → Detail Kepala Sekolah")

cabdin_list = sorted(df["Cabang Dinas"].unique())

cols = st.columns(4)

for i, cabdin in enumerate(cabdin_list):
    with cols[i % 4]:
        with st.expander(f"📍 {cabdin}", expanded=False):

            df_cab = df[df["Cabang Dinas"] == cabdin]

            for _, row in df_cab.iterrows():
                danger = row["Keterangan Akhir"] == "Harus Diberhentikan"
                card_class = "card-danger" if danger else "card"

                st.markdown(
                    f"""
                    <div class="{card_class}">
                        <h4>🏫 {row['Nama Sekolah']}</h4>
                        <b>👤 {row['Nama Kepala Sekolah']}</b><br>
                        <span style="color:red; font-weight:700;">
                            {row['Keterangan Akhir']}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                with st.expander("🔍 Lihat Detail", expanded=False):
                    st.write(f"**NIP:** {row.get('NIP','-')}")
                    st.write(f"**Jabatan:** {row.get('Jabatan','-')}")
                    st.write(f"**Jenjang:** {row.get('Jenjang','-')}")
                    st.write(f"**Sertifikat BCKS:** {row.get('Sertifikat BCKS','-')}")
                    st.write(f"**Tahun Pengangkatan:** {row.get('Tahun Pengangkatan','-')}")

# ======================
# FOOTER
# ======================
st.markdown("""
<hr>
<p style='text-align:center; color:gray; font-size:13px;'>
Dashboard Kepala Sekolah • Dinas Pendidikan Provinsi • Streamlit
</p>
""", unsafe_allow_html=True)
