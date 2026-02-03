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
# LOAD DATA
# ======================
@st.cache_data
def load_data():
    ks = pd.read_excel("data_kepala_sekolah.xlsx")
    guru = pd.read_excel("data_guru_simpeg.xlsx")
    return ks, guru

df_ks, df_guru = load_data()

# ======================
# VALIDASI KOLOM KS
# ======================
kolom_ks = [
    "Cabang Dinas", "Nama Sekolah", "Nama Kepala Sekolah",
    "NIP", "Jabatan", "Jenjang",
    "Sertifikat BCKS", "Tahun Pengangkatan",
    "Keterangan Akhir"
]

for k in kolom_ks:
    if k not in df_ks.columns:
        st.error(f"❌ Kolom '{k}' tidak ada di data_kepala_sekolah.xlsx")
        st.stop()

# ======================
# TENTUKAN KOLOM NAMA GURU (INI PENTING)
# ======================
# 🔴 SESUAIKAN DENGAN EXCEL SIMPEG ANDA
NAMA_GURU_COL = "NAMA"   # ← GANTI JIKA DI EXCEL BEDA

if NAMA_GURU_COL not in df_guru.columns:
    st.error(
        f"❌ Kolom '{NAMA_GURU_COL}' tidak ditemukan di data_guru_simpeg.xlsx\n\n"
        f"👉 Buka Excel SIMPEG dan SESUAIKAN nama kolom"
    )
    st.stop()

# ======================
# HEADER
# ======================
st.title("📊 Dashboard Kepala Sekolah – Dinas Pendidikan")

# ======================
# FILTER SIDEBAR
# ======================
st.sidebar.header("🔎 Filter")

jenjang = st.sidebar.selectbox(
    "Jenjang",
    ["Semua"] + sorted(df_ks["Jenjang"].dropna().unique())
)

if jenjang != "Semua":
    df_ks = df_ks[df_ks["Jenjang"] == jenjang]

# ======================
# TAMPILAN CABANG DINAS
# ======================
st.subheader("🏢 Cabang Dinas Wilayah")

for cabdin in sorted(df_ks["Cabang Dinas"].unique()):
    with st.expander(f"📍 {cabdin}", expanded=False):

        df_cab = df_ks[df_ks["Cabang Dinas"] == cabdin]

        for _, row in df_cab.iterrows():

            status = row["Keterangan Akhir"]
            warna = "red" if status in ["PLT", "Harus Diberhentikan"] else "green"

            st.markdown(
                f"""
                **🏫 {row['Nama Sekolah']}**  
                👤 {row['Nama Kepala Sekolah']}  
                <span style="color:{warna}; font-weight:700;">{status}</span>
                """,
                unsafe_allow_html=True
            )

            with st.expander("🔍 Lihat Detail"):
                st.write(f"**NIP:** {row['NIP']}")
                st.write(f"**Jabatan:** {row['Jabatan']}")
                st.write(f"**Jenjang:** {row['Jenjang']}")
                st.write(f"**BCKS:** {row['Sertifikat BCKS']}")
                st.write(f"**Tahun Pengangkatan:** {row['Tahun Pengangkatan']}")

                # ======================
                # CALON PENGGANTI
                # ======================
                if status in ["PLT", "Harus Diberhentikan"]:
                    st.warning("⚠ Kepala Sekolah perlu diganti")

                    calon = st.selectbox(
                        "Pilih Calon Pengganti (Guru SIMPEG)",
                        options=sorted(df_guru[NAMA_GURU_COL].dropna().unique()),
                        key=f"{row['Nama Sekolah']}_pengganti"
                    )

                    st.success(f"✅ Calon Pengganti Dipilih: **{calon}**")

# ======================
# FOOTER
# ======================
st.markdown("---")
st.caption("Dashboard Kepala Sekolah • Streamlit • Dinas Pendidikan")
