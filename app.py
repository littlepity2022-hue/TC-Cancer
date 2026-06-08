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
        font-size: 14px;
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
        # 第一列：0.途徑(2) 與 1.癌症(8)
        # ==========================================
        row1_col1, row1_col2 = st.columns([2, 8])
        
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
        # 第二列：2.治療線別(1) 與 3.處方方案(1)
        # ==========================================
        row2_col1, row2_col2 = st.columns([5, 5])  # 比例 1:1

        with row2_col1:
            if not df_route.empty and not df_cancer.empty:
                line_options = df_cancer['治療線別'].unique()
                treatment_line = st.selectbox("2. 選擇治療線別", line_options)
                df_line = df_cancer[df_cancer['治療線別'] == treatment_line]
            else:
                st.selectbox("2. 選擇治療線別", ["-"], disabled=True)

        with row2_col2:
            if not df_route.empty and not df_line.empty:
                regimen_options = df_line['處方方案 / 條件'].unique()
                regimen = st.selectbox("3. 選擇處方方案 / 條件", regimen_options)
                final_df = df_line[df_line['處方方案 / 條件'] == regimen]
            else:
                st.selectbox("3. 選擇處方方案 / 條件", ["-"], disabled=True)

        st.divider()

        # 檢查是否有最終篩選結果，才顯示下方內容
        if 'final_df' in locals() and not final_df.empty:
            st.subheader(f"📌 {regimen}")
            display_columns = ['藥品名', '劑量 (Dose)', '輸注時間 (Rate)', '給藥日', '間隔時間/頻率', '週期']
            st.dataframe(final_df[display_columns], hide_index=True, use_container_width=True)

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
            # 🧮 處方總劑量自動試算
            # ==========================================
            st.markdown("### 🧮 處方總劑量自動試算")
            needs_bsa = any(('mg/m2' in str(d).lower() or 'mg/m²' in str(d).lower()) for d in final_df['劑量 (Dose)'])
            needs_bw = any('mg/kg' in str(d).lower() for d in final_df['劑量 (Dose)'])
            
            global_bsa, global_bw = 1.60, 60.0
            if needs_bsa or needs_bw:
                ci1, ci2 = st.columns(2)
                if needs_bsa: global_bsa = ci1.number_input("📏 病人 BSA (m²):", value=1.60, step=0.01)
                if needs_bw: global_bw = (ci2 if needs_bsa else ci1).number_input("⚖️ 病人體重 (kg):", value=60.0, step=1.0)

            def calc_dose_str(val_str, multiplier):
                try:
                    if '-' in val_str:
                        p = val_str.split('-')
                        return f"{float(p[0])*multiplier:.2f} ~ {float(p[1])*multiplier:.2f}"
                    elif '~' in val_str:
                        p = val_str.split('~')
                        return f"{float(p[0])*multiplier:.2f} ~ {float(p[1])*multiplier:.2f}"
                    return f"{float(val_str)*multiplier:.2f}"
                except: return None

            for _, row in final_df.iterrows():
                d_name, d_str = row['藥品名'], str(row['劑量 (Dose)']).lower()
                if 'mg/kg' in d_str:
                    m = re.search(r'([\d\.\-\~]+)\s*mg/kg', d_str)
                    if m: st.info(f"💡 **【{d_name}】** 總劑量： **{calc_dose_str(m.group(1), global_bw)} mg**")
                elif 'mg/m2' in d_str or 'mg/m²' in d_str:
                    m = re.search(r'([\d\.\-\~]+)\s*mg/m[2²]', d_str)
                    if m: st.info(f"💡 **【{d_name}】** 總劑量： **{calc_dose_str(m.group(1), global_bsa)} mg**")
                else:
                    st.markdown(f"💊 **【{d_name}】**: 固定劑量 ({row['劑量 (Dose)']})")

            st.divider()

            # ==========================================
            # 📅 施打間隔安全核對器 (優化版：截止日邏輯)
            # ==========================================
            st.markdown("### 📅 施打間隔安全核對器")
            target_date = st.date_input("🗓️ 本次預計施打日期：", datetime.date.today())

            for _, row in final_df.iterrows():
                freq = str(row['間隔時間/頻率']).upper()
                match = re.search(r'Q(\d+)W', freq)
                if match:
                    deadline = target_date - datetime.timedelta(days=int(match.group(1)) * 7)
                    st.warning(f"⏳ **{row['藥品名']}** ({freq}): 上次施打應早於或等於 **{deadline}**")
                elif "SINGLE DOSE" in freq:
                    st.info(f"ℹ️ **{row['藥品名']}**: 單一劑量。")
                else:
                    st.info(f"ℹ️ **{row['藥品名']}**: 頻率為 {freq}。")

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
