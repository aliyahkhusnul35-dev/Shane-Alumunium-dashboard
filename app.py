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
        .main-header { font-size: 26px; font-weight: bold; color: #1E3A8A; }
        .sub-header { font-size: 16px; color: #4B5563; }
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
# PANEL KONTROL (FILTER INTERAKTIF & BERSIH)
# ==========================================
st.sidebar.title("Panel Kontrol")
st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Info:** Dashboard secara *default* menampilkan **seluruh data"
    " keseluruhan**. Gunakan filter di bawah jika ingin menyaring data"
    " tertentu."
)

with st.sidebar.expander("⚙️ Filter Data Interaktif", expanded=True):
  # 1. FILTER BULAN MENGGUNAKAN RENTANG (SLIDER)
  # Jauh lebih rapi daripada mencentang satu-persatu bulan yang panjang
  bulan_list = sorted(df['Bulan'].unique())
  st.markdown("📅 **Rentang Periode Bulan**")
  selected_start_bulan, selected_end_bulan = st.select_slider(
      "Pilih Rentang Bulan:",
      options=bulan_list,
      value=(bulan_list[0], bulan_list[-1]),
  )

  st.markdown("---")

  # 2. FILTER METODE PEMBAYARAN MENGGUNAKAN CHECKBOX RINGKAS
  st.markdown("💳 **Metode Pembayaran**")
  pembayaran_list = sorted(df['Kategori_Pembayaran'].unique())

  # Tombol pilih semua otomatis aktif di awal (Default tampil semua)
  select_all_payment = st.checkbox("Pilih Semua Pembayaran", value=True)

  selected_pembayaran = []
  for p in pembayaran_list:
    # Jika select all aktif, otomatis tercentang semua
    if select_all_payment:
      checked = st.checkbox(p, value=True, key=f"pay_{p}")
    else:
      checked = st.checkbox(p, value=False, key=f"pay_{p}")

    if checked:
      selected_pembayaran.append(p)

# Filter Data Berdasarkan Pilihan Interaktif
df_filtered = df[
    (df['Bulan'] >= selected_start_bulan)
    & (df['Bulan'] <= selected_end_bulan)
    & (df['Kategori_Pembayaran'].isin(selected_pembayaran))
]

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
    " Performa Penjualan dan Perilaku Pelanggan</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# KPI Kartu Ringkasan
total_penjualan = df_filtered['Jumlah'].sum()
total_unit = df_filtered['Total Unit'].sum()
total_transaksi = len(df_filtered)
total_pelanggan = df_filtered['Pelanggan_Clean'].nunique()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Nilai Penjualan", f"Rp {total_penjualan:,.0f}")
col2.metric("Total Unit Terjual", f"{int(total_unit):,} Unit")
col3.metric("Jumlah Transaksi", f"{total_transaksi:,} Transaksi")
col4.metric("Total Pelanggan Aktif", f"{total_pelanggan:,} Toko")

st.markdown("---")

# Grafik Analisis
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
        linewidth=2,
    )
    ax.set_title("Total Penjualan per Bulan (Juta IDR)")
    ax.set_xlabel("Bulan")
    ax.set_ylabel("Penjualan (Juta Rp)")
    plt.xticks(rotation=45)
    st.pyplot(fig)
  else:
    st.warning("Data tidak ditemukan untuk rentang filter tersebut.")

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
    st.warning("Data tidak ditemukan untuk rentang filter tersebut.")

st.markdown("---")
st.subheader("📋 Detail Data Transaksi")
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
else:
  st.warning("Tidak ada data transaksi yang sesuai dengan filter.")
