import streamlit as st
import pandas as pd
import os

# =========================================================
# KONFIGURASI APP
# =========================================================
st.set_page_config(page_title="Dashboard Kepala Sekolah", layout="wide")

DATA_SAVE = "perubahan_kepsek.xlsx"
DATA_FILE = "data_kepala_seIet = st.sidebar.selectbox("Keterangan Akhir", ["Semua"] + sorted(df_ks["Keterangan Akhir"].dropna().unique()))

# =========================================================
# APPLY FILTER
# =========================================================
def apply_filter(df):
    if jenjang_filter != "Semua":
        df = df[df["Jenjang"] == jenjang_filter]

    if ket_filter != "Semua":
        df = df[df["Keterangan Akhir"] == ket_filter]

    if search_nama:
        df = df[df["Nama Kepala Sekolah"].astype(str).str.contains(search_nama, case=False, na=False)]

    if search_sekolah:
        df = df[df["Nama Sekolah"].astype(str).str.contains(search_sekolah, case=False, na=False)]

    return df

# =========================================================
# PENCARIAN SIMPEG
# =========================================================
with st.expander("🔍 Pencarian Guru (SIMPEG)", expanded=False):
    keyword = st.text_input("Ketik Nama Guru atau NIP", placeholder="contoh: Mhd Aripin Ritonga / 1994")

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
# HALAMAN CABDIN
# =========================================================
def page_cabdin():
    col1, col2, col3, col4, col5 = st.columns([5, 2, 2, 2, 2])

    with col1:
        st.markdown("## 📊 Dashboard Kepala Sekolah")

    with col2:
        if st.button("🔄 Refresh SIMPEG", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Data SIMPEG diperbarui")
            st.rerun()

    with col3:
        if st.button("🔄 Refresh Kepsek", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Data Kepala Sekolah diperbarui")
            st.rerun()

    with col4:
        if st.button("📌 Rekapitulasi", use_container_width=True):
            st.session_state.page = "rekap"
            st.rerun()

    with col5:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.login = False
            st.session_state.role = None
            st.session_state.page = "cabdin"
            st.session_state.selected_cabdin = None
            st.session_state.selected_sekolah = None
            st.rerun()

    st.divider()

    df_rekap = df_ks.copy()
    df_rekap["Status Regulatif"] = df_rekap.apply(map_status, axis=1)

    jumlah_p1 = int((df_rekap["Status Regulatif"] == "Aktif Periode 1").sum())
    jumlah_p2 = int((df_rekap["Status Regulatif"] == "Aktif Periode 2").sum())
    jumlah_lebih2 = int((df_rekap["Status Regulatif"] == "Lebih dari 2 Periode").sum())
    jumlah_plt = int((df_rekap["Status Regulatif"] == "Plt").sum())

    total_bisa_diberhentikan = jumlah_p2 + jumlah_lebih2 + jumlah_plt

    st.markdown("## 📌 Rekap Status Kepala Sekolah (Provinsi)")

    colx1, colx2, colx3, colx4, colx5 = st.columns(5)
    colx1.metric("Aktif Periode 1", jumlah_p1)
    colx2.metric("Aktif Periode 2", jumlah_p2)
    colx3.metric("Lebih 2 Periode", jumlah_lebih2)
    colx4.metric("Kasek Plt", jumlah_plt)
    colx5.metric("Bisa Diberhentikan", total_bisa_diberhentikan)

    st.divider()

    # =========================================================
    # DAFTAR CABDIN CARD
    # =========================================================
    st.subheader("🏢 Cabang Dinas Pendidikan Wilayah")

    df_view = apply_filter(df_ks)
    cabdin_list = urutkan_cabdin(df_view["Cabang Dinas"].dropna().unique())

    cols = st.columns(4)
    for i, cabdin in enumerate(cabdin_list):
        with cols[i % 4]:
            if st.button(f"📍 {cabdin}", key=f"cabdin_{i}", use_container_width=True):
                st.session_state.selected_cabdin = cabdin
                st.session_state.page = "sekolah"
                st.session_state.selected_status_filter = "SEMUA"
                st.rerun()

    st.divider()

    # =========================================================
    # REKAP PER CABDIN (KLIK ANGKA)
    # =========================================================
    st.markdown("## 📑 Rekap Kepala Sekolah per Cabang Dinas")
    st.caption("Klik angka P1 / P2 / >2 / Plt / Bisa Diberhentikan untuk melihat daftar sekolahnya.")

    rekap_cabdin = (
        df_rekap
        .groupby(["Cabang Dinas", "Status Regulatif"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    for col in ["Aktif Periode 1", "Aktif Periode 2", "Lebih dari 2 Periode", "Plt"]:
        if col not in rekap_cabdin.columns:
            rekap_cabdin[col] = 0

    rekap_cabdin["Bisa Diberhentikan"] = (
        rekap_cabdin["Aktif Periode 2"] +
        rekap_cabdin["Lebih dari 2 Periode"] +
        rekap_cabdin["Plt"]
    )

    rekap_cabdin["__urut__"] = rekap_cabdin["Cabang Dinas"].apply(
        lambda x: int("".join(filter(str.isdigit, str(x)))) if "".join(filter(str.isdigit, str(x))) else 999
    )
    rekap_cabdin = rekap_cabdin.sort_values("__urut__").drop(columns="__urut__")

    # HEADER
    h = st.columns([4, 1, 1, 1, 1, 1.5])
    h[0].markdown("**Nama Cabdis**")
    h[1].markdown("**P1**")
    h[2].markdown("**P2**")
    h[3].markdown("**>2**")
    h[4].markdown("**Plt**")
    h[5].markdown("**Bisa Diberhentikan**")

    st.divider()

    # ROW DATA
    for i, row in rekap_cabdin.iterrows():
        cabdin = row["Cabang Dinas"]

        c1, c2, c3, c4, c5, c6 = st.columns([4, 1, 1, 1, 1, 1.5])

        c1.write(f"🏢 {cabdin}")

        with c2:
            if st.button(str(int(row["Aktif Periode 1"])), key=f"p1_{i}"):
                st.session_state.selected_cabdin = cabdin
                st.session_state.selected_status_filter = "Aktif Periode 1"
                st.session_state.page = "sekolah"
                st.rerun()

        with c3:
            if st.button(str(int(row["Aktif Periode 2"])), key=f"p2_{i}"):
                st.session_state.selected_cabdin = cabdin
                st.session_state.selected_status_filter = "Aktif Periode 2"
                st.session_state.page = "sekolah"
                st.rerun()

        with c4:
            if st.button(str(int(row["Lebih dari 2 Periode"])), key=f"lebih2_{i}"):
                st.session_state.selected_cabdin = cabdin
                st.session_state.selected_status_filter = "Lebih dari 2 Periode"
                st.session_state.page = "sekolah"
                st.rerun()

        with c5:
            if st.button(str(int(row["Plt"])), key=f"plt_{i}"):
                st.session_state.selected_cabdin = cabdin
                st.session_state.selected_status_filter = "Plt"
                st.session_state.page = "sekolah"
                st.rerun()

        with c6:
            if st.button(str(int(row["Bisa Diberhentikan"])), key=f"bisa_{i}"):
                st.session_state.selected_cabdin = cabdin
                st.session_state.selected_status_filter = "BISA_DIBERHENTIKAN"
                st.session_state.page = "sekolah"
                st.rerun()

    st.divider()

# =========================================================
# HALAMAN SEKOLAH
# =========================================================
def page_sekolah():
    if st.session_state.selected_cabdin is None:
        st.session_state.page = "cabdin"
        st.rerun()

    status_filter = st.session_state.get("selected_status_filter", "SEMUA")

    col_a, col_b, col_c = st.columns([1, 6, 1])

    with col_a:
        if st.button("🏠", key="home_sekolah"):
            st.session_state.page = "cabdin"
            st.session_state.selected_cabdin = None
            st.session_state.selected_sekolah = None
            st.session_state.selected_status_filter = "SEMUA"
            st.rerun()

    with col_b:
        if status_filter == "SEMUA":
            st.subheader(f"🏫 Daftar Sekolah — {st.session_state.selected_cabdin}")
        else:
            st.subheader(f"🏫 Sekolah {status_filter} — {st.session_state.selected_cabdin}")

    with col_c:
        if st.button("⬅️", key="back_sekolah"):
            st.session_state.page = "cabdin"
            st.session_state.selected_cabdin = None
            st.session_state.selected_sekolah = None
            st.session_state.selected_status_filter = "SEMUA"
            st.rerun()

    df_cab = df_ks[df_ks["Cabang Dinas"] == st.session_state.selected_cabdin].copy()
    df_cab = apply_filter(df_cab)

    if df_cab.empty:
        st.warning("⚠️ Tidak ada data sekolah pada Cabang Dinas ini.")
        st.stop()

    df_cab["Status Regulatif"] = df_cab.apply(map_status, axis=1)

    # FILTER SESUAI KLIK ANGKA
    if status_filter == "Aktif Periode 1":
        df_cab = df_cab[df_cab["Status Regulatif"] == "Aktif Periode 1"]

    elif status_filter == "Aktif Periode 2":
        df_cab = df_cab[df_cab["Status Regulatif"] == "Aktif Periode 2"]

    elif status_filter == "Lebih dari 2 Periode":
        df_cab = df_cab[df_cab["Status Regulatif"] == "Lebih dari 2 Periode"]

    elif status_filter == "Plt":
        df_cab = df_cab[df_cab["Status Regulatif"] == "Plt"]

    elif status_filter == "BISA_DIBERHENTIKAN":
        df_cab = df_cab[df_cab["Status Regulatif"].isin(["Aktif Periode 2", "Lebih dari 2 Periode", "Plt"])]

    st.markdown(f"### 📌 Jumlah Sekolah Ditampilkan: {len(df_cab)}")
    st.divider()

    cols = st.columns(4)
    idx = 0

    for _, row in df_cab.iterrows():
        nama_sekolah = str(row.get("Nama Sekolah", "-"))
        status_reg = map_status(row)

        if status_reg == "Aktif Periode 1":
            warna = "🟦"
        elif status_reg == "Aktif Periode 2":
            warna = "🟨"
        elif status_reg == "Lebih dari 2 Periode":
            warna = "🟥"
        elif status_reg == "Plt":
            warna = "🟩"
        else:
            warna = "⬜"

        with cols[idx % 4]:
            if st.button(f"{warna} {nama_sekolah}", key=f"btn_sekolah_{idx}", use_container_width=True):
                st.session_state.selected_sekolah = nama_sekolah
                st.session_state.page = "detail"
                st.rerun()

        idx += 1

# =========================================================
# FIELD WARNA
# =========================================================
def tampil_colored_field(label, value, bg="#f1f1f1", text_color="black"):
    st.markdown(f"""
    <div style="padding:10px; border-radius:10px; background:{bg}; margin-bottom:8px;">
        <b>{label}:</b>
        <span style="color:{text_color}; font-weight:700;"> {value}</span>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# HALAMAN DETAIL SEKOLAH
# =========================================================
def page_detail():
    if st.session_state.selected_sekolah is None:
        st.session_state.page = "sekolah"
        st.rerun()

    col_a, col_b, col_c = st.columns([1, 6, 1])

    with col_a:
        if st.button("🏠", key="home_detail"):
            st.session_state.page = "cabdin"
            st.session_state.selected_cabdin = None
            st.session_state.selected_sekolah = None
            st.session_state.selected_status_filter = "SEMUA"
            st.rerun()

    with col_b:
        st.subheader(f"📄 Detail Sekolah: {st.session_state.selected_sekolah}")

    with col_c:
        if st.button("⬅️", key="back_detail"):
            st.session_state.page = "sekolah"
            st.session_state.selected_sekolah = None
            st.rerun()

    nama = str(st.session_state.selected_sekolah).replace("\xa0", " ").strip()

    row_detail = df_ks[
        df_ks["Nama Sekolah"]
        .astype(str)
        .str.replace("\xa0", " ", regex=False)
        .str.strip()
        == nama
    ]

    if row_detail.empty:
        st.error("❌ Data sekolah tidak ditemukan.")
        st.stop()

    row = row_detail.iloc[0]

    st.divider()
    st.markdown("## 📝 Data Lengkap (Sesuai Excel)")

    status_regulatif = map_status(row)

    jabatan = str(row.get("Keterangan Jabatan", "")).lower()
    bcks = str(row.get("Ket Sertifikat BCKS", "")).lower()

    bg_ket = "#dbeeff"
    if "periode 2" in status_regulatif.lower():
        bg_ket = "#fff3cd"
    if "lebih dari 2" in status_regulatif.lower():
        bg_ket = "#f8d7da"
    if "plt" in status_regulatif.lower():
        bg_ket = "#d1e7dd"

    bg_jabatan = "#dbeeff"
    if "plt" in jabatan:
        bg_jabatan = "#d1e7dd"

    bg_bcks = "#dbeeff"
    if "belum" in bcks or "tidak" in bcks:
        bg_bcks = "#f8d7da"

    col_left, col_right = st.columns(2)

    with col_left:
        tampil_colored_field("NO", row.get("NO", "-"))
        tampil_colored_field("Nama Kepala Sekolah", row.get("Nama Kepala Sekolah", "-"))
        tampil_colored_field("Status", row.get("Status", "-"))
        tampil_colored_field("Cabang Dinas", row.get("Cabang Dinas", "-"))
        tampil_colored_field("Ket Sertifikat BCKS", row.get("Ket Sertifikat BCKS", "-"), bg=bg_bcks)
        tampil_colored_field("Tahun Berjalan", row.get("Tahun Berjalan", "-"))
        tampil_colored_field("Keterangan Akhir (Regulatif)", status_regulatif, bg=bg_ket)

    with col_right:
        tampil_colored_field("Nama Sekolah", row.get("Nama Sekolah", "-"))
        tampil_colored_field("Jenjang", row.get("Jenjang", "-"))
        tampil_colored_field("Kabupaten", row.get("Kabupaten", "-"))
        tampil_colored_field("Keterangan Jabatan", row.get("Keterangan Jabatan", "-"), bg=bg_jabatan)
        tampil_colored_field("Tahun Pengangkatan", row.get("Tahun Pengangkatan", "-"))
        tampil_colored_field("Masa Periode Sesuai KSPSTK", row.get("Masa Periode Sesuai KSPSTK", "-"))
        tampil_colored_field("Riwayat Dapodik", row.get("Riwayat Dapodik", "-"))

        pengganti = perubahan_kepsek.get(nama, "-")
        tampil_colored_field("Calon Pengganti jika Sudah Harus di Berhentikan", pengganti)

    st.divider()

    is_view_only = st.session_state.role in ["Kadis", "View"]
    calon_tersimpan = perubahan_kepsek.get(nama)

    if is_view_only:
        st.info("ℹ️ Anda login sebagai **View Only**. Tidak dapat mengubah data.")
    else:
        calon = st.selectbox("👤 Pilih Calon Pengganti (SIMPEG)", guru_list, key=f"calon_{nama}")

        if st.button("💾 Simpan Pengganti", key="btn_simpan_pengganti", use_container_width=True):
            perubahan_kepsek[nama] = calon
            save_perubahan(perubahan_kepsek)
            st.success(f"✅ Diganti dengan: {calon}")
            st.rerun()

    if calon_tersimpan:
        st.info(f"👤 Pengganti Saat Ini: **{calon_tersimpan}**")

        if not is_view_only:
            if st.button("✏️ Kembalikan ke Kepala Sekolah Lama", key="btn_kembali_lama", use_container_width=True):
                perubahan_kepsek.pop(nama, None)
                save_perubahan(perubahan_kepsek)
                st.success("🔄 Berhasil dikembalikan")
                st.rerun()

# =========================================================
# HALAMAN REKAP
# =========================================================
def page_rekap():
    st.markdown("## 📌 Rekap Kepala Sekolah Bisa Diberhentikan")
    st.info("Fitur rekap bisa ditambah sesuai kebutuhan")

# =========================================================
# ROUTING UTAMA
# =========================================================
if st.session_state.page == "cabdin":
    page_cabdin()

elif st.session_state.page == "sekolah":
    page_sekolah()

elif st.session_state.page == "detail":
    page_detail()

elif st.session_state.page == "rekap":
    page_rekap()

# =========================================================
# FOOTER
# =========================================================
st.divider()
st.caption("Dashboard Kepala Sekolah • MHD. ARIPIN RITONGA, S.Kom")
