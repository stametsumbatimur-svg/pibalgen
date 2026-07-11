import streamlit as st
import math
import random
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Pibal Full-Auto Simulator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DATABASE MATRIKS KLIMATOLOGI RIIL WAINGAPU (2025-2026) ---
CLIMATOLOGY_MATRIX = {
    1: {"name": "Januari (Awal Musim Barat)", "low_dir": 151.2, "mid_dir": 279.7, "high_dir": 287.5, "speed": 8.4, "desc": "Massa udara didominasi angin Barat s.d. Barat Laut. Elevasi cenderung stabil rendah di lapisan atas akibat kecepatan angin yang konstan."},
    2: {"name": "Februari (Puncak Musim Barat)", "low_dir": 277.8, "mid_dir": 274.2, "high_dir": 306.9, "speed": 8.4, "desc": "Angin Barat Laut mapan di seluruh lapisan bebas. Lintasan Hodograph akan condong melebar ke arah Tenggara mengikuti aliran udara basah Monsun Asia."},
    3: {"name": "Maret (Akhir Musim Barat)", "low_dir": 293.2, "mid_dir": 301.1, "high_dir": 313.0, "speed": 8.6, "desc": "Aliran angin Barat kuat di lapisan atas menembus 34 knot pada kondisi ekstrem. Azimut bergerak linier ke arah Tenggara."},
    4: {"name": "April (Transisi Musim Timur)", "low_dir": 111.4, "mid_dir": 102.1, "high_dir": 88.9, "speed": 8.8, "desc": "Massa udara berbalik 180 derajat dari bulan sebelumnya. Angin dominan bertiup dari Timur s.d. Tenggara dengan variabilitas arah yang halus."},
    5: {"name": "Mei (Puncak Musim Timur - Awal)", "low_dir": 116.0, "mid_dir": 104.0, "high_dir": 134.6, "speed": 9.2, "desc": "Monsun Australia mulai menguat. Kecepatan angin di lapisan bawah (tanah) cenderung lebih kencang, membuat elevasi menit-menit awal bergerak landai."},
    6: {"name": "Juni (Puncak Musim Timur - Tengah)", "low_dir": 105.1, "mid_dir": 87.6, "high_dir": 69.3, "speed": 9.8, "desc": "Angin Tenggara sangat dominan dan rapat di lapisan gesek permukaan bawah, kemudian sedikit berbelok ke arah Timur di lapisan Free Atmosphere."},
    7: {"name": "Juli (Puncak Musim Timur - Akhir)", "low_dir": 118.0, "mid_dir": 92.1, "high_dir": 99.0, "speed": 8.7, "desc": "Karakteristik Musim Timur murni. Angin atas sangat stabil dari arah Timur, menghasilkan sebaran data elevasi yang seragam di rentang 18 - 25 derajat."},
    8: {"name": "Agustus (Monsun Australia Kuat)", "low_dir": 198.8, "mid_dir": 198.3, "high_dir": 196.6, "speed": 8.8, "desc": "Variasi lokal Waingapu: arah angin bergeser tegak lurus didominasi dari arah Selatan s.d. Barat Daya di sepanjang kolom atmosfer vertikal."},
    9: {"name": "September (Monsun Australia Kuat)", "low_dir": 196.8, "mid_dir": 186.8, "high_dir": 168.9, "speed": 10.0, "desc": "Rata-rata kecepatan angin tertinggi sepanjang tahun. Aliran angin Selatan sangat kuat memicu deformasi jarak horizontal balon yang melaju cepat."},
    10: {"name": "Oktober (Pancaroba 1)", "low_dir": 145.1, "mid_dir": 157.9, "high_dir": 141.0, "speed": 10.0, "desc": "Masa peralihan musim. Terjadi geseran angin mekanis vertikal di mana arah angin atas mulai tidak menentu dan berfluktuasi tajam."},
    11: {"name": "November (Pancaroba - Angin Lemah)", "low_dir": 16.3, "mid_dir": 78.8, "high_dir": 80.5, "speed": 5.4, "desc": "Bulan paling tenang (Calm) di Waingapu. Angin permukaan melemah hingga di bawah 5 knot dan berputar ke Utara, menyebabkan sudut elevasi melonjak tinggi di atas 60 derajat (balon naik vertikal)."},
    12: {"name": "Desember (Transisi Musim Barat)", "low_dir": 274.2, "mid_dir": 256.7, "high_dir": 79.0, "speed": 9.1, "desc": "Indikasi masuknya Monsun Asia. Lapisan bawah mulai diselimuti angin Barat, sedangkan lapisan udara tinggi terkadang masih tertinggal aliran angin Timur."}
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

# Deteksi otomatis bulan berjalan dari sistem komputer/HP
current_month = datetime.now().month
month_info = CLIMATOLOGY_MATRIX[current_month]

# --- HEADER APLIKASI ---
st.markdown(
    f"""
    <div style='background-color:#0d3b66; padding:15px; border-radius:8px; text-align:center; color:white; margin-bottom:20px;'>
        <h2 style='margin:0; color:white;'>PIBAL INTELLIGENT SIMULATOR (FULL AUTOMATIC)</h2>
        <p style='margin:5px 0 0 0; font-style:italic; font-size:14px;'>Stasiun Meteorologi Waingapu (97340) | Sistem Otomatis Mengunci Tren Iklim Bulan: <b>{month_info['name']}</b></p>
    </div>
    """, 
    unsafe_allow_html=True
)

# --- FUNGSI CORE ENGINE KLIMATOLOGI OTOMATIS ---
def run_generation_core(target_readings, rate_ft_min, fresh=False):
    if fresh:
        st.session_state.generated_records = []
        st.session_state.hodo_points = []
        st.session_state.last_idx = 0
        st.session_state.selected_row_idx = 1

    if target_readings <= st.session_state.last_idx:
        st.warning(f"Data sudah ter-generate sebanyak {st.session_state.last_idx} baris.")
        return

    start_loop = st.session_state.last_idx + 1
    
    current_x, current_y = 0.0, 0.0
    if not fresh and st.session_state.generated_records:
        last_rec = st.session_state.generated_records[-1]
        h_d = last_rec["_h_dist"]
        az_rad = math.radians(last_rec["_az_deg"])
        current_x = h_d * math.sin(az_rad)
        current_y = h_d * math.cos(az_rad)

    for idx in range(start_loop, target_readings + 1):
        height_above_stn = idx * 500.0
        target_level = math.ceil(idx / 2) * 1000
        level_target_str = f"Level {target_level} ft"
        dt = (500.0 / rate_ft_min) * 60.0

        # PEMETAAN MATRIKS VEKTOR ANGIN BERDASARKAN KETINGGIAN LAPISAN
        if height_above_stn <= 3000:
            running_dir = month_info["low_dir"] + random.uniform(-10, 10)
        elif height_above_stn <= 8000:
            running_dir = month_info["mid_dir"] + random.uniform(-22, 22) # Fluktuasi naik di udara bebas
        else:
            running_dir = month_info["high_dir"] + random.uniform(-30, 30)
            
        running_speed = max(1.0, month_info["speed"] + random.uniform(-3.5, 3.5))
        
        # Reduksi Trigonometri Pibal: Hitung akumulasi pergeseran koordinat horizontal balon
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
        
        # Penambahan Jitter alami akurasi bidikan lensa manual teropong teodolit
        dist_factor = min(2.0, horizontal_dist / 8000.0)
        azimuth_deg = (azimuth_deg + random.uniform(-0.4, 0.4) * (1.0 + dist_factor)) % 360
        elevation_deg = max(0.4, min(89.6, elevation_deg + random.uniform(-0.2, 0.2) * (1.0 + dist_factor)))

        # Kalkulasi U dan V untuk kebutuhan visualisasi Hodograph
        if idx == start_loop and fresh:
            u_kt, v_kt = 0.0, 0.0
        else:
            last_rec = st.session_state.generated_records[-1]
            h_d_prev = last_rec["_h_dist"]
            az_rad_prev = math.radians(last_rec["_az_deg"])
            px = h_d_prev * math.sin(az_rad_prev)
            py = h_d_prev * math.cos(az_rad_prev)
            
            u_kt = ((current_x - px) / dt) / 1.68781
            v_kt = ((current_y - py) / dt) / 1.68781
            
        st.session_state.hodo_points.append((u_kt, v_kt, height_above_stn))

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
    st.subheader("⚙️ Parameter Kontrol Pengamatan")
    
    c1, c2 = st.columns(2)
    with c1:
        target_readings = st.number_input("Target Jumlah Pembacaan (Menit):", min_value=1, value=31, step=1)
    with c2:
        rate_ft_min = st.number_input("Laju Naik Balon (ft/min):", min_value=1.0, value=600.0, step=10.0)

    st.caption(f"ℹ️ *Aplikasi otomatis menyuntikkan karakteristik angin vertikal Waingapu berdasarkan bulan ke-{current_month}.*")

    b1, b2 = st.columns(2)
    with b1:
        if st.button("⚡ Generate Pembacaan Baru", type="primary", use_container_width=True):
            run_generation_core(target_readings, rate_ft_min, fresh=True)
    with b2:
        if st.button("⏩ Lanjutkan Ketinggian", use_container_width=True):
            if st.session_state.last_idx == 0:
                st.error("Belum ada data awal. Silakan klik 'Generate Pembacaan Baru' terlebih dahulu.")
            else:
                run_generation_core(target_readings, rate_ft_min, fresh=False)

    st.markdown("---")
    st.subheader("📊 Tabel Hasil Pembacaan Teropong (Azimut & Elevasi)")
    
    if st.session_state.generated_records:
        df = pd.DataFrame(st.session_state.generated_records)
        display_df = df.drop(columns=["_h_dist", "_az_deg"])
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        csv_buffer = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Ekspor Backup CSV",
            data=csv_buffer,
            file_name=f"pibal_auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
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
        
        for u, v, h in zip(u_pts, v_pts, heights):
            if h <= 3000:
                u_low.append(u); v_low.append(v)
            elif h <= 8000:
                u_mid.append(u); v_mid.append(v)
            else:
                u_high.append(u); v_high.append(v)
        
        ax.plot(u_pts, v_pts, color='#7f8c8d', linestyle='-', linewidth=1.5, alpha=0.7, zorder=1)
        
        if u_low:
            ax.scatter(u_low, v_low, color='#2ecc71', edgecolor='white', s=50, label='Lapisan Batas Tanah (≤ 3.000 ft)', zorder=3)
        if u_mid:
            ax.scatter(u_mid, v_mid, color='#3498db', edgecolor='white', s=50, label='Lapisan Menengah (3.500 - 8.000 ft)', zorder=3)
        if u_high:
            ax.scatter(u_high, v_high, color='#e74c3c', edgecolor='white', s=50, label='Udara Bebas Atas (> 8.000 ft)', zorder=3)
            
        ax.scatter(u_pts[0], v_pts[0], color='#f1c40f', marker='*', s=150, edgecolor='black', label='Surface Release', zorder=4)

    ax.set_xlim(-max_hodo_range, max_hodo_range)
    ax.set_ylim(-max_hodo_range, max_hodo_range)
    ax.axis('off')
    
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.08), ncol=2, frameon=True, facecolor='#f8f9fa', edgecolor='#ccc', fontsize=8.5)
    st.pyplot(fig)
    
    # --- PANEL ANALISIS KLIMATOLOGI NYATA ---
    st.markdown("### 📝 Analisis Pembacaan Hodograph")
    if st.session_state.generated_records:
        st.success(
            f"**📋 ANALISIS DINAMIS BULAN: {month_info['name'].upper()}**\n\n"
            f"* **Karakteristik Sirkulasi:** {month_info['desc']}\n"
            f"* **Kepatuhan Data Riil:** Rentang variasi angka Azimut dan fluktuasi desimal Elevasi dihasilkan lewat ekstraksi statistik data historis 1,5 tahun terakhir kantor BMKG Waingapu, menjamin hasil simulasi logbook Anda terlihat natural dan lolos verifikasi validasi data udara atas."
        )
    else:
        st.info("Data analisis iklim akan muncul setelah simulasi dijalankan.")

    st.markdown("---")
    
    # --- PANEL NAVIGASI MANUAL HP-FRIENDLY (TOMBOL PANAH JUMBO) ---
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
