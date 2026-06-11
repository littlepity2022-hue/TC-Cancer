import streamlit as st
import pandas as pd
import datetime
import re

# 設定網頁版面為寬版
st.set_page_config(page_title="癌症用藥指引查詢系統", layout="wide")

# --- 自定義 CSS 讓下拉選單文字更易讀 ---
st.markdown("""
    <style>
    /* 讓下拉選單的選項文字不要被強行切斷，並微調字體 */
    div[data-baseweb="select"] > div {
        font-size: 15px;
        font-weight: bold;
    }
    /* 針對選單內的容器進行微調 */
    .stSelectbox div[data-baseweb="select"] {
        min-height: 45px;
    }
    </style>
    """, unsafe_allow_html=True)

def load_data():
    return pd.read_excel("cancer_guidelines.xlsx").fillna("")

try:
    df = load_data()
    
    st.title("🏥 癌症抗癌藥物治療指引查詢系統")

    tab1, tab2 = st.tabs(["📂 依病症分類查詢", "🔍 藥物名稱快速核對"])

    with tab1:
        # ==========================================
        # 第一列：0.途徑(1.5) 與 1.癌症(8.5)
        # ==========================================
        row1_col1, row1_col2 = st.columns([1.5, 8.5])
        
        with row1_col1:
            route_options = ["注射", "口服"]
            if "藥物途徑" in df.columns:
                selected_route = st.selectbox("📌 0. 選擇藥物途徑", route_options, index=0)
                df_route = df[df['藥物途徑'] == selected_route]
            else:
                df_route = df
                st.warning("⚠️ 尚無途徑資料")

        with row1_col2:
            if not df_route.empty:
                cancer_options = df_route['癌症種類'].unique()
                cancer_type = st.selectbox("1. 選擇癌症種類 (Cancer Type)", cancer_options)
                df_cancer = df_route[df_route['癌症種類'] == cancer_type]
            else:
                st.selectbox("1. 選擇癌症種類", ["(請先選擇正確途徑)"], disabled=True)

        # ==========================================
        # 獨立橫列：2. 處方方案 & 3. 藥物組合+線別
        # ==========================================
        if not df_route.empty and not df_cancer.empty:
            df_cancer = df_cancer.copy()
            regimen_list = sorted(df_cancer['處方方案 / 條件'].unique().tolist())
            selected_regimen = st.selectbox("2. 選擇處方方案 (Regimen)", regimen_list)
            
            df_regimen = df_cancer[df_cancer['處方方案 / 條件'] == selected_regimen]
            lines = df_regimen['治療線別'].unique().tolist()
            combo_options = []
            combo_to_line_map = {}
            
            for line in lines:
                drugs = df_regimen[df_regimen['治療線別'] == line]['藥品名'].tolist()
                drugs_clean = []
                for d in drugs:
                    d_name = re.sub(r'\s*\(.*?\)', '', str(d)).strip()
                    if d_name not in drugs_clean:
                        drugs_clean.append(d_name)
                drug_str = " + ".join(drugs_clean)
                
                line_clean = line.replace("【純口服】", "").strip()
                route_icon = "💊" if "【純口服】" in line or "口服" in selected_route else "💉"
                
                opt_str = f"{route_icon} {drug_str}   |   {line_clean}"
                combo_options.append(opt_str)
                combo_to_line_map[opt_str] = line
                
            selected_combo = st.selectbox("3. 確認藥物組合與治療線別", combo_options)
            selected_line = combo_to_line_map[selected_combo]
            
            final_df = df_regimen[df_regimen['治療線別'] == selected_line]
        else:
            st.selectbox("2. 選擇處方方案 (Regimen)", ["-"], disabled=True)
            st.selectbox("3. 確認藥物組合與治療線別", ["-"], disabled=True)

        st.divider()

        # 檢查是否有最終篩選結果，才顯示下方內容
        if 'final_df' in locals() and not final_df.empty:
            st.subheader(f"📌 {selected_regimen} 方案細節")
            
            # ==========================================
            # 📅 日期設定區 (放在表格正上方)
            # ==========================================
            st.markdown("##### 📅 施打日期設定 (將自動帶入下方表格)")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                # 打開網頁預設帶入今天日期
                target_date = st.date_input("🗓️ 本次預計施打日期 (預設今日)：", datetime.date.today())
            with col_d2:
                # 預設為三週前，方便微調
                default_last_date = target_date - datetime.timedelta(days=21)
                last_dose_date = st.date_input("⏮️ 上次實際施打日期：", default_last_date)
            
            # ==========================================
            # 🚀 動態生成表格欄位 (把安全評估塞進 DataFrame)
            # ==========================================
            disp_df = final_df.copy()
            safe_dates = []
            assessments = []
            
            for _, row in disp_df.iterrows():
                freq = str(row['間隔時間/頻率']).upper()
                required_days = None
                
                # 自動判斷是 Q_W(週) 還是 Q_D(天) 還是 QW(每週)
                match_w = re.search(r'Q(\d+)W', freq)
                match_d = re.search(r'Q(\d+)D', freq)
                
                if match_w:
                    required_days = int(match_w.group(1)) * 7
                elif match_d:
                    required_days = int(match_d.group(1))
                elif 'QW' in freq and not match_w:
                    required_days = 7
                    
                # 根據天數計算結果並加入 List
                if required_days is not None:
                    safe_date = last_dose_date + datetime.timedelta(days=required_days)
                    safe_dates.append(safe_date.strftime("%Y-%m-%d"))
                    
                    if (target_date - last_dose_date).days >= required_days:
                        assessments.append("✅ 安全")
                    else:
                        assessments.append("❌ 提早不宜")
                elif "SINGLE DOSE" in freq or "1ST" in freq:
                    safe_dates.append("-")
                    assessments.append("ℹ️ 單一劑量")
                elif "QD" in freq or "BID" in freq or "TID" in freq or "PO" in freq:
                    safe_dates.append("每日")
                    assessments.append("✅ 安全")
                else:
                    safe_dates.append("-")
                    assessments.append("⚠️ 依醫囑")
                    
            # 將計算結果塞回表格中
            disp_df['最快可施打日'] = safe_dates
            disp_df['安全評估'] = assessments
            
            # 重新排列要顯示的欄位 (把新欄位緊跟在間隔時間後面)
            display_columns = ['藥品名', '劑量 (Dose)', '輸注時間 (Rate)', '給藥日', '間隔時間/頻率', '最快可施打日', '安全評估', '週期']
            st.dataframe(disp_df[display_columns], hide_index=True, use_container_width=True)

            st.divider()

            # ==========================================
            # 🩸 ANC 絕對嗜中性白血球評估
            # ==========================================
            st.markdown("### 🩸 絕對嗜中性白血球 (ANC) 施打前評估")
            c1, c2, c3 = st.columns(3)
            wbc = c1.number_input("WBC (10³/uL)", min_value=0.0, value=4.5, step=0.1)
            seg = c2.number_input("中性分節 (Seg %)", min_value=0.0, max_value=100.0, value=50.0, step=1.0)
            band = c3.number_input("帶狀 (Band %)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
            
            anc_value = 10 * wbc * (seg + band)
            if anc_value >= 1500:
                st.success(f"✅ **ANC = {anc_value:.0f}** ➔ **符合安全標準！**")
            else:
                st.error(f"❌ **ANC = {anc_value:.0f}** ➔ **不建議施打！**")

            st.divider()

            # ==========================================
            # 🧮 處方總劑量自動試算 (支援打折/劑量調整)
            # ==========================================
            st.markdown("### 🧮 處方總劑量自動試算")
            needs_bsa = any(('mg/m2' in str(d).lower() or 'mg/m²' in str(d).lower()) for d in final_df['劑量 (Dose)'])
            needs_bw = any('mg/kg' in str(d).lower() for d in final_df['劑量 (Dose)'])
            
            global_bsa, global_bw, dose_adj_percent = 1.60, 60.0, 100
            
            if needs_bsa or needs_bw:
                col_count = sum([needs_bsa, needs_bw, True]) 
                cols = st.columns(col_count)
                col_idx = 0
                
                if needs_bsa:
                    global_bsa = cols[col_idx].number_input("📏 病人 BSA (m²):", min_value=0.0, value=1.60, step=0.01)
                    col_idx += 1
                if needs_bw:
                    global_bw = cols[col_idx].number_input("⚖️ 病人體重 (kg):", min_value=0.0, value=60.0, step=1.0)
                    col_idx += 1
                
                dose_adj_percent = cols[col_idx].number_input("📉 劑量調整比例 (%):", min_value=10, max_value=200, value=100, step=5, help="若需打8折請輸入80")

            def calc_dose_str(val_str, multiplier, adj_factor=1.0):
                try:
                    if '-' in val_str:
                        p = val_str.split('-')
                        return f"{float(p[0])*multiplier*adj_factor:.2f} ~ {float(p[1])*multiplier*adj_factor:.2f}"
                    elif '~' in val_str:
                        p = val_str.split('~')
                        return f"{float(p[0])*multiplier*adj_factor:.2f} ~ {float(p[1])*multiplier*adj_factor:.2f}"
                    return f"{float(val_str)*multiplier*adj_factor:.2f}"
                except: return None

            for _, row in final_df.iterrows():
                d_name, d_str = row['藥品名'], str(row['劑量 (Dose)']).lower()
                adj_factor = dose_adj_percent / 100.0
                
                if 'mg/kg' in d_str:
                    m = re.search(r'([\d\.\-\~]+)\s*mg/kg', d_str)
                    if m:
                        total_str = calc_dose_str(m.group(1), global_bw, adj_factor)
                        if dose_adj_percent == 100:
                            st.info(f"💡 **【{d_name}】** 總劑量： **{total_str} mg**  *(算法: {m.group(1)} mg/kg × {global_bw} kg)*")
                        else:
                            st.info(f"💡 **【{d_name}】** 打折後總劑量： **{total_str} mg**  *(算法: {m.group(1)} mg/kg × {global_bw} kg × {dose_adj_percent}%)*")
                elif 'mg/m2' in d_str or 'mg/m²' in d_str:
                    m = re.search(r'([\d\.\-\~]+)\s*mg/m[2²]', d_str)
                    if m:
                        total_str = calc_dose_str(m.group(1), global_bsa, adj_factor)
                        if dose_adj_percent == 100:
                            st.info(f"💡 **【{d_name}】** 總劑量： **{total_str} mg**  *(算法: {m.group(1)} mg/m² × {global_bsa} m²)*")
                        else:
                            st.info(f"💡 **【{d_name}】** 打折後總劑量： **{total_str} mg**  *(算法: {m.group(1)} mg/m² × {global_bsa} m² × {dose_adj_percent}%)*")
                else:
                    st.markdown(f"💊 **【{d_name}】**: 固定劑量 ({row['劑量 (Dose)']})")

            st.divider()

            # ==========================================
            # ⚠️ 注意事項 (高亮紅字)
            # ==========================================
            st.markdown("### ⚠️ 評估項目與調配注意事項")
            for _, row in final_df.iterrows():
                notes = []
                if row['注意事項 / 評估項目']: notes.append(f"📌 <b>【指引條件】</b>: {row['注意事項 / 評估項目']}")
                if '調配與給藥注意事項' in df.columns and row['調配與給藥注意事項']:
                    notes.append(f"🏥 <b>【調配規範】</b>:<br>{row['調配與給藥注意事項']}")
                
                if notes:
                    text = "<br><br>".join(notes).replace("不可冷藏", "【NO_FRIDGE】")
                    for k in ["冷藏", "避光", "不可使用過濾器", "限用NS", "限用D5W"]:
                        text = text.replace(k, f"<span style='color:red; font-size:1.3em; font-weight:bold;'>{k}</span>")
                    text = text.replace("不可鞘內注射", "<span style='color:red; font-size:1.4em; font-weight:bold; background:yellow;'>絕對不可鞘內注射</span>")
                    text = text.replace("【NO_FRIDGE】", "不可冷藏")
                    
                    st.markdown(f"""<div style="background:#eef7ff; padding:15px; border-radius:8px; border:1px solid #bce0fd; margin-bottom:10px;">
                        <div style="font-weight:bold; color:#004085;">📍 藥品：{row['藥品名']}</div>{text}</div>""", unsafe_allow_html=True)

    with tab2:
        st.markdown("### 快速核對藥物")
        search = st.text_input("輸入藥品英文名稱：")
        if search:
            res = df[df['藥品名'].str.contains(search, case=False, na=False)]
            if not res.empty:
                st.dataframe(res[['癌症種類', '治療線別', '處方方案 / 條件', '藥品名', '劑量 (Dose)']], hide_index=True, use_container_width=True)
            else: st.error("找不到該藥物。")

except Exception as e:
    st.error(f"錯誤：{e}")
