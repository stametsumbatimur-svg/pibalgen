import streamlit as st
import math
import random
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Pibal Generator Stamet Waingapu",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INSTANSIASI STATE MEMORI SIMULASI ---
if 'generated_records' not in st.session_state:
    st.session_state.generated_records = []
if 'hodo_points' not in st.session_state:
    st.session_state.hodo_points = []
if 'current_x' not in st.session_state:
    st.session_state.current_x = 0.0
if 'current_y' not in st.session_state:
    st.session_state.current_y = 0.0
if 'last_idx' not in st.session_state:
    st.session_state.last_idx = 0
if 'base_dir' not in st.session_state:
    st.session_state.base_dir = None
if 'base_speed_kt' not in st.session_state:
    st.session_state.base_speed_kt = None

elevation_waingapu = 32.8

# --- HEADER APLIKASI ---
st.markdown(
    f"""
    <div style='background-color:#0d3b66; padding:15px; border-radius:8px; text-align:center; color:white; margin-bottom:20px;'>
        <h2 style='margin:0; color:white;'>APLIKASI SIMULATOR PIBAL</h2>
        <p style='margin:5px 0 0 0; font-style:italic; font-size:14px;'>Stasiun Meteorologi Waingapu (97340) | Elevasi: {elevation_waingapu} ft</p>
    </div>
    """, 
    unsafe_allow_html=True
)

# --- DETEKSI OTOMATIS MUSIM ---
current_month = datetime.now().month
if current_month in [5, 6, 7, 8, 9]:
    default_season_idx = 0  # Musim Timur
    status_deteksi = f"*Deteksi Otomatis: Musim Timur (Bulan {current_month})"
elif current_month in [11, 12, 1, 2, 3]:
    default_season_idx = 1  # Musim Barat
    status_deteksi = f"*Deteksi Otomatis: Musim Barat (Bulan {current_month})"
else:
    default_season_idx = 2  # Pancaroba
    status_deteksi = f"*Deteksi Otomatis: Pancaroba (Bulan {current_month})"

