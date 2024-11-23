import streamlit as st
import pandas as pd
import numpy as np
from .database import Database
from .version_manager import render_version_tags
import io

def export_clauses(clauses, format):
    """导出选中的条款"""
    db = Database()
    clause_uuids = [clause['UUID'] for clause in clauses]
    return db.export_selected_clauses(clause_uuids, format)

def handle_version_select(db, clause_uuid, version):
    """处理版本选择"""
    if db.activate_clause_version(clause_uuid, version):
        st.rerun()

def handle_version_delete(db, clause_uuid, version):
    """处理版本删除"""
    if db.delete_clause_version(clause_uuid, version):
        st.success("版本删除成功")
        st.rerun()
    else:
        st.error("无法删除最后一个版本")

def handle_content_save(db, clause_uuid, content):
    """处理内容保存"""
    if db.update_clause(clause_uuid, content=content):
        st.success("已保存为新版本")
        st.rerun()
    else:
        st.error("保存失败")

def render_clause_manager():
    """渲染条款管理界面"""
    st.markdown("""
    <style>
    .stDataFrame {
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 初始化数据库
    db = Database()
    
    # 初始化session state
    if 'selected_clauses' not in st.session_state:
        st.session_state.selected_clauses = []
    if 'previous_selection' not in st.session_state:
        st.session_state.previous_selection = []
    
    # 创建两列布局
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("条款管理")
        
        # 数据库操作
        db_col1, db_col2, db_col3 = st.columns(3)
        with db_col1:
            if st.button("清空数据库"):
                db.clear_database()
                st.session_state.selected_clauses = []
                st.success("数据库已清空")
                st.rerun()
        
        with db_col2:
            exported_db = db.export_database()
            if exported_db:
                st.download_button(
                    "导出数据库",
                    exported_db,
                    file_name="clauses.db",
                    mime="application/octet-stream"
                )
        
        with db_col3:
            uploaded_db = st.file_uploader("导入数据库", type=['db'])
            if uploaded_db:
                db.import_database(uploaded_db.read())
                st.success("数据库导入成功")
                st.rerun()
        
        # 文件上传
        uploaded_file = st.file_uploader("导入条款库", type=['csv', 'xlsx'])
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                db.import_clauses(df)
                st.success("条款库导入成功！")
            except Exception as e:
                st.error(f"文件导入错误：{str(e)}")
        
        # 获取所有条款
        clauses_df = db.export_clauses('dataframe')
        if not clauses_df.empty:
            # 创建筛选条件
            st.subheader("筛选条件")
            filter_cols = st.columns(3)
            
            # 动态生成筛选框
            filters = {}
            exclude_columns = ['UUID', 'PINYIN', 'QUANPIN', '扩展条款正文', '序号', '版本号']
            filter_columns = [col for col in clauses_df.columns if col not in exclude_columns]
            
            for i, col in enumerate(filter_columns):
                with filter_cols[i % 3]:
                    unique_values = sorted(clauses_df[col].unique())
                    filters[col] = st.multiselect(
                        f"选择{col}",
                        options=unique_values,
                        key=f"filter_{col}"
                    )
            
            # 搜索框
            search_term = st.text_input(
                "搜索条款",
                placeholder="输入条款名称、拼音或关键词",
                help="支持条款名称、拼音首字母和全拼搜索"
            )
            
            # 应用筛选条件
            filtered_df = clauses_df.copy()
            
            # 应用搜索条件
            if search_term:
                search_term = search_term.lower()
                mask = (
                    filtered_df['扩展条款标题'].str.contains(search_term, na=False, case=False) |
                    filtered_df['PINYIN'].str.contains(search_term, na=False, case=False) |
                    filtered_df['QUANPIN'].str.contains(search_term, na=False, case=False)
                )
                filtered_df = filtered_df[mask]
            
            # 应用筛选条件
            for col, selected_values in filters.items():
                if selected_values:
                    filtered_df = filtered_df[filtered_df[col].isin(selected_values)]
            
            if not filtered_df.empty:
                # 分页设置
                ITEMS_PER_PAGE = 20
                total_pages = max(1, (len(filtered_df) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
                
                page_cols = st.columns([1, 4])
                with page_cols[0]:
                    current_page = st.number_input("页码", min_value=1, max_value=total_pages, value=1)
                
                start_idx = (current_page - 1) * ITEMS_PER_PAGE
                end_idx = min(start_idx + ITEMS_PER_PAGE, len(filtered_df))
                
                # 显示分页信息
                st.write(f"显示第 {start_idx + 1} 到 {end_idx} 条，共 {len(filtered_df)} 条")
                
                # 准备当前页的数据
                display_df = filtered_df.iloc[start_idx:end_idx].copy()
                display_df = display_df.reset_index(drop=True)
                
                # 全选功能
                select_all = st.checkbox("全选当前筛选结果", key="select_all")
                
                if select_all:
                    # 全选时，将所有筛选后的条款添加到已选列表
                    st.session_state.selected_clauses = filtered_df.to_dict('records')
                    st.rerun()
                
                # 使用container和custom CSS来控制表格宽度
                with st.container():
                    st.markdown("""
                    <style>
                        .stDataFrame {
                            width: 75% !important;
                        }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # 创建数据表格，确保选择列是布尔类型
                    selection_array = np.zeros(len(display_df), dtype=bool)
                    for i in range(len(display_df)):
                        if any(c['UUID'] == display_df.iloc[i]['UUID'] for c in st.session_state.selected_clauses):
                            selection_array[i] = True
                    
                    edited_df = pd.DataFrame({
                        "选择": selection_array,
                        "序号": display_df['序号'].astype(str),
                        "条款名称": display_df['扩展条款标题'],
                        "条款正文": display_df['扩展条款正文'].str[:100] + '...',
                        "版本": display_df['版本号'].astype(str)
                    })
                    
                    # 显示数据表格
                    edited_result = st.data_editor(
                        edited_df,
                        hide_index=True,
                        use_container_width=True,
                        key=f"data_editor_{current_page}",
                        column_config={
                            "选择": st.column_config.CheckboxColumn(
                                "选择",
                                help="选择条款",
                                default=False,
                                width="small"
                            ),
                            "序号": st.column_config.TextColumn(
                                "序号",
                                help="条款序号",
                                disabled=True,
                                width="small"
                            ),
                            "条款名称": st.column_config.TextColumn(
                                "条款名称",
                                help="条款标题",
                                disabled=True,
                                width="medium"
                            ),
                            "条款正文": st.column_config.TextColumn(
                                "条款正文预览",
                                help="条款内容预览",
                                disabled=True,
                                width="large"
                            ),
                            "版本": st.column_config.TextColumn(
                                "版本号",
                                help="条款版本",
                                disabled=True,
                                width="small"
                            )
                        }
                    )
                
                # 更新选择状态
                if not select_all:
                    # 获取当前页面选中的行
                    current_page_selected = []
                    for i, is_selected in enumerate(edited_result['选择']):
                        if is_selected:
                            # 获取实际的条款数据
                            clause_data = display_df.iloc[i].to_dict()
                            if not any(c['UUID'] == clause_data['UUID'] for c in st.session_state.selected_clauses):
                                current_page_selected.append(clause_data)
                    
                    # 移除当前页面取消选择的条款
                    st.session_state.selected_clauses = [
                        clause for clause in st.session_state.selected_clauses
                        if clause['UUID'] not in [
                            display_df.iloc[i]['UUID']
                            for i, is_selected in enumerate(edited_result['选择'])
                            if not is_selected
                        ]
                    ]
                    
                    # 添加新选择的条款
                    st.session_state.selected_clauses.extend(current_page_selected)
                    
                    # 检查选择状态是否发生变化
                    current_selection = [c['UUID'] for c in st.session_state.selected_clauses]
                    if current_selection != st.session_state.previous_selection:
                        st.session_state.previous_selection = current_selection
                        st.rerun()
            else:
                st.info("没有找到匹配的条款")
        else:
            st.info("数据库中暂无条款，请先导入条款库")
    
    # 在右侧显示已选条款列表
    with col2:
        st.header("已选条款")
        if st.session_state.selected_clauses:
            # 导出选项
            export_format = st.selectbox(
                "导出格式",
                ["XLSX", "DOCX", "Markdown"],
                key="export_format"
            )
            
            if st.button("导出选中条款"):
                export_data = export_clauses(
                    st.session_state.selected_clauses,
                    export_format.lower()
                )
                
                if export_format == "XLSX":
                    st.download_button(
                        "下载Excel文件",
                        export_data,
                        file_name="selected_clauses.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                elif export_format == "DOCX":
                    st.download_button(
                        "下载Word文件",
                        export_data,
                        file_name="selected_clauses.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                elif export_format == "Markdown":
                    st.download_button(
                        "下载Markdown文件",
                        export_data,
                        file_name="selected_clauses.md",
                        mime="text/markdown"
                    )
            
            # 显示已选条款
            for i, clause in enumerate(st.session_state.selected_clauses):
                with st.expander(f"{i+1}. {clause['扩展条款标题']}", expanded=False):
                    # 获取条款版本历史
                    versions = db.get_clause_versions(clause['UUID'])
                    
                    # 渲染版本标签并获取编辑后的内容
                    content, should_save = render_version_tags(
                        versions,
                        clause['版本号'],
                        lambda version: handle_version_select(db, clause['UUID'], version),
                        lambda version: handle_version_delete(db, clause['UUID'], version),
                        f"clause_{clause['UUID']}",  # 使用条款的UUID作为key前缀
                        clause['扩展条款正文']  # 传递当前内容
                    )
                    
                    # 如果需要保存，则保存内容
                    if should_save:
                        handle_content_save(db, clause['UUID'], content)
        else:
            st.info("还未选择任何条款")
