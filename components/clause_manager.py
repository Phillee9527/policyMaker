import streamlit as st
import pandas as pd

def render_clause_manager():
    st.header("条款管理")
    
    # 文件上传
    uploaded_file = st.file_uploader("导入条款库", type=['csv', 'xlsx'])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            st.session_state.clauses_df = df
        except Exception as e:
            st.error(f"文件导入错误：{str(e)}")
    
    if st.session_state.clauses_df is not None:
        # 搜索和筛选
        search_term = st.text_input("搜索条款", "")
        filtered_df = st.session_state.clauses_df
        
        if search_term:
            filtered_df = filtered_df[
                filtered_df['扩展条款标题'].str.contains(search_term, na=False) |
                filtered_df['扩展条款正文'].str.contains(search_term, na=False)
            ]
        
        # 显示条款列表
        st.dataframe(
            filtered_df[['序号', '扩展条款标题', '险种', '保险公司']],
            use_container_width=True
        )
        
        # 选择条款
        selected_indices = st.multiselect(
            "选择条款",
            filtered_df.index.tolist(),
            format_func=lambda x: filtered_df.loc[x, '扩展条款标题']
        )
        
        if selected_indices:
            st.session_state.selected_clauses = filtered_df.loc[selected_indices].to_dict('records') 