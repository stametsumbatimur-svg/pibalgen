import streamlit as st
import math
import random
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Pibal Teodolit & Sandi Generator",
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
        <h2 style='margin:0; color:white;'>APLIKASI REDUKSI PIBAL & GENERATOR SANDI PILOT</h2>
        <p style='margin:5px 0 0 0; font-style:italic; font-size:14px;'>Stasiun Meteorologi Waingapu (97340) | Input: Azimut & Elevasi ➡️ Output: dddfff & Sandi PPBB</p>
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

# --- FUNGSI CORE ENGINE: SIMULASI BIDIKAN & REDUKSI ANGIN ---
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
    
    # Koordinat balon sebelumnya untuk perhitungan delta angin
    prev_x, prev_y = 0.0, 0.0
    if not fresh and st.session_state.generated_records:
        # Menarik data koordinat internal dari langkah terakhir jika kontinu
        last_rec = st.session_state.generated_records[-1]
        # Rekonstruksi posisi X, Y terakhir
        h_d = last_rec["_h_dist"]
        az_rad = math.radians(last_rec["_az_deg"])
        prev_x = h_d * math.sin(az_rad)
        prev_y = h_d * math.cos(az_rad)

    for idx in range(start_loop, target_readings + 1):
        height_above_stn = idx * 500.0
        dt = (500.0 / rate_ft_min) * 60.0 # Durasi waktu (detik) per interval kenaikan

        # 1. GENERATOR BIDIKAN ANGKA MENTAH (Mengikuti Karakteristik Gambar Sampel Asli)
        if atmos_mode == "Tipe A (Meliuk Balik / Sampel 1)":
            # Azimut: Turun dulu lalu naik melengkung balik
            azimuth_deg = (base_azimuth - (idx * 3.5) + 25 * math.sin(idx * 0.2) + random.uniform(-0.4, 0.4)) % 360
            # Elevasi: Turun ke ~23 derajat lalu melambung naik tinggi ke ~64 derajat
            if idx <= 6:
                elevation_deg = max(20.0, 28.5 - (idx * 1.1) + random.uniform(-0.2, 0.2))
            elif idx <= 18:
                elevation_deg = min(65.0, 23.0 + ((idx - 6) * 3.4) + random.uniform(-0.3, 0.3))
            else:
                elevation_deg = max(40.0, 64.0 - ((idx - 18) * 1.3) + random.uniform(-0.2, 0.2))
                
        elif atmos_mode == "Tipe B (Lapisan Stabil / Sampel 2)":
            # Azimut: Mengalami shifting tajam di awal, lalu stabil konstan di arah ~280-290
            azimuth_deg = (base_azimuth - (idx * 0.8) + random.uniform(-0.3, 0.3)) % 360
            # Elevasi: Drop tajam dari tinggi, lalu terkunci stabil datar di angka 17 - 21 derajat
            if idx <= 5:
                elevation_deg = max(20.0, 47.0 - (idx * 5.2) + random.uniform(-0.4, 0.4))
            else:
                elevation_deg = 18.0 + (math.sin(idx * 0.4) * 1.2) + random.uniform(-0.3, 0.3)
                
        else: # Tipe C (Angin Tenang / Sampel 3)
            # Azimut: Bergerak sangat sempit berputar-putar di area dekat baseline awal
            azimuth_deg = (base_azimuth + random.uniform(-2.5, 2.5)) % 360
            # Elevasi: Konstan sangat tinggi (> 55 derajat), menandakan balon naik hampir vertikal tegak lurus
            elevation_deg = 60.0 + (math.sin(idx * 0.5) * 4.0) + random.uniform(-0.5, 0.5)

        # 2. PROSEDUR MATEMATIS REDUKSI PIBAL (Menghitung ddd & fff dari Azimut & Elevasi)
        elev_rad = math.radians(elevation_deg)
        # Jarak Horizontal Balon dari Stasiun (ft): d = H / tan(el)
        horizontal_dist = height_above_stn / math.tan(elev_rad)
        
        az_rad = math.radians(azimuth_deg)
        # Posisi Koordinat Kartesius Balon (X = Timur, Y = Utara)
        current_x = horizontal_dist * math.sin(az_rad)
        current_y = horizontal_dist * math.cos(az_rad)
        
        # Hitung perbedaan jarak pergerakan dari titik menit sebelumnya
        dx = current_x - prev_x
        dy = current_y - prev_y
        
        # Kecepatan komponen angin (kaki per detik)
        u_comp = dx / dt
        v_comp = dy / dt
        
        # Konversi total kecepatan ke satuan Knot (1 knot = 1.68781 kaki/detik)
        speed_kt = math.hypot(u_comp, v_comp) / 1.68781
        
        # Menentukan arah datangnya angin (Arah ddd = atan2(-X, -Y))
        dir_deg = math.degrees(math.atan2(-u_comp, -v_comp)) % 360
        
        # Amankan data koordinat saat ini untuk iterasi menit selanjutnya
        prev_x, prev_y = current_x, current_y

        # 3. ENCODING FORMAT TELEGRAM RESMI WMO (ddfff)
        dd_val = int(round(dir_deg / 10.0))
        if dd_val > 36: dd_val = 1
        if dd_val == 0: dd_val = 36
        speed_round = int(round(speed_kt))
        sandi_group = f"{dd_val:02d}{speed_round:03d}" if speed_round > 0 else "00000"

        # Simpan titik komponen angin asli untuk plot Hodograph kelurusan angin
        hodo_u = -speed_kt * math.sin(math.radians(dir_deg))
        hodo_v = -speed_kt * math.cos(math.radians(dir_deg))
        st.session_state.hodo_points.append((hodo_u, hodo_v, idx))

        target_level = math.ceil(idx / 2) * 1000
        level_target_str = f"Level {target_level} ft"

        st.session_state.generated_records.append({
            "Pembacaan Ke-": idx,
            "Tinggi (ft)": f"{int(height_above_stn)} ft",
            "Target Level": level_target_str,
            "AZIMUT": f"{azimuth_deg:.1f}".replace('.', ','),
            "ELEVASI": f"{elevation_deg:.1f}".replace('.', ','),
            "ARAH (ddd)": f"{dir_deg:.0f}°",
            "KEC (fff)": f"{speed_kt:.0f} kt",
            "SANDI WMO": sandi_group,
            "_h_dist": horizontal_dist,
            "_az_deg": azimuth_deg
        })

    st.session_state.last_idx = target_readings