# --- FUNGSI CORE GENERATOR DATA ---
def run_generation_core(target_readings, rate_ft_min, surf_ddd, surf_ff, season, fresh=False):
    if fresh or st.session_state.base_dir is None:
        st.session_state.generated_records = []
        st.session_state.hodo_points = []
        st.session_state.current_x = 0.0
        st.session_state.current_y = 0.0
        st.session_state.last_idx = 0
        st.session_state.base_dir = surf_ddd
        st.session_state.base_speed_kt = surf_ff

    if target_readings <= st.session_state.last_idx:
        st.warning(f"Data sudah ter-generate sebanyak {st.session_state.last_idx} baris. Naikkan target untuk melanjutkan.")
        return

    # Penjagaan dari pembagian dengan nol
    safe_rate = max(rate_ft_min, 1.0)

    start_loop = st.session_state.last_idx + 1
    current_x = st.session_state.current_x
    current_y = st.session_state.current_y

    for idx in range(start_loop, target_readings + 1):
        if idx == 1:
            height_above_stn = 100.0
            dt = 10.0
            sim_dir = st.session_state.base_dir
            sim_speed_kt = st.session_state.base_speed_kt
            level_target_str = "Diabaikan (Rilis)"
        else:
            height_above_stn = (idx - 1) * 500.0
            prev_height = 100.0 if idx == 2 else (idx - 2) * 500.0
            dt = ((height_above_stn - prev_height) / safe_rate) * 60.0
            layer_factor = height_above_stn / 1000.0
            
            # Pemodelan Lapisan Udara Atas Dinamis (Inversion & Shear)
            if season == "timur":
                if height_above_stn < 7000:
                    dir_shear = -(layer_factor * 4.0)
                    speed_shear = layer_factor * 0.5
                else:
                    dir_shear = -(7.0 * 4.0) - ((layer_factor - 7.0) * 12.0)
                    speed_shear = (7.0 * 0.5) + ((layer_factor - 7.0) * 1.2)
                
                sim_dir = (st.session_state.base_dir + dir_shear + random.uniform(-6, 6)) % 360
                sim_speed_kt = max(2.5, st.session_state.base_speed_kt + speed_shear + random.uniform(-1.5, 1.5))
                
            elif season == "barat":
                if height_above_stn < 8000:
                    dir_shear = (layer_factor * 3.0)
                    speed_shear = layer_factor * 0.4
                else:
                    dir_shear = (8.0 * 3.0) + ((layer_factor - 8.0) * 9.0)
                    speed_shear = (8.0 * 0.4) + ((layer_factor - 8.0) * 1.0)
                    
                sim_dir = (st.session_state.base_dir + dir_shear + random.uniform(-6, 6)) % 360
                sim_speed_kt = max(2.5, st.session_state.base_speed_kt + speed_shear + random.uniform(-1.5, 1.5))
            else:
                sim_dir = (st.session_state.base_dir + random.uniform(-15, 15)) % 360
                sim_speed_kt = max(2.0, st.session_state.base_speed_kt + random.uniform(-3, 3))

            target_level = math.ceil((idx - 1) / 2) * 1000
            level_target_str = f"Level {target_level} ft"

        # Vektor Hodograph
        rad_dir = math.radians(sim_dir)
        u_comp = -sim_speed_kt * math.sin(rad_dir)
        v_comp = -sim_speed_kt * math.cos(rad_dir)
        st.session_state.hodo_points.append((u_comp, v_comp, idx))

        # Perpindahan Balon
        speed_ft_sec = sim_speed_kt * 1.68781
        balloon_move_dir = (sim_dir + 180) % 360
        move_rad = math.radians(balloon_move_dir)
        
        current_x += speed_ft_sec * math.sin(move_rad) * dt
        current_y += speed_ft_sec * math.cos(move_rad) * dt
        
        horizontal_dist = math.hypot(current_x, current_y)
        
        if horizontal_dist == 0:
            azimuth_deg = 0.0
            elevation_deg = 90.0
        else:
            azimuth_deg = math.degrees(math.atan2(current_x, current_y)) % 360
            elevation_deg = math.degrees(math.atan2(height_above_stn, horizontal_dist))

        # Efek Jitter Bidikan
        if idx > 1:
            azimuth_deg = (azimuth_deg + random.uniform(-0.4, 0.4)) % 360
            elevation_deg = max(0.5, min(89.5, elevation_deg + random.uniform(-0.2, 0.2)))

        height_display = "Awal" if idx == 1 else f"{int(height_above_stn)} ft"

        # Simpan nilai numerik murni agar CSV mudah diolah
        st.session_state.generated_records.append({
            "Pembacaan Ke-": idx,
            "Tinggi Balon (ft)": height_display,
            "Level Target (BMKG)": level_target_str,
            "AZIMUT": round(azimuth_deg, 1),
            "ELEVASI": round(elevation_deg, 1)
        })

    st.session_state.current_x = current_x
    st.session_state.current_y = current_y
    st.session_state.last_idx = target_readings

# --- LAYOUT DENGAN DUA KOLOM UTAMA ---
col_left, col_right = st.columns([7, 5], gap="large")

# === KOLOM KIRI: INPUT & TABEL DATA ===
with col_left:
    st.subheader("⚙️ Parameter Kontrol Pengamatan")
    
    # Grid input parameter
    c1, c2 = st.columns(2)
    with c1:
        target_readings = st.number_input("Target Jumlah Pembacaan:", min_value=1, value=25, step=1)
        surf_ddd = st.number_input("Angin Permukaan ddd (°):", min_value=0.0, max_value=360.0, value=190.0, step=5.0)
    with c2:
        rate_ft_min = st.number_input("Laju Naik (ft/min):", min_value=1.0, value=600.0, step=10.0)
        surf_ff = st.number_input("Kec Angin Perm ff (kt):", min_value=0.0, value=5.0, step=1.0)
        
    season_options = ["timur", "barat", "pancaroba"]
    season_labels = ["Musim Timur", "Musim Barat", "Pancaroba"]
    selected_season = st.radio("Pola Kebiasaan Musim:", season_labels, index=default_season_idx, horizontal=True)
    season_key = season_options[season_labels.index(selected_season)]

    # Tombol Aksi Kiri-Kanan
    b1, b2 = st.columns(2)
    with b1:
        if st.button("⚡ Generate Baru", type="primary", use_container_width=True):
            run_generation_core(target_readings, rate_ft_min, surf_ddd, surf_ff, season_key, fresh=True)
    with b2:
        if st.button("⏩ Lanjutkan ke Target", use_container_width=True):
            if st.session_state.last_idx == 0:
                st.error("Belum ada data awal. Silakan klik 'Generate Baru' terlebih dahulu.")
            else:
                run_generation_core(target_readings, rate_ft_min, surf_ddd, surf_ff, season_key, fresh=False)

    st.markdown("---")
    st.subheader("📊 Tabel Hasil Pembacaan")
    
    if st.session_state.generated_records:
        df = pd.DataFrame(st.session_state.generated_records)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Ekspor CSV
        csv_buffer = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Ekspor Backup CSV",
            data=csv_buffer,
            file_name=f"pibal_waingapu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("Belum ada data yang dibuat. Atur parameter lalu pilih 'Generate Baru'.")

