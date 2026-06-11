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
                # 取得該途徑下的癌症清單
                cancer_options = df_route['癌症種類'].unique()
                cancer_type = st.selectbox("1. 選擇癌症種類 (Cancer Type)", cancer_options)
                df_cancer = df_route[df_route['癌症種類'] == cancer_type]
            else:
                st.selectbox("1. 選擇癌症種類", ["(請先選擇正確途徑)"], disabled=True)

        # ==========================================
        # 獨立橫列：2. 處方方案 (滿版) & 3. 藥物組合 (滿版)
        # ==========================================
        if not df_route.empty and not df_cancer.empty:
            
            df_cancer = df_cancer.copy()
            df_cancer['Line_Regimen'] = df_cancer['治療線別'] + " | " + df_cancer['處方方案 / 條件']
            
            # 抓出該癌症所有的「處方方案」並強制 A-Z 排序
            regimen_list = sorted(df_cancer['處方方案 / 條件'].unique().tolist(), key=lambda x: str(x).upper())
            
            # 🌟 讓處方方案自己獨佔一橫列 (滿版寬度)
            selected_regimen = st.selectbox("2. 選擇處方方案 (Regimen)", regimen_list)
            
            # 過濾出該處方方案的資料
            df_regimen = df_cancer[df_cancer['處方方案 / 條件'] == selected_regimen]
            
            # 抓出該處方方案對應的所有「治療線別」
            lines = df_regimen['治療線別'].unique().tolist()
            combo_options = []
            combo_to_line_map = {}
            
            for line in lines:
                # 抓出該線別下的所有藥物
                drugs = df_regimen[df_regimen['治療線別'] == line]['藥品名'].tolist()
                drugs_clean = []
                for d in drugs:
                    # 移除括號內的文字以保持清爽 (例如商品名)
                    d_name = re.sub(r'\s*\(.*?\)', '', str(d)).strip()
                    if d_name not in drugs_clean:
                        drugs_clean.append(d_name)
                drug_str = " + ".join(drugs_clean)
                
                # 整理標籤與圖示
                line_clean = line.replace("【純口服】", "").strip()
                route_icon = "💊" if "【純口服】" in line or "口服" in selected_route else "💉"
                
                # 組合出：💉 藥A + 藥B | 治療線別
                opt_str = f"{route_icon} {drug_str}   |   {line_clean}"
                combo_options.append(opt_str)
                combo_to_line_map[opt_str] = line
                
            # 將選項依照「藥物名稱字母 A-Z」進行排序
            combo_options = sorted(combo_options, key=lambda x: x.split("   |   ")[0].replace("💊 ", "").replace("💉 ", "").strip().upper())
            
            # 🌟 讓藥物組合與治療線別也自己獨佔下一橫列 (滿版寬度)
            selected_combo = st.selectbox("3. 確認藥物組合與治療線別", combo_options)
            selected_line = combo_to_line_map[selected_combo]
            
            # 最終過濾出要顯示的 DataFrame
            final_df = df_regimen[df_regimen['治療線別'] == selected_line]
            display_drugs = selected_combo.split("   |   ")[0]
            
        else:
            st.selectbox("2. 選擇處方方案 (Regimen)", ["-"], disabled=True)
            st.selectbox("3. 確認藥物組合與治療線別", ["-"], disabled=True)

        st.divider()

        # 檢查是否有最終篩選結果，才顯示下方內容
        if 'final_df' in locals() and not final_df.empty:
            st.subheader(f"📌 {selected_regimen} 方案細節")
            
            # ==========================================
            # 📅 日期設定與表格生成區
            # ==========================================
            today_date = datetime.date.today()
            st.caption(f"*(系統已自動帶入今日日期：**{today_date.strftime('%Y-%m-%d')}**，為您逆推算上次最晚施打日)*")
            
            disp_df = final_df.copy()
            deadlines = []
            
            for _, row in disp_df.iterrows():
                freq = str(row['間隔時間/頻率']).upper()
                required_days = None
                
                match_w = re.search(r'Q(\d+)W', freq)
                match_d = re.search(r'Q(\d+)D', freq)
                
                if match_w:
                    required_days = int(match_w.group(1)) * 7
                elif match_d:
                    required_days = int(match_d.group(1))
                elif 'QW' in freq and not match_w:
                    required_days = 7
                    
                # 萃取月與日，格式化為：≤ MM月DD日
                if required_days is not None:
                    deadline = today_date - datetime.timedelta(days=required_days)
                    deadlines.append(f"≤ {deadline.strftime('%m月%d日')}")
                elif "SINGLE DOSE" in freq or "1ST" in freq:
                    deadlines.append("單一劑量 / 首次")
                elif "QD" in freq or "BID" in freq or "TID" in freq or "PO" in freq or "CONTINUOUS" in freq:
                    deadlines.append("每日口服")
                else:
                    deadlines.append("-")
                    
            disp_df['若今日施打，上次應'] = deadlines
            
            display_columns = ['藥品名', '劑量 (Dose)', '輸注時間 (Rate)', '給藥日', '間隔時間/頻率', '若今日施打，上次應', '週期']
            
            # 使用 Pandas Styler 讓「≤ MM月DD日」變成紅色放大粗體
            def highlight_date(val):
                if isinstance(val, str) and '≤' in val:
                    return 'color: #ff4b4b; font-weight: bold; font-size: 1.25em;'
                return ''
            
            # 支援新舊版 Pandas 的寫法
            if hasattr(disp_df.style, "map"):
                styled_df = disp_df[display_columns].style.map(highlight_date, subset=['若今日施打，上次應'])
            else:
                styled_df = disp_df[display_columns].style.applymap(highlight_date, subset=['若今日施打，上次應'])
                
            st.dataframe(styled_df, hide_index=True, use_container_width=True)

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
            # 🧮 處方總劑量自動試算 (小數點打折版)
            # ==========================================
            st.markdown("### 🧮 處方總劑量自動試算")
            needs_bsa = any(('mg/m2' in str(d).lower() or 'mg/m²' in str(d).lower()) for d in final_df['劑量 (Dose)'])
            needs_bw = any('mg/kg' in str(d).lower() for d in final_df['劑量 (Dose)'])
            
            global_bsa, global_bw, dose_adj_factor = 1.60, 60.0, 1.0
            
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
                
                # 🌟 劑量調整比例改為臨床常用的小數點格式 (如 0.8)
                dose_adj_factor = cols[col_idx].number_input("📉 劑量調整比例 (如 0.8 為 8折):", min_value=0.1, max_value=2.0, value=1.0, step=0.05, format="%.2f")

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
                
                if 'mg/kg' in d_str:
                    m = re.search(r'([\d\.\-\~]+)\s*mg/kg', d_str)
                    if m:
                        total_str = calc_dose_str(m.group(1), global_bw, dose_adj_factor)
                        if dose_adj_factor == 1.0:
                            st.info(f"💡 **【{d_name}】** 總劑量： **{total_str} mg**  *(算法: {m.group(1)} mg/kg × {global_bw} kg)*")
                        else:
                            st.info(f"💡 **【{d_name}】** 調整後總劑量： **{total_str} mg**  *(算法: {m.group(1)} mg/kg × {global_bw} kg × {dose_adj_factor})*")
                elif 'mg/m2' in d_str or 'mg/m²' in d_str:
                    m = re.search(r'([\d\.\-\~]+)\s*mg/m[2²]', d_str)
                    if m:
                        total_str = calc_dose_str(m.group(1), global_bsa, dose_adj_factor)
                        if dose_adj_factor == 1.0:
                            st.info(f"💡 **【{d_name}】** 總劑量： **{total_str} mg**  *(算法: {m.group(1)} mg/m² × {global_bsa} m²)*")
                        else:
                            st.info(f"💡 **【{d_name}】** 調整後總劑量： **{total_str} mg**  *(算法: {m.group(1)} mg/m² × {global_bsa} m² × {dose_adj_factor})*")
                else:
                    st.markdown(f"💊 **【{d_name}】**: 固定劑量 ({row['劑量 (Dose)']})")

            st.divider()

            # ==========================================
            # ⚠️ 注意事項 (深色模式相容 + 高亮紅字)
            # ==========================================
            st.markdown("### ⚠️ 評估項目與調配注意事項")
            for _, row in final_df.iterrows():
                notes = []
                if row['注意事項 / 評估項目']: notes.append(f"📌 <b>【指引條件】</b>: {row['注意事項 / 評估項目']}")
                if '調配與給藥注意事項' in df.columns and row['調配與給藥注意事項']:
                    notes.append(f"🏥 <b>【調配規範】</b>:<br>{row['調配與給藥注意事項']}")
                
                if notes:
                    text = "<br><br>".join(notes).replace("不可冷藏", "【NO_FRIDGE】")
                    
                    # 紅字放大防呆標籤 (包含避光)
                    for k in ["冷藏", "避光", "不可使用過濾器", "限用NS", "限用D5W"]:
                        text = text.replace(k, f"<span style='color:#ff4b4b; font-size:1.3em; font-weight:bold;'>{k}</span>")
                    
                    # 致命警告黃底紅字
                    text = text.replace("不可鞘內注射", "<span style='color:#ff4b4b; font-size:1.4em; font-weight:bold; background-color:#ffeb3b; padding:0 4px; border-radius:4px;'>絕對不可鞘內注射</span>")
                    
                    text = text.replace("【NO_FRIDGE】", "不可冷藏")
                    text = text.replace("\n", "<br>")
                    
                    # 完美相容深色/淺色模式的 HTML Card
                    html_card = f"""
                    <div style="background-color: var(--secondary-background-color); padding: 15px; border-radius: 8px; border: 1px solid var(--primary-color); margin-bottom: 10px;">
                        <div style="font-size: 1.1em; font-weight: bold; margin-bottom: 10px; color: var(--primary-color);">📍 藥品：{row['藥品名']}</div>
                        <div style="line-height: 1.6; color: var(--text-color);">{text}</div>
                    </div>
                    """
                    st.markdown(html_card, unsafe_allow_html=True)

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
