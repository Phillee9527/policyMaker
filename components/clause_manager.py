import streamlit as st
import pandas as pd
import numpy as np
from .database import Database
from .version_manager import render_version_tags
import io
import difflib
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def export_clauses(clauses, format):
    """导出选中的条款"""
    db = Database()
    clause_uuids = [clause['UUID'] for clause in clauses]
    return db.export_selected_clauses(clause_uuids, format)

def handle_version_select(db, clause_uuid, version_number, clause):
    """处理版本选择"""
    logger.info(f"\n=== 处理版本选择 ===")
    logger.info(f"条款UUID: {clause_uuid}")
    logger.info(f"目标版本号: {version_number}")
    logger.info(f"当前版本号: {clause.get('版本号', 1)}")
    
    try:
        # 获取要切换到的版本
        version = db.session.query(db.ClauseVersion).filter_by(
            clause_uuid=clause_uuid,
            version_number=version_number
        ).first()
        
        if version:
            # 更新当前条款对象
            clause_obj = db.session.query(db.Clause).filter_by(uuid=clause_uuid).first()
            if clause_obj:
                # 更新条款对象
                clause_obj.title = version.title
                clause_obj.content = version.content
                clause_obj.version_number = version.version_number
                clause_obj.updated_at = version.created_at
                
                # 提交更改
                db.session.commit()
                
                # 更新session state中的条款内容
                updated_clauses = []
                for c in st.session_state.selected_clauses:
                    if c['UUID'] == clause_uuid:
                        logger.info(f"更新条款内容：从 V{c['版本号']} 到 V{version_number}")
                        c = c.copy()  # 创建副本以确保状态更新
                        c['版本号'] = version_number
                        c['扩展条款标题'] = version.title
                        c['扩展条款正文'] = version.content
                    updated_clauses.append(c)
                
                # 更新整个selected_clauses列表
                st.session_state.selected_clauses = updated_clauses
                
                # 确保version_info存在并更新
                if 'version_info' not in st.session_state:
                    st.session_state.version_info = {}
                st.session_state.version_info[clause_uuid] = version_number
                
                # 保存到数据库
                if 'current_policy_id' in st.session_state:
                    success = db.save_policy_clauses(
                        st.session_state.current_policy_id,
                        [c['UUID'] for c in st.session_state.selected_clauses]
                    )
                    logger.info(f"保存到数据库: {'成功' if success else '失败'}")
                
                logger.info(f"版本切换成功，新版本号: {version_number}")
                logger.info(f"version_info更新后: {st.session_state.version_info}")
                
                # 强制重新渲染前清理缓存
                for key in list(st.session_state.keys()):
                    if key.startswith('data_editor_'):
                        del st.session_state[key]
                
                # 强制重新渲染
                st.rerun()
                return True
                
    except Exception as e:
        logger.error(f"版本切换失败: {str(e)}")
        db.session.rollback()
    return False

def handle_version_delete(db, clause_uuid, version_number):
    """处理版本删除"""
    if db.delete_clause_version(clause_uuid, version_number):
        st.success(f"版本 V{version_number} 已删除")
        st.rerun()
    else:
        st.error("无法删除此版本")

def handle_content_save(db, clause_uuid, content, version_note=""):
    """处理内容保存"""
    if db.update_clause(clause_uuid, content=content, version_note=version_note):
        st.success("已保存为新版本")
        st.rerun()
    else:
        st.error("保存失败")

def show_version_diff(old_version, new_version):
    """显示版本之间的差异"""
    d = difflib.Differ()
    diff = list(d.compare(old_version.content.splitlines(), new_version.content.splitlines()))
    
    st.markdown("### 版本差异对比")
    for line in diff:
        if line.startswith('+'):
            st.markdown(f'<p style="color: green">{line}</p>', unsafe_allow_html=True)
        elif line.startswith('-'):
            st.markdown(f'<p style="color: red">{line}</p>', unsafe_allow_html=True)
        elif line.startswith('?'):
            continue
        else:
            st.markdown(line)

def handle_version_rollback(db, clause_uuid, version_number):
    """处理版本回滚"""
    if db.activate_clause_version(clause_uuid, version_number):
        st.success("已回滚到选中版本")
        st.rerun()
    else:
        st.error("版本回滚失败")

