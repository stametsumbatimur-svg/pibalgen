import streamlit as st
import math
import random
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import pytz

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Pibal Intelligent Simulator - Waingapu",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MATRIKS KLIMATOLOGI MULTI-TAHUN WAINGAPU (INTEGRASI DATA 2024 - 2026) ---
CLIMATOLOGY_MATRIX = {
    1: {"name": "Januari (Puncak Musim Barat 1)", "low_dir": 151.2, "mid_dir": 279.7, "high_dir": 287.5, "low_spd": 8.6, "mid_spd": 8.6, "high_spd": 7.9, "desc": "Massa udara didominasi angin Barat s.d. Barat Laut di lapisan atas, sementara lapisan bawah dipengaruhi sirkulasi darat local Waingapu."},
    2: {"name": "Februari (Puncak Musim Barat 2)", "low_dir": 277.8, "mid_dir": 274.2, "high_dir": 306.9, "low_spd": 7.3, "mid_spd": 8.9, "high_spd": 8.9, "desc": "Angin Barat Laut sangat mapan dan tebal. Vektor Hodograph akan melebar stabil ke sektor Tenggara dengan kecepatan merata."},
    3: {"name": "Maret (Akhir Musim Barat)", "low_dir": 293.2, "mid_dir": 301.1, "high_dir": 313.0, "low_spd": 7.8, "mid_spd": 8.7, "high_spd": 9.3, "desc": "Penghujung Monsun Asia. Kecepatan angin udara atas meningkat stabil mencapai rata-rata 9.3 knot, memicu penurunan sudut elevasi secara perlahan."},
    4: {"name": "April (Transisi Musim Timur)", "low_dir": 111.4, "mid_dir": 102.1, "high_dir": 88.9, "low_spd": 8.6, "mid_spd": 9.3, "high_spd": 8.6, "desc": "Peralihan sirkulasi udara besar. Arah angin berbalik total 180 derajat menuju sektor Timur - Tenggara dengan profil kecepatan yang seragam."},
    5: {"name": "Mei (Puncak Musim Timur - Awal)", "low_dir": 105.5, "mid_dir": 90.9, "high_dir": 68.8, "low_spd": 11.5, "mid_spd": 10.1, "high_spd": 10.6, "desc": "Monsun Australia masuk dengan kuat. Angin lapisan bawah permukaan bumi berhembus kencang (rata-rata 11.5 knot) memicu elevasi awal yang landai."},
    6: {"name": "Juni (Puncak Musim Timur - Tengah)", "low_dir": 105.1, "mid_dir": 87.6, "high_dir": 69.3, "low_spd": 10.4, "mid_spd": 8.9, "high_spd": 10.1, "desc": "Angin Tenggara mendominasi lapisan bawah sabana Sumba, bergeser halus menjadi arah Timur seiring bertambahnya ketinggian balon."},
    7: {"name": "Juli (Puncak Musim Timur - Akhir)", "low_dir": 70.7, "mid_dir": 54.3, "high_dir": 55.7, "low_spd": 10.3, "mid_spd": 10.0, "high_spd": 10.6, "desc": "Udara atas sangat kering dan konstan dari arah Timur Laut - Timur. Sudut elevasi akan mengunci sangat rapi pada rentang 18 - 25 derajat hingga akhir pembacaan."},
    8: {"name": "Agustus (Monsun Australia Kuat)", "low_dir": 83.0, "mid_dir": 95.5, "high_dir": 80.9, "low_spd": 10.0, "mid_spd": 9.9, "high_spd": 9.6, "desc": "Karakteristik tiupan angin dari Benua Kangguru sangat mantap. Kecepatan stabil di angka 10 knot di seluruh kolom udara vertikal Waingapu."},
    9: {"name": "September (Monsun Australia Akhir)", "low_dir": 102.4, "mid_dir": 101.4, "high_dir": 127.7, "low_spd": 8.9, "mid_spd": 11.3, "high_spd": 11.8, "desc": "Angin lapisan Free Atmosphere (>8000 ft) meningkat kencang rata-rata 11.8 knot dari arah Tenggara, memperjauh jarak horizontal balon secara cepat."},
    10: {"name": "Oktober (Pancaroba Awal)", "low_dir": 93.4, "mid_dir": 80.2, "high_dir": 84.1, "low_spd": 8.2, "mid_spd": 11.2, "high_spd": 12.3, "desc": "Memasuki transisi sirkulasi iklim makro. Udara atas bertiup kencang dari Timur, namun arah angin mulai menunjukkan riak turbulensi lokal."},
    11: {"name": "November (Pancaroba Akhir - Angin Lemah)", "low_dir": 20.3, "mid_dir": 37.1, "high_dir": 22.4, "low_spd": 7.0, "mid_spd": 8.2, "high_spd": 9.6, "desc": "Bulan paling tenang (Calm) di Sumba. Angin permukaan melemah dan berputar ke Utara, memicu sudut elevasi melonjak tinggi di atas 60 derajat (balon terbang dominan vertikal)."},
    12: {"name": "Desember (Awal Musim Barat)", "low_dir": 39.7, "mid_dir": 70.4, "high_dir": 68.0, "low_spd": 7.8, "mid_spd": 7.5, "high_spd": 7.9, "desc": "Indikasi awal masuknya pola Monsun Asia. Aliran arah angin mulai bergeser tidak menentu di rentang Utara hingga Timur Laut."}
}

