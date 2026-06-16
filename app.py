import streamlit as st
import pandas as pd
import datetime
import re

# 設定網頁版面為寬版
st.set_page_config(page_title="癌症用藥指引查詢系統", layout="wide")

st.markdown("""
    <style>
    div[data-baseweb="select"] > div {
        font-size: 15px;
        font-weight: bold;
    }
    .stSelectbox div[data-baseweb="select"] {
        min-height: 45px;
    }
    </style>
    """, unsafe_allow_html=True)

def load_data():
    return pd.read_excel("cancer_guidelines.xlsx").fillna("")

def get_drug_icon_html(drug_name, route, recon_note, guide_note, prep_note):
    recon_str = str(recon_note).upper()
    combined_text = f"{route} {recon_note} {guide_note} {prep_note}"
    is_oral = False
    
    if "口服" in combined_text:
        is_oral = True
    elif re.search(r'\bPO\b', combined_text, re.IGNORECASE):
        is_oral = True
        
    if is_oral:
        return '<span style="font-size:1.8em; line-height:1; vertical-align:middle; margin-right:8px;">💊</span>'
    
    vial_svg = '''
    <svg width="22" height="28" viewBox="0 0 24 30" style="vertical-align: middle; margin-right:4px;">
        <rect x="5" y="2" width="14" height="5" rx="1.5" fill="#007BFF"/>
        <rect x="6" y="7" width="12" height="3" fill="#CED4DA"/>
        <path d="M4 13 C4 10 7 10 7 10 L17 10 C17 10 20 10 20 13 L20 27 C20 29 18 30 16 30 L8 30 C6 30 4 29 4 27 Z" fill="#E9ECEF" stroke="#ADB5BD" stroke-width="1.5"/>
        <rect x="4.5" y="15" width="15" height="10" fill="#FFFFFF"/>
        <rect x="4.5" y="15" width="15" height="3" fill="#FFC107"/>
        <line x1="7" y1="20" x2="17" y2="20" stroke="#CED4DA" stroke-width="1"/>
        <line x1="7" y1="22" x2="14" y2="22" stroke="#CED4DA" stroke-width="1"/>
    </svg>
    '''
    
    if "液劑" in recon_str or "無須配製" in recon_str or recon_str.strip() == "無":
        return f'{vial_svg}<span style="margin-right:8px;"></span>'
    else:
        ampoule_tag = ""
        drop_svg = '<svg width="10" height="14" viewBox="0 0 10 14" style="margin-right:4px; fill:#fff; vertical-align:middle;"><path d="M5,0 C5,0 2,4 2,7 C2,9 3.5,11 5,11 C6.5,11 8,9 8,7 C8,4 5,0 5,0 Z"/></svg>'
        if "注射用水" in recon_str or "WATER" in recon_str:
            ampoule_tag = f'<span style="display:inline-flex; align-items:center; background:#007BFF; color:#fff; font-size:0.75em; padding:3px 8px; border-radius:12px; margin-left:4px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">{drop_svg}注射用水</span>'
        elif "N/S" in recon_str or "食鹽水" in recon_str or "NS" in recon_str:
            ampoule_tag = f'<span style="display:inline-flex; align-items:center; background:#28A745; color:#fff; font-size:0.75em; padding:3px 8px; border-radius:12px; margin-left:4px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">{drop_svg}生理食鹽水</span>'
        elif "D5W" in recon_str:
            ampoule_tag = f'<span style="display:inline-flex; align-items:center; background:#FD7E14; color:#fff; font-size:0.75em; padding:3px 8px; border-radius:12px; margin-left:4px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">{drop_svg}D5W</span>'
        
        return f'{vial_svg}{ampoule_tag}<span style="margin-right:8px;"></span>'

