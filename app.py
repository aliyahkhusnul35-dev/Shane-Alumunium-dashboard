import datetime
from datetime import datetime as dt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import seaborn as sns
import streamlit as st

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Dashboard BI Shane Aluminium",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Palet Warna Lembut (Soft Blue Theme sesuai preferensi)
PRIMARY_COLOR = "#1f77b4"
SECONDARY_COLOR = "#aec7e8"
BG_COLOR = "#f4f6f9"


# Fungsi untuk memuat dan membersihkan data dengan caching
@st.cache_data
def load_data():
  file_path = "Data Penjualan Gabungan Nov 2025-Sept 2026.xlsx"
  df = pd.read_excel(file_path, sheet_name=0)

  # Membersihkan spasi pada nama kolom
  df.columns = df.columns.str.strip()
  df["Tanggal"] = pd.to_datetime(df["Tanggal"])

  # Menangani missing values pada varian produk
  produk_cols = ["Model Rak Solid 2p", "Model Rak Magic 2p", "Model Rak Magic 3p"]
  for col in produk_cols:
    df[col] = df[col].fillna(0)

  # Ekstraksi Bulan dan Tahun untuk filter
  df["Bulan"] = df["Tanggal"].dt.to_period("M").astype(str)
  return df


try:
  df_raw = load_data()
except Exception as e:
  st.error(
      f"Gagal memuat file dataset. Pastikan file Excel berada di direktori"
      f" yang sama dengan app.py. Error: {e}"
  )
  st.stop()

# ==========================================
# SIDEBAR: FILTER & NAVIGASI
# ==========================================
st.sidebar.title("🎛️ Panel Kontrol & Filter")
st.sidebar.markdown(
    "---"
)  # Filter default menampilkan seluruh data historis secara utuh

# Filter Rentang Tanggal
min_date = df_raw["Tanggal"].min().date()
max_date = df_raw["Tanggal"].max().date()

