import streamlit as st
import pandas as pd

def render_insurance_form():
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
        st.subheader("第一部分 物质损失")
        
        # 使用可编辑的数据表格
        material_loss_data = st.data_editor(
            pd.DataFrame(
                columns=["标的类别", "保险金额（元）", "费率（%）", "保费（元）"]
            ),
            num_rows="dynamic"
        )
        
        submit_button = st.form_submit_button("保存信息")
        
        if submit_button:
            return {
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
                "material_loss": material_loss_data.to_dict('records')
            }
    return None 