# --- INSTANSIASI STATE MEMORI SIMULASI ---
if 'generated_records' not in st.session_state:
    st.session_state.generated_records = []
if 'hodo_points' not in st.session_state:
    st.session_state.hodo_points = []
if 'last_idx' not in st.session_state:
    st.session_state.last_idx = 0
if 'selected_row_idx' not in st.session_state:
    st.session_state.selected_row_idx = 1

# --- DETEKSI OTOMATIS IKILIM & WAKTU (ZONA WAKTU WITA) ---
tz_wita = pytz.timezone('Asia/Makassar')
now = datetime.now(tz_wita)
current_month = now.month
current_hour = now.hour

month_info = CLIMATOLOGY_MATRIX[current_month]

# Aturan Otomatis Laju Naik BMKG: Siang (polos) = 600 ft/min, Malam (senter pibal) = 500 ft/min
if 5 <= current_hour < 17:
    auto_rate_ft_min = 600.0
    waktu_label = "☀️ Pengamatan Siang (Balon Polos)"
else:
    auto_rate_ft_min = 500.0
    waktu_label = "🌙 Pengamatan Malam (Membawa Senter Pibal)"

# --- HEADER APLIKASI ---
st.markdown(
    f"""
    <div style='background-color:#0d3b66; padding:15px; border-radius:8px; text-align:center; color:white; margin-bottom:20px;'>
        <h2 style='margin:0; color:white;'>PIBAL INTELLIGENT SIMULATOR (CLIMATOLOGY ENGINE)</h2>
        <p style='margin:5px 0 0 0; font-size:14px;'>Stasiun Meteorologi Umbu Mehang Kunda, Waingapu (97340) | Elevasi: 32.8 m</p>
        <p style='margin:2px 0 0 0; font-style:italic; font-size:13px; color:#f1c40f;'>
            Bulan Aktif: <b>{month_info['name']}</b> | Laju Naik Balon: <b>{int(auto_rate_ft_min)} ft/min</b> ({waktu_label})
        </p>
    </div>
    """, 
    unsafe_allow_html=True
)