def render_regimen_details(final_df, display_title, df_full, prefix_key):
    st.subheader(f"📌 {display_title} 方案細節")
    
    today_date = datetime.date.today()
    st.caption(f"*(系統已自動帶入今日日期：**{today_date.strftime('%Y-%m-%d')}**，為您逆推算上次最晚施打日)*")
    
    disp_df = final_df.copy()
    deadlines = []
    
    for _, row in disp_df.iterrows():
        freq = str(row['間隔時間/頻率']).upper()
        required_days = None
        match_w = re.search(r'Q(\d+)W', freq)
        match_d = re.search(r'Q(\d+)D', freq)
        
        if match_w: required_days = int(match_w.group(1)) * 7
        elif match_d: required_days = int(match_d.group(1))
        elif 'QW' in freq and not match_w: required_days = 7
            
        if required_days is not None:
            deadline = today_date - datetime.timedelta(days=required_days)
            deadlines.append(f"🚨 ≤ {deadline.strftime('%m月%d日')}")
        elif "SINGLE DOSE" in freq or "1ST" in freq:
            deadlines.append("單一劑量 / 首次")
        elif "QD" in freq or "BID" in freq or "TID" in freq or "PO" in freq or "CONTINUOUS" in freq:
            deadlines.append("每日口服")
        else:
            deadlines.append("-")
            
    disp_df['若今日施打，上次應'] = deadlines
    display_columns = ['藥品名', '劑量 (Dose)', '輸注時間 (Rate)', '給藥日', '間隔時間/頻率', '若今日施打，上次應', '週期']
    
    def highlight_date(val):
        if isinstance(val, str) and '≤' in val:
            return 'color: #ff0000; font-weight: 900; font-size: 16px;'
        return ''
    
    if hasattr(disp_df.style, "map"):
        styled_df = disp_df[display_columns].style.map(highlight_date, subset=['若今日施打，上次應'])
    else:
        styled_df = disp_df[display_columns].style.applymap(highlight_date, subset=['若今日施打，上次應'])
        
    st.dataframe(styled_df, hide_index=True, use_container_width=True)
    st.divider()

    # --- CINV 評估 ---
    st.markdown("### 🤢 化療致吐風險 (CINV) 自動評估")
    drug_names_upper = [str(d).upper() for d in final_df['藥品名'].tolist()]
    combined_drugs = " ".join(drug_names_upper)
    
    is_hec = False
    hec_triggers = []
    is_mec = False
    mec_triggers = []

    if "CISPLATIN" in combined_drugs:
        is_hec = True
        hec_triggers.append("Cisplatin")
    if "DACARBAZINE" in combined_drugs:
        is_hec = True
        hec_triggers.append("Dacarbazine")
    if "CARMUSTINE" in combined_drugs:
        is_hec = True
        hec_triggers.append("Carmustine")
    if ("DOXORUBICIN" in combined_drugs or "EPIRUBICIN" in combined_drugs) and "CYCLOPHOSPHAMIDE" in combined_drugs:
        is_hec = True
        hec_triggers.append("Anthracycline + Cyclophosphamide (AC或EC處方)")

    if "OXALIPLATIN" in combined_drugs:
        is_mec = True
        mec_triggers.append("Oxaliplatin")
    if "CARBOPLATIN" in combined_drugs:
        is_mec = True
        mec_triggers.append("Carboplatin")
    if "IRINOTECAN" in combined_drugs:
        is_mec = True
        mec_triggers.append("Irinotecan")
    if "IFOSFAMIDE" in combined_drugs:
        is_mec = True
        mec_triggers.append("Ifosfamide")
    if "DOXORUBICIN" in combined_drugs and "CYCLOPHOSPHAMIDE" not in combined_drugs:
        is_mec = True
        mec_triggers.append("Doxorubicin")
    if "EPIRUBICIN" in combined_drugs and "CYCLOPHOSPHAMIDE" not in combined_drugs:
        is_mec = True
        mec_triggers.append("Epirubicin")

    if is_hec:
        st.error(f"🚨 **【高致吐風險 (HEC)】警示**：此處方包含 **{', '.join(hec_triggers)}**。\n\n依據指引，建議給予 **三合一或四合一強效止吐預防** (如 NK1 RA + 5-HT3 RA + Dexamethasone ± Olanzapine)。")
    elif is_mec:
        st.warning(f"⚠️ **【中度致吐風險 (MEC)】警示**：此處方包含 **{', '.join(mec_triggers)}**。\n\n依據指引，建議給予 **二合一或三合一止吐預防** (如 5-HT3 RA + Dexamethasone ± NK1 RA)。")
    else:
        st.success("✅ **【低/極低致吐風險】**：此處方無常見的高/中度致吐化療藥物，依據指引視病人症狀需要給予常規止吐藥物即可。")

    st.divider()

    # --- ANC 計算 ---
    st.markdown("### 🩸 絕對嗜中性白血球 (ANC) 施打前評估")
    c1, c2, c3 = st.columns(3)
    wbc = c1.number_input("WBC (10³/uL)", min_value=0.0, value=4.5, step=0.1, key=f"wbc_{prefix_key}")
    seg = c2.number_input("中性分節 (Seg %)", min_value=0.0, max_value=100.0, value=50.0, step=1.0, key=f"seg_{prefix_key}")
    band = c3.number_input("帶狀 (Band %)", min_value=0.0, max_value=100.0, value=0.0, step=1.0, key=f"band_{prefix_key}")
    
    anc_value = 10 * wbc * (seg + band)
    if anc_value >= 1500: st.success(f"✅ **ANC = {anc_value:.0f}** ➔ **符合安全標準！**")
    else: st.error(f"❌ **ANC = {anc_value:.0f}** ➔ **不建議施打！**")
    st.divider()

    # --- 劑量計算 ---
    st.markdown("### 🧮 處方總劑量自動試算")
    needs_bsa = any(('mg/m2' in str(d).lower() or 'mg/m²' in str(d).lower()) for d in final_df['劑量 (Dose)'])
    needs_bw = any('mg/kg' in str(d).lower() for d in final_df['劑量 (Dose)'])
    needs_auc = any('auc' in str(d).lower() for d in final_df['劑量 (Dose)'])
    
    global_bsa, global_bw, dose_adj_factor = 1.60, 60.0, 1.0
    global_auc, global_egfr = 5.0, 60.0
    
    if needs_bsa or needs_bw or needs_auc:
        col_count = sum([needs_bsa, needs_bw, needs_auc*2, True]) 
        cols = st.columns(col_count)
        col_idx = 0
        
        if needs_bsa:
            global_bsa = cols[col_idx].number_input("📏 病人 BSA (m²):", min_value=0.0, value=1.60, step=0.01, key=f"bsa_{prefix_key}")
            col_idx += 1
        if needs_bw:
            global_bw = cols[col_idx].number_input("⚖️ 病人體重 (kg):", min_value=0.0, value=60.0, step=1.0, key=f"bw_{prefix_key}")
            col_idx += 1
        if needs_auc:
            global_auc = cols[col_idx].number_input("🎯 目標 AUC:", min_value=0.0, value=5.0, step=0.5, key=f"auc_{prefix_key}")
            col_idx += 1
            global_egfr = cols[col_idx].number_input("🩸 eGFR (請填入 Clcr):", min_value=0.0, value=60.0, step=1.0, key=f"egfr_{prefix_key}")
            col_idx += 1
        
        dose_adj_factor = cols[col_idx].number_input("📉 調整比例 (如 0.8為8折):", min_value=0.1, max_value=2.0, value=1.0, step=0.05, format="%.2f", key=f"adj_{prefix_key}")

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
        if 'auc' in d_str:
            total_dose = global_auc * (global_egfr + 25) * dose_adj_factor
            if dose_adj_factor == 1.0: st.info(f"💡 **【{d_name}】** 總劑量： **{total_dose:.2f} mg**  *(Calvert公式: AUC {global_auc} × ({global_egfr:.0f} + 25))*")
            else: st.info(f"💡 **【{d_name}】** 調整後總劑量： **{total_dose:.2f} mg**  *(Calvert公式: AUC {global_auc} × ({global_egfr:.0f} + 25) × {dose_adj_factor})*")
        elif 'mg/kg' in d_str:
            m = re.search(r'([\d\.\-\~]+)\s*mg/kg', d_str)
            if m:
                total_str = calc_dose_str(m.group(1), global_bw, dose_adj_factor)
                if dose_adj_factor == 1.0: st.info(f"💡 **【{d_name}】** 總劑量： **{total_str} mg**  *(算法: {m.group(1)} mg/kg × {global_bw} kg)*")
                else: st.info(f"💡 **【{d_name}】** 調整後總劑量： **{total_str} mg**  *(算法: {m.group(1)} mg/kg × {global_bw} kg × {dose_adj_factor})*")
        elif 'mg/m2' in d_str or 'mg/m²' in d_str:
            m = re.search(r'([\d\.\-\~]+)\s*mg/m[2²]', d_str)
            if m:
                total_str = calc_dose_str(m.group(1), global_bsa, dose_adj_factor)
                if dose_adj_factor == 1.0: st.info(f"💡 **【{d_name}】** 總劑量： **{total_str} mg**  *(算法: {m.group(1)} mg/m² × {global_bsa} m²)*")
                else: st.info(f"💡 **【{d_name}】** 調整後總劑量： **{total_str} mg**  *(算法: {m.group(1)} mg/m² × {global_bsa} m² × {dose_adj_factor})*")
        else:
            st.markdown(f"💊 **【{d_name}】**: 固定劑量 ({row['劑量 (Dose)']})")
    st.divider()

    # ==========================================
    # ⚠️ 評估項目與調配注意事項
    # ==========================================
    st.markdown("### ⚠️ 評估項目與調配注意事項")
    for _, row in final_df.iterrows():
        notes = []
        if row['注意事項 / 評估項目']: notes.append(f"📌 <b>【指引條件】</b>: {row['注意事項 / 評估項目']}")
        if '再生液配製' in df_full.columns and row['再生液配製']:
            recon_text = str(row['再生液配製'])
            if "液劑" not in recon_text and "無須配製" not in recon_text and "口服" not in recon_text and recon_text.strip() != "無":
                notes.append(f"🧪 <b>【再生液配製】</b>: {recon_text}")
        if '調配與給藥注意事項' in df_full.columns and row['調配與給藥注意事項']:
            notes.append(f"🏥 <b>【調配規範】</b>:<br>{row['調配與給藥注意事項']}")
        
        if notes:
            text = "<br><br>".join(notes).replace("不可冷藏", "【NO_FRIDGE】")
            for k in ["冷藏", "避光", "不可使用過濾器", "限用NS", "限用D5W"]:
                text = text.replace(k, f"<span style='color:#ff4b4b; font-size:1.3em; font-weight:bold;'>{k}</span>")
            text = text.replace("不可鞘內注射", "<span style='color:#ff4b4b; font-size:1.4em; font-weight:bold; background-color:#ffeb3b; padding:0 4px; border-radius:4px;'>絕對不可鞘內注射</span>")
            text = text.replace("【NO_FRIDGE】", "不可冷藏").replace("\n", "<br>")
            
            drug_icon = get_drug_icon_html(row['藥品名'], row.get('藥物途徑', ''), row.get('再生液配製', ''), row.get('注意事項 / 評估項目', ''), row.get('調配與給藥注意事項', ''))
            html_card = f"""
            <div style="background-color: var(--secondary-background-color); padding: 15px; border-radius: 8px; border: 1px solid var(--primary-color); margin-bottom: 10px;">
                <div style="font-size: 1.2em; font-weight: bold; margin-bottom: 12px; color: var(--primary-color); display: flex; align-items: center;">
                    {drug_icon} 藥品：{row['藥品名']}
                </div>
                <div style="line-height: 1.6; color: var(--text-color);">{text}</div>
            </div>
            """
            st.markdown(html_card, unsafe_allow_html=True)

    # ==========================================
    # 🏥 本院專屬調配提醒 (新增最底部顯示)
    # ==========================================
    if '本院調配提醒' in final_df.columns:
        # 檢查該處方內是否有任何藥物帶有本院提醒
        has_hospital_notes = any(str(n).strip() != "" for n in final_df['本院調配提醒'])
        if has_hospital_notes:
            st.divider()
            st.markdown("### 📝 本院專屬配製注意事項")
            for _, row in final_df.iterrows():
                h_note = str(row.get('本院調配提醒', '')).strip()
                if h_note:
                    h_text = h_note.replace("不可冷藏", "【NO_FRIDGE】")
                    for k in ["冷藏", "避光", "不可使用過濾器", "不可搖晃", "勿振搖", "不可震搖", "限用NS", "限用D5W"]:
                        h_text = h_text.replace(k, f"<span style='color:#ff4b4b; font-weight:bold;'>{k}</span>")
                    h_text = h_text.replace("【NO_FRIDGE】", "不可冷藏").replace("\n", "<br>")
                    
                    card_html = f"""
                    <div style="background-color: var(--secondary-background-color); padding: 15px; border-radius: 8px; border-left: 5px solid #28a745; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <div style="font-size: 1.1em; font-weight: bold; color: var(--text-color); margin-bottom: 8px;">
                            📌 {row['藥品名']}
                        </div>
                        <div style="color: var(--text-color); line-height: 1.6; opacity: 0.9;">
                            {h_text}
                        </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)


try:
    df = load_data()
    st.title("🏥 癌症抗癌藥物治療指引查詢系統")

    tab1, tab2, tab3 = st.tabs(["💊 依已知用藥逆向查詢", "📂 依病症分類查詢", "🔍 藥物名稱快速核對"])

    with tab1:
        st.markdown("#### 🎯 依已知用藥逆向尋找處方組套")
        col1_1, col1_2 = st.columns([4, 6])
        
        with col1_1:
            known_drug = st.text_input("1. 輸入藥單上的已知藥物 (如: Trastuzumab)", placeholder="輸入部分英文即可", key="drug_t1_new")
            
        if known_drug:
            df_has_drug = df[df['藥品名'].str.contains(known_drug, case=False, na=False)]
            
            if df_has_drug.empty:
                st.warning(f"❌ 找不到包含「{known_drug}」的處方紀錄。")
            else:
                with col1_2:
                    cancer_opts = df_has_drug['癌症種類'].unique()
                    known_cancer = st.selectbox("2. 確認目標癌症種類", cancer_opts, key="cancer_t1_new")
                
                st.divider()
                st.markdown("##### 3. 選擇包含此藥物的處方組套：")
                
                df_drug_cancer = df_has_drug[df_has_drug['癌症種類'] == known_cancer].copy()
                df_drug_cancer['Line_Regimen'] = df_drug_cancer['治療線別'] + " | " + df_drug_cancer['處方方案 / 條件']
                matching_regimens = df_drug_cancer['Line_Regimen'].unique()
                
                df_cancer_all = df[df['癌症種類'] == known_cancer]
                combo_options_t1 = []
                combo_to_line_map_t1 = {}
                combo_to_reg_map_t1 = {}
                
                for lr in matching_regimens:
                    line, reg = lr.split(" | ", 1)
                    drugs = df_cancer_all[(df_cancer_all['治療線別'] == line) & (df_cancer_all['處方方案 / 條件'] == reg)]['藥品名'].tolist()
                    drugs_clean = []
                    for d in drugs:
                        d_name = re.sub(r'\s*\(.*?\)', '', str(d)).strip()
                        if d_name not in drugs_clean: drugs_clean.append(d_name)
                    drug_str = " + ".join(drugs_clean)
                    
                    line_clean = line.replace("【純口服】", "").strip()
                    reg_clean = reg.replace("【純口服】", "").strip()
                    route_icon = "💊" if "【純口服】" in line or "口服" in line else "💉"
                    
                    opt_str = f"{route_icon} {drug_str}   |   {line_clean} ({reg_clean})"
                    combo_options_t1.append(opt_str)
                    combo_to_line_map_t1[opt_str] = line
                    combo_to_reg_map_t1[opt_str] = reg
                
                combo_options_t1 = sorted(combo_options_t1, key=lambda x: x.split("   |   ")[0].replace("💊 ", "").replace("💉 ", "").strip().upper())
                
                selected_combo_t1 = st.selectbox("👇 符合條件的組套如下，請點選確認：", combo_options_t1, key="combo_t1_new")
                
                sel_line_t1 = combo_to_line_map_t1[selected_combo_t1]
                sel_reg_t1 = combo_to_reg_map_t1[selected_combo_t1]
                final_df_t1 = df_cancer_all[(df_cancer_all['治療線別'] == sel_line_t1) & (df_cancer_all['處方方案 / 條件'] == sel_reg_t1)]
                
                st.divider()
                if not final_df_t1.empty:
                    display_title_t1 = selected_combo_t1.split("   |   ")[0]
                    render_regimen_details(final_df_t1, display_title_t1, df, "t1_new")

    with tab2:
        row2_col1, row2_col2 = st.columns([1.5, 8.5])
        with row2_col1:
            route_options = ["注射", "口服"]
            if "藥物途徑" in df.columns:
                selected_route = st.selectbox("📌 0. 選擇藥物途徑", route_options, index=0, key="route_t2_new")
                df_route = df[df['藥物途徑'] == selected_route]
            else:
                df_route = df
        with row2_col2:
            if not df_route.empty:
                cancer_type = st.selectbox("1. 選擇癌症種類 (Cancer Type)", df_route['癌症種類'].unique(), key="cancer_t2_new")
                df_cancer = df_route[df_route['癌症種類'] == cancer_type]
            else:
                st.selectbox("1. 選擇癌症種類", ["-"], disabled=True, key="cancer_t2_new")

        if not df_route.empty and not df_cancer.empty:
            df_cancer = df_cancer.copy()
            df_cancer['Line_Regimen'] = df_cancer['治療線別'] + " | " + df_cancer['處方方案 / 條件']
            
            regimen_list = sorted(df_cancer['處方方案 / 條件'].unique().tolist(), key=lambda x: str(x).upper())
            selected_regimen = st.selectbox("2. 選擇處方方案 (Regimen)", regimen_list, key="reg_t2_new")
            
            df_regimen = df_cancer[df_cancer['處方方案 / 條件'] == selected_regimen]
            lines = df_regimen['治療線別'].unique().tolist()
            combo_options = []
            combo_to_line_map = {}
            
            for line in lines:
                drugs = df_regimen[df_regimen['治療線別'] == line]['藥品名'].tolist()
                drugs_clean = []
                for d in drugs:
                    d_name = re.sub(r'\s*\(.*?\)', '', str(d)).strip()
                    if d_name not in drugs_clean: drugs_clean.append(d_name)
                drug_str = " + ".join(drugs_clean)
                
                line_clean = line.replace("【純口服】", "").strip()
                route_icon = "💊" if "【純口服】" in line or "口服" in selected_route else "💉"
                opt_str = f"{route_icon} {drug_str}   |   {line_clean}"
                
                combo_options.append(opt_str)
                combo_to_line_map[opt_str] = line
                
            combo_options = sorted(combo_options, key=lambda x: x.split("   |   ")[0].replace("💊 ", "").replace("💉 ", "").strip().upper())
            selected_combo = st.selectbox("3. 確認藥物組合與治療線別", combo_options, key="combo_t2_new")
            selected_line = combo_to_line_map[selected_combo]
            
            final_df = df_regimen[df_regimen['治療線別'] == selected_line]
            st.divider()
            render_regimen_details(final_df, selected_regimen, df, "t2_new")
        else:
            st.selectbox("2. 選擇處方方案 (Regimen)", ["-"], disabled=True, key="reg_t2_new")
            st.selectbox("3. 確認藥物組合與治療線別", ["-"], disabled=True, key="combo_t2_new")

    with tab3:
        st.markdown("### 快速核對藥物是否在指引內")
        search = st.text_input("輸入藥品英文名稱：", key="search_t3")
        if search:
            res = df[df['藥品名'].str.contains(search, case=False, na=False)]
            if not res.empty:
                st.success(f"✅ 找到 {len(res)} 筆紀錄")
                st.dataframe(res[['癌症種類', '治療線別', '處方方案 / 條件', '藥品名', '劑量 (Dose)']], hide_index=True, use_container_width=True)
            else: st.error("找不到該藥物。")

except Exception as e:
    st.error(f"錯誤：{e}")
