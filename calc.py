import streamlit as st
import math
import random
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Pibal Teodolit & Hodograph Analyzer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INSTANSIASI STATE MEMORI SIMULASI ---
if 'generated_records' not in st.session_state:
    st.session_state.generated_records = []
if 'hodo_points' not in st.session_state:
    st.session_state.hodo_points = []
if 'last_idx' not in st.session_state:
    st.session_state.last_idx = 0
if 'selected_row_idx' not in st.session_state:
    st.session_state.selected_row_idx = 1

elevation_waingapu = 32.8

# --- HEADER APLIKASI ---
st.markdown(
    """
    <div style='background-color:#0d3b66; padding:15px; border-radius:8px; text-align:center; color:white; margin-bottom:20px;'>
        <h2 style='margin:0; color:white;'>APLIKASI SIMULATOR PIBAL & ANALIS HODOGRAPH</h2>
        <p style='margin:5px 0 0 0; font-style:italic; font-size:14px;'>Stasiun Meteorologi Waingapu (97340) | Analisis Angin Udara Atas Realistis</p>
    </div>
    """, 
    unsafe_allow_html=True
)

# --- DETEKSI OTOMATIS MUSIM ---
current_month = datetime.now().month
if current_month in [5, 6, 7, 8, 9]:
    status_deteksi = f"*Deteksi Otomatis Musim: Musim Timur (Bulan {current_month})"
elif current_month in [11, 12, 1, 2, 3]:
    status_deteksi = f"*Deteksi Otomatis Musim: Musim Barat (Bulan {current_month})"
else:
    status_deteksi = f"*Deteksi Otomatis Musim: Pancaroba (Bulan {current_month})"

# --- FUNGSI CORE ENGINE GENERATOR AZIMUT & ELEVASI ---
def run_generation_core(target_readings, rate_ft_min, base_azimuth, atmos_mode, fresh=False):
    if fresh:
        st.session_state.generated_records = []
        st.session_state.hodo_points = []
        st.session_state.last_idx = 0
        st.session_state.selected_row_idx = 1

    if target_readings <= st.session_state.last_idx:
        st.warning(f"Data sudah ter-generate sebanyak {st.session_state.last_idx} baris.")
        return

    start_loop = st.session_state.last_idx + 1
    
    # Inisialisasi posisi tracking untuk kalkulasi reduksi angin internal
    prev_x, prev_y = 0.0, 0.0
    if not fresh and st.session_state.generated_records:
        # Rekonstruksi posisi koordinat terakhir jika melanjutkan data
        last_rec = st.session_state.generated_records[-1]
        h_d = last_rec["_h_dist"]
        az_rad = math.radians(last_rec["_az_deg"])
        prev_x = h_d * math.sin(az_rad)
        prev_y = h_d * math.cos(az_rad)

    for idx in range(start_loop, target_readings + 1):
        height_above_stn = idx * 500.0
        target_level = math.ceil(idx / 2) * 1000
        level_target_str = f"Level {target_level} ft"
        dt = (500.0 / rate_ft_min) * 60.0

        # PEMODELAN TRACKING UTAMA (Mengacu Tren Asli Foto Logbook)
        if atmos_mode == "Tipe A (Meliuk Balik / Sampel 1)":
            azimuth_deg = (base_azimuth - (idx * 4.0) + 32 * math.sin(idx * 0.22) + random.uniform(-0.5, 0.5)) % 360
            if idx <= 5:
                elevation_deg = max(20.0, 28.5 - ((idx - 1) * 1.35) + random.uniform(-0.3, 0.3))
            elif idx <= 17:
                elevation_deg = min(66.0, 23.0 + ((idx - 5) * 3.42) + random.uniform(-0.4, 0.4))
            else:
                elevation_deg = max(40.0, 64.0 - ((idx - 17) * 1.32) + random.uniform(-0.3, 0.3))
                
        elif atmos_mode == "Tipe B (Lapisan Stabil / Sampel 2)":
            if idx <= 4:
                azimuth_deg = (base_azimuth - ((idx - 1) * 24.0) + random.uniform(-1.0, 1.0)) % 360
            else:
                azimuth_deg = (315.0 - ((idx - 4) * 1.0) + random.uniform(-0.4, 0.4)) % 360
            if idx <= 6:
                elevation_deg = max(20.0, 47.0 - ((idx - 1) * 5.4) + random.uniform(-0.4, 0.4))
            else:
                elevation_deg = 20.0 - ((idx - 6) * 0.05) + (math.sin(idx * 0.5) * 0.4) + random.uniform(-0.2, 0.2)
                
        else: # Tipe C (Angin Tenang / Sampel 3)
            azimuth_deg = (base_azimuth + (math.sin(idx * 0.6) * 4.0) + random.uniform(-0.6, 0.6)) % 360
            if idx <= 4:
                elevation_deg = min(70.0, 63.0 + ((idx - 1) * 1.5) + random.uniform(-0.4, 0.4))
            else:
                elevation_deg = 59.0 + (math.cos(idx * 0.4) * 2.5) + random.uniform(-0.3, 0.3)

        # REDUKSI PIBAL: Menghitung komponen angin riil (U, V) untuk plot Hodograph sejati
        elev_rad = math.radians(elevation_deg)
        horizontal_dist = height_above_stn / math.tan(elev_rad) if math.tan(elev_rad) != 0 else 0
        az_rad = math.radians(azimuth_deg)
        x_pos = horizontal_dist * math.sin(az_rad)
        y_pos = horizontal_dist * math.cos(az_rad)
        
        dx = x_pos - prev_x
        dy = y_pos - prev_y
        
        # Konversi pergerakan jarak komponen ke satuan Knot (1 kt = 1.68781 ft/s)
        u_kt = (dx / dt) / 1.68781
        v_kt = (dy / dt) / 1.68781
        
        # Plot arah tiup (simpan komponen inversi U/V meteo)
        st.session_state.hodo_points.append((u_kt, v_kt, height_above_stn))
        
        prev_x, prev_y = x_pos, y_pos

        azimuth_str = f"{azimuth_deg:.1f}".replace('.', ',')
        elevation_str = f"{elevation_deg:.1f}".replace('.', ',')

        st.session_state.generated_records.append({
            "Pembacaan Ke-": idx,
            "Tinggi Balon (ft)": f"{int(height_above_stn)} ft",
            "Level Target (BMKG)": level_target_str,
            "AZIMUT": azimuth_str,
            "ELEVASI": elevation_str,
            "_h_dist": horizontal_dist,
            "_az_deg": azimuth_deg
        })

    st.session_state.last_idx = target_readings

