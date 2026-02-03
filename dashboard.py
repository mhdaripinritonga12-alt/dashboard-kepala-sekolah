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
    ks = pd.read_excel("data_kepala_sekolah.xlsx", sheet_name="KEPALA_SEKOLAH")
    guru = pd.read_excel("data_kepala_sekolah.xlsx", sheet_name="SIMPEG_GURU")
    return ks, guru

df_ks, df_guru = load_data()

# ======================
# VALIDASI KOLOM
# ======================
wajib_ks = [
    "Cabang Dinas", "Nama Sekolah", "Nama Kepala Sekolah",
    "Jenjang", "NIP", "Keterangan Akhir"
]
for c in wajib_ks:
    if c not in df_ks.columns:
        st.error(f"❌ Kolom '{c}' tidak ada di Sheet KEPALA_SEKOLAH")
        st.stop()

wajib_guru = ["Nama Guru", "NIP", "Jenjang", "Cabang Dinas", "Status PNS"]
for c in wajib_guru:
    if c not in df_guru.columns:
        st.error(f"❌ Kolom '{c}' tidak ada di Sheet SIMPEG_GURU")
        st.stop()

# ======================
# HEADER
# ======================
st.markdown("""
<h1 style="color:#0B5394;font-weight:800;">
📊 DASHBOARD KEPALA SEKOLAH DINAS PENDIDIKAN
</h1>
<hr>
""", unsafe_allow_html=True)

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
# CSS CARD
# ======================
st.markdown("""
<style>
.card {padding:16px;border-radius:12px;margin-bottom:12px;background:#f4f6f9;}
.red {background:#fdecea;border-left:6px solid #d93025;}
.blue {border-left:6px solid #1f77b4;}
</style>
""", unsafe_allow_html=True)

# ======================
# TAMPILAN PER CABDIN
# ======================
st.subheader("🏢 Cabang Dinas Wilayah")

for cabdin in sorted(df_ks["Cabang Dinas"].unique()):
    with st.expander(f"📍 {cabdin}", expanded=False):
        df_c = df_ks[df_ks["Cabang Dinas"] == cabdin]

        for _, row in df_c.iterrows():

            diberhentikan = row["Keterangan Akhir"] == "Harus Diberhentikan"
            warna = "red" if diberhentikan else "blue"

            st.markdown(
                f"""
                <div class="card {warna}">
                <b>🏫 {row['Nama Sekolah']}</b><br>
                👤 {row['Nama Kepala Sekolah']}<br>
                <b style="color:red;">{row['Keterangan Akhir']}</b>
                </div>
                """,
                unsafe_allow_html=True
            )

            # ======================
            # DETAIL + CALON PENGGANTI
            # ======================
            with st.expander("🔍 Detail & Penetapan Pengganti", expanded=False):

                st.write(f"**NIP:** {row['NIP']}")
                st.write(f"**Jenjang:** {row['Jenjang']}")
                st.write(f"**Cabang Dinas:** {row['Cabang Dinas']}")

                # 🔴 LOGIKA CALON PENGGANTI
                if diberhentikan:
                    st.markdown("### 🧑‍🏫 Calon Pengganti (SIMPEG)")

                    kandidat = df_guru[
                        (df_guru["Status PNS"] == "PNS") &
                        (df_guru["Jenjang"] == row["Jenjang"]) &
                        (df_guru["Cabang Dinas"] == row["Cabang Dinas"])
                    ]

                    if kandidat.empty:
                        st.warning("⚠️ Tidak ada calon pengganti tersedia")
                    else:
                        pilihan = kandidat["Nama Guru"].tolist()

                        calon = st.selectbox(
                            "Pilih Calon Pengganti",
                            ["-- Pilih Guru --"] + pilihan,
                            key=f"{row['NIP']}"
                        )

                        if calon != "-- Pilih Guru --":
                            nip_calon = kandidat[kandidat["Nama Guru"] == calon]["NIP"].values[0]
                            st.success(f"✅ Calon Pengganti: {calon} ({nip_calon})")

                else:
                    st.info("ℹ️ Kepala sekolah masih aktif")

# ======================
# FOOTER
# ======================
st.markdown("""
<hr>
<p style="text-align:center;font-size:13px;color:gray;">
Dashboard Kepala Sekolah • Final • Anti Error
</p>
""", unsafe_allow_html=True)