# --- LAYOUT DENGAN DUA KOLOM UTAMA ---
col_left, col_right = st.columns([7, 5], gap="large")

# === KOLOM KIRI: INPUT & TABEL DATA UTAMA ===
with col_left:
    st.subheader("⚙️ Parameter Kontrol Pengamatan Teropong")
    
    c1, c2 = st.columns(2)
    with c1:
        target_readings = st.number_input("Target Jumlah Pembacaan (Menit):", min_value=1, value=31, step=1)
        base_azimuth = st.number_input("Azimut Awal Pelepasan (°):", min_value=0.0, max_value=360.0, value=313.0, step=1.0)
    with c2:
        rate_ft_min = st.number_input("Laju Naik Balon (ft/min):", min_value=1.0, value=600.0, step=10.0)
        selected_mode = st.selectbox(
            "🎯 Karakteristik Bidikan (Mengacu Pola Logbook Asli):",
            ["Tipe A (Meliuk Balik / Sampel 1)", "Tipe B (Lapisan Stabil / Sampel 2)", "Tipe C (Angin Tenang / Sampel 3)"]
        )
        
    season_options = ["timur", "barat", "pancaroba"]
    season_labels = ["Musim Timur", "Musim Barat", "Pancaroba"]
    selected_season = st.radio("Pola Kebiasaan Musim:", season_labels, index=default_season_idx, horizontal=True)
    season_key = season_options[season_labels.index(selected_season)]

    b1, b2 = st.columns(2)
    with b1:
        if st.button("⚡ Generate Data Pembacaan Baru", type="primary", use_container_width=True):
            run_generation_core(target_readings, rate_ft_min, base_azimuth, selected_mode, fresh=True)
    with b2:
        if st.button("⏩ Lanjutkan ke Target Ketinggian", use_container_width=True):
            if st.session_state.last_idx == 0:
                st.error("Belum ada data awal. Klik 'Generate Data Pembacaan Baru' terlebih dahulu.")
            else:
                run_generation_core(target_readings, rate_ft_min, base_azimuth, selected_mode, fresh=False)

    st.markdown("---")
    st.subheader("📊 Tabel Hasil Reduksi Geometri Teodolit")
    
    if st.session_state.generated_records:
        # Menghapus kolom internal(_) sebelum dilempar ke tabel antarmuka user
        display_df = pd.DataFrame(st.session_state.generated_records).drop(columns=["_h_dist", "_az_deg"])
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        csv_buffer = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Ekspor Backup File CSV",
            data=csv_buffer,
            file_name=f"reduksi_pibal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("Belum ada data bidikan teodolit yang dibuat. Tentukan parameter lalu pilih 'Generate Data Pembacaan Baru'.")