# --- LAYOUT DENGAN DUA KOLOM UTAMA ---
col_left, col_right = st.columns([6, 6], gap="large")

# === KOLOM KIRI: PARAMETER INPUT & TABEL DATA ===
with col_left:
    st.subheader("⚙️ Parameter Kontrol Simulator")
    
    c1, c2 = st.columns(2)
    with c1:
        target_readings = st.number_input("Target Jumlah Pembacaan (Menit):", min_value=1, value=31, step=1)
        base_azimuth = st.number_input("Azimut Menit Ke-1 (°):", min_value=0.0, max_value=360.0, value=313.0, step=1.0)
    with c2:
        rate_ft_min = st.number_input("Laju Naik Balon (ft/min):", min_value=1.0, value=600.0, step=10.0)
        selected_mode = st.selectbox(
            "🎯 Tren Karakteristik Data (Sesuai Logbook Asli):",
            ["Tipe A (Meliuk Balik / Sampel 1)", "Tipe B (Lapisan Stabil / Sampel 2)", "Tipe C (Angin Tenang / Sampel 3)"]
        )

    b1, b2 = st.columns(2)
    with b1:
        if st.button("⚡ Generate Baru", type="primary", use_container_width=True):
            run_generation_core(target_readings, rate_ft_min, base_azimuth, selected_mode, fresh=True)
    with b2:
        if st.button("⏩ Lanjutkan Ketinggian", use_container_width=True):
            if st.session_state.last_idx == 0:
                st.error("Belum ada data awal. Silakan klik 'Generate Baru' terlebih dahulu.")
            else:
                run_generation_core(target_readings, rate_ft_min, base_azimuth, selected_mode, fresh=False)

    st.markdown("---")
    st.subheader("📊 Tabel Hasil Pembacaan Teropong")
    
    if st.session_state.generated_records:
        df = pd.DataFrame(st.session_state.generated_records)
        display_df = df.drop(columns=["_h_dist", "_az_deg"])
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data. Atur parameter lalu klik 'Generate Baru'.")

