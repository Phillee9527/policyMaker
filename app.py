import streamlit as st
from components.form_components import render_insurance_form
from components.clause_manager import render_clause_manager
from components.document_generator import generate_document
from components.project_manager import render_project_manager

def init_session_state():
    """初始化session state"""
    if 'insurance_data' not in st.session_state:
        st.session_state.insurance_data = None
    if 'selected_clauses' not in st.session_state:
        st.session_state.selected_clauses = []
    if 'db_path' not in st.session_state:
        st.session_state.db_path = 'clauses.db'

def main():
    st.set_page_config(
        page_title="保险方案生成平台",
        page_icon="📋",
        layout="wide"
    )
    
    # 初始化session state
    init_session_state()
    
    # 渲染项目管理器
    render_project_manager()
    
    # 如果没有选择项目，显示提示信息
    if 'project_name' not in st.session_state:
        st.warning("请先选择或创建一个项目")
        return
    
    # 显示当前项目名称
    st.title(f"项目：{st.session_state.project_name}")
    
    # 使用选项卡展示主要功能
    tab1, tab2, tab3 = st.tabs(["投保信息", "条款管理", "生成方案"])
    
    with tab1:
        st.session_state.insurance_data = render_insurance_form()
    
    with tab2:
        render_clause_manager()
    
    with tab3:
        if not st.session_state.insurance_data:
            st.warning("请先填写投保信息")
            return
        
        if not st.session_state.selected_clauses:
            st.warning("请先选择扩展条款")
            return
        
        st.header("生成保险方案")
        
        # 选择导出格式
        format = st.selectbox(
            "选择格式",
            ["Markdown", "Word"],
            key="generate_format"  # 修改key以避免重复
        )
        
        if st.button("生成方案"):
            if format == "Markdown":
                content = generate_document(
                    st.session_state.insurance_data,
                    st.session_state.selected_clauses,
                    'markdown'
                )
                st.download_button(
                    "下载Markdown文件",
                    content,
                    file_name="insurance_policy.md",
                    mime="text/markdown"
                )
                st.markdown(content)
            else:
                docx_file = generate_document(
                    st.session_state.insurance_data,
                    st.session_state.selected_clauses,
                    'docx'
                )
                st.download_button(
                    "下载Word文件",
                    docx_file,
                    file_name="insurance_policy.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

if __name__ == "__main__":
    main()
