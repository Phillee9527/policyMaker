import streamlit as st

def render_version_tags(versions, current_version, on_version_select, on_version_delete, key_prefix):
    """渲染版本标签"""
    st.markdown("""
    <style>
    .version-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 10px 0;
    }
    
    .version-tag {
        display: inline-flex;
        align-items: center;
        padding: 4px 8px;
        background-color: #f0f2f6;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        font-size: 12px;
        cursor: pointer;
        margin-right: 8px;
        margin-bottom: 8px;
    }
    
    .version-tag.active {
        background-color: #2196f3;
        color: white;
        border-color: #1976d2;
    }
    
    .version-tag:hover {
        background-color: #e3f2fd;
    }
    
    .version-tag.active:hover {
        background-color: #1976d2;
    }
    
    .version-delete {
        margin-left: 6px;
        color: #999;
        font-size: 10px;
        padding: 2px 4px;
        border-radius: 2px;
    }
    
    .version-delete:hover {
        color: #f44336;
        background-color: rgba(244, 67, 54, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

    st.write("版本历史")
    
    # 创建版本标签列表
    cols = st.columns(4)  # 每行最多4个标签
    for i, version in enumerate(versions):
        with cols[i % 4]:
            tag_container = st.container()
            
            # 创建标签按钮
            is_current = version.version_number == current_version
            tag_style = "active" if is_current else ""
            tag_html = f"""
            <div class="version-tag {tag_style}" 
                 onclick="document.dispatchEvent(new CustomEvent('version_select', {{detail: {version.version_number}}}))">
                V{version.version_number}
                <span style="font-size: 10px; margin-left: 4px;">
                    ({version.created_at.strftime('%m-%d %H:%M')})
                </span>
                {f'<span class="version-delete" onclick="event.stopPropagation(); document.dispatchEvent(new CustomEvent(\'version_delete\', {{detail: {version.version_number}}}))">×</span>' if not is_current and len(versions) > 1 else ''}
            </div>
            """
            tag_container.markdown(tag_html, unsafe_allow_html=True)
    
    # 处理版本选择事件
    if st.session_state.get(f'version_select_{key_prefix}'):
        version = st.session_state[f'version_select_{key_prefix}']
        del st.session_state[f'version_select_{key_prefix}']
        on_version_select(version)
    
    # 处理版本删除事件
    if st.session_state.get(f'version_delete_{key_prefix}'):
        version = st.session_state[f'version_delete_{key_prefix}']
        del st.session_state[f'version_delete_{key_prefix}']
        on_version_delete(version)
    
    # 添加JavaScript事件处理
    st.markdown(f"""
    <script>
    document.addEventListener('version_select', function(e) {{
        window.streamlitPyRepl.setComponentValue('{f"version_select_{key_prefix}"}', e.detail);
    }});
    
    document.addEventListener('version_delete', function(e) {{
        if (confirm('确定要删除此版本吗？')) {{
            window.streamlitPyRepl.setComponentValue('{f"version_delete_{key_prefix}"}', e.detail);
        }}
    }});
    </script>
    """, unsafe_allow_html=True)