# --- FUNGSI CORE ENGINE KLIMATOLOGI ---
def run_generation_core(target_amount, rate_ft_min, fresh=False):
    if fresh:
        st.session_state.generated_records = []
        st.session_state.hodo_points = []
        st.session_state.last_idx = 0
        st.session_state.selected_row_idx = 1
        target_readings = target_amount
    else:
        target_readings = st.session_state.last_idx + target_amount

    start_loop = st.session_state.last_idx + 1
    
    current_x, current_y = 0.0, 0.0
    if not fresh and st.session_state.generated_records:
        last_rec = st.session_state.generated_records[-1]
        current_x = last_rec["_real_x"]
        current_y = last_rec["_real_y"]

    for idx in range(start_loop, target_readings + 1):
        
        # LOGIKA BMKG: Pembacaan 1 diabaikan dari elevasi, 31 pembacaan = 15.000 ft
        height_above_stn = (idx - 1) * 500.0
        
        target_level = math.ceil((idx - 1) / 2) * 1000
        if target_level == 0:
            level_target_str = "Surface (Elevasi 32.8m)"
        else:
            level_target_str = f"Level {target_level} ft"

        dt = (500.0 / rate_ft_min) * 60.0

        if idx == 1:
            # Manipulasi Visual Pembacaan 1 agar seragam & natural di web BMKG
            azimuth_deg = (month_info["low_dir"] + random.uniform(-8, 8)) % 360
            elevation_deg = random.uniform(87.1, 89.6) # Balon baru lepas, elevasi tinggi
            
            # Titik asal (origin) di belakang layar tetap murni 0 agar Hodograph akurat
            current_x, current_y = 0.0, 0.0
            horizontal_dist = 0.0
            u_kt, v_kt = 0.0, 0.0
        else:
            # PEMODELAN ARAH & KECEPATAN ANGIN BERBASIS DATA RIIL
            if height_above_stn <= 3000:
                running_dir = month_info["low_dir"] + random.uniform(-10, 10)
                running_speed = max(1.0, month_info["low_spd"] + random.uniform(-2.5, 2.5))
            elif height_above_stn <= 8000:
                running_dir = month_info["mid_dir"] + random.uniform(-20, 20)
                running_speed = max(1.0, month_info["mid_spd"] + random.uniform(-3.0, 3.0))
            else:
                running_dir = month_info["high_dir"] + random.uniform(-28, 28)
                running_speed = max(1.0, month_info["high_spd"] + random.uniform(-3.5, 3.5))
            
            speed_ft_sec = running_speed * 1.68781
            move_rad = math.radians((running_dir + 180) % 360)
            
            current_x += speed_ft_sec * math.sin(move_rad) * dt
            current_y += speed_ft_sec * math.cos(move_rad) * dt
            
            horizontal_dist = math.hypot(current_x, current_y)
            if horizontal_dist == 0:
                azimuth_deg = 0.0
                elevation_deg = 90.0
            else:
                azimuth_deg = math.degrees(math.atan2(current_x, current_y)) % 360
                elevation_deg = math.degrees(math.atan2(height_above_stn, horizontal_dist))
            
            # Fluktuasi ketelitian teodolit
            dist_factor = min(2.0, horizontal_dist / 8000.0)
            azimuth_deg = (azimuth_deg + random.uniform(-0.4, 0.4) * (1.0 + dist_factor)) % 360
            elevation_deg = max(0.4, min(89.6, elevation_deg + random.uniform(-0.2, 0.2) * (1.0 + dist_factor)))

            # Hitung komponen Hodograph
            if idx == 2 and fresh:
                # Pergerakan murni pertama setelah lepas landas
                u_kt = ((current_x - 0.0) / dt) / 1.68781
                v_kt = ((current_y - 0.0) / dt) / 1.68781
            else:
                last_rec = st.session_state.generated_records[-1]
                px = last_rec["_real_x"]
                py = last_rec["_real_y"]
                u_kt = ((current_x - px) / dt) / 1.68781
                v_kt = ((current_y - py) / dt) / 1.68781
            
        st.session_state.hodo_points.append((u_kt, v_kt, height_above_stn))

        # Format desimal agar koma ( , ) sesuai web BMKG
        azimuth_str = f"{azimuth_deg:.1f}".replace('.', ',')
        elevation_str = f"{elevation_deg:.1f}".replace('.', ',')

        st.session_state.generated_records.append({
            "Pembacaan Ke-": idx,
            "Tinggi Balon (ft)": f"{int(height_above_stn)} ft",
            "Level Target (BMKG)": level_target_str,
            "AZIMUT": azimuth_str,
            "ELEVASI": elevation_str,
            "_real_x": current_x,
            "_real_y": current_y
        })

    st.session_state.last_idx = target_readings

# --- LAYOUT APLIKASI ---
col_left, col_right = st.columns([6, 6], gap="large")

# === KOLOM KIRI: PARAMETER INPUT & TABEL DATA ===
with col_left:
    st.subheader("⚙️ Parameter Kontrol Pengamatan")
    
    target_readings = st.number_input("Input Durasi / Tambahan Menit:", min_value=1, value=31, step=1)

    st.markdown(
        f"""
        <div style='background-color:#e8f4fd; padding:10px; border-radius:6px; border-left:4px solid #1e88e5; font-size:13px; color:#0d47a1;'>
            Pembacaan Ke-1 (elevasi stasiun 32.8m) digenerate otomatis agar seragam. Untuk mencapai ketinggian <b>15.000 ft</b>, masukkan minimal <b>31</b> pembacaan.
        </div>
        """, 
        unsafe_allow_html=True
    )
    st.write("")

    b1, b2 = st.columns(2)
    with b1:
        if st.button("⚡ Generate Pembacaan Baru", type="primary", use_container_width=True):
            run_generation_core(target_readings, auto_rate_ft_min, fresh=True)
    with b2:
        if st.button("⏩ Lanjutkan Ketinggian", use_container_width=True):
            if st.session_state.last_idx == 0:
                st.error("Belum ada data awal. Silakan klik 'Generate Pembacaan Baru' terlebih dahulu.")
            else:
                run_generation_core(target_readings, auto_rate_ft_min, fresh=False)

    st.markdown("---")
    st.subheader("📊 Tabel Hasil Pembacaan Teropong (Azimut & Elevasi)")
    
    if st.session_state.generated_records:
        df = pd.DataFrame(st.session_state.generated_records)
        display_df = df.drop(columns=["_real_x", "_real_y"])
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        csv_buffer = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Ekspor Backup CSV",
            data=csv_buffer,
            file_name=f"pibal_waingapu_{datetime.now(tz_wita).strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("Belum ada data. Klik 'Generate Pembacaan Baru' untuk memproduksi angka.")

