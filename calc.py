# --- GENERATOR INTEGRASI MAJU (REALISTIS: ADA TREN & TURBULENSI HALUS) ---
def run_generation_core(target_readings, surf_ddd, surf_ff, month_idx, fresh=False):
    if fresh or not st.session_state.generated_records:
        st.session_state.generated_records = []
        st.session_state.hodo_points = []
        st.session_state.last_idx = 0
        st.session_state.active_row = 1

    if target_readings <= st.session_state.last_idx:
        st.warning(f"Data sudah ter-generate sebanyak {st.session_state.last_idx} baris.")
        return

    # Cari referensi data historis
    hist_rows = []
    if df_historical is not None and obs_metadata is not None:
        match_res = find_best_historical_match(surf_ddd, surf_ff, month_idx, obs_metadata)
        if match_res:
            match_ts, match_dt, h_ddd, h_ff = match_res
            hist_rows = df_historical[df_historical['data_timestamp'] == match_ts].sort_values('pembacaan').to_dict('records')
            dt_str = match_dt.strftime('%d %B %Y %H:%M UTC')
            st.session_state.matched_info = f"📌 **Pola Historis Acuan:** {dt_str} (Permukaan: {h_ddd:.0f}° / {min(h_ff, MAX_SPEED_KT):.0f} kt)"
        else:
            st.session_state.matched_info = "📌 **Pola Simulasi Profil Atmosfer Waingapu (Fallback)**"
    else:
        st.session_state.matched_info = "📌 **Pola Simulasi Profil Atmosfer Waingapu (Dataset Offline)**"

    hist_dict = {r['pembacaan']: r for r in hist_rows}
    rate_ft_min = 600.0  # Laju naik balon standar BMKG (600 ft/menit)
    
    x_curr, y_curr = 0.0, 0.0
    
    # Vektor Awal
    u_surf = -surf_ff * math.sin(math.radians(surf_ddd))
    v_surf = -surf_ff * math.cos(math.radians(surf_ddd))
    u_prev, v_prev = u_surf, v_surf
    
    # Alpha dinaikkan ke 0.65 agar gerigi alami atmosfer tidak terhapus total
    alpha = 0.65 

    for idx in range(1, target_readings + 1):
        target_level = math.ceil((idx - 1) / 2) * 1000 if idx > 1 else 0
        level_target_str = "Diabaikan (Rilis)" if idx == 1 else f"Level {target_level} ft"
        height_above_stn = 100.0 if idx == 1 else (idx - 1) * 500.0
        
        # 1. Penentuan Vektor Mentah
        if idx in hist_dict:
            az_m = hist_dict[idx]['azimuth']
            el_m = max(2.0, min(88.0, hist_dict[idx]['elevasi']))
            d_m = height_above_stn / math.tan(math.radians(el_m))
            x_m = d_m * math.sin(math.radians(az_m))
            y_m = d_m * math.cos(math.radians(az_m))
            
            dt_step = 10.0 if idx == 1 else ((height_above_stn - ((idx - 2) * 500.0 if idx > 2 else 100.0)) / rate_ft_min) * 60.0
            u_raw = ((x_m - x_curr) / dt_step) / 1.68781
            v_raw = ((y_m - y_curr) / dt_step) / 1.68781
        else:
            # Profil sintetis non-linier khas lapisan batas Waingapu
            shear_angle = math.radians(surf_ddd + (math.log(idx + 1) * 8.0))
            speed_target = min(surf_ff + (math.sqrt(idx) * 1.5), MAX_SPEED_KT)
            u_raw = -speed_target * math.sin(shear_angle)
            v_raw = -speed_target * math.cos(shear_angle)

        # 2. Injeksi Micro-Turbulence Atmosfer (Derau Halus 0.3 - 0.5 kt)
        if idx > 1:
            u_raw += np.random.normal(0, 0.4)
            v_raw += np.random.normal(0, 0.4)

        # 3. Smoothing Ringan (Menjaga Tren Tanpa Menghilangkan Karakter Alami)
        u_smooth = alpha * u_raw + (1 - alpha) * u_prev
        v_smooth = alpha * v_raw + (1 - alpha) * v_prev
        
        # 4. Batas Maksimum Kecepatan Strictly 19 Knot
        current_speed = math.hypot(u_smooth, v_smooth)
        if current_speed > MAX_SPEED_KT:
            scale = MAX_SPEED_KT / current_speed
            u_smooth *= scale
            v_smooth *= scale

        u_prev, v_prev = u_smooth, v_smooth

        # 5. Integrasi Maju Posisi Balon (x, y)
        if idx == 1:
            dt = 10.0
            x_curr = u_smooth * 1.68781 * dt
            y_curr = v_smooth * 1.68781 * dt
        else:
            prev_h = 100.0 if idx == 2 else (idx - 2) * 500.0
            dt = ((height_above_stn - prev_h) / rate_ft_min) * 60.0
            x_curr += u_smooth * 1.68781 * dt
            y_curr += v_smooth * 1.68781 * dt

        # 6. Hitung Ulang Azimut & Elevasi Berbasis Geometri Posisi Riil
        d_horiz = math.hypot(x_curr, y_curr)
        if d_horiz > 0:
            clean_az = math.degrees(math.atan2(x_curr, y_curr)) % 360
            clean_el = math.degrees(math.atan2(height_above_stn, d_horiz))
        else:
            clean_az, clean_el = surf_ddd, 85.0

        # Simpan Hasil
        if idx > st.session_state.last_idx or fresh:
            height_display = "Awal" if idx == 1 else f"{int(height_above_stn)} ft"
            st.session_state.generated_records.append({
                "Pembacaan Ke-": idx,
                "Tinggi Balon (ft)": height_display,
                "Level Target (BMKG)": level_target_str,
                "AZIMUT": round(clean_az, 1),
                "ELEVASI": round(clean_el, 1)
            })
            st.session_state.hodo_points.append((u_smooth, v_smooth, idx))

    st.session_state.last_idx = target_readings
    st.session_state.active_row = target_readings
