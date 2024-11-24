import streamlit as st
import pandas as pd

def render_insurance_form():
    """渲染投保信息表单"""
    # 添加自定义CSS样式
    st.markdown("""
    <style>
    /* 原有的样式保持不变 */
    .special-terms-editor {
        min-height: 200px !important;
    }
    
    /* 页面最顶层标题样式 (项目名称等) */
    .main h1:first-of-type {
        color: #1e3d59 !important;  /* 藏蓝色 */
        font-size: 1.5rem !important;  /* 较大字号 */
        font-weight: 600 !important;
        margin-top: 0.5em !important;
        margin-bottom: 1em !important;
    }
    
    /* 主要section标题样式 (投保人信息、被保险人信息等) */
    .main > .block-container h1 {
        color: #1e3d59 !important;  /* 藏蓝色 */
        font-size: 1.3rem !important;  /* 比正文大2号 */
        font-weight: 500 !important;
        margin-top: 1.2em !important;
        margin-bottom: 0.8em !important;
        border-bottom: 1px solid #e6e6e6;
        padding-bottom: 0.3em;
    }
    
    /* 子标题样式保持不变 */
    .stMarkdown h2 {
        color: #1e3d59 !important;
        font-size: 1.1rem !important;
        font-weight: 500 !important;
        margin-top: 1.2em !important;
        margin-bottom: 0.6em !important;
    }
    
    /* 确保表单中的标题也使用相同样式 */
    .stForm h1 {
        color: #1e3d59 !important;
        font-size: 1.3rem !important;
        font-weight: 500 !important;
        border-bottom: 1px solid #e6e6e6;
        padding-bottom: 0.3em;
    }
    
    /* 调整标签文字大小 */
    .stTextInput label, .stTextArea label, .stSelectbox label {
        font-size: 1rem !important;
    }
    
    /* 其他信息区域样式 */
    .other-info-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e9ecef;
        margin: 1rem 0;
    }
    
    /* 其他信息标题样式 */
    .other-info-title {
        color: #1e3d59 !important;
        font-size: 1.3rem !important;
        font-weight: 500 !important;
        margin-bottom: 1rem !important;
        padding-bottom: 0.3em;
        border-bottom: 1px solid #e6e6e6;
    }
    
    /* 其他信息内容样式 */
    .other-info-content {
        padding: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 使用markdown来渲染标题，以应用自定义样式
    def section_header(text):
        st.markdown(f"# {text}")
    
    def subsection_header(text):
        st.markdown(f"## {text}")
    
    # 初始化 session_state
    if 'insurance_data' not in st.session_state:
        st.session_state.insurance_data = {}
    
    # 确保 insurance_data 不为 None
    if st.session_state.insurance_data is None:
        st.session_state.insurance_data = {}
    
    # 从session state获取已保存的数据
    insurance_data = st.session_state.insurance_data
    
    # 确保 other_info_data 存在
    if 'other_info_data' not in insurance_data:
        insurance_data['other_info_data'] = {}
    
    # 表单部分
    with st.form("insurance_form"):
        st.markdown("# 📋 投保人信息")
        st.info("🎯 请填写投保人的基本信息，这些信息将出现在保险方案的开头部分")
        policyholder_name = st.text_area(
            "✍️ 名称",
            value=insurance_data.get('policyholder', ''),
            height=100
        )
        
        st.markdown("# 👥 被保险人信息")
        st.info("📝 被保险人是保险合同中受保护的主体，请认真填写相关信息")
        insured_name = st.text_area(
            "✍️ 被保险人名称",
            value=insurance_data.get('insured', {}).get('name', ''),
            height=100
        )
        id_type = st.selectbox(
            "证件类型",
            ["身份证", "统一社会信用代码"],
            index=0 if insurance_data.get('insured', {}).get('id_type', '') == "身份证" else 1
        )
        id_number = st.text_input(
            "证件号码",
            value=insurance_data.get('insured', {}).get('id_number', '')
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            contact_person = st.text_input(
                "联系人",
                value=insurance_data.get('insured', {}).get('contact', {}).get('name', '')
            )
        with col2:
            contact_phone = st.text_input(
                "联系人电话",
                value=insurance_data.get('insured', {}).get('contact', {}).get('phone', '')
            )
        with col3:
            contact_email = st.text_input(
                "联系人邮箱",
                value=insurance_data.get('insured', {}).get('contact', {}).get('email', '')
            )
            
        address = st.text_input(
            "联系地址",
            value=insurance_data.get('insured', {}).get('contact', {}).get('address', '')
        )
        postal_code = st.text_input(
            "联系邮编",
            value=insurance_data.get('insured', {}).get('contact', {}).get('postal_code', '')
        )
        
        st.markdown("# 🏢 被保险人标的地址")
        st.info("📍 这里填写被保险标的物所在的具体位置信息")
        
        property_name = st.text_input(
            "标的名称",
            value=insurance_data.get('property', {}).get('name', '')
        )
        property_address = st.text_input(
            "标的地址",
            value=insurance_data.get('property', {}).get('address', '')
        )
        
        st.markdown("# 💰 主险")
        st.info("📊 主险是保险方案的核心部分，请仔细填写各项数据")
        
        # 使用选项卡来展示不同部分
        insurance_tabs = st.tabs(["💼 物质损失", "⚖️ 第三者责任", "🔍 免赔额"])
        
        with insurance_tabs[0]:
            subsection_header("第一部分 物质损失")
            
            # 使用container和custom CSS来控制表格宽度
            with st.container():
                st.markdown("""
                <style>
                    .stDataFrame {
                        width: 75% !important;
                    }
                </style>
                """, unsafe_allow_html=True)
                
                # 获取已保存的物质损失数据，确保至少有一行空数据
                saved_material_loss = insurance_data.get('material_loss', [{"标的类别": "", "保险金额（元）": "", "费率（%）": "", "保费（元）": ""}])
                
                # 确保所有行都有完整的列
                for row in saved_material_loss:
                    if "标的类别" not in row:
                        row["标的类别"] = ""
                    if "保险金额（元）" not in row:
                        row["保险金额（元）"] = ""
                    if "费率（%）" not in row:
                        row["费率（%）"] = ""
                    if "保费（元）" not in row:
                        row["保费（元）"] = ""
                
                # 使用可编辑的数据表格
                material_loss_data = st.data_editor(
                    pd.DataFrame(saved_material_loss),
                    num_rows="dynamic",
                    use_container_width=True,
                    column_config={
                        "标的类别": st.column_config.TextColumn(
                            "标的类别",
                            width="medium",
                            required=False  # 改为不必填
                        ),
                        "保险金额（元）": st.column_config.NumberColumn(
                            "保险金额（元）",
                            width="medium",
                            format="%.2f",
                            required=False  # 改为不必填
                        ),
                        "费率（%）": st.column_config.NumberColumn(
                            "费率（%）",
                            width="medium",
                            format="%.4f",
                            required=False  # 改为不必填
                        ),
                        "保费（元）": st.column_config.NumberColumn(
                            "保费（元）",
                            width="medium",
                            format="%.2f",
                            required=False  # 改为不必填
                        )
                    }
                )
        
        with insurance_tabs[1]:
            subsection_header("第二部分 第三者责任")
            
            # 获取已保存的第三者责任数据，确保至少有一行空数据
            saved_liability = insurance_data.get('liability', [{"限额名称": "", "责任限额（元）": "", "保费（元）": ""}])
            
            # 确保所有行都有完整的列
            for row in saved_liability:
                if "限额名称" not in row:
                    row["限额名称"] = ""
                if "责任限额（元）" not in row:
                    row["责任限额（元）"] = ""
                if "保费（元）" not in row:
                    row["保费（元）"] = ""
            
            liability_data = st.data_editor(
                pd.DataFrame(saved_liability),
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "限额名称": st.column_config.TextColumn(
                        "限额名称",
                        width="medium",
                        required=False  # 改为不必填
                    ),
                    "责任限额（元）": st.column_config.NumberColumn(
                        "责任限额（元）",
                        width="medium",
                        format="%.2f",
                        required=False  # 改为不必填
                    ),
                    "保费（元）": st.column_config.NumberColumn(
                        "保费（元）",
                        width="medium",
                        format="%.2f",
                        required=False  # 改为不必填
                    )
                }
            )
        
        with insurance_tabs[2]:
            subsection_header("免赔额")
            
            # 获取已保存的免赔额数据，确保至少有一行空数据
            saved_deductibles = insurance_data.get('deductibles', [{"免赔项目": "", "免赔额 / 免赔约定": ""}])
            
            # 确保所有行都有完整的列
            for row in saved_deductibles:
                if "免赔项目" not in row:
                    row["免赔项目"] = ""
                if "免赔额 / 免赔约定" not in row:
                    row["免赔额 / 免赔约定"] = ""
            
            deductibles_data = st.data_editor(
                pd.DataFrame(saved_deductibles),
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "免赔项目": st.column_config.TextColumn(
                        "免赔项目",
                        width="small",
                        required=False  # 改为不必填
                    ),
                    "免赔额 / 免赔约定": st.column_config.TextColumn(
                        "免赔额 / 免赔约定",
                        width="large",
                        required=False,  # 改为不必填
                        max_chars=1000
                    )
                },
                hide_index=True
            )
        
        if st.form_submit_button("💾 保存信息"):
            insurance_data = {
                "policyholder": policyholder_name,
                "insured": {
                    "name": insured_name,
                    "id_type": id_type,
                    "id_number": id_number,
                    "contact": {
                        "name": contact_person,
                        "phone": contact_phone,
                        "email": contact_email,
                        "address": address,
                        "postal_code": postal_code
                    }
                },
                "property": {
                    "name": property_name,
                    "address": property_address
                },
                "material_loss": material_loss_data.to_dict('records'),
                "liability": liability_data.to_dict('records'),
                "deductibles": deductibles_data.to_dict('records'),
                "other_info_tabs": st.session_state.other_info_tabs,
                "other_info_data": insurance_data.get('other_info_data', {})
            }
            st.session_state.insurance_data = insurance_data
            st.success("🎉 信息已成功保存！")
    
    # 添加分隔线
    st.markdown("---")
    
    # 其他信息部分
    st.markdown('<div class="other-info-container">', unsafe_allow_html=True)
    st.markdown('<p class="other-info-title">📑 其他信息</p>', unsafe_allow_html=True)
    st.info("🔧 在这里可以添加和管理自定义的信息分类，让您的保险方案更加完整")
    
    # 初始化其他信息的选项卡配置
    if 'other_info_tabs' not in st.session_state:
        st.session_state.other_info_tabs = [{"name": "新选项卡1", "id": "tab1", "order": 0}]
    
    # 使用data_editor管理选项卡
    tabs_df = pd.DataFrame(st.session_state.other_info_tabs)
    edited_tabs = st.data_editor(
        tabs_df,
        column_config={
            "name": st.column_config.TextColumn(
                "选项卡名称",
                width="medium",
                required=True
            ),
            "id": st.column_config.TextColumn(
                "ID",
                width="small",
                disabled=True
            ),
            "order": st.column_config.NumberColumn(
                "排序",
                width="small",
                disabled=True,
                default=0
            )
        },
        hide_index=True,
        num_rows="dynamic",
        key="tabs_editor"
    )
    
    # 更新选项卡配置
    st.session_state.other_info_tabs = edited_tabs.to_dict('records')
    
    # 创建动态选项卡
    if st.session_state.other_info_tabs:
        tab_names = [tab["name"] for tab in st.session_state.other_info_tabs]
        other_info_tabs = st.tabs(tab_names)
        
        # 初始化或获取其他信息数据
        if 'insurance_data' not in st.session_state:
            st.session_state.insurance_data = {}
        if 'other_info_data' not in st.session_state.insurance_data:
            st.session_state.insurance_data['other_info_data'] = {}
        
        # 渲染每个选项卡的内容
        for i, (tab, tab_content) in enumerate(zip(st.session_state.other_info_tabs, other_info_tabs)):
            with tab_content:
                # 获取当前选项卡的数据，确保至少有一行空数据
                current_tab_data = st.session_state.insurance_data.get('other_info_data', {}).get(
                    tab['id'],
                    [{"项目": "", "内容说明": ""}]
                )
                
                # 确保所有行都有完整的列
                for row in current_tab_data:
                    if "项目" not in row:
                        row["项目"] = ""
                    if "内容说明" not in row:
                        row["内容说明"] = ""
                
                # 创建数据编辑器，使用唯一的key
                tab_data = st.data_editor(
                    pd.DataFrame(current_tab_data),
                    num_rows="dynamic",
                    use_container_width=True,
                    column_config={
                        "项目": st.column_config.TextColumn(
                            "项目",
                            width="small",
                            required=False  # 改为不必填
                        ),
                        "内容说明": st.column_config.TextColumn(
                            "内容说明",
                            width="large",
                            required=False,  # 改为不必填
                            max_chars=1000
                        )
                    },
                    hide_index=True,
                    key=f"other_info_table_{tab['id']}_{i}"
                )
                
                # 添加保存按钮
                if st.button("💾 保存此选项卡内容", key=f"save_tab_{tab['id']}"):
                    # 保存前确保数据结构完整
                    if 'insurance_data' not in st.session_state:
                        st.session_state.insurance_data = {}
                    if 'other_info_data' not in st.session_state.insurance_data:
                        st.session_state.insurance_data['other_info_data'] = {}
                    
                    # 处理数据，确保空值也被保存
                    saved_data = []
                    for _, row in tab_data.iterrows():
                        saved_data.append({
                            "项目": row["项目"] if pd.notna(row["项目"]) else "",
                            "内容说明": row["内容说明"] if pd.notna(row["内容说明"]) else ""
                        })
                    
                    # 只更新当前选项卡的数据，保留其他选项卡的数据
                    st.session_state.insurance_data['other_info_data'][tab['id']] = saved_data
                    st.success("✨ 内容已保存")
    
    # 添加全部保存按钮
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💾 保存所有其他信息", key="save_all_other_info"):
            # 确保数据被正确保存到 session_state
            if 'insurance_data' not in st.session_state:
                st.session_state.insurance_data = {}
            
            # 保存选项卡配置
            st.session_state.insurance_data['other_info_tabs'] = st.session_state.other_info_tabs
            
            # 确保 other_info_data 存在
            if 'other_info_data' not in st.session_state.insurance_data:
                st.session_state.insurance_data['other_info_data'] = {}
            
            st.success("🎉 所有其他信息已保存！")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    return st.session_state.insurance_data
