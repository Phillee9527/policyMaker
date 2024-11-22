import streamlit as st
from components.form_components import render_insurance_form
from components.clause_manager import render_clause_manager
from components.document_generator import generate_document
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
if 'insurance_data' not in st.session_state:
    st.session_state.insurance_data = None
if 'special_terms' not in st.session_state:
    st.session_state.special_terms = []

def main():
    st.title("保险方案生成平台")
    
    # 创建主要标签页
    tab1, tab2, tab3 = st.tabs(["📝 保单信息", "📚 条款管理", "📄 生成方案"])
    
    with tab1:
        insurance_data = render_insurance_form()
        if insurance_data:
            st.session_state.insurance_data = insurance_data
            st.success("保单信息已保存")
    
    with tab2:
        st.markdown("""
        <style>
        .main .block-container {
            max-width: 1200px;
            padding-top: 2rem;
            padding-right: 2rem;
            padding-left: 2rem;
            padding-bottom: 3rem;
        }
        </style>
        """, unsafe_allow_html=True)
        render_clause_manager()
    
    with tab3:
        st.header("生成保险方案")
        
        if st.session_state.insurance_data and st.session_state.selected_clauses:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # 选择导出格式
                export_format = st.selectbox(
                    "选择导出格式",
                    ["Markdown", "DOCX"],
                    help="选择生成的文档格式"
                )
            
            with col2:
                if st.button("生成保险方案", help="点击生成完整的保险方案文档"):
                    try:
                        with st.spinner("正在生成文档..."):
                            if export_format == "Markdown":
                                doc = generate_document(
                                    st.session_state.insurance_data,
                                    st.session_state.selected_clauses,
                                    'markdown'
                                )
                                st.download_button(
                                    "下载Markdown文档",
                                    doc,
                                    file_name="insurance_proposal.md",
                                    mime="text/markdown"
                                )
                                # 预览生成的文档
                                with st.expander("预览生成的文档", expanded=True):
                                    st.markdown(doc)
                            
                            else:  # DOCX
                                doc_buffer = generate_document(
                                    st.session_state.insurance_data,
                                    st.session_state.selected_clauses,
                                    'docx'
                                )
                                st.download_button(
                                    "下载Word文档",
                                    doc_buffer,
                                    file_name="insurance_proposal.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                )
                        
                        st.success("文档生成成功！")
                    
                    except Exception as e:
                        st.error(f"生成文档时出错：{str(e)}")
        else:
            if not st.session_state.insurance_data:
                st.warning("请先填写保单信息")
            if not st.session_state.selected_clauses:
                st.warning("请先选择条款")

    # 添加帮助信息在侧边栏
    with st.sidebar:
        with st.expander("使用说明", expanded=False):
            st.markdown("""
            ### 使用步骤
            1. 在"保单信息"页面填写基本信息
            2. 在"条款管理"页面导入和选择条款
            3. 在"生成方案"页面选择格式并生成文档
            
            ### 注意事项
            - 所有必填字段都需要填写
            - 可以随时保存和修改信息
            - 支持导出为Markdown和Word格式
            
            ### 快捷键
            - Ctrl + S: 保存当前表单
            - Ctrl + F: 搜索条款
            - Esc: 关闭弹窗
            """)

if __name__ == "__main__":
    main()
