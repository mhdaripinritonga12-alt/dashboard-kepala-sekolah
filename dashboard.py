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
# LOAD DATA (FIX)
# ======================
@st.cache_data
def load_data():
    ks = pd.read_excel(
        "data_kepala_sekolah.xlsx",
        sheet_name="Dashboard_Kepala_Sekolah"
    )

    guru = pd.read_excel(
        "data_guru_simpeg.xlsx",
        sheet_name="GURU"
    )

    return ks, guru

df_ks, df_guru = load_data()

# ======================
# JUDUL
# ======================
st.markdown("""
<h1 style='color:#0B5394;'>📊 DASHBOARD KEPALA SEKOLAH DINAS PENDIDIKAN</h1>
<hr>
""", unsafe_allow_html=True)

# ======================
# SEARCH GLOBAL KEPALA SEKOLAH
# ======================
search_nama = st.text_input("🔍 Cari Nama Kepala Sekolah")

if search_nama:
    df_ks = df_ks[df_ks["Nama Kepala Sekolah"]
                  .str.contains(search_nama, case=False, na=False)]

# ======================
# SIDEBAR FILTER
# ======================
st.sidebar.header("🔎 Filter Data")

filter_jenjang = st.sidebar.selectbox(
    "Jenjang",
    ["Semua"] + sorted(df_ks["Jenjang"].dropna().unique())
)

filter_status = st.sidebar.selectbox(
    "Keterangan Akhir",
    ["Semua"] + sorted(df_ks["Keterangan Akhir"].dropna().unique())
)

if filter_jenjang != "Semua":
    df_ks = df_ks[df_ks["Jenjang"] == filter_jenjang]

if filter_status != "Semua":
    df_ks = df_ks[df_ks["Keterangan Akhir"] == filter_status]

# ======================
# TAMPILAN CARD CABDIN
# ======================
st.subheader("🏢 Cabang Dinas")

cabdin_list = sorted(df_ks["Cabang Dinas"].unique())

cols = st.columns(4)

for i, cabdin in enumerate(cabdin_list):
    with cols[i % 4]:
        jumlah = df_ks[df_ks["Cabang Dinas"] == cabdin].shape[0]
        st.markdown(f"""
        <div style='border-radius:12px;padding:15px;
        background:#f4f7fb;border-left:6px solid #0B5394;'>
        <h4>📍 {cabdin}</h4>
        <b>{jumlah} Kepala Sekolah</b>
        </div>
        """, unsafe_allow_html=True)

# ======================
# DETAIL PER CABDIN
# ======================
st.subheader("📂 Data Kepala Sekolah per Cabang Dinas")

for cabdin in cabdin_list:
    with st.expander(f"📍 {cabdin}", expanded=False):

        df_c = df_ks[df_ks["Cabang Dinas"] == cabdin]

        for _, row in df_c.iterrows():

            warna = "#ffd6d6" if row["Keterangan Akhir"] == "Harus Diberhentikan" else "#f9f9f9"

            with st.expander(
                f"🏫 {row['Nama Sekolah']} — {row['Nama Kepala Sekolah']}"
            ):
                st.markdown(
                    f"<div style='background:{warna};padding:15px;border-radius:10px'>",
                    unsafe_allow_html=True
                )

                st.write("**Nama Kepala Sekolah:**", row["Nama Kepala Sekolah"])
                st.write("**NIP:**", row["NIP"])
                st.write("**Jenjang:**", row["Jenjang"])
                st.write("**Status Jabatan:**", row["Status Jabatan"])
                st.write("**Keterangan Akhir:**", row["Keterangan Akhir"])

                # ======================
                # CALON PENGGANTI
                # ======================
                if row["Keterangan Akhir"] == "Harus Diberhentikan" or row["Status Jabatan"] == "PLT":

                    calon = df_guru[
                        (df_guru["Jenjang"] == row["Jenjang"]) &
                        (df_guru["Cabang Dinas"] == cabdin)
                    ]["Nama Guru"].tolist()

                    if calon:
                        pengganti = st.selectbox(
                            "👤 Pilih Calon Pengganti",
                            calon,
                            key=f"{row['NIP']}"
                        )
                        st.success(f"Calon pengganti dipilih: {pengganti}")
                    else:
                        st.warning("Tidak ada data guru SIMPEG sesuai")

                st.markdown("</div>", unsafe_allow_html=True)
