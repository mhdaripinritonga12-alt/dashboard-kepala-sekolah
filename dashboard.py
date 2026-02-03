import streamlit as st
import pandas as pd

st.title("🔍 DEBUG EXCEL")

st.write("## File: data_kepala_sekolah.xlsx")
xls1 = pd.ExcelFile("data_kepala_sekolah.xlsx")
st.write(xls1.sheet_names)

st.write("## File: data_guru_simpeg.xlsx")
xls2 = pd.ExcelFile("data_guru_simpeg.xlsx")
st.write(xls2.sheet_names)
