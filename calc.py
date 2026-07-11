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
if 'selected_row_idx' not in st.session_state:
    st.session_state.selected_row_idx = 1

elevation_waingapu = 32.8

# --- HEADER APLIKASI ---
st.markdown(
    """
    <div style='background-color:#0d3b66; padding:15px; border-radius:8px; text-align:center; color:white; margin-bottom:20px;'>
        <h2 style='margin:0; color:white;'>APLIKASI SIMULATOR PIBAL</h2>
        <p style='margin:5px 0 0 0; font-style:italic; font-size:14px;'>Stasiun Meteorologi Waingapu (97340) | Elevasi: 32.8 ft</p>
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

# --- FUNGSI CORE ENGINE KALIBRASI REAL DATA ---
def run_generation_core(target_readings, rate_ft_min, surf_ddd, surf_ff, season, atmos_mode, fresh=False):
    if fresh:
        st.session_state.generated_records = []
        st.session_state.hodo_points = []
        st.session_state.current_x = 0.0
        st.session_state.current_y = 0.0
        st.session_state.last_idx = 0
        st.session_state.base_dir = surf_ddd
        st.session_state.base_speed_kt = surf_ff
        st.session_state.selected_row_idx = 1

    if target_readings <= st.session_state.last_idx:
        st.warning(f"Data sudah ter-generate sebanyak {st.session_state.last_idx} baris.")
        return

    start_loop = st.session_state.last_idx + 1
    current_x = st.session_state.current_x
    current_y = st.session_state.current_y

    for idx in range(start_loop, target_readings + 1):
        height_above_stn = idx * 500.0
        dt = (500.0 / rate_ft_min) * 60.0

        # PEMODELAN MATEMATIS MENGACU PADA FOTO LOG SAMPEL NYATA
        if atmos_mode == "Tipe A (Meliuk Balik / Sampel 1)":
            # Arah berputar tajam membentuk kurva meliuk (U-Turn Jet)
            sim_dir = (surf_ddd - (idx * 4.5) + 40 * math.sin(idx * 0.25) + random.uniform(-3, 3)) % 360
            # Kecepatan melambat drastis di pertengahan membuat elevasi melonjak naik
            sim_speed_kt = max(1.5, surf_ff + 8.0 * math.cos(idx * 0.18) + random.uniform(-1.0, 1.0))
            
        elif atmos_mode == "Tipe B (Lapisan Stabil / Sampel 2)":
            # Arah konstan landai
            sim_dir = (surf_ddd - (idx * 0.8) + random.uniform(-1.5, 1.5)) % 360
            # Kecepatan mengunci rasio konstan setelah melewati boundary layer permukaan
            if idx < 5:
                sim_speed_kt = max(2.0, surf_ff + (idx * 1.8) + random.uniform(-1, 1))
            else:
                sim_speed_kt = max(2.0, 13.5 + random.uniform(-0.6, 0.6))
                
        else: # Tipe C (Angin Tenang / Sampel 3)
            # Arah acak berputar-putar (Variabel) karena kecepatan angin sangat lemah
            sim_dir = (surf_ddd + (idx * 2.0) + random.uniform(-6, 6)) % 360
            # Kecepatan dikunci sangat rendah (< 3 knot) agar elevasi stabil di atas 60 derajat
            sim_speed_kt = max(0.6, 2.2 + random.uniform(-0.5, 0.5))

        target_level = math.ceil(idx / 2) * 1000
        level_target_str = f"Level {target_level} ft"

        # Vektor Hodograph
        rad_dir = math.radians(sim_dir)
        u_comp = -sim_speed_kt * math.sin(rad_dir)
        v_comp = -sim_speed_kt * math.cos(rad_dir)
        st.session_state.hodo_points.append((u_comp, v_comp, idx))

        # Posisi Balon
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

        # Mikro Jitter pembacaan lensa teleskop
        dist_factor = min(2.0, horizontal_dist / 8000.0)
        azimuth_deg = (azimuth_deg + random.uniform(-0.4, 0.4) * (1.0 + dist_factor)) % 360
        elevation_deg = max(0.2, min(89.8, elevation_deg + random.uniform(-0.2, 0.2) * (1.0 + dist_factor)))

        height_display = f"{int(height_above_stn)} ft"
        azimuth_str = f"{azimuth_deg:.1f}".replace('.', ',')
        elevation_str = f"{elevation_deg:.1f}".replace('.', ',')

        st.session_state.generated_records.append({
            "Pembacaan Ke-": idx,
            "Tinggi Balon (ft)": height_display,
            "Level Target (BMKG)": level_target_str,
            "AZIMUT": azimuth_str,
            "ELEVASI": elevation_str
        })

    st.session_state.current_x = current_x
    st.session_state.current_y = current_y
    st.session_state.last_idx = target_readings

# --- LAYOUT DENGAN DUA KOLOM UTAMA ---
col_left, col_right = st.columns([7, 5], gap="large")

# === KOLOM KIRI: INPUT & TABEL DATA ===
with col_left:
    st.subheader("⚙️ Parameter Kontrol Pengamatan")
    
    c1, c2 = st.columns(2)
    with c1:
        target_readings = st.number_input("Target Jumlah Pembacaan:", min_value=1, value=31, step=1)
        surf_ddd = st.number_input("Angin Permukaan ddd (°):", min_value=0.0, max_value=360.0, value=315.0, step=5.0)
    with c2:
        rate_ft_min = st.number_input("Laju Naik (ft/min):", min_value=1.0, value=600.0, step=10.0)
        surf_ff = st.number_input("Kec Angin Perm ff (kt):", min_value=0.0, value=5.0, step=1.0)
        
    selected_mode = st.selectbox(
        "🎯 Karakteristik Perubahan Atmosfer (Mengacu Tren Asli):",
        ["Tipe A (Meliuk Balik / Sampel 1)", "Tipe B (Lapisan Stabil / Sampel 2)", "Tipe C (Angin Tenang / Sampel 3)"]
    )
        
    season_options = ["timur", "barat", "pancaroba"]
    season_labels = ["Musim Timur", "Musim Barat", "Pancaroba"]
    selected_season = st.radio("Pola Kebiasaan Musim:", season_labels, index=default_season_idx, horizontal=True)
    season_key = season_options[season_labels.index(selected_season)]

    b1, b2 = st.columns(2)
    with b1:
        if st.button("⚡ Generate Baru", type="primary", use_container_width=True):
            run_generation_core(target_readings, rate_ft_min, surf_ddd, surf_ff, season_key, selected_mode, fresh=True)
    with b2:
        if st.button("⏩ Lanjutkan ke Target", use_container_width=True):
            if st.session_state.last_idx == 0:
                st.error("Belum ada data awal. Silakan klik 'Generate Baru' terlebih dahulu.")
            else:
                run_generation_core(target_readings, rate_ft_min, surf_ddd, surf_ff, season_key, selected_mode, fresh=False)

    st.markdown("---")
    st.subheader("📊 Tabel Hasil Pembacaan")
    
    if st.session_state.generated_records:
        df = pd.DataFrame(st.session_state.generated_records)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        csv_buffer = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Ekspor Backup CSV",
            data=csv_buffer,
            file_name=f"pibal_waingapu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("Belum ada data. Atur parameter lalu pilih 'Generate Baru'.")

# === KOLOM KANAN: HODOGRAPH & ASISTEN FORM ===
with col_right:
    st.subheader("🎯 Verifikasi Kelurusan Angin (Hodograph)")
    
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_aspect('equal')
    
    for knots in [10, 20, 30]:
        circle = plt.Circle((0, 0), knots, color='#e9ecef', fill=False, linestyle='--', linewidth=1.5)
        ax.add_patch(circle)
        ax.text(knots - 2.5, 0.8, f"{knots}kt", color='darkgray', fontsize=8)
        
    ax.axhline(0, color='#ddd', linestyle=':', linewidth=1)
    ax.axvline(0, color='#ddd', linestyle=':', linewidth=1)
    
    ax.text(0, 33, "U (N)", weight='bold', ha='center', va='bottom', color='black')
    ax.text(0, -33, "S", weight='bold', ha='center', va='top', color='black')
    ax.text(33, 0, "T", weight='bold', ha='left', va='center', color='black')
    ax.text(-33, 0, "B", weight='bold', ha='right', va='center', color='black')
    
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
    st.caption(status_deteksi)
    st.markdown("---")
    
    # --- PANEL NAVIGASI MANUAL HP-FRIENDLY (TOMBOL BESAR DAN RAPAT) ---
    st.subheader("🔍 Panel Bantuan Ketik Manual")
    
    if st.session_state.generated_records:
        readings_list = [r["Pembacaan Ke-"] for r in st.session_state.generated_records]
        
        if st.session_state.selected_row_idx > len(readings_list):
            st.session_state.selected_row_idx = len(readings_list)
        if st.session_state.selected_row_idx < 1:
            st.session_state.selected_row_idx = 1
            
        # GRID BUTTON TOMBOL PANAH JUMBO
        nv1, nv2, nv3 = st.columns([3, 6, 3])
        with nv1:
            if st.button("◀️ PREV", use_container_width=True, key="btn_prev_mobile"):
                if st.session_state.selected_row_idx > 1:
                    st.session_state.selected_row_idx -= 1
                    st.rerun()
        with nv2:
            st.markdown(
                f"<div style='text-align:center; font-size:16px; font-weight:bold; color:#0d3b66; "
                f"background:#e9ecef; border-radius:6px; padding:7px; border: 1px solid #ccc;'>"
                f"Baris Ke-{st.session_state.selected_row_idx}</div>", 
                unsafe_allow_html=True
            )
        with nv3:
            if st.button("NEXT ▶️", use_container_width=True, key="btn_next_mobile"):
                if st.session_state.selected_row_idx < len(readings_list):
                    st.session_state.selected_row_idx += 1
                    st.rerun()
                    
        st.session_state.selected_row_idx = st.slider(
            "Geser cepat indeks:", 
            min_value=1, 
            max_value=len(readings_list), 
            value=st.session_state.selected_row_idx
        )
        
        active_rec = next(item for item in st.session_state.generated_records if item["Pembacaan Ke-"] == st.session_state.selected_row_idx)
        
        st.markdown(
            f"""
            <div style="background-color: #fffdf0; padding: 20px; border-radius: 8px; border: 2px solid #d62828; text-align: center; margin-top: 10px;">
                <div style="text-align: left; margin-bottom: 10px;">
                    <span style="font-size: 15px; font-weight: bold; color: #333;">Tinggi Target: {active_rec['Tinggi Balon (ft)']}</span><br>
                    <span style="font-size: 14px; font-style: italic; color: #e67e22; font-weight: bold;">Posisi Form: {active_rec['Level Target (BMKG)']}</span>
                </div>
                <div style="display: flex; justify-content: space-around; margin-top: 15px;">
                    <div>
                        <div style="color: gray; font-size: 12px; font-weight: bold; letter-spacing: 1px;">AZIMUT</div>
                        <div style="color: #005b96; font-size: 45px; font-weight: bold; line-height: 1;">{active_rec['AZIMUT']}</div>
                    </div>
                    <div>
                        <div style="color: gray; font-size: 12px; font-weight: bold; letter-spacing: 1px;">ELEVASI</div>
                        <div style="color: #d62828; font-size: 45px; font-weight: bold; line-height: 1;">{active_rec['ELEVASI']}</div>
                    </div>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    else:
        st.info("Silakan generate data terlebih dahulu.")