def render_clause_content(clause, db):
    """渲染条款内容编辑器"""
    logger.debug(f"\n=== 开始渲染条款内容 ===")
    logger.debug(f"条款UUID: {clause['UUID']}")
    logger.debug(f"当前版本号: {clause.get('版本号', 1)}")
    
    with st.expander(f"{clause['扩展条款标题']}", expanded=False):
        try:
            # 获取所有版本
            versions = db.get_clause_versions(clause['UUID'])
            logger.debug(f"获取到版本数量: {len(versions)}")
            
            # 从session state获取当前版本号
            current_version = st.session_state.version_info.get(
                clause['UUID'], 
                clause.get('版本号', 1)
            )
            
            def handle_version_select_wrapper(version_number):
                """处理版本选择装函数"""
                return handle_version_select(db, clause['UUID'], version_number, clause)
            
            # 渲染版本标签
            try:
                content, should_save, version_note = render_version_tags(
                    versions,
                    current_version,
                    handle_version_select_wrapper,
                    handle_version_delete,
                    clause['UUID'],
                    clause['扩展条款正文']
                )
                
                # 如果需要保存新版本
                if should_save:
                    logger.info("保存新版本")
                    if db.update_clause(clause['UUID'], content=content, version_note=version_note):
                        st.success("新版本保存成功")
                        st.rerun()
            except Exception as e:
                logger.error(f"渲染版本标签时出错: {str(e)}")
                st.error(f"渲染版本标签时出错: {str(e)}")
        
        except Exception as e:
            logger.error(f"渲染条款内容时出错: {str(e)}")
            st.error(f"渲染条款内容时出错: {str(e)}")
    
    logger.debug("=== 条款内容渲染结束 ===\n")

