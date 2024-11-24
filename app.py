import streamlit as st
import os
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
    if 'project_name' not in st.session_state:
        st.session_state.project_name = None
    if 'project_dir' not in st.session_state:
        st.session_state.project_dir = None

def main():
    st.set_page_config(
        page_title="📋 保险方案生成平台",
        page_icon="📋",
        layout="wide"
    )
    
    # 添加全局样式
    st.markdown("""
    <style>
    /* 页面主标题样式 */
    .main h1:first-of-type {
        color: #1e3d59 !important;
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        margin-top: 0.5em !important;
        margin-bottom: 1em !important;
    }
    
    /* 功能区标题样式 */
    .main .block-container h1, 
    .stTabs [data-baseweb="tab-panel"] h1 {
        color: #1e3d59 !important;
        font-size: 1.3rem !important;
        font-weight: 500 !important;
        margin-top: 1.2em !important;
        margin-bottom: 0.8em !important;
        border-bottom: 1px solid #e6e6e6;
        padding-bottom: 0.3em;
    }
    
    /* 选项卡标题样式 */
    .stTabs [data-baseweb="tab-list"] button {
        color: #1e3d59 !important;
        font-size: 1.2rem !important;
        font-weight: 500 !important;
    }
    
    /* 子标题样式 */
    .main h2, 
    .stTabs [data-baseweb="tab-panel"] h2 {
        color: #1e3d59 !important;
        font-size: 1.2rem !important;
        font-weight: 500 !important;
        margin-top: 1em !important;
        margin-bottom: 0.5em !important;
    }
    
    /* 数据库操作按钮区域样式 */
    .db-operations {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 初始化session state
    init_session_state()
    
    # 确保项目目录存在
    if not os.path.exists('projects'):
        os.makedirs('projects')
    
    # 渲染项目管理器
    render_project_manager()
    
    # 如果没有选择项目，显示提示信息
    if not st.session_state.project_name:
        st.warning("🎯 请先选择或创建一个项目开始您的保险方案之旅~")
        return
    
    # 显示当前项目名称
    st.markdown(f"# 📁 项目：{st.session_state.project_name}")
    
    # 使用选项卡展示主要功能
    tab1, tab2, tab3 = st.tabs(["📝 投保信息", "📚 条款管理", "📄 生成方案"])
    
    with tab1:
        st.session_state.insurance_data = render_insurance_form()
    
    with tab2:
        render_clause_manager()
    
    with tab3:
        # 更安全地检查 insurance_data
        insurance_data = st.session_state.get('insurance_data', {})
        if not insurance_data:
            st.warning("✍️ 还没有填写投保信息哦，让我们先去完善一下吧~")
            return
        
        selected_clauses = st.session_state.get('selected_clauses', [])
        if not selected_clauses:
            st.warning("📌 还没有选择任何条款呢，去挑选一些合适的条款吧~")
            return
        
        st.markdown("# 📄 生成保险方案")
        st.info("🎨 选择您喜欢的格式，让我们为您生成一份完美的保险方案~")
        
        # 选择导出格式
        format = st.selectbox(
            "📎 选择格式",
            ["Markdown", "Word"],
            key="generate_format",
            help="Markdown格式支持在线预览，Word格式更适合打印"
        )
        
        if st.button("🚀 生成方案"):
            with st.spinner("📊 正在精心排版您的保险方案..."):
                try:
                    if format == "Markdown":
                        content = generate_document(
                            insurance_data,
                            selected_clauses,
                            'markdown'
                        )
                        if content:
                            st.download_button(
                                "⬇️ 下载Markdown文件",
                                content,
                                file_name="insurance_policy.md",
                                mime="text/markdown"
                            )
                            st.success("🎉 生成成功！以下是预览内容：")
                            st.markdown(content)
                    else:
                        docx_file = generate_document(
                            insurance_data,
                            selected_clauses,
                            'docx'
                        )
                        if docx_file:
                            st.success("🎉 生成成功！")
                            st.download_button(
                                "⬇️ 下载Word文件",
                                docx_file,
                                file_name="insurance_policy.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                except Exception as e:
                    st.error(f"❌ 生成文档时出错：{str(e)}")

if __name__ == "__main__":
    main()
