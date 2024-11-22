import streamlit as st
import datetime

def render_version_timeline(versions, current_version, on_version_select, on_version_delete):
    """渲染版本时间线"""
    st.markdown("""
    <style>
    .version-timeline {
        display: flex;
        align-items: center;
        margin: 20px 0;
        position: relative;
        padding: 10px 0;
    }
    
    .version-point {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background-color: #1f77b4;
        margin: 0 10px;
        cursor: pointer;
        position: relative;
        z-index: 2;
    }
    
    .version-point:hover {
        background-color: #2196f3;
    }
    
    .version-point.active {
        background-color: #4caf50;
        box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.3);
    }
    
    .version-line {
        height: 2px;
        background-color: #ddd;
        flex-grow: 1;
        position: relative;
        z-index: 1;
    }
    
    .version-info {
        position: absolute;
        top: -25px;
        transform: translateX(-50%);
        font-size: 12px;
        color: #666;
        white-space: nowrap;
    }
    
    .version-delete {
        position: absolute;
        bottom: -25px;
        transform: translateX(-50%);
        font-size: 12px;
        color: #f44336;
        cursor: pointer;
        display: none;
    }
    
    .version-point:hover .version-delete {
        display: block;
    }
    </style>
    """, unsafe_allow_html=True)

    # 生成时间线HTML
    timeline_html = '<div class="version-timeline">'
    
    for i, version in enumerate(versions):
        # 添加连接线
        if i > 0:
            timeline_html += '<div class="version-line"></div>'
        
        # 添加版本点
        active_class = "active" if version.version_number == current_version else ""
        timeline_html += f"""
        <div class="version-point {active_class}" 
             onclick="document.dispatchEvent(new CustomEvent('version_select', {{detail: {version.version_number}}}))">
            <div class="version-info">V{version.version_number}<br>{version.created_at.strftime('%Y-%m-%d %H:%M')}</div>
            {f'<div class="version-delete" onclick="document.dispatchEvent(new CustomEvent(\'version_delete\', {{detail: {version.version_number}}}))">删除</div>' if len(versions) > 1 else ''}
        </div>
        """
    
    timeline_html += '</div>'
    
    # 添加JavaScript事件处理
    st.markdown(f"""
    <script>
    document.addEventListener('version_select', function(e) {{
        window.streamlitPyRepl.sendMessageToHost({{
            type: 'version_select',
            version: e.detail
        }});
    }});
    
    document.addEventListener('version_delete', function(e) {{
        e.stopPropagation();
        if (confirm('确定要删除此版本吗？')) {{
            window.streamlitPyRepl.sendMessageToHost({{
                type: 'version_delete',
                version: e.detail
            }});
        }}
    }});
    </script>
    {timeline_html}
    """, unsafe_allow_html=True)
    
    # 处理版本选择事件
    if st.session_state.get('version_select'):
        version = st.session_state.version_select
        on_version_select(version)
        del st.session_state.version_select
    
    # 处理版本删除事件
    if st.session_state.get('version_delete'):
        version = st.session_state.version_delete
        on_version_delete(version)
        del st.session_state.version_delete
