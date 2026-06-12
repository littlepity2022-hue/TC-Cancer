import streamlit as st
import pandas as pd
import datetime
import re

# 設定網頁版面為寬版
st.set_page_config(page_title="癌症用藥指引查詢系統", layout="wide")

# --- 自定義 CSS 讓下拉選單文字更易讀 ---
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

# ==========================================
# 🎨 動態產生藥品專屬 SVG 圖示與標籤
# ==========================================
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

# ==========================================
# 🤢 NCCN 止吐藥物智慧分析模組
# ==========================================
def get_antiemetic_recommendation_html(drugs_list):
    combined_drugs = " ".join([str(d).upper() for d in drugs_list])
    
    is_high = False
    is_mod = False
    
    # 1. 檢查 AC Regimen (Anthracycline + Cyclophosphamide) = 高度致吐
    has_anthra = any(a in combined_drugs for a in ["DOXORUBICIN", "EPIRUBICIN", "IDARUBICIN", "DAUNORUBICIN"])
    has_cyclo = "CYCLOPHOSPHAMIDE" in combined_drugs
    if has_anthra and has_cyclo:
        is_high = True

    # 2. 檢查其他高度致吐藥物
    high_keywords = ["CISPLATIN", "DACARBAZINE", "STREPTOZOCIN", "MECHLORETHAMINE", "CARMUSTINE"]
    if any(h in combined_drugs for h in high_keywords):
        is_high = True

    # 3. 檢查中度致吐藥物
    mod_keywords = ["CARBOPLATIN", "OXALIPLATIN", "IRINOTECAN", "CYCLOPHOSPHAMIDE", "DOXORUBICIN", "EPIRUBICIN", "IFOSFAMIDE", "CYTARABINE", "MELPHALAN", "ARSENIC", "DACTINOMYCIN", "MITOXANTRONE", "IDARUBICIN", "DAUNORUBICIN"]
    if not is_high and any(m in combined_drugs for m in mod_keywords):
        is_mod = True

    if is_high:
        return """
        <div style="padding: 15px 20px; border-radius: 8px; border-left: 8px solid #dc3545; background-color: rgba(220, 53, 69, 0.1); margin-bottom: 20px;">
            <h4 style="color: #dc3545; margin-top: 0; margin-bottom: 12px;">🚨 高致吐風險 (High Emetic Risk >90%) - 建議預防用藥</h4>
            <div style="display: flex; flex-direction: column; gap: 10px; color: var(--text-color);">
                <div>
                    <span style="font-weight: bold; background-color: #dc3545; color: white; padding: 2px 8px; border-radius: 4px;">第 1 日 (化療注射前)</span>
                    <ul style="margin-top: 5px; margin-bottom: 0;">
                        <li><b>5-HT3 antagonist:</b> Ondansetron (Zofran®) 16-24 mg PO <b>或</b> 8-16 mg IV <br><i>(或 Palonosetron (Aloxi®) 0.25 mg IV / Tropisetron (Navoban®) 5 mg IV)</i></li>
                        <li><b>NK-1 antagonist:</b> Aprepitant 125 mg PO <b>或</b> Fosaprepitant 150 mg IV</li>
                        <li><b>Steroid:</b> Dexamethasone 12 mg IV</li>
                    </ul>
                </div>
                <div style="border-top: 1px dashed rgba(128,128,128,0.3); padding-top: 10px;">
                    <span style="font-weight: bold; background-color: #6c757d; color: white; padding: 2px 8px; border-radius: 4px;">第 2, 3, 4 日</span>
                    <ul style="margin-top: 5px; margin-bottom: 0;">
                        <li><b>5-HT3 antagonist:</b> <span style="color:#888;">不需再給予此類藥品</span></li>
                        <li><b>NK-1 antagonist:</b> Aprepitant 80 mg PO 第 2 及 3 日 <i>(若 Day 1 使用 Fosaprepitant 則不需再給予)</i></li>
                        <li><b>Steroid:</b> Dexamethasone 8 mg IV 第 2 及 3 日</li>
                    </ul>
                </div>
            </div>
        </div>
        """
    elif is_mod:
        return """
        <div style="padding: 15px 20px; border-radius: 8px; border-left: 8px solid #fd7e14; background-color: rgba(253, 126, 20, 0.1); margin-bottom: 20px;">
            <h4 style="color: #fd7e14; margin-top: 0; margin-bottom: 12px;">⚠️ 中致吐風險 (Moderate Emetic Risk 30%-90%) - 建議預防用藥</h4>
            <div style="display: flex; flex-direction: column; gap: 10px; color: var(--text-color);">
                <div>
                    <span style="font-weight: bold; background-color: #fd7e14; color: white; padding: 2px 8px; border-radius: 4px;">第 1 日 (化療注射前)</span>
                    <ul style="margin-top: 5px; margin-bottom: 0;">
                        <li><b>5-HT3 antagonist:</b> Ondansetron (Zofran®) 16-24 mg PO <b>或</b> 8-16 mg IV <br><i>(或 Palonosetron (Aloxi®) 0.25 mg IV / Tropisetron (Navoban®) 5 mg IV <b>或</b> 5 mg PO)</i></li>
                        <li><b>Steroid:</b> Dexamethasone 12 mg IV</li>
                        <li><b style="color:#ff4b4b;">NK-1 antagonist (病人自費):</b> Aprepitant 125 mg PO <b>或</b> Fosaprepitant 150 mg IV</li>
                    </ul>
                </div>
                <div style="border-top: 1px dashed rgba(128,128,128,0.3); padding-top: 10px;">
                    <span style="font-weight: bold; background-color: #6c757d; color: white; padding: 2px 8px; border-radius: 4px;">第 2, 3, 4 日</span>
                    <ul style="margin-top: 5px; margin-bottom: 0;">
                        <li><b>5-HT3 antagonist (單獨使用):</b> Ondansetron (Zofran®) 8-16 mg IV <b>或</b> 16 mg/day PO <br><i>(或 Tropisetron (Navoban®) 5 mg/day PO)</i></li>
                        <li><b>或 Steroid (單獨使用):</b> Dexamethasone 12 mg IV</li>
                        <li><b style="color:#ff4b4b;">NK-1 antagonist (病人自費):</b> Aprepitant 80 mg PO 第 2 及 3 日 <i>(若 Day 1 使用 Fosaprepitant 則不需再給予)</i></li>
                    </ul>
                </div>
            </div>
        </div>
        """
    else:
        return """
        <div style="padding: 15px 20px; border-radius: 8px; border-left: 8px solid #28a745; background-color: rgba(40, 167, 69, 0.1); margin-bottom: 20px;">
            <h4 style="color: #28a745; margin-top: 0; margin-bottom: 12px;">✅ 低/微量致吐風險 (Low Emetic Risk) - 建議預防用藥</h4>
            <ul style="color: var(--text-color); margin-bottom: 0; font-size: 1.05em;">
                <li>Dexamethasone 12 mg IV QD</li>
                <li><b>或</b> Metoclopramide 10-40 mg IV Q6H PRN</li>
                <li><b>或</b> Prochlorperazine 10 mg IV Q6H PRN (max 40 mg/day)</li>
            </ul>
        </div>
        """


