import streamlit as st
import uuid

def render_version_tags(versions, current_version, on_version_select, on_version_delete, key_prefix, current_content):
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
            
            # 显示版本标签
            if st.button(
                f"V{version.version_number}\n{version.created_at.strftime('%m-%d %H:%M')}",
                key=f"version_{key_prefix}_{version.version_number}_{timestamp}_{unique_id}",
                type="primary" if is_current else "secondary",
                help="点击切换到此版本",
                use_container_width=True
            ):
                on_version_select(version.version_number)
            
            # 只有非当前版本且不是唯一版本时才显示删除按钮
            if not is_current and len(versions) > 1:
                if st.button(
                    "删除",
                    key=f"delete_{key_prefix}_{version.version_number}_{timestamp}_{unique_id}",
                    type="secondary",
                    help="删除此版本",
                    use_container_width=True
                ):
                    on_version_delete(version.version_number)
    
    # 显示当前版本内容
    st.markdown("### 当前版本内容")
    st.markdown(current_content)
    
    # 编辑功能
    if st.button("编辑条款", key=f"edit_{key_prefix}"):
        st.session_state[f"editing_{key_prefix}"] = True
    
    # 如果处于编辑状态，显示编辑器
    if st.session_state.get(f"editing_{key_prefix}", False):
        edited_content = st.text_area(
            "编辑条款内容",
            value=current_content,
            height=300,
            key=f"edit_area_{key_prefix}"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("保存为新版本", key=f"save_{key_prefix}"):
                st.session_state[f"editing_{key_prefix}"] = False
                return edited_content, True
        with col2:
            if st.button("取消", key=f"cancel_{key_prefix}"):
                st.session_state[f"editing_{key_prefix}"] = False
    
    return current_content, False
