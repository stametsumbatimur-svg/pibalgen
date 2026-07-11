import streamlit as st
import math
import random
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Pibal Code Generator Stamet Waingapu",
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
        <h2 style='margin:0; color:white;'>APLIKASI GENERATOR SANDI PIBAL (PILOT)</h2>
        <p style='margin:5px 0 0 0; font-style:italic; font-size:14px;'>Stasiun Meteorologi Waingapu (97340) | Format Kode Resmi WMO FM-32 (PPBB)</p>
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

# --- FUNGSI CORE ENGINE ENCODER SANDI PIBAL ---
def run_generation_core(target_readings, rate_ft_min, surf_ddd, surf_ff, season, atmos_mode, fresh=False):
    if fresh:
        st.session_state.generated_records = []
        st.session_state.hodo_points = []
        st.session_state.last_idx = 0
        st.session_state.base_dir = surf_ddd
        st.session_state.base_speed_kt = surf_ff
        st.session_state.selected_row_idx = 1

    if target_readings <= st.session_state.last_idx:
        st.warning(f"Data sudah ter-generate sebanyak {st.session_state.last_idx} baris.")
        return

    start_loop = st.session_state.last_idx + 1
    
    # Ambil kondisi running last session jika ada lanjutan kontinu
    if not fresh and st.session_state.generated_records:
        running_dir = float(st.session_state.generated_records[-1]["ARAH (°)"])
        running_speed = float(st.session_state.generated_records[-1]["KECEPATAN (kt)"])
    else:
        running_dir = st.session_state.base_dir
        running_speed = st.session_state.base_speed_kt

    for idx in range(start_loop, target_readings + 1):
        height_above_stn = idx * 500.0

        # Model Simulasi Berbasis Karakteristik Asli Atmosfer Waingapu
        if atmos_mode == "Tipe A (Meliuk Balik / Sampel 1)":
            sim_dir = (surf_ddd - (idx * 4.5) + 40 * math.sin(idx * 0.25) + random.uniform(-3, 3)) % 360
            sim_speed_kt = max(1.5, surf_ff + 8.0 * math.cos(idx * 0.18) + random.uniform(-1.0, 1.0))
        elif atmos_mode == "Tipe B (Lapisan Stabil / Sampel 2)":
            sim_dir = (surf_ddd - (idx * 0.8) + random.uniform(-1.5, 1.5)) % 360
            if idx < 5:
                sim_speed_kt = max(2.0, surf_ff + (idx * 1.8) + random.uniform(-1, 1))
            else:
                sim_speed_kt = max(2.0, 13.5 + random.uniform(-0.6, 0.6))
        else: # Tipe C (Angin Tenang / Sampel 3)
            sim_dir = (surf_ddd + (idx * 2.0) + random.uniform(-6, 6)) % 360
            sim_speed_kt = max(0.6, 2.2 + random.uniform(-0.5, 0.5))

        # Kunci nilai ke running tracker untuk kesinambungan baris berikutnya
        running_dir = sim_dir
        running_speed = sim_speed_kt

        target_level = math.ceil(idx / 2) * 1000
        level_target_str = f"Level {target_level} ft"

        # --- ENCODING PROSEDUR SANDI WMO (ddfff) ---
        # 1. Arah dd (Puluhan derajat terdekat, e.g. 264 -> 26, 267 -> 27)
        dd_val = int(round(sim_dir / 10.0))
        if dd_val > 36: dd_val = 1
        if dd_val == 0: dd_val = 36
        
        # 2. Kecepatan fff (3 Digit standar)
        speed_round = int(round(sim_speed_kt))
        
        if speed_round == 0:
            sandi_group = "00000"
        else:
            sandi_group = f"{dd_val:02d}{speed_round:03d}"

        # Simpan titik koordinat polar untuk verifikasi Hodograph
        rad_dir = math.radians(sim_dir)
        u_comp = -sim_speed_kt * math.sin(rad_dir)
        v_comp = -sim_speed_kt * math.cos(rad_dir)
        st.session_state.hodo_points.append((u_comp, v_comp, idx))

        st.session_state.generated_records.append({
            "Pembacaan Ke-": idx,
            "Tinggi Ketinggian": f"{int(height_above_stn)} ft",
            "Target Form": level_target_str,
            "ARAH (°)": f"{sim_dir:.0f}",
            "KECEPATAN (kt)": f"{sim_speed_kt:.0f}",
            "KELOMPOK SANDI": sandi_group
        })

    st.session_state.last_idx = target_readings

# --- LAYOUT APLIKASI ---
col_left, col_right = st.columns([7, 5], gap="large")

