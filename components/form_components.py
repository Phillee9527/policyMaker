import streamlit as st
import pandas as pd

def render_special_terms_editor():
    """渲染特别约定编辑器"""
    st.markdown("""
    <style>
    .special-terms-editor {
        min-height: 200px !important;
    }
    .fullscreen-editor {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: 9999;
        background: white;
        padding: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if 'special_terms' not in st.session_state:
        st.session_state.special_terms = []
    
    st.subheader("特别约定")
    
    # 添加新的特别约定
    with st.expander("添加新的特别约定", expanded=True):
        new_term = st.text_area(
            "输入特别约定内容",
            height=200,
            key="new_term_input",
            help="支持基本的文本格式编辑"
        )
        
        if st.button("添加特别约定"):
            if new_term:
                st.session_state.special_terms.append({
                    'content': new_term,
                    'timestamp': pd.Timestamp.now()
                })
                st.success("特别约定已添加")
                st.rerun()
    
    # 显示已有的特别约定
    if st.session_state.special_terms:
        st.subheader("已添加的特别约定")
        for i, term in enumerate(st.session_state.special_terms):
            with st.expander(f"特别约定 {i+1} (添加时间: {term['timestamp'].strftime('%Y-%m-%d %H:%M')})", expanded=False):
                edited_content = st.text_area(
                    "编辑内容",
                    value=term['content'],
                    height=200,
                    key=f"term_{i}"
                )
                term['content'] = edited_content
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("删除", key=f"delete_{i}"):
                        st.session_state.special_terms.pop(i)
                        st.rerun()
                with col2:
                    if st.button("全屏编辑", key=f"fullscreen_{i}"):
                        st.session_state[f"fullscreen_{i}"] = not st.session_state.get(f"fullscreen_{i}", False)
                        if st.session_state[f"fullscreen_{i}"]:
                            st.markdown("""
                            <div class="fullscreen-editor">
                                <div style="padding: 20px;">
                                    <h3>全屏编辑</h3>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

def render_insurance_form():
    insurance_data = {}
    
    with st.form("insurance_form"):
        st.header("投保人信息")
        policyholder_name = st.text_input("名称")
        
        st.header("被保险人信息")
        insured_name = st.text_input("被保险人名称")
        id_type = st.selectbox("证件类型", ["身份证", "统一社会信用代码"])
        id_number = st.text_input("证件号码")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            contact_person = st.text_input("联系人")
        with col2:
            contact_phone = st.text_input("联系人电话")
        with col3:
            contact_email = st.text_input("联系人邮箱")
            
        address = st.text_input("联系地址")
        postal_code = st.text_input("联系邮编")
        
        st.header("被保险人标的地址")
        property_name = st.text_input("标的名称")
        property_address = st.text_input("标的地址")
        
        st.header("主险")
        
        # 使用选项卡来展示不同部分
        insurance_tabs = st.tabs(["物质损失", "第三者责任"])
        
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
                
                # 使用可编辑的数据表格，并设置初始行数
                material_loss_data = st.data_editor(
                    pd.DataFrame(
                        columns=["标的类别", "保险金额（元）", "费率（%）", "保费（元）"],
                        data=[["", "", "", ""]] * 3  # 初始显示3行
                    ),
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
            liability_data = st.data_editor(
                pd.DataFrame(
                    columns=["限额名称", "责任限额（元）", "保费（元）"],
                    data=[["", "", ""]] * 3  # 初始显示3行
                ),
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
                "special_terms": [term['content'] for term in st.session_state.special_terms]
            }
    
    # 在form外部渲染特别约定编辑器
    render_special_terms_editor()
    
    return insurance_data