# ==========================================
# 🧩 共用模組：渲染處方細節 (包含表格、計算、注意事項)
# ==========================================
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
    global_egfr = 60.0
    
    default_auc = 5.0
    if needs_auc:
        for d_val in final_df['劑量 (Dose)']:
            d_str = str(d_val).lower()
            if 'auc' in d_str:
                m = re.search(r'auc\s*[=:-]?\s*(\d+(?:\.\d+)?)', d_str)
                if m:
                    default_auc = float(m.group(1))
                    break
    
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
            global_auc = cols[col_idx].number_input("🎯 目標 AUC (**:red[依照實際方案修改]**):", min_value=0.0, value=default_auc, step=0.5, key=f"auc_{prefix_key}")
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

    # --- 新增：NCCN 止吐藥物建議 ---
    st.markdown("### 🤢 止吐預防建議 (依據 NCCN 指引)")
    st.markdown(get_antiemetic_recommendation_html(final_df['藥品名'].tolist()), unsafe_allow_html=True)
    st.divider()

    # --- 注意事項 ---
    st.markdown("### ⚠️ 評估項目與調配注意事項")
    for _, row in final_df.iterrows():
        notes = []
        if row['注意事項 / 評估項目']: notes.append(f"📌 <b>【指引條件】</b>: {row['注意事項 / 評估項目']}")
        if '再生液配製' in df_full.columns and row['再生液配製']:
            recon_text = str(row['再生液配製'])
            if "液劑" not in recon_text and "無須配製" not in recon_text and "口服" not in recon_text and recon_text.strip() != "無":
                recon_text = recon_text.replace("N/S", "N/S食鹽水")
                recon_text = re.sub(r'(\d+(?:\.\d+)?\s*(?:ml|mL|cc|CC))', 
                                r"<span style='color:#ff4b4b; font-size:1.3em; font-weight:bold;'>\1</span>", 
                                recon_text)
                for sol in ["專用水", "N/S食鹽水", "注射用水"]:
                    recon_text = recon_text.replace(sol, f"<span style='color:#ff4b4b; font-size:1.3em; font-weight:bold;'>{sol}</span>")
                notes.append(f"🧪 <b>【再生液配製】</b>: {recon_text}")
                
        if '調配與給藥注意事項' in df_full.columns and row['調配與給藥注意事項']:
            notes.append(f"🏥 <b>【調配規範】</b>:<br>{row['調配與給藥注意事項']}")
        
        if notes:
            text = "<br><br>".join(notes).replace("不可冷藏", "【NO_FRIDGE】")
            for k in ["冷藏", "避光", "不可使用過濾器", "限用D5W"]:
                text = text.replace(k, f"<span style='color:#ff4b4b; font-size:1.3em; font-weight:bold;'>{k}</span>")
            text = text.replace("不可鞘內注射", "<span style='color:#ff4b4b; font-size:1.4em; font-weight:bold; background-color:#ffeb3b; padding:0 4px; border-radius:4px;'>絕對不可鞘內注射</span>")
            text = text.replace("【NO_FRIDGE】", "不可冷藏").replace("\n", "<br>")
            
            drug_icon = get_drug_icon_html(row['藥品名'], row.get('藥物途徑', ''), row.get('再生液配製', ''), row.get('注意事項 / 評估項目', ''), row.get('調配與給藥注意事項', ''))
            html_card = f"""
            <div style="
                background-color: rgba(128, 128, 128, 0.1); 
                padding: 20px; 
                border-radius: 10px; 
                border: 1px solid rgba(128, 128, 128, 0.4); 
                border-left: 8px solid #ff4b4b; 
                margin-bottom: 25px; 
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            ">
                <div style="
                    font-size: 1.3em; 
                    font-weight: bold; 
                    margin-bottom: 15px; 
                    border-bottom: 2px solid rgba(128, 128, 128, 0.2); 
                    padding-bottom: 10px;
                    display: flex; align-items: center;
                ">
                    {drug_icon} <span style="margin-left:5px;">藥品：{row['藥品名']}</span>
                </div>
                <div style="line-height: 1.8; font-size: 1.05em; color: var(--text-color);">
                    {text}
                </div>
            </div>
            """
            st.markdown(html_card, unsafe_allow_html=True)


