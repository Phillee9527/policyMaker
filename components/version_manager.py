import streamlit as st
import uuid

def render_version_tags(versions, current_version, on_version_select, on_version_delete, key_prefix):
    """渲染版本标签"""
    st.write("版本历史")
    
    # 使用水平布局显示版本标签
    cols = st.columns(4)  # 每行最多4个标签
    for i, version in enumerate(versions):
        with cols[i % 4]:
            # 创建版本标签
            is_current = version.version_number == current_version
            
            # 生成唯一的key
            unique_id = str(uuid.uuid4())
            timestamp = version.created_at.strftime('%Y%m%d%H%M%S')
            
            # 显示版本标签和删除按钮
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(
                    f"V{version.version_number}\n{version.created_at.strftime('%m-%d %H:%M')}",
                    key=f"version_{key_prefix}_{version.version_number}_{timestamp}_{unique_id}",
                    type="primary" if is_current else "secondary",
                    help="点击切换到此版本",
                    use_container_width=True
                ):
                    on_version_select(version.version_number)
                    st.rerun()  # 强制重新渲染
            
            # 只有非当前版本且不是唯一版本时才显示删除按钮
            if not is_current and len(versions) > 1:
                with col2:
                    if st.button(
                        "×",
                        key=f"delete_{key_prefix}_{version.version_number}_{timestamp}_{unique_id}",
                        type="secondary",
                        help="删除此版本",
                        use_container_width=True
                    ):
                        on_version_delete(version.version_number)
                        st.rerun()  # 强制重新渲染
