import streamlit as st
import pandas as pd

def render_insurance_form():
    """渲染投保信息表单"""
    st.markdown("""
    <style>
    .special-terms-editor {
        min-height: 200px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 初始化session state
    if 'insurance_data' not in st.session_state:
        st.session_state.insurance_data = {}
    
    # 从session state获取已保存的数据
    insurance_data = st.session_state.insurance_data or {}
    
    # 其他信息选项卡管理（移到表单外部）
    st.header("其他信息")
    
    # 初始化其他信息的选项卡配置
    if 'other_info_tabs' not in st.session_state:
        st.session_state.other_info_tabs = [{"name": "新选项卡1", "id": "tab1"}]
    
    # 添加新选项卡的按钮
    if st.button("添加新选项卡", key="add_tab"):
        new_tab_id = f"tab{len(st.session_state.other_info_tabs) + 1}"
        st.session_state.other_info_tabs.append({
            "name": f"新选项卡{len(st.session_state.other_info_tabs) + 1}",
            "id": new_tab_id
        })
        st.rerun()
    
    # 渲染选项卡编辑区域
    tab_names = []
    tabs_to_remove = []
    
    for i, tab in enumerate(st.session_state.other_info_tabs):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            new_name = st.text_input(
                "选项卡名称",
                value=tab["name"],
                key=f"tab_name_{tab['id']}"
            )
            tab["name"] = new_name
            tab_names.append(new_name)
        
        with col2:
            if st.button("删除", key=f"delete_{tab['id']}"):
                tabs_to_remove.append(tab)
    
    # 处理要删除的选项卡
    for tab in tabs_to_remove:
        st.session_state.other_info_tabs.remove(tab)
        if 'insurance_data' in st.session_state and 'other_info_data' in st.session_state.insurance_data:
            st.session_state.insurance_data['other_info_data'].pop(tab['id'], None)
        st.rerun()
    
    # 表单部分开始
    with st.form("insurance_form"):
        st.header("投保人信息")
        policyholder_name = st.text_area(
            "名称",
            value=insurance_data.get('policyholder', ''),
            height=100
        )
        
        st.header("被保险人信息")
        insured_name = st.text_area(
            "被保险人名称",
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
        
        st.header("被保险人标的地址")
        property_name = st.text_input(
            "标的名称",
            value=insurance_data.get('property', {}).get('name', '')
        )
        property_address = st.text_input(
            "标的地址",
            value=insurance_data.get('property', {}).get('address', '')
        )
        
        st.header("主险")
        
        # 使用选项卡来展示不同部分
        insurance_tabs = st.tabs(["物质损失", "第三者责任", "免赔额"])
        
        with insurance_tabs[0]:
            st.subheader("第一部分 物质损失")
            
            # 使用container和custom CSS来控制表格宽度
            with st.container():
                st.markdown("""
                <style>
                    .stDataFrame {
                        width: 75% !important;
                    }
                </style>
                """, unsafe_allow_html=True)
                
                # 获取已保存的物质损失数据
                saved_material_loss = insurance_data.get('material_loss', [{"标的类别": "", "保险金额（元）": "", "费率（%）": "", "保费（元）": ""}] * 3)
                
                # 使用可编辑的数据表格
                material_loss_data = st.data_editor(
                    pd.DataFrame(saved_material_loss),
                    num_rows="dynamic",
                    use_container_width=True,
                    column_config={
                        "标的类别": st.column_config.TextColumn(
                            "标的类别",
                            width="medium",
                            required=True
                        ),
                        "保险金额（元）": st.column_config.NumberColumn(
                            "保险金额（元）",
                            width="medium",
                            format="%.2f",
                            required=True
                        ),
                        "费率（%）": st.column_config.NumberColumn(
                            "费率（%）",
                            width="medium",
                            format="%.4f",
                            required=True
                        ),
                        "保费（元）": st.column_config.NumberColumn(
                            "保费（元）",
                            width="medium",
                            format="%.2f",
                            required=True
                        )
                    }
                )
        
        with insurance_tabs[1]:
            st.subheader("第二部分 第三者责任")
            
            # 获取已保存的第三者责任数据
            saved_liability = insurance_data.get('liability', [{"限额名称": "", "责任限额（元）": "", "保费（元）": ""}] * 3)
            
            liability_data = st.data_editor(
                pd.DataFrame(saved_liability),
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "限额名称": st.column_config.TextColumn(
                        "限额名称",
                        width="medium",
                        required=True
                    ),
                    "责任限额（元）": st.column_config.NumberColumn(
                        "责任限额（元）",
                        width="medium",
                        format="%.2f",
                        required=True
                    ),
                    "保费（元）": st.column_config.NumberColumn(
                        "保费（元）",
                        width="medium",
                        format="%.2f",
                        required=True
                    )
                }
            )
        
        with insurance_tabs[2]:
            st.subheader("免赔额")
            
            # 获取已保存的免赔额数据
            saved_deductibles = insurance_data.get('deductibles', [{"免赔项目": "", "免赔额 / 免赔约定": ""}])
            
            deductibles_data = st.data_editor(
                pd.DataFrame(saved_deductibles),
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "免赔项目": st.column_config.TextColumn(
                        "免赔项目",
                        width="small",
                        required=True
                    ),
                    "免赔额 / 免赔约定": st.column_config.TextColumn(
                        "免赔额 / 免赔约定",
                        width="large",
                        required=True,
                        max_chars=1000
                    )
                },
                hide_index=True
            )
        
        # 其他信息表格编辑部分
        if st.session_state.other_info_tabs:
            other_info_tabs = st.tabs(tab_names)
            
            # 渲染每个选项卡的内容
            for i, (tab, tab_content) in enumerate(zip(st.session_state.other_info_tabs, other_info_tabs)):
                with tab_content:
                    # 获取已保存的数据
                    saved_data = st.session_state.insurance_data.get('other_info_data', {}).get(
                        tab['id'],
                        [{"项目": "", "内容说明": ""}]
                    )
                    
                    # 创建数据编辑器
                    tab_data = st.data_editor(
                        pd.DataFrame(saved_data),
                        num_rows="dynamic",
                        use_container_width=True,
                        column_config={
                            "项目": st.column_config.TextColumn(
                                "项目",
                                width="small",
                                required=True
                            ),
                            "内容说明": st.column_config.TextColumn(
                                "内容说明",
                                width="large",
                                required=True,
                                max_chars=1000
                            )
                        },
                        hide_index=True,
                        key=f"table_{tab['id']}"
                    )
                    
                    # 保存表格数据到session state
                    if 'other_info_data' not in st.session_state.insurance_data:
                        st.session_state.insurance_data['other_info_data'] = {}
                    st.session_state.insurance_data['other_info_data'][tab['id']] = tab_data.to_dict('records')
        
        submit_button = st.form_submit_button("保存信息")
        
        if submit_button:
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
                "other_info_data": st.session_state.insurance_data.get('other_info_data', {})
            }
            st.session_state.insurance_data = insurance_data
            st.success("信息已保存")
    
    return st.session_state.insurance_data