try:
    df = load_data()
    st.title("🏥 癌症抗癌藥物治療指引查詢系統")

    tab1, tab2, tab3 = st.tabs(["💊 依已知用藥逆向查詢", "📂 依病症分類查詢", "🔍 藥物名稱快速核對"])

    # ==========================================
    # 分頁 1：【依已知用藥逆向查詢】(置於首頁)
    # ==========================================
    with tab1:
        st.markdown("#### 🎯 依已知用藥逆向尋找處方組套")
        col1_1, col1_2 = st.columns([4, 6])
        
        with col1_1:
            known_drug = st.text_input("1. 輸入藥單上的已知藥物 (如: Trastuzumab)", placeholder="輸入部分英文即可", key="drug_t1_new")
            
        if known_drug:
            # 找出所有包含此藥物的紀錄
            df_has_drug = df[df['藥品名'].str.contains(known_drug, case=False, na=False)]
            
            if df_has_drug.empty:
                st.warning(f"❌ 找不到包含「{known_drug}」的處方紀錄。")
            else:
                with col1_2:
                    cancer_opts = df_has_drug['癌症種類'].unique()
                    known_cancer = st.selectbox("2. 確認目標癌症種類", cancer_opts, key="cancer_t1_new")
                
                st.divider()
                st.markdown("##### 3. 選擇包含此藥物的處方組套：")
                
                # 篩選出該癌症下，包含此藥物的方案 (Line + Regimen)
                df_drug_cancer = df_has_drug[df_has_drug['癌症種類'] == known_cancer].copy()
                df_drug_cancer['Line_Regimen'] = df_drug_cancer['治療線別'] + " | " + df_drug_cancer['處方方案 / 條件']
                matching_regimens = df_drug_cancer['Line_Regimen'].unique()
                
                # 去原 DataFrame 抓取完整的方案資料 (才能顯示該方案內「所有的」藥物)
                df_cancer_all = df[df['癌症種類'] == known_cancer]
                combo_options_t1 = []
                combo_to_line_map_t1 = {}
                combo_to_reg_map_t1 = {}
                
                for lr in matching_regimens:
                    line, reg = lr.split(" | ", 1)
                    # 抓出這個方案的所有藥物
                    drugs = df_cancer_all[(df_cancer_all['治療線別'] == line) & (df_cancer_all['處方方案 / 條件'] == reg)]['藥品名'].tolist()
                    drugs_clean = []
                    for d in drugs:
                        d_name = re.sub(r'\s*\(.*?\)', '', str(d)).strip()
                        if d_name not in drugs_clean: drugs_clean.append(d_name)
                    drug_str = " + ".join(drugs_clean)
                    
                    line_clean = line.replace("【純口服】", "").strip()
                    reg_clean = reg.replace("【純口服】", "").strip()
                    route_icon = "💊" if "【純口服】" in line or "口服" in line else "💉"
                    
                    # 顯示格式：💉 藥A + 藥B | 線別 (處方名稱)
                    opt_str = f"{route_icon} {drug_str}   |   {line_clean} ({reg_clean})"
                    combo_options_t1.append(opt_str)
                    combo_to_line_map_t1[opt_str] = line
                    combo_to_reg_map_t1[opt_str] = reg
                
                combo_options_t1 = sorted(combo_options_t1, key=lambda x: x.split("   |   ")[0].replace("💊 ", "").replace("💉 ", "").strip().upper())
                
                selected_combo_t1 = st.selectbox("👇 符合條件的組套如下，請點選確認：", combo_options_t1, key="combo_t1_new")
                
                # 反向過濾出最終資料
                sel_line_t1 = combo_to_line_map_t1[selected_combo_t1]
                sel_reg_t1 = combo_to_reg_map_t1[selected_combo_t1]
                final_df_t1 = df_cancer_all[(df_cancer_all['治療線別'] == sel_line_t1) & (df_cancer_all['處方方案 / 條件'] == sel_reg_t1)]
                
                st.divider()
                # 呼叫共用模組渲染
                if not final_df_t1.empty:
                    display_title_t1 = selected_combo_t1.split("   |   ")[0]
                    render_regimen_details(final_df_t1, display_title_t1, df, "t1_new")

    # ==========================================
    # 分頁 2：原本的【依病症分類查詢】
    # ==========================================
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

    # ==========================================
    # 分頁 3：快速核對
    # ==========================================
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