# === KOLOM KANAN: HODOGRAPH & ASISTEN FORM ===
with col_right:
    st.subheader("🎯 Verifikasi Kelurusan Angin (Hodograph)")
    
    # Penggambaran Grafis Hodograph
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_aspect('equal')
    
    # Lingkaran batas knot (10kt, 20kt, 30kt)
    for knots in [10, 20, 30]:
        circle = plt.Circle((0, 0), knots, color='#e9ecef', fill=False, linestyle='--', linewidth=1.5)
        ax.add_patch(circle)
        ax.text(knots - 2.5, 0.8, f"{knots}kt", color='darkgray', fontsize=8)
        
    # Sumbu tengah
    ax.axhline(0, color='#ddd', linestyle=':', linewidth=1)
    ax.axvline(0, color='#ddd', linestyle=':', linewidth=1)
    
    # Label Arah Mata Angin
    ax.text(0, 33, "U (N)", weight='bold', ha='center', va='bottom', color='black')
    ax.text(0, -33, "S", weight='bold', ha='center', va='top', color='black')
    ax.text(33, 0, "T", weight='bold', ha='left', va='center', color='black')
    ax.text(-33, 0, "B", weight='bold', ha='right', va='center', color='black')
    
    # Menggambar titik lintasan
    if st.session_state.hodo_points:
        u_pts = [p[0] for p in st.session_state.hodo_points]
        v_pts = [p[1] for p in st.session_state.hodo_points]
        idxs = [p[2] for p in st.session_state.hodo_points]
        colors = ["#005b96" if idx <= 25 else "#e67e22" for idx in idxs]
        
        ax.plot(u_pts, v_pts, color='#005b96', linewidth=2, zorder=1)
        ax.scatter(u_pts, v_pts, color=colors, edgecolor='white', s=45, zorder=2)
        
    ax.set_xlim(-36, 36)
    ax.set_ylim(-36, 36)
    ax.axis('off')
    
    st.pyplot(fig)
    plt.close(fig)  # Mencegah penumpukan objek figure di memori server
    
    st.caption(status_deteksi)
    st.markdown("---")
    
    # --- PANEL ASISTEN KETIK MANUAL ---
    st.subheader("🔍 Panel Bantuan Ketik Manual")
    
    if st.session_state.generated_records:
        readings_list = [r["Pembacaan Ke-"] for r in st.session_state.generated_records]
        selected_row_idx = st.select_slider("Geser/Pilih Nomor Pembacaan:", options=readings_list, value=readings_list[-1])
        
        active_rec = next(item for item in st.session_state.generated_records if item["Pembacaan Ke-"] == selected_row_idx)
        
        # Format angka menggunakan koma khusus untuk tampilan visual UI
        azimuth_fmt = f"{active_rec['AZIMUT']:.1f}".replace('.', ',')
        elevation_fmt = f"{active_rec['ELEVASI']:.1f}".replace('.', ',')
        
        st.markdown(
            f"""
            <div style="background-color: #fffdf0; padding: 20px; border-radius: 8px; border: 2px solid #d62828; text-align: center;">
                <div style="text-align: left; margin-bottom: 10px;">
                    <span style="font-size: 16px; font-weight: bold; color: #333;">Pembacaan Ke: {active_rec['Pembacaan Ke-']}</span><br>
                    <span style="font-size: 14px; font-style: italic; color: #e67e22; font-weight: bold;">Target Form: {active_rec['Level Target (BMKG)']}</span>
                </div>
                <div style="display: flex; justify-content: space-around; margin-top: 15px;">
                    <div>
                        <div style="color: gray; font-size: 12px; font-weight: bold; letter-spacing: 1px;">AZIMUT</div>
                        <div style="color: #005b96; font-size: 45px; font-weight: bold; line-height: 1;">{azimuth_fmt}</div>
                    </div>
                    <div>
                        <div style="color: gray; font-size: 12px; font-weight: bold; letter-spacing: 1px;">ELEVASI</div>
                        <div style="color: #d62828; font-size: 45px; font-weight: bold; line-height: 1;">{elevation_fmt}</div>
                    </div>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    else:
        st.info("Silakan generate data terlebih dahulu untuk memunculkan panel bantuan ketik manual.")
