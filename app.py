import streamlit as st
from components.form_components import render_insurance_form
from components.clause_manager import render_clause_manager
from components.document_generator import generate_markdown
import pandas as pd

st.set_page_config(
    page_title="保险方案生成平台",
    page_icon="📋",
    layout="wide"
)

# 初始化session state
if 'clauses_df' not in st.session_state:
    st.session_state.clauses_df = None
if 'selected_clauses' not in st.session_state:
    st.session_state.selected_clauses = []

def main():
    st.title("保险方案生成平台")
    
    # 创建两个主要标签页
    tab1, tab2 = st.tabs(["📝 保单信息", "📚 条款管理"])
    
    with tab1:
        insurance_data = render_insurance_form()
        if st.button("生成保险方案"):
            if insurance_data and st.session_state.selected_clauses:
                markdown_doc = generate_markdown(insurance_data, st.session_state.selected_clauses)
                st.download_button(
                    "下载保险方案",
                    markdown_doc,
                    file_name="insurance_proposal.md",
                    mime="text/markdown"
                )
    
    with tab2:
        render_clause_manager()

if __name__ == "__main__":
    main() 