# === KOLOM KANAN: HODOGRAPH PREMIUM & ANALISIS METEO ===
with col_right:
    st.subheader("🎯 Hodograph Vektor Angin Hasil Reduksi (Knots)")
    
    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    ax.set_aspect('equal')
    
    max_hodo_range = 40
    for knots in [10, 20, 30, 40]:
        circle = plt.Circle((0, 0), knots, color='#bdc3c7', fill=False, linestyle='--', linewidth=1.0)
        ax.add_patch(circle)
        ax.text(0.5, knots + 0.5, f"{knots} kt", color='#7f8c8d', fontsize=8, style='italic')
        
    ax.axhline(0, color='#95a5a6', linestyle='-', linewidth=1.0)
    ax.axvline(0, color='#95a5a6', linestyle='-', linewidth=1.0)
    
    ax.text(0, max_hodo_range - 3, "U (360°)", weight='bold', ha='center', va='bottom', color='#2c3e50')
    ax.text(0, -max_hodo_range + 1, "S (180°)", weight='bold', ha='center', va='top', color='#2c3e50')
    ax.text(max_hodo_range - 1, 0, "T (90°)", weight='bold', ha='left', va='center', color='#2c3e50')
    ax.text(-max_hodo_range + 1, 0, "B (270°)", weight='bold', ha='right', va='center', color='#2c3e50')
    
    if st.session_state.hodo_points:
        u_pts = [p[0] for p in st.session_state.hodo_points]
        v_pts = [p[1] for p in st.session_state.hodo_points]
        heights = [p[2] for p in st.session_state.hodo_points]
        
        u_low, v_low = [], []
        u_mid, v_mid = [], []
        u_high, v_high = [], []
        
        for i, (u, v, h) in enumerate(zip(u_pts, v_pts, heights)):
            if i == 0: continue # Skip plot untuk data pembacaan 1 (Surface)
            if h <= 3000:
                u_low.append(u); v_low.append(v)
            elif h <= 8000:
                u_mid.append(u); v_mid.append(v)
            else:
                u_high.append(u); v_high.append(v)
        
        # Plot garis hodograph mengabaikan titik pertama
        ax.plot(u_pts[1:], v_pts[1:], color='#7f8c8d', linestyle='-', linewidth=1.5, alpha=0.7, zorder=1)
        
        if u_low:
            ax.scatter(u_low, v_low, color='#2ecc71', edgecolor='white', s=50, label='Lapisan Batas Tanah (≤ 3.000 ft)', zorder=3)
        if u_mid:
            ax.scatter(u_mid, v_mid, color='#3498db', edgecolor='white', s=50, label='Lapisan Menengah (3.500 - 8.000 ft)', zorder=3)
        if u_high:
            ax.scatter(u_high, v_high, color='#e74c3c', edgecolor='white', s=50, label='Udara Bebas Atas (> 8.000 ft)', zorder=3)
            
        ax.scatter(0, 0, color='#f1c40f', marker='*', s=150, edgecolor='black', label='Surface Station', zorder=4)

    ax.set_xlim(-max_hodo_range, max_hodo_range)
    ax.set_ylim(-max_hodo_range, max_hodo_range)
    ax.axis('off')
    
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.08), ncol=2, frameon=True, facecolor='#f8f9fa', edgecolor='#ccc', fontsize=8.5)
    st.pyplot(fig)
    
    # --- PANEL ANALISIS KLIMATOLOGI ---
    st.markdown("### 📝 Analisis Pembacaan Hodograph")
    if st.session_state.generated_records:
        st.success(
            f"**📋 ANALISIS METEOROLOGI BULANAN - {month_info['name'].upper()}**\n\n"
            f"* **Karakteristik Aliran Angin:** {month_info['desc']}\n"
            f"* **Verifikasi Kecepatan Riil:** Pergerakan balon diatur otomatis menggunakan profil kecepatan angin rata-rata Waingapu di Lapisan Bawah ({month_info['low_spd']} kt), Lapisan Menengah ({month_info['mid_spd']} kt), dan Lapisan Atas ({month_info['high_spd']} kt)."
        )
    else:
        st.info("Data analisis iklim akan muncul setelah simulasi dijalankan.")

    st.markdown("---")
    
    # --- PANEL NAVIGASI MANUAL HP-FRIENDLY ---
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
                f"Pembacaan Ke- {st.session_state.selected_row_idx}</div>", 
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
                    Tinggi Target: <b>{active_rec['Tinggi Balon (ft)']}</b> | <i>{active_rec['Level Target (BMKG)']}</i>
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
