import streamlit as st
import math
import random
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Pibal Azimut & Elevasi Generator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INSTANSIASI STATE MEMORI SIMULASI ---
if 'generated_records' not in st.session_state:
    st.session_state.generated_records = []
if 'traj_points' not in st.session_state:
    st.session_state.traj_points = []
if 'last_idx' not in st.session_state:
    st.session_state.last_idx = 0
if 'selected_row_idx' not in st.session_state:
    st.session_state.selected_row_idx = 1

elevation_waingapu = 32.8

# --- HEADER APLIKASI ---
st.markdown(
    """
    <div style='background-color:#0d3b66; padding:15px; border-radius:8px; text-align:center; color:white; margin-bottom:20px;'>
        <h2 style='margin:0; color:white;'>APLIKASI SIMULATOR DATA PIBAL (TEODOLIT)</h2>
        <p style='margin:5px 0 0 0; font-style:italic; font-size:14px;'>Stasiun Meteorologi Waingapu (97340) | Output: Murni Azimut & Elevasi Realistis</p>
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
        st.session_state.traj_points = []
        st.session_state.last_idx = 0
        st.session_state.selected_row_idx = 1

    if target_readings <= st.session_state.last_idx:
        st.warning(f"Data sudah ter-generate sebanyak {st.session_state.last_idx} baris.")
        return

    start_loop = st.session_state.last_idx + 1

    for idx in range(start_loop, target_readings + 1):
        height_above_stn = idx * 500.0
        target_level = math.ceil(idx / 2) * 1000
        level_target_str = f"Level {target_level} ft"

        # MATRIKS PEMODELAN SUDUT BERDASARKAN FOTO LOGBOOK ASLI USER
        if atmos_mode == "Tipe A (Meliuk Balik / Sampel 1)":
            # Azimut: Mulai dari base, meliuk turun ke area 250-an, lalu naik berputar balik ke 290-an
            azimuth_deg = (base_azimuth - (idx * 4.0) + 32 * math.sin(idx * 0.22) + random.uniform(-0.5, 0.5)) % 360
            # Elevasi: Mulai dari ~28°, drop tipis ke 23°, lalu melambung naik drastis hingga 64°, kemudian turun perlahan
            if idx <= 5:
                elevation_deg = max(20.0, 28.5 - ((idx - 1) * 1.35) + random.uniform(-0.3, 0.3))
            elif idx <= 17:
                elevation_deg = min(66.0, 23.0 + ((idx - 5) * 3.42) + random.uniform(-0.4, 0.4))
            else:
                elevation_deg = max(40.0, 64.0 - ((idx - 17) * 1.32) + random.uniform(-0.3, 0.3))
                
        elif atmos_mode == "Tipe B (Lapisan Stabil / Sampel 2)":
            # Azimut: Mengalami shifting tajam di awal pembacaan, lalu stabil bergerak halus
            if idx <= 4:
                azimuth_deg = (base_azimuth - ((idx - 1) * 24.0) + random.uniform(-1.0, 1.0)) % 360
            else:
                azimuth_deg = (315.0 - ((idx - 4) * 1.0) + random.uniform(-0.4, 0.4)) % 360
            # Elevasi: Drop dari tinggi (~47°), lalu terkunci sangat rapat dan stabil di rentang 17° - 21°
            if idx <= 6:
                elevation_deg = max(20.0, 47.0 - ((idx - 1) * 5.4) + random.uniform(-0.4, 0.4))
            else:
                elevation_deg = 20.0 - ((idx - 6) * 0.05) + (math.sin(idx * 0.5) * 0.4) + random.uniform(-0.2, 0.2)
                
        else: # Tipe C (Angin Tenang / Sampel 3)
            # Azimut: Bergerak sempit berputar-putar di area baseline awal (10° - 21°)
            azimuth_deg = (base_azimuth + (math.sin(idx * 0.6) * 4.0) + random.uniform(-0.6, 0.6)) % 360
            # Elevasi: Bertahan sangat tinggi (56° - 67°) karena balon terbang hampir tegak lurus ke atas
            if idx <= 4:
                elevation_deg = min(70.0, 63.0 + ((idx - 1) * 1.5) + random.uniform(-0.4, 0.4))
            else:
                elevation_deg = 59.0 + (math.cos(idx * 0.4) * 2.5) + random.uniform(-0.3, 0.3)

        # Menghitung koordinat horizontal balon (X, Y) murni untuk keperluan visualisasi grafik lintasan
        elev_rad = math.radians(elevation_deg)
        horizontal_dist = height_above_stn / math.tan(elev_rad) if math.tan(elev_rad) != 0 else 0
        az_rad = math.radians(azimuth_deg)
        x_pos = horizontal_dist * math.sin(az_rad)
        y_pos = horizontal_dist * math.cos(az_rad)
        st.session_state.traj_points.append((x_pos, y_pos))

        # Format desimal menggunakan koma sesuai template form kantor
        azimuth_str = f"{azimuth_deg:.1f}".replace('.', ',')
        elevation_str = f"{elevation_deg:.1f}".replace('.', ',')

        st.session_state.generated_records.append({
            "Pembacaan Ke-": idx,
            "Tinggi Balon (ft)": f"{int(height_above_stn)} ft",
            "Level Target (BMKG)": level_target_str,
            "AZIMUT": azimuth_str,
            "ELEVASI": elevation_str
        })

    st.session_state.last_idx = target_readings

# --- LAYOUT DENGAN DUA KOLOM UTAMA ---
col_left, col_right = st.columns([7, 5], gap="large")

# === KOLOM KIRI: INPUT PARAMETER & TABEL DATA ===
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
        if st.button("⏩ Lanjutkan Target Ketinggian", use_container_width=True):
            if st.session_state.last_idx == 0:
                st.error("Belum ada data awal. Silakan klik 'Generate Baru' terlebih dahulu.")
            else:
                run_generation_core(target_readings, rate_ft_min, base_azimuth, selected_mode, fresh=False)

    st.markdown("---")
    st.subheader("📊 Tabel Hasil Pembacaan Teropong")
    
    if st.session_state.generated_records:
        df = pd.DataFrame(st.session_state.generated_records)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        csv_buffer = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Ekspor Backup CSV",
            data=csv_buffer,
            file_name=f"pibal_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("Belum ada data. Atur parameter lalu klik 'Generate Baru'.")

# === KOLOM KANAN: GRAFIK LINTASAN BALON & PANEL BANTUAN HP ===
with col_right:
    st.subheader("🎯 Visualisasi Lintasan Horizontal Balon")
    
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_aspect('equal')
    
    # Garis bantu sumbu grid radar stasiun
    ax.axhline(0, color='#ccc', linestyle=':', linewidth=1)
    ax.axvline(0, color='#ccc', linestyle=':', linewidth=1)
    
    # Grid lingkaran imaginer penanda jarak horizontal
    for r in [2000, 5000, 10000, 15000]:
        circle = plt.Circle((0, 0), r, color='#e9ecef', fill=False, linestyle='--', linewidth=1.2)
        ax.add_patch(circle)
        
    ax.text(0, 16000, "U (N)", weight='bold', ha='center', va='bottom', color='black')
    ax.text(0, -16000, "S", weight='bold', ha='center', va='top', color='black')
    ax.text(16000, 0, "T", weight='bold', ha='left', va='center', color='black')
    ax.text(-16000, 0, "B", weight='bold', ha='right', va='center', color='black')
    
    # Plotting jejak koordinat balon
    if st.session_state.traj_points:
        x_pts = [p[0] for p in st.session_state.traj_points]
        y_pts = [p[1] for p in st.session_state.traj_points]
        
        ax.plot(x_pts, y_pts, color='#d62828', linewidth=2.5, zorder=1, label="Jalur Balon")
        ax.scatter(x_pts, y_pts, color='#005b96', edgecolor='white', s=40, zorder=2)
        # Mark titik stasiun teodolit di pusat (0,0)
        ax.scatter(0, 0, color='black', marker='x', s=100, zorder=3)
        
    ax.set_xlim(-18000, 18000)
    ax.set_ylim(-18000, 18000)
    ax.axis('off')
    
    st.pyplot(fig)
    st.caption(status_deteksi)
    st.markdown("---")
    
    # --- PANEL NAVIGASI MANUSIA DENGAN TOMBOL PANAH JUMBO UNTUK LAYAR HP ---
    st.subheader("🔍 Panel Bantuan Ketik Manual (Mobile Friendly)")
    
    if st.session_state.generated_records:
        readings_list = [r["Pembacaan Ke-"] for r in st.session_state.generated_records]
        
        if st.session_state.selected_row_idx > len(readings_list):
            st.session_state.selected_row_idx = len(readings_list)
        if st.session_state.selected_row_idx < 1:
            st.session_state.selected_row_idx = 1
            
        # GRID LAYOUT TOMBOL PANAH JUMBO RAMAH JEMPOL HP
        nv1, nv2, nv3 = st.columns([3, 6, 3])
        with nv1:
            if st.button("◀️ PREV", use_container_width=True, key="btn_prev_hp"):
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
            if st.button("NEXT ▶️", use_container_width=True, key="btn_next_hp"):
                if st.session_state.selected_row_idx < len(readings_list):
                    st.session_state.selected_row_idx += 1
                    st.rerun()
                    
        st.session_state.selected_row_idx = st.slider(
            "Atau geser cepat baris:", 
            min_value=1, 
            max_value=len(readings_list), 
            value=st.session_state.selected_row_idx
        )
        
        active_rec = st.session_state.generated_records[st.session_state.selected_row_idx - 1]
        
        # Tampilan Display Font Gajah untuk mempermudah pengetikan ulang
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
    else:
        st.info("Silakan generate data terlebih dahulu untuk memunculkan panel keyboard.")