# === KOLOM KANAN: HODOGRAPH PREMIUM & ANALISIS METEO ===
with col_right:
    st.subheader("🎯 Hodograph Profil Angin Udara Atas (Knots)")
    
    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    ax.set_aspect('equal')
    
    # Membuat lingkaran konsentrik batas kecepatan knot (10, 20, 30, 40 Knots)
    max_hodo_range = 40
    for knots in [10, 20, 30, 40]:
        circle = plt.Circle((0, 0), knots, color='#bdc3c7', fill=False, linestyle='--', linewidth=1.0)
        ax.add_patch(circle)
        ax.text(0.5, knots + 0.5, f"{knots} kt", color='#7f8c8d', fontsize=8, weight='italic')
        
    # Garis bantu sumbu salib tengah
    ax.axhline(0, color='#95a5a6', linestyle='-', linewidth=1.0)
    ax.axvline(0, color='#95a5a6', linestyle='-', linewidth=1.0)
    
    # Label Kardinal Arah Datangnya Angin
    ax.text(0, max_hodo_range - 3, "U (360°)", weight='bold', ha='center', va='bottom', color='#2c3e50')
    ax.text(0, -max_hodo_range + 1, "S (180°)", weight='bold', ha='center', va='top', color='#2c3e50')
    ax.text(max_hodo_range - 1, 0, "T (90°)", weight='bold', ha='left', va='center', color='#2c3e50')
    ax.text(-max_hodo_range + 1, 0, "B (270°)", weight='bold', ha='right', va='center', color='#2c3e50')
    
    # Pemetaan Data Titik Vektor Hodograph
    if st.session_state.hodo_points:
        u_pts = [p[0] for p in st.session_state.hodo_points]
        v_pts = [p[1] for p in st.session_state.hodo_points]
        heights = [p[2] for p in st.session_state.hodo_points]
        
        # Membagi warna plot berdasarkan kelompok kluster ketinggian meteorologi resmi
        u_low, v_low = [], []
        u_mid, v_mid = [], []
        u_high, v_high = [], []
        
        for u, v, h in zip(u_pts, v_pts, heights):
            if h <= 3000:
                u_low.append(u); v_low.append(v)
            elif h <= 8000:
                u_mid.append(u); v_mid.append(v)
            else:
                u_high.append(u); v_high.append(v)
        
        # Plot garis total konektivitas
        ax.plot(u_pts, v_pts, color='#7f8c8d', linestyle='-', linewidth=1.5, alpha=0.7, zorder=1)
        
        # Scatter kelompok titik berkode warna untuk Legenda
        if u_low:
            ax.scatter(u_low, v_low, color='#2ecc71', edgecolor='white', s=50, label='Lapisan Bawah (≤ 3.000 ft)', zorder=3)
        if u_mid:
            ax.scatter(u_mid, v_mid, color='#3498db', edgecolor='white', s=50, label='Lapisan Menengah (3.500 - 8.000 ft)', zorder=3)
        if u_high:
            ax.scatter(u_high, v_high, color='#e74c3c', edgecolor='white', s=50, label='Udara Bebas Atas (> 8.000 ft)', zorder=3)
            
        # Beri tanda bintang emas di lokasi rilis awal (Permukaan)
        ax.scatter(u_pts[0], v_pts[0], color='#f1c40f', marker='*', s=150, edgecolor='black', label='Titik Pelepasan (Surface)', zorder=4)

    # Konfigurasi Frame Batas Luar & Peletakan Kotak Legenda Resmi
    ax.set_xlim(-max_hodo_range, max_hodo_range)
    ax.set_ylim(-max_hodo_range, max_hodo_range)
    ax.axis('off')
    
    # Tampilkan Legenda Profesional di area bawah
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.08), ncol=2, frameon=True, facecolor='#f8f9fa', edgecolor='#ccc', fontsize=8.5)
    st.pyplot(fig)
    
    # --- SECTION BARU: ANALISA PEMBACAAN HODOGRAPH SINGKAT ---
    st.markdown("### 📝 Analisis Ringkas Profil Hodograph")
    if st.session_state.hodo_points:
        if selected_mode == "Tipe A (Meliuk Balik / Sampel 1)":
            st.info(
                "**📋 INTERPRETASI METEOROLOGI (TIPE A):**\n\n"
                "* **Wind Shear Vertikal Kuat:** Terjadi belokan arah angin tajam melengkung balik (*Veering/Backing* ekstrem) di lapisan menengah.\n"
                "* **Indikasi Dinamis:** Penurunan Elevasi di awal diikuti lonjakan drastis hingga 64° menandakan adanya lapisan angin kencang di bawah yang mendadak melambat (*calm pockets*) di atas, memicu balon bergerak memutar kembali mendekati stasiun secara horizontal."
            )
        elif selected_mode == "Tipe B (Lapisan Stabil / Sampel 2)":
            st.success(
                "**📋 INTERPRETASI METEOROLOGI (TIPE B):**\n\n"
                "* **Uniform Geostrophic Flow:** Plot hodograph menunjukkan konsentrasi titik yang mengunci rapat pada jarak lingkar kecepatan konstan (17° - 21°).\n"
                "* **Indikasi Dinamis:** Kondisi atmosfer atas sangat stabil dengan pola pergerakan angin searah yang konstan. Karakteristik ini mencerminkan kondisi **Angin Monsun yang mapan** di wilayah Waingapu."
            )
        else:
            st.warning(
                "**📋 INTERPRETASI METEOROLOGI (TIPE C):**\n\n"
                "* **Kondisi Udara Lemah / Calm:** Vektor titik menumpuk sangat dekat dengan pusat koordinat poros sumbu nol (kecepatan rata-rata < 5 knot).\n"
                "* **Indikasi Dinamis:** Sudut elevasi konstan sangat tinggi (> 55°). Udara horizontal pasif, pergerakan vertikal didominasi gaya apung murni balon, mengindikasikan **aktivitas konvektif lokal** atau minimnya gradien tekanan makro."
            )
    else:
        st.info("Silakan buat data terlebih dahulu untuk memunculkan teks analisis.")

    st.markdown("---")
    
    # --- PANEL NAVIGASI MANUAL HP-FRIENDLY OLEH USER ---
    st.subheader("🔍 Panel Bantuan Ketik Manual")
    if st.session_state.generated_records:
        readings_list = [r["Pembacaan Ke-"] for r in st.session_state.generated_records]
        
        if st.session_state.selected_row_idx > len(readings_list):
            st.session_state.selected_row_idx = len(readings_list)
            
        nv1, nv2, nv3 = st.columns([3, 6, 3])
        with nv1:
            if st.button("◀️ PREV", use_container_width=True):
                if st.session_state.selected_row_idx > 1:
                    st.session_state.selected_row_idx -= 1
                    st.rerun()
        with nv2:
            st.markdown(
                f"<div style='text-align:center; font-size:16px; font-weight:bold; color:#0d3b66; "
                f"background:#e9ecef; border-radius:6px; padding:7px; border: 1px solid #ccc;'>"
                f"Menit Ke- {st.session_state.selected_row_idx}</div>", 
                unsafe_allow_html=True
            )
        with nv3:
            if st.button("NEXT ▶️", use_container_width=True):
                if st.session_state.selected_row_idx < len(readings_list):
                    st.session_state.selected_row_idx += 1
                    st.rerun()
                    
        active_rec = st.session_state.generated_records[st.session_state.selected_row_idx - 1]
        
        st.markdown(
            f"""
            <div style="background-color: #fffdf0; padding: 20px; border-radius: 8px; border: 2px solid #d62828; text-align: center; margin-top: 10px;">
                <div style="text-align: left; margin-bottom: 10px; font-size: 14px; color: #555;">
                    Tinggi: <b>{active_rec['Tinggi Balon (ft)']}</b> | <i>{active_rec['Level Target (BMKG)']}</i>
                </div>
                <div style="display: flex; justify-content: space-around; margin-top: 15px;">
                    <div>
                        <div style="color: gray; font-size: 13px; font-weight: bold; letter-spacing: 1px;">AZIMUT</div>
                        <div style="color: #005b96; font-size: 48px; font-weight: bold; line-height: 1;">{active_rec['AZIMUT']}</div>
                    </div>
                    <div>
                        <div style="color: gray; font-size: 13px; font-weight: bold; letter-spacing: 1px;">ELEVASI</div>
                        <div style="color: #d62828; font-size: 48px; font-weight: bold; line-height: 1;">{active_rec['ELEVASI']}</div>
                    </div>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