# === KOLOM KIRI: PARAMETER & TABEL DATA ===
with col_left:
    st.subheader("⚙️ Parameter Kontrol Pengamatan")
    
    c1, c2 = st.columns(2)
    with c1:
        target_readings = st.number_input("Target Jumlah Pembacaan:", min_value=1, value=31, step=1)
        surf_ddd = st.number_input("Angin Permukaan ddd (°):", min_value=0.0, max_value=360.0, value=315.0, step=5.0)
    with c2:
        rate_ft_min = st.number_input("Laju Naik Balon (ft/min):", min_value=1.0, value=600.0, step=10.0)
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
        if st.button("⚡ Generate Sandi Baru", type="primary", use_container_width=True):
            run_generation_core(target_readings, rate_ft_min, surf_ddd, surf_ff, season_key, selected_mode, fresh=True)
    with b2:
        if st.button("⏩ Lanjutkan ke Target", use_container_width=True):
            if st.session_state.last_idx == 0:
                st.error("Belum ada data awal. Silakan klik 'Generate Sandi Baru' terlebih dahulu.")
            else:
                run_generation_core(target_readings, rate_ft_min, surf_ddd, surf_ff, season_key, selected_mode, fresh=False)

    st.markdown("---")
    st.subheader("📊 Tabel Hasil Analisis Sandi PILOT")
    
    if st.session_state.generated_records:
        df = pd.DataFrame(st.session_state.generated_records)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        csv_buffer = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Ekspor Dokumen CSV",
            data=csv_buffer,
            file_name=f"pibal_sandi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("Belum ada data sandi yang dibuat. Atur parameter lalu pilih 'Generate Sandi Baru'.")

# === KOLOM KANAN: HODOGRAPH & TEXT BLOCK TELEGRAM ===
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
    
    # --- PANEL NAVIGASI MANUAL HP-FRIENDLY & DISPLAY KODE BESAR ---
    st.subheader("🔍 Panel Bantuan Ketik Manual")
    
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
                f"Tinggi: {st.session_state.selected_row_idx * 500} ft</div>", 
                unsafe_allow_html=True
            )
        with nv3:
            if st.button("NEXT ▶️", use_container_width=True, key="btn_next_mobile"):
                if st.session_state.selected_row_idx < len(readings_list):
                    st.session_state.selected_row_idx += 1
                    st.rerun()
                    
        active_rec = next(item for item in st.session_state.generated_records if item["Pembacaan Ke-"] == st.session_state.selected_row_idx)
        
        st.markdown(
            f"""
            <div style="background-color: #fffdf0; padding: 15px; border-radius: 8px; border: 2px solid #d62828; text-align: center; margin-top: 10px;">
                <div style="display: flex; justify-content: space-around; align-items: center;">
                    <div>
                        <div style="color: gray; font-size: 11px; font-weight: bold;">ARAH</div>
                        <div style="color: #333; font-size: 28px; font-weight: bold;">{active_rec['ARAH (°)']}°</div>
                    </div>
                    <div>
                        <div style="color: gray; font-size: 11px; font-weight: bold;">KECEPATAN</div>
                        <div style="color: #333; font-size: 28px; font-weight: bold;">{active_rec['KECEPATAN (kt)']} kt</div>
                    </div>
                    <div style="background-color: #e1f5fe; padding: 5px 15px; border-radius: 6px; border: 1px dashed #0288d1;">
                        <div style="color: #0288d1; font-size: 11px; font-weight: bold;">SANDI WMO</div>
                        <div style="color: #0d47a1; font-size: 32px; font-weight: bold; line-height: 1.1;">{active_rec['KELOMPOK SANDI']}</div>
                    </div>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # --- GENERATOR BLOK TEKS TELEGRAM ASLI (PPBB) ---
        st.markdown("### 📝 Teks Telegram Sandi PILOT (PPBB)")
        
        now = datetime.now()
        day_str = now.strftime("%d")
        hour_str = now.strftime("%H")
        
        # Format Header PILOT: PPBB YYGG4 (4 berarti satuan Knot & tracking Optik)
        telegram_lines = [f"PPBB {day_str}{hour_str}4", "97340"]
        
        # Satukan data sandi per kelompok kelompok baris telegram
        sandi_list = [r["KELOMPOK SANDI"] for r in st.session_state.generated_records]
        
        # Gabungkan menjadi format baris telegram (max 3-4 kelompok per baris agar rapi)
        chunk_size = 4
        for i in range(0, len(sandi_list), chunk_size):
            line_chunk = sandi_list[i:i+chunk_size]
            telegram_lines.append(" ".join(line_chunk))
            
        full_telegram_text = "\n".join(telegram_lines)
        
        st.text_area(
            label="Tinggal Blok & Copy untuk Pengiriman Meteorologi:",
            value=full_telegram_text,
            height=180,
            key="txt_telegram_block"
        )
    else:
        st.info("Data teks telegram sandi akan otomatis muncul di sini setelah Anda melakukan generate.")
