import streamlit as st
import difflib
from .logger import logger

def render_version_tags(versions, current_version, on_version_select, on_version_delete, key_prefix, current_content):
    """渲染版本标签"""
    logger.debug("\n=== 版本标签渲染开始 ===")
    logger.debug(f"当前版本号: {current_version}")
    logger.debug(f"条款UUID: {key_prefix}")
    
    # 获取当前生效的版本对象
    current_ver = next((v for v in versions if v.version_number == current_version), None)
    if current_ver:
        logger.debug(f"当前版本内容: {current_ver.content[:50]}...")
    
    # 显示版本历史和当前生效版本
    st.write(f"📚 版本历史（当前生效：V{current_version}）")
    st.info("🔄 您可以在这里管理条款的不同版本，切换到需要的版本或创建新版本")
    
    # 使用下拉菜单选择版本
    version_options = [
        f"V{v.version_number} ({v.created_at.strftime('%Y-%m-%d %H:%M')})" 
        for v in versions
    ]
    logger.debug(f"可用版本数量: {len(versions)}")
    logger.debug("可用版本列表:")
    for v in versions:
        logger.debug(f"  - V{v.version_number} ({v.created_at})")
    
    selected_idx = st.selectbox(
        "🔍 选择版本",
        range(len(version_options)),
        format_func=lambda x: version_options[x],
        key=f"version_select_{key_prefix}"
    )
    
    # 获取选中的版本
    selected_version = versions[selected_idx]
    logger.debug(f"选中的版本号: {selected_version.version_number}")
    logger.debug(f"选中版本内容: {selected_version.content[:50]}...")
    
    # 如果选中的版本不是当前版本，显示切换按钮和对比按钮
    if selected_version.version_number != current_version:
        col1, col2 = st.columns(2)
        with col1:
            switch_key = f"switch_{key_prefix}_{selected_version.version_number}_{current_version}"
            if st.button("切换到此版本", key=switch_key):
                logger.info("\n=== 版本切换操作开始 ===")
                logger.info(f"尝试从 V{current_version} 切换到 V{selected_version.version_number}")
                success = on_version_select(selected_version.version_number)
                logger.info(f"版本切换结果: {success}")
                
                if success:
                    # 强制更新session state
                    if 'version_info' not in st.session_state:
                        st.session_state.version_info = {}
                    st.session_state.version_info[key_prefix] = selected_version.version_number
                    
                    # 更新selected_clauses
                    for clause in st.session_state.selected_clauses:
                        if clause['UUID'] == key_prefix:
                            clause['版本号'] = selected_version.version_number
                            clause['扩展条款标题'] = selected_version.title
                            clause['扩展条款正文'] = selected_version.content
                            break
                    
                    # 强制重新渲染
                    st.rerun()
                    
        with col2:
            if st.button("与当前版本对比", key=f"compare_{key_prefix}_{selected_version.version_number}"):
                if current_ver:
                    show_version_diff(current_ver, selected_version)
    
    # 显示选中版本的内容
    st.markdown("### 当前显示的版本内容")
    st.markdown(selected_version.content)
    
    # 编辑功能
    if st.button("编辑条款", key=f"edit_{key_prefix}"):
        st.session_state[f"editing_{key_prefix}"] = True
        print(f"进入编辑模式: {key_prefix}")
    
    # 如果处于编辑状态，显示编辑器
    if st.session_state.get(f"editing_{key_prefix}", False):
        edited_content = st.text_area(
            "编辑条款内容",
            value=selected_version.content,
            height=300,
            key=f"edit_area_{key_prefix}"
        )
        
        version_note = st.text_input("版本说明", key=f"version_note_{key_prefix}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("保存为新版本", key=f"save_{key_prefix}"):
                print(f"\n=== 保存新版本 ===")
                print(f"条款: {key_prefix}")
                print(f"版本说明: {version_note}")
                print(f"新内容: {edited_content[:50]}...")
                st.session_state[f"editing_{key_prefix}"] = False
                return edited_content, True, version_note
        with col2:
            if st.button("取消", key=f"cancel_{key_prefix}"):
                print(f"取消编辑: {key_prefix}")
                st.session_state[f"editing_{key_prefix}"] = False
    
    print("=== 版本标签渲染结束 ===\n")
    return selected_version.content, False, ""

def show_version_diff(old_version, new_version):
    """显示版本之间的差异"""
    d = difflib.Differ()
    diff = list(d.compare(old_version.content.splitlines(), new_version.content.splitlines()))
    
    st.markdown("### 版本差异对比")
    st.markdown(f"对比 V{old_version.version_number} 和 V{new_version.version_number}")
    
    for line in diff:
        if line.startswith('+'):
            st.markdown(f'<p style="color: green">{line}</p>', unsafe_allow_html=True)
        elif line.startswith('-'):
            st.markdown(f'<p style="color: red">{line}</p>', unsafe_allow_html=True)
        elif line.startswith('?'):
            continue
        else:
            st.markdown(line)