st.sidebar.subheader("Filter Periode Transaksi")
start_date = st.sidebar.date_input("Tanggal Mulai", min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("Tanggal Akhir", max_date, min_value=min_date, max_value=max_date)

# Filter Berdasarkan Keterangan Pembayaran
payment_options = ["Semua"] + list(df_raw["Keterangan"].unique())
selected_payment = st.sidebar.selectbox(
    "Kategori Pembayaran", payment_options
)

# Menerapkan Filter ke DataFrame
df_filtered = df_raw[
    (df_raw["Tanggal"].dt.date >= start_date)
    & (df_raw["Tanggal"].dt.date <= end_date)
]

if selected_payment != "Semua":
  df_filtered = df_filtered[df_filtered["Keterangan"] == selected_payment]

# ==========================================
# HEADER UTAMA DASHBOARD
# ==========================================
st.title("📊 Dashboard Business Intelligence Analisis Perilaku Pelanggan")
st.markdown("**Studi Kasus: Shane Aluminium (Periode Nov 2025 - Sept 2026)**")
st.markdown(
    "Dashboard ini menyajikan informasi penjualan, kinerja produk, perilaku"
    " pembelian pelanggan, dan distribusi pembayaran sebagai pendukung"
    " strategi pemasaran digital[cite: 1]."
)
st.markdown("---")

# ==========================================
# METRIK UTAMA (KPIs)
# ==========================================
total_transaksi = len(df_filtered)
total_penjualan = df_filtered["Jumlah"].sum()
total_unit = df_filtered["Total Unit"].sum()
pelanggan_unik = df_filtered["Toko/Pelanggan"].nunique()
atv = total_penjualan / total_transaksi if total_transaksi > 0 else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
  st.metric(
      label="Total Penjualan", value=f"Rp {total_penjualan:,.0f}".replace(",", ".")
  )
with col2:
  st.metric(label="Total Transaksi", value=f"{total_transaksi} Transaksi")
with col3:
  st.metric(label="Total Unit Terjual", value=f"{total_unit:,} Unit")
with col4:
  st.metric(label="Pelanggan Unik", value=f"{pelanggan_unik} Toko")

st.markdown("---")

# ==========================================
# BARIS 1: TREN PENJUALAN & KINERJA PRODUK
# ==========================================
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
  st.subheader("📈 Tren Nilai Penjualan Bulanan")
  df_filtered["Bulan_Periode"] = df_filtered["Tanggal"].dt.to_period("M").astype(str)
  trend_df = (
      df_filtered.groupby("Bulan_Periode")["Jumlah"]
      .sum()
      .reset_index()
  )

  fig_trend = px.line(
      trend_df,
      x="Bulan_Periode",
      y="Jumlah",
      markers=True,
      labels={
          "Bulan_Periode": "Bulan",
          "Jumlah": "Total Penjualan (Rp)",
      },
      color_discrete_sequence=[PRIMARY_COLOR],
  )
  fig_trend.update_layout(
      xaxis_title="Bulan", yaxis_title="Total Penjualan (Rp)", margin=dict(t=20, b=20)
  )
  st.plotly_chart(fig_trend, use_container_width=True)

with row1_col2:
  st.subheader("📦 Kontribusi Penjualan Berdasarkan Model Rak")
  prod_sales = pd.DataFrame({
      "Produk": ["Rak Solid 2P", "Rak Magic 2P", "Rak Magic 3P"],
      "Total Unit": [
          df_filtered["Model Rak Solid 2p"].sum(),
          df_filtered["Model Rak Magic 2p"].sum(),
          df_filtered["Model Rak Magic 3p"].sum(),
      ],
  })

  fig_prod = px.bar(
      prod_sales,
      x="Produk",
      y="Total Unit",
      text="Total Unit",
      color="Produk",
      color_discrete_sequence=px.colors.qualitative.Pastel,
  )
  fig_prod.update_layout(
      xaxis_title="Model Produk",
      yaxis_title="Jumlah Unit Terjual",
      showlegend=False,
      margin=dict(t=20, b=20),
  )
  st.plotly_chart(fig_prod, use_container_width=True)

st.markdown("---")

# ==========================================
# BARIS 2: ANALISIS PELANGGAN (RFM) & PEMBAYARAN
# ==========================================
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
  st.subheader("🏆 Top 10 Pelanggan (Berdasarkan Nilai Pembelian)")
  rfm_df = (
      df_filtered.groupby("Toko/Pelanggan")
      .agg(
          Frekuensi=("Invoice", "count"),
          Total_Belanja=("Jumlah", "sum"),
      )
      .reset_index()
      .sort_values(by="Total_Belanja", ascending=False)
      .head(10)
  )

  # Format rupiah untuk tabel
  rfm_df["Total_Belanja_Fmt"] = rfm_df["Total_Belanja"].apply(
      lambda x: f"Rp {x:,.0f}".replace(",", ".")
  )
  st.dataframe(
      rfm_df[["Toko/Pelanggan", "Frekuensi", "Total_Belanja_Fmt"]].rename(
          columns={"Total_Belanja_Fmt": "Total Pembelian"}
      ),
      use_container_width=True,
      hide_index=True,
  )

with row2_col2:
  st.subheader("💳 Distribusi Metode Pembayaran")
  pay_df = (
      df_filtered.groupby("Keterangan")["Jumlah"].sum().reset_index()
  )

  fig_pay = px.pie(
      pay_df,
      names="Keterangan",
      values="Jumlah",
      hole=0.4,
      color_discrete_sequence=px.colors.sequential.Blues_r,
  )
  fig_pay.update_layout(margin=dict(t=20, b=20))
  st.plotly_chart(fig_pay, use_container_width=True)

st.markdown("---")

# ==========================================
# BARIS 3: TABEL DETAIL TRANSAKSI
# ==========================================
st.subheader("📋 Ringkasan Data Transaksi Terfilter")
st.markdown(
    "Menampilkan rincian catatan transaksi sesuai dengan filter periode dan"
    " kategori pembayaran yang dipilih."
)

display_df = df_filtered[[
    "Tanggal",
    "Invoice",
    "Toko/Pelanggan",
    "Alamat",
    "Total Unit",
    "Jumlah",
    "Keterangan",
]].copy()
display_df["Tanggal"] = display_df["Tanggal"].dt.strftime("%d-%m-%Y")
display_df["Jumlah"] = display_df["Jumlah"].apply(
    lambda x: f"Rp {x:,.0f}".replace(",", ".")
)

st.dataframe(
    display_df.rename(columns={"Jumlah": "Nilai Transaksi (Rp)"}),
    use_container_width=True,
    hide_index=True,
)

# Catatan kaki Evaluasi/Informasi
st.markdown("---")
st.caption(
    "💡 *Catatan Akademik: Dashboard ini dievaluasi berdasarkan kesesuaian"
    " fungsi, akurasi perhitungan terhadap data sumber, dan kemudahan"
    " penggunaan untuk mendukung strategi pemasaran digital Shane"
    " Aluminium[cite: 1].*"
)
