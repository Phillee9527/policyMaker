import streamlit as st
import pandas as pd
import numpy as np

def render_clause_manager():
    st.markdown("""
    <style>
    .stDataFrame {
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 初始化session state
    if 'clauses_df' not in st.session_state:
        st.session_state.clauses_df = None
    if 'selected_clauses' not in st.session_state:
        st.session_state.selected_clauses = []
    if 'selected_indices' not in st.session_state:
        st.session_state.selected_indices = set()
    
    # 创建两列布局
    col1, col2 = st.columns([2, 1])
    
    with col1:
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
                st.success("条款库导入成功！")
            except Exception as e:
                st.error(f"文件导入错误：{str(e)}")
        
        if st.session_state.clauses_df is not None:
            # 创建筛选条件
            st.subheader("筛选条件")
            filter_cols = st.columns(3)
            
            # 动态生成筛选框
            filters = {}
            exclude_columns = ['UUID', 'PINYIN', 'QUANPIN', '扩展条款正文']
            filter_columns = [col for col in st.session_state.clauses_df.columns if col not in exclude_columns]
            
            for i, col in enumerate(filter_columns):
                with filter_cols[i % 3]:
                    unique_values = sorted(st.session_state.clauses_df[col].unique())
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
            filtered_df = st.session_state.clauses_df.copy()
            
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
                st.session_state.selected_indices = set(filtered_df.index.tolist())
                st.session_state.selected_clauses = [
                    st.session_state.clauses_df.iloc[idx].to_dict() 
                    for idx in st.session_state.selected_indices
                ]
            
            # 创建数据表格
            edited_df = pd.DataFrame({
                "选择": [idx in st.session_state.selected_indices for idx in filtered_df.index[start_idx:end_idx]],
                "序号": display_df['序号'].astype(str),
                "条款名称": display_df['扩展条款标题'],
                "条款正文": display_df['扩展条款正文'].str[:100] + '...'
            })
            
            # 显示数据表格
            edited_result = st.data_editor(
                edited_df,
                hide_index=True,
                column_config={
                    "选择": st.column_config.CheckboxColumn(
                        "选择",
                        help="选择条款",
                        default=False
                    ),
                    "序号": st.column_config.TextColumn(
                        "序号",
                        help="条款序号",
                        disabled=True
                    ),
                    "条款名称": st.column_config.TextColumn(
                        "条款名称",
                        help="条款标题",
                        disabled=True
                    ),
                    "条款正文": st.column_config.TextColumn(
                        "条款正文预览",
                        help="条款内容预览",
                        disabled=True
                    )
                }
            )
            
            # 更新选择状态
            if not select_all:
                # 获取当前页面选中的行
                current_page_selected = set(
                    filtered_df.index[start_idx + i]
                    for i, is_selected in enumerate(edited_result['选择'])
                    if is_selected
                )
                
                # 更新总的选择状态
                st.session_state.selected_indices = (
                    st.session_state.selected_indices - set(filtered_df.index[start_idx:end_idx]) | 
                    current_page_selected
                )
                
                # 更新选中的条款
                st.session_state.selected_clauses = [
                    st.session_state.clauses_df.iloc[idx].to_dict() 
                    for idx in st.session_state.selected_indices
                ]
    
    # 在右侧显示已选条款列表
    with col2:
        st.header("已选条款")
        if st.session_state.selected_clauses:
            for i, clause in enumerate(st.session_state.selected_clauses):
                with st.expander(f"{i+1}. {clause['扩展条款标题']}", expanded=False):
                    edited_content = st.text_area(
                        "编辑条款内容",
                        value=clause['扩展条款正文'],
                        height=300,
                        key=f"edit_{i}"
                    )
                    
                    cols = st.columns([1, 1])
                    with cols[0]:
                        if st.button("保存", key=f"save_{i}"):
                            clause['扩展条款正文'] = edited_content
                            st.success("保存成功")
                    with cols[1]:
                        if st.button("删除", key=f"delete_{i}"):
                            st.session_state.selected_clauses.pop(i)
                            st.rerun()
        else:
            st.info("还未选择任何条款")
