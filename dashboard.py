import streamlit as st
import pandas as pd

# ======================
# KONFIGURASI
# ======================
st.set_page_config(
    page_title="Dashboard Kepala Sekolah",
    layout="wide"
)

# ======================
# LOAD DATA (AMAN, TIDAK ERROR)
# ======================
@st.cache_data
def load_data():
    ks = pd.read_excel("data_kepala_sekolah.xlsx", sheet_name="KEPALA_SEKOLAH")
    guru = pd.read_excel("data_kepala_sekolah.xlsx", sheet_name="GURU_SIMPEG")
    return ks, guru

try:
    df_ks, df_guru = load_data()
except Exception as e:
    st.error(f"❌ Gagal membaca Excel: {e}")
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
# SEARCH GLOBAL KEPALA SEKOLAH
# ======================
search = st.text_input("🔍 Cari Nama Kepala Sekolah")

if search:
    df_ks = df_ks[df_ks["Nama Kepala Sekolah"].str.contains(search, case=False, na=False)]

# ======================
# SIDEBAR FILTER
# ======================
st.sidebar.header("🔎 Filter")

jenjang = st.sidebar.selectbox(
    "Jenjang",
    ["Semua"] + sorted(df_ks["Jenjang"].dropna().unique())
)

if jenjang != "Semua":
    df_ks = df_ks[df_ks["Jenjang"] == jenjang]

# ======================
# CSS
# ======================
st.markdown("""
<style>
.card {
    border-radius:12px;
    padding:14px;
    margin-bottom:12px;
    background:#f4f6f9;
    border-left:6px solid #1f77b4;
}
.danger {
    background:#fdecea;
    border-left:6px solid #d93025;
}
</style>
""", unsafe_allow_html=True)

# ======================
# CABANG DINAS (FOTO 1)
# ======================
st.subheader("🏢 Cabang Dinas Wilayah")

cabdin_list = sorted(df_ks["Cabang Dinas"].unique())
cols = st.columns(4)

for i, cabdin in enumerate(cabdin_list):
    with cols[i % 4]:
        if st.button(f"📍 {cabdin}", use_container_width=True):
            st.session_state["cabdin"] = cabdin

# ======================
# SEKOLAH DALAM CABDIN (FOTO 2)
# ======================
if "cabdin" in st.session_state:
    st.markdown("---")
    st.subheader(f"📂 {st.session_state['cabdin']}")

    df_cab = df_ks[df_ks["Cabang Dinas"] == st.session_state["cabdin"]]

    for _, row in df_cab.iterrows():
        is_danger = row["Keterangan Akhir"] in ["Harus Diberhentikan", "PLT"]
        css = "danger" if is_danger else "card"

        st.markdown(f"""
        <div class="{css}">
        <b>🏫 {row['Nama Sekolah']}</b><br>
        👤 {row['Nama Kepala Sekolah']}<br>
        <span style="color:red;font-weight:700;">
        {row['Keterangan Akhir']}
        </span>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🔍 Lihat Detail"):
            st.write(f"**NIP:** {row['NIP']}")
            st.write(f"**Jabatan:** {row['Jabatan']}")
            st.write(f"**Jenjang:** {row['Jenjang']}")
            st.write(f"**BCKS:** {row['Sertifikat BCKS']}")
            st.write(f"**Tahun Pengangkatan:** {row['Tahun Pengangkatan']}")

            # ======================
            # CALON PENGGANTI (FOTO 3)
            # ======================
            if is_danger:
                kandidat = df_guru[df_guru["Jenjang"] == row["Jenjang"]]

                pilihan = st.selectbox(
                    "👥 Pilih Calon Pengganti",
                    kandidat["Nama Guru"].tolist(),
                    key=f"{row['NIP']}"
                )

                st.success(f"✅ Calon pengganti dipilih: {pilihan}")

# ======================
# FOOTER
# ======================
st.markdown("""
<hr>
<p style='text-align:center;color:gray;font-size:13px;'>
Dashboard Kepala Sekolah • Dinas Pendidikan Provinsi • Streamlit
</p>
""", unsafe_allow_html=True)
