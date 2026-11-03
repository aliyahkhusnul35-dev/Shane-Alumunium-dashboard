import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

# Konfigurasi Halaman Dashboard
st.set_page_config(
    page_title="Dashboard Penjualan Shane Aluminium",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
    <style>
        .main-header { font-size: 28px; font-weight: bold; color: #1E3A8A; }
        .sub-header { font-size: 16px; color: #4B5563; }
        .metric-card { background-color: #F8FAFC; padding: 15px; border-radius: 10px; border: 1px solid #E2E8F0; }
    </style>
""", unsafe_allow_html=True)


@st.cache_data
def load_and_preprocess_data():
  file_path = "Data Penjualan Gabungan Nov 2025-Sept 2026.xlsx"
  xls = pd.ExcelFile(file_path)
  df = pd.read_excel(file_path, sheet_name=xls.sheet_names[0])

  df['Tanggal'] = pd.to_datetime(df['Tanggal '])
  df['Bulan'] = df['Tanggal'].dt.to_period('M').astype(str)

  rak_cols = ['Model Rak Solid 2p', 'Model Rak Magic 2p', 'Model Rak Magic 3p']
  df[rak_cols] = df[rak_cols].fillna(0)

  df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
  df['Total Unit'] = df[rak_cols].sum(axis=1)

  df['Pelanggan_Clean'] = (
      df['Toko/Pelanggan']
      .astype(str)
      .str.strip()
      .str.upper()
  )

  def categorize_payment(ket):
    ket_lower = str(ket).strip().lower()
    if 'cash' in ket_lower or 'tf' in ket_lower:
      return 'Cash / Transfer'
    elif (
        'kredit' in ket_lower
        or 'tempo' in ket_lower
        or 'kontra bon' in ket_lower
        or 'kospin' in ket_lower
    ):
      return 'Kredit / Tempo'
    elif 'giro' in ket_lower:
      return 'Giro'
    else:
      return 'Lainnya'

  df['Kategori_Pembayaran'] = df['Keterangan'].apply(categorize_payment)
  return df


df = load_and_preprocess_data()

# ==========================================
# PANEL KONTROL (SIDEBAR)
# ==========================================
st.sidebar.title("🔍 Filter Dashboard")
st.sidebar.markdown("---")

# 1. Filter Bulan
bulan_list = sorted(df['Bulan'].unique())
bulan_options = ["Semua Bulan"] + bulan_list
selected_bulan_dropdown = st.sidebar.selectbox(
    "Pilih Periode Bulan", options=bulan_options
)

if selected_bulan_dropdown == "Semua Bulan":
  df_filtered_bulan = df
else:
  df_filtered_bulan = df[df['Bulan'] == selected_bulan_dropdown]

# 2. Filter Metode Pembayaran
pembayaran_list = sorted(df['Kategori_Pembayaran'].unique())
pembayaran_options = ["Semua Metode Pembayaran"] + pembayaran_list
selected_pembayaran_dropdown = st.sidebar.selectbox(
    "Metode Pembayaran", options=pembayaran_options
)

if selected_pembayaran_dropdown == "Semua Metode Pembayaran":
  df_filtered = df_filtered_bulan
else:
  df_filtered = df_filtered_bulan[
      df_filtered_bulan['Kategori_Pembayaran'] == selected_pembayaran_dropdown
  ]

# 3. FITUR BARU: Pencarian Toko / Pelanggan Interaktif
st.sidebar.markdown("---")
st.sidebar.markdown("🏪 **Pencarian Toko**")
search_toko = st.sidebar.text_input(
    "Cari Nama Toko / Pelanggan:", placeholder="Contoh: Barokah"
)

if search_toko:
  df_filtered = df_filtered[
      df_filtered['Pelanggan_Clean'].str.contains(search_toko.upper(), na=False)
  ]

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Total Data Terpilih:** {len(df_filtered):,} baris")


# ==========================================
# KONTEN UTAMA DASHBOARD
# ==========================================
st.markdown(
    '<p class="main-header">📊 Dashboard Analisis Penjualan - Shane'
    " Aluminium</p>",
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="sub-header">Sistem Business Intelligence untuk Pemantauan'
    " Performa Penjualan dan Perilaku Pelanggan (CRISP-DM Framework)</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# KPI Kartu Ringkasan (Ditambah rata-rata nilai transaksi)
total_penjualan = df_filtered['Jumlah'].sum()
total_unit = df_filtered['Total Unit'].sum()
total_transaksi = len(df_filtered)
avg_transaksi = (
    total_penjualan / total_transaksi if total_transaksi > 0 else 0
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Total Penjualan", f"Rp {total_penjualan:,.0f}")
col2.metric("📦 Total Unit Terjual", f"{int(total_unit):,} Unit")
col3.metric("📋 Jumlah Transaksi", f"{total_transaksi:,} Transaksi")
col4.metric("📈 Rata-rata / Transaksi", f"Rp {avg_transaksi:,.0f}")

st.markdown("---")

# Baris Grafik 1: Tren Penjualan & Produk
row1_col1, row1_col2 = st.columns(2)
with row1_col1:
  st.subheader("📈 Tren Penjualan Bulanan")
  if not df_filtered.empty:
    trend_data = df_filtered.groupby("Bulan")["Jumlah"].sum().reset_index()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(
        trend_data["Bulan"],
        trend_data["Jumlah"] / 1e6,
        marker="o",
        color="#2563EB",
        linewidth=2.5,
    )
    ax.set_title("Total Penjualan per Bulan (Juta IDR)")
    ax.set_xlabel("Bulan")
    ax.set_ylabel("Penjualan (Juta Rp)")
    plt.xticks(rotation=45)
    st.pyplot(fig)
  else:
    st.warning("Data tidak ditemukan.")

with row1_col2:
  st.subheader("📦 Kontribusi Model Produk Rak")
  if not df_filtered.empty:
    prod_data = pd.Series({
        "Rak Solid 2P": df_filtered["Model Rak Solid 2p"].sum(),
        "Rak Magic 2P": df_filtered["Model Rak Magic 2p"].sum(),
        "Rak Magic 3P": df_filtered["Model Rak Magic 3p"].sum(),
    })
    fig, ax = plt.subplots(figsize=(8, 4))
    prod_data.plot(
        kind="bar",
        ax=ax,
        color=["#0EA5E9", "#F59E0B", "#8B5CF6"],
        edgecolor="black",
    )
    ax.set_title("Total Unit Terjual Berdasarkan Model Rak")
    ax.set_xlabel("Model Produk")
    ax.set_ylabel("Jumlah Unit")
    plt.xticks(rotation=0)
    st.pyplot(fig)
  else:
    st.warning("Data tidak ditemukan.")

st.markdown("---")

# Baris Grafik 2 (FITUR BARU): Distribusi Metode Pembayaran (Pie Chart)
st.subheader("💳 Proporsi Metode Pembayaran")
if not df_filtered.empty:
  pay_counts = df_filtered['Kategori_Pembayaran'].value_counts()
  fig, ax = plt.subplots(figsize=(6, 3.5))
  ax.pie(
      pay_counts,
      labels=pay_counts.index,
      autopct="%1.1f%%",
      startangle=90,
      colors=['#3B82F6', '#10B981', '#F59E0B', '#EF4444'],
  )
  ax.axis("equal")
  st.pyplot(fig)
else:
  st.warning("Data pembayaran tidak tersedia.")

st.markdown("---")

# Bagian Tabel Detail & Fitur Download CSV
st.subheader("📋 Detail Data Transaksi Terfilter")
if not df_filtered.empty:
  st.dataframe(
      df_filtered[[
          "Tanggal",
          "Invoice",
          "Toko/Pelanggan",
          "Alamat",
          "Total Unit",
          "Jumlah",
          "Keterangan",
          "Kategori_Pembayaran",
      ]],
      use_container_width=True,
  )

  # FITUR BARU: Tombol Unduh Laporan CSV
  csv_data = df_filtered.to_csv(index=False).encode('utf-8')
  st.download_button(
      label="📥 Unduh Data Terfilter (CSV)",
      data=csv_data,
      file_name="laporan_penjualan_shane_aluminium.csv",
      mime="text/csv",
  )
else:
  st.warning("Tidak ada data transaksi yang sesuai dengan filter.")