# === KOLOM KANAN: HODOGRAPH & PANEL ASISTEN HP ===
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
    
    # --- PANEL NAVIGASI MANUAL HP-FRIENDLY (TOMBOL PANAH BESAR) ---
    st.subheader("🔍 Panel Bantuan Salin Manual ke Form Komputer")
    
    if st.session_state.generated_records:
        readings_list = [r["Pembacaan Ke-"] for r in st.session_state.generated_records]
        
        if st.session_state.selected_row_idx > len(readings_list):
            st.session_state.selected_row_idx = len(readings_list)
        if st.session_state.selected_row_idx < 1:
            st.session_state.selected_row_idx = 1
            
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
                f"Data Menit Ke-{st.session_state.selected_row_idx}</div>", 
                unsafe_allow_html=True
            )
        with nv3:
            if st.button("NEXT ▶️", use_container_width=True, key="btn_next_mobile"):
                if st.session_state.selected_row_idx < len(readings_list):
                    st.session_state.selected_row_idx += 1
                    st.rerun()
                    
        active_rec = st.session_state.generated_records[st.session_state.selected_row_idx - 1]
        
        # Display Box Informasi Data Mentah & Data Terhitung Sekaligus
        st.markdown(
            f"""
            <div style="background-color: #fffdf0; padding: 15px; border-radius: 8px; border: 2px solid #d62828; margin-top: 10px;">
                <div style="text-align: left; font-size: 13px; color: gray; font-weight: bold; margin-bottom: 5px;">
                     Ketinggian: {active_rec['Tinggi (ft)']} | {active_rec['Target Level']}
                </div>
                <div style="display: flex; justify-content: space-between; text-align: center; background: white; padding: 10px; border-radius: 6px; border: 1px solid #ddd;">
                    <div>
                        <div style="color: gray; font-size: 11px; font-weight: bold;">AZIMUT (Input)</div>
                        <div style="color: #4caf50; font-size: 24px; font-weight: bold;">{active_rec['AZIMUT']}</div>
                    </div>
                    <div>
                        <div style="color: gray; font-size: 11px; font-weight: bold;">ELEVASI (Input)</div>
                        <div style="color: #f44336; font-size: 24px; font-weight: bold;">{active_rec['ELEVASI']}</div>
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; text-align: center;">
                    <div>
                        <div style="color: gray; font-size: 10px; font-weight: bold;">ARAH ANGIN</div>
                        <div style="color: #333; font-size: 18px; font-weight: bold;">{active_rec['ARAH (ddd)']}</div>
                    </div>
                    <div>
                        <div style="color: gray; font-size: 10px; font-weight: bold;">KEC ANGIN</div>
                        <div style="color: #333; font-size: 18px; font-weight: bold;">{active_rec['KEC (fff)']}</div>
                    </div>
                    <div style="background-color: #e1f5fe; padding: 5px 12px; border-radius: 6px; border: 1px dashed #0288d1;">
                        <div style="color: #0288d1; font-size: 10px; font-weight: bold;">GRUP SANDI PILOT</div>
                        <div style="color: #0d47a1; font-size: 24px; font-weight: bold; line-height: 1.1;">{active_rec['SANDI WMO']}</div>
                    </div>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # --- GENERATOR TEKS TELEGRAM PPBB OTOMATIS ---
        st.markdown("### 📝 Teks Telegram Sandi PILOT (PPBB)")
        
        now = datetime.now()
        day_str = now.strftime("%d")
        # Format Pibal WMO: Jam Pelaporan + Indikator Satuan (4 = Satuan Knot, Metode Optik Teodolit)
        hour_indicator = now.strftime("%H") + "4" 
        
        telegram_lines = [f"PPBB {day_str}{hour_indicator}", "97340"]
        
        sandi_list = [r["SANDI WMO"] for r in st.session_state.generated_records]
        
        # Susun telegram menjadi baris pendek (maksimal 4 kelompok sandi per baris telegram)
        for i in range(0, len(sandi_list), 4):
            chunk = sandi_list[i:i+4]
            telegram_lines.append(" ".join(chunk))
            
        full_telegram_text = "\n".join(telegram_lines)
        
        st.text_area(
            label="Salin Kode Blok Telegram Ini untuk Pengiriman Balai/Pusat:",
            value=full_telegram_text,
            height=180,
            key="txt_telegram_block"
        )
    else:
        st.info("Jalankan modul simulasi di sisi kiri untuk memunculkan teks kode telegram.")