def render_selected_clauses(clauses, db, page_size=25):
    """分页渲染已选条款"""
    # 使用markdown渲染标题以应用样式
    st.markdown("## 已选条款")
    
    # 计算总条款数和总页数
    total_clauses = len(clauses)
    total_pages = max(1, (total_clauses + page_size - 1) // page_size)
    
    # 初始化当前页码
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    
    # 使用单行多列布局实现分页控件
    st.write("---")  # 分隔线
    
    # 使用单行6列布局
    c1, c2, c3, c4, c5, c6 = st.columns([1, 1, 1, 1, 1, 2])
    
    # 首页按钮
    with c1:
        if st.button("⏮️", disabled=st.session_state.current_page <= 1, key="first_page", help="首页"):
            st.session_state.current_page = 1
    
    # 上一页按钮
    with c2:
        if st.button("◀️", disabled=st.session_state.current_page <= 1, key="prev_page", help="上一页"):
            st.session_state.current_page -= 1
    
    # 页码输入
    with c3:
        new_page = st.number_input(
            "",  # 空标签
            min_value=1,
            max_value=total_pages,
            value=st.session_state.current_page,
            key="page_input",
            label_visibility="collapsed"
        )
        if new_page != st.session_state.current_page:
            st.session_state.current_page = new_page
    
    # 下一页按钮
    with c4:
        if st.button("▶️", disabled=st.session_state.current_page >= total_pages, key="next_page", help="下一页"):
            st.session_state.current_page += 1
    
    # 末页按钮
    with c5:
        if st.button("⏭️", disabled=st.session_state.current_page >= total_pages, key="last_page", help="末页"):
            st.session_state.current_page = total_pages
    
    # 页码信息
    with c6:
        st.write(f"第 {st.session_state.current_page}/{total_pages} 页，共 {total_clauses} 条")
    
    st.write("---")  # 分隔线
    
    # 计算当前页的条款范围
    start_idx = (st.session_state.current_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_clauses)
    
    # 渲染当前页的条款
    for i in range(start_idx, end_idx):
        clause = clauses[i]
        render_clause_content(clause, db)

def render_clause_manager():
    """渲染条款管理界面"""
    logger.debug("\n=== 开始渲染条款管理界面 ===")
    
    # 初始化数据库
    db = Database()
    
    # 使用markdown渲染标题以应用样式
    st.markdown("# 条款管理")
    
    # 创建两个独立的容器
    left_container = st.container()
    right_container = st.container()
    
    # 使用两列布局
    col1, col2 = st.columns([2, 1])
    
    # 左侧条款管理区域
    with col1:
        with left_container:
            # 数据库操作按钮区域
            st.markdown('<div class="db-operations">', unsafe_allow_html=True)
            
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
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 文件上传区域
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
            
            # 筛选条件部分
            st.markdown("## 筛选条件")
            render_clause_list(db)
    
    # 右侧已选条款区域
    with col2:
        with right_container:
            st.markdown(f"## 已选条款 (共{len(st.session_state.selected_clauses)}个)")
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
                
                # 使用独立容器渲染已选条款列表
                with st.container():
                    render_selected_clauses(st.session_state.selected_clauses, db)
            else:
                st.info("还未选择任何条款")
    
    logger.debug("=== 条款管理界面渲染结束 ===\n")

def render_clause_list(db):
    """渲染条款列表和筛选功能"""
    # 获取所有条款
    clauses_df = db.export_clauses('dataframe')
    if not clauses_df.empty:
        # 创建筛选条件
        st.markdown("## 筛选条件")
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
            "搜索条",
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
            col1, col2 = st.columns(2)
            
            # 初始化select_all状态
            if 'select_all_state' not in st.session_state:
                st.session_state.select_all_state = False
            
            with col1:
                select_all = st.checkbox("全选当前筛选结果", 
                                       key="select_all",
                                       value=st.session_state.select_all_state)
                
                # 更新select_all状态
                st.session_state.select_all_state = select_all
            
            with col2:
                if st.button("取消全选当前结果", key="cancel_all"):
                    # 不直接修改checkbox状态，而是通过session_state
                    st.session_state.select_all_state = False
                    # 清空当前筛选结果的选择
                    if not filtered_df.empty:
                        current_uuids = filtered_df['UUID'].tolist()
                        st.session_state.selected_clauses = [
                            clause for clause in st.session_state.selected_clauses 
                            if clause['UUID'] not in current_uuids
                        ]
                        # 立即保存到数据库
                        handle_clause_selection(db, True)
                        st.rerun()
            
            # 如果全选被勾选，更新选择状态
            if st.session_state.select_all_state:
                # 直接将所有筛选后的条款添加到selected_clauses
                st.session_state.selected_clauses = filtered_df.to_dict('records')
                selection_array = np.ones(len(display_df), dtype=bool)
                # 立即保存到数据库
                handle_clause_selection(db, True)
            else:
                selection_array = np.zeros(len(display_df), dtype=bool)
                # 检查当前行是否已被选中
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
            
            # 处理单选择
            if not select_all:
                # 取当前页面选中的行
                current_page_selected = []
                selection_changed = False
                
                for i, is_selected in enumerate(edited_result['选择']):
                    clause_data = display_df.iloc[i].to_dict()
                    current_selected = any(c['UUID'] == clause_data['UUID'] for c in st.session_state.selected_clauses)
                    
                    if is_selected and not current_selected:
                        current_page_selected.append(clause_data)
                        selection_changed = True
                    elif not is_selected and current_selected:
                        selection_changed = True
                
                if selection_changed:
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
                    
                    # 立即保存到数据库
                    handle_clause_selection(db, True)
                    
                    # 使用session_state来控制刷新
                    if 'refresh_counter' not in st.session_state:
                        st.session_state.refresh_counter = 0
                    st.session_state.refresh_counter += 1
                    
                    # 每隔几次选择才刷新一次页面
                    if st.session_state.refresh_counter >= 3:
                        st.session_state.refresh_counter = 0
                        st.rerun()
        else:
            st.info("没找到匹配的条款")
    else:
        st.info("数据库中暂无条款，请先导入条款库")

# 在选择条款时立即保存到数据库
def handle_clause_selection(db, selection_changed):
    """处理条款选择变更"""
    if selection_changed and 'current_policy_id' in st.session_state:
        clause_uuids = []
        version_info = {}
        
        for clause in st.session_state.selected_clauses:
            clause_uuids.append(clause['UUID'])
            version_info[clause['UUID']] = clause.get('版本号', 1)
        
        # 保存条款选择和版本信息
        db.save_policy_clauses(st.session_state.current_policy_id, clause_uuids)
        
        # 更新session state中的版本信息
        if 'version_info' not in st.session_state:
            st.session_state.version_info = {}
        st.session_state.version_info.update(version_info)
