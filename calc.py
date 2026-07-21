import streamlit as st
import math
import random
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
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
if 'active_row' not in st.session_state:
    st.session_state.active_row = 1

elevation_waingapu = 32.8

# --- FUNGSI CALLBACK NAVIGASI MOBILE ---
def prev_row():
    if st.session_state.active_row > 1:
        st.session_state.active_row -= 1

def next_row():
    if st.session_state.active_row < len(st.session_state.generated_records):
        st.session_state.active_row += 1

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
    default_season_idx = 0
    status_deteksi = f"*Deteksi Otomatis: Musim Timur (Bulan {current_month})"
elif current_month in [11, 12, 1, 2, 3]:
    default_season_idx = 1
    status_deteksi = f"*Deteksi Otomatis: Musim Barat (Bulan {current_month})"
else:
    default_season_idx = 2
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
        st.session_state.active_row = 1

    if target_readings <= st.session_state.last_idx:
        st.warning(f"Data sudah ter-generate sebanyak {st.session_state.last_idx} baris. Naikkan target untuk melanjutkan.")
        return

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

        rad_dir = math.radians(sim_dir)
        u_comp = -sim_speed_kt * math.sin(rad_dir)
        v_comp = -sim_speed_kt * math.cos(rad_dir)
        st.session_state.hodo_points.append((u_comp, v_comp, idx))

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

        if idx > 1:
            azimuth_deg = (azimuth_deg + random.uniform(-0.4, 0.4)) % 360
            elevation_deg = max(0.5, min(89.5, elevation_deg + random.uniform(-0.2, 0.2)))

        height_display = "Awal" if idx == 1 else f"{int(height_above_stn)} ft"

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
    
    # Otomatis arahkan panel bacaan manual ke data paling baru
    st.session_state.active_row = target_readings

# --- LAYOUT DENGAN DUA KOLOM UTAMA ---
col_left, col_right = st.columns([7, 5], gap="large")

# === KOLOM KIRI: INPUT & TABEL DATA ===
with col_left:
    st.subheader("⚙️ Parameter Kontrol Pengamatan")
    
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
        # Fitur ekspor CSV dihilangkan sesuai permintaan
    else:
        st.info("Belum ada data yang dibuat. Atur parameter lalu pilih 'Generate Baru'.")

# === KOLOM KANAN: HODOGRAPH & ASISTEN FORM ===
with col_right:
    st.subheader("🎯 Verifikasi Kelurusan Angin (Hodograph)")
    
    # Penggambaran Grafis Hodograph Lebih Menarik
    fig, ax = plt.subplots(figsize=(6, 6), facecolor='#f8f9fa')
    ax.set_facecolor('#ffffff')
    ax.set_aspect('equal')
    
    # Lingkaran batas kecepatan angin yang lebih jelas
    for knots in [10, 20, 30, 40]:
        circle = plt.Circle((0, 0), knots, color='#cbd5e1', fill=False, linestyle='-', linewidth=1)
        ax.add_patch(circle)
        # Label dengan kotak background agar tidak bertumpuk dengan garis
        ax.text(0, knots, f"{knots} kt", color='#64748b', fontsize=8, ha='center', va='center',
                bbox=dict(facecolor='white', edgecolor='none', pad=2, alpha=0.8))
        
    # Sumbu tengah putus-putus halus
    ax.axhline(0, color='#94a3b8', linestyle='--', linewidth=0.8)
    ax.axvline(0, color='#94a3b8', linestyle='--', linewidth=0.8)
    
    # Label Arah Mata Angin Berwarna
    c_props = dict(boxstyle='round,pad=0.3', facecolor='#0d3b66', edgecolor='none', alpha=0.9)
    ax.text(0, 45, "U", weight='bold', ha='center', va='center', color='white', bbox=c_props)
    ax.text(0, -45, "S", weight='bold', ha='center', va='center', color='white', bbox=c_props)
    ax.text(45, 0, "T", weight='bold', ha='center', va='center', color='white', bbox=c_props)
    ax.text(-45, 0, "B", weight='bold', ha='center', va='center', color='white', bbox=c_props)
    
    # Menggambar titik lintasan dengan Gradasi Warna dan Penanda Ujung
    if st.session_state.hodo_points:
        u_pts = [p[0] for p in st.session_state.hodo_points]
        v_pts = [p[1] for p in st.session_state.hodo_points]
        
        # Garis lintasan transparan
        ax.plot(u_pts, v_pts, color='#94a3b8', linewidth=1.5, zorder=1)
        
        # Titik pembacaan dengan gradasi warna (plasma colormap)
        colors = [cm.plasma(i/len(u_pts)) for i in range(len(u_pts))]
        ax.scatter(u_pts, v_pts, color=colors, edgecolor='white', s=55, zorder=2)
        
        # Penanda Mulai (Bawah) & Akhir (Atas)
        ax.plot(u_pts[0], v_pts[0], marker='s', color='#10b981', markersize=9, markeredgecolor='white', zorder=3, label='Mulai (Bawah)')
        ax.plot(u_pts[-1], v_pts[-1], marker='X', color='#ef4444', markersize=10, markeredgecolor='white', zorder=3, label='Akhir (Atas)')
        
        # Legenda indikator
        ax.legend(loc='lower right', fontsize=8, framealpha=0.9)
        
    ax.set_xlim(-50, 50)
    ax.set_ylim(-50, 50)
    ax.axis('off')
    
    st.pyplot(fig)
    plt.close(fig)
    
    st.caption(status_deteksi)
    st.markdown("---")
    
    # --- PANEL ASISTEN KETIK MANUAL ---
    st.subheader("🔍 Panel Bantuan Ketik Manual")
    
    if st.session_state.generated_records:
        total_rec = len(st.session_state.generated_records)
        
        # Navigasi Panah Khusus HP
        st.markdown("<p style='text-align:center; font-weight:bold; margin-bottom:5px;'>Navigasi Baris Form:</p>", unsafe_allow_html=True)
        nav1, nav2, nav3 = st.columns([1, 2, 1])
        with nav1:
            st.button("⬅️ Mundur", on_click=prev_row, use_container_width=True)
        with nav2:
            st.slider("Pilih Baris", min_value=1, max_value=total_rec, key='active_row', label_visibility="collapsed")
        with nav3:
            st.button("Maju ➡️", on_click=next_row, use_container_width=True)
        
        # Ambil data spesifik sesuai nilai di session_state
        active_rec = st.session_state.generated_records[st.session_state.active_row - 1]
        
        azimuth_fmt = f"{active_rec['AZIMUT']:.1f}".replace('.', ',')
        elevation_fmt = f"{active_rec['ELEVASI']:.1f}".replace('.', ',')
        
        st.markdown(
            f"""
            <div style="background-color: #fffdf0; padding: 20px; border-radius: 8px; border: 2px solid #d62828; text-align: center; margin-top:10px;">
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
