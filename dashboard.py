import streamlit as st
import pandas as pd

# ======================
# KONFIGURASI HALAMAN
# ======================
st.set_page_config(
    page_title="Dashboard Kepala Sekolah Dinas Pendidikan",
    layout="wide"
)

# ======================
# LOAD DATA
# ======================
@st.cache_data
def load_data():
    ks = pd.read_excel(
        "data_kepala_sekolah.xlsx",
        sheet_name="Dashboard_Kepala_Sekolah"
    )
    guru = pd.read_excel("data_guru_simpeg.xlsx")
    return ks, guru

df_ks, df_guru = load_data()

# ======================
# VALIDASI KOLOM WAJIB
# ======================
kolom_wajib = [
    "Nama Kepala Sekolah", "NIP", "Jenjang",
    "Nama Sekolah", "Cabang Dinas",
    "Sertifikat BCKS", "Tahun Pengangkatan",
    "Jabatan", "Keterangan Akhir"
]

for col in kolom_wajib:
    if col not in df_ks.columns:
        st.error(f"❌ Kolom '{col}' tidak ditemukan di Excel Kepala Sekolah")
        st.stop()

# ======================
# JUDUL
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
    ["Semua"] + sorted(df_ks["Jenjang"].unique())
)

status = st.sidebar.selectbox(
    "Keterangan Akhir",
    ["Semua"] + sorted(df_ks["Keterangan Akhir"].unique())
)

df = df_ks.copy()

if jenjang != "Semua":
    df = df[df["Jenjang"] == jenjang]

if status != "Semua":
    df = df[df["Keterangan Akhir"] == status]

# ======================
# TAMPILAN PER CABANG DINAS (CARD STYLE)
# ======================
st.subheader("🏢 Data Kepala Sekolah per Cabang Dinas")
st.caption("Klik Cabang Dinas → Sekolah → Detail & Calon Pengganti")

for cabdin in sorted(df["Cabang Dinas"].unique()):
    with st.expander(f"📍 {cabdin}", expanded=False):

        df_cab = df[df["Cabang Dinas"] == cabdin]

        for _, row in df_cab.iterrows():

            warna = "#ffebee" if row["Keterangan Akhir"] == "Harus Diberhentikan" else "#e3f2fd"

            with st.expander(
                f"🏫 {row['Nama Sekolah']} — {row['Nama Kepala Sekolah']}",
                expanded=False
            ):
                st.markdown(
                    f"<div style='background:{warna}; padding:15px; border-radius:10px;'>",
                    unsafe_allow_html=True
                )

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"""
                    **Nama Kepala Sekolah:** {row['Nama Kepala Sekolah']}  
                    **NIP:** {row['NIP']}  
                    **Jabatan:** {row['Jabatan']}  
                    """)

                with col2:
                    st.markdown(f"""
                    **Jenjang:** {row['Jenjang']}  
                    **Sertifikat BCKS:** {row['Sertifikat BCKS']}  
                    **Tahun Pengangkatan:** {row['Tahun Pengangkatan']}  
                    """)

                st.markdown(f"""
                **📌 Status Akhir:**  
                <b style='color:red;'>{row['Keterangan Akhir']}</b>
                """, unsafe_allow_html=True)

                # ======================
                # CALON PENGGANTI
                # ======================
                if row["Keterangan Akhir"] == "Harus Diberhentikan":
                    st.markdown("### 👥 Calon Pengganti (Guru SIMPEG)")

                    calon = df_guru[
                        (df_guru["JENJANG"] == row["Jenjang"])
                        & (df_guru["JABATAN"].str.lower() == "guru")
                    ]

                    if calon.empty:
                        st.warning("⚠️ Tidak ada calon pengganti tersedia")
                    else:
                        st.dataframe(
                            calon[["NAMA GURU", "NIP", "UNOR"]],
                            use_container_width=True
                        )

                st.markdown("</div>", unsafe_allow_html=True)

# ======================
# FOOTER
# ======================
st.markdown("""
<hr>
<p style='text-align:center; font-size:13px; color:gray;'>
Dashboard Kepala Sekolah • Dinas Pendidikan Provinsi • Streamlit
</p>
""", unsafe_allow_html=True)
