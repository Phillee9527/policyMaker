import streamlit as st

def render_version_tags(versions, current_version, on_version_select, on_version_delete):
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
        border-radius: 4px;
        font-size: 12px;
        cursor: pointer;
    }
    
    .version-tag.active {
        background-color: #4caf50;
        color: white;
    }
    
    .version-tag:hover {
        background-color: #e0e2e6;
    }
    
    .version-tag.active:hover {
        background-color: #3d8b40;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 版本选择
        selected_version = st.selectbox(
            "选择版本",
            [v.version_number for v in versions],
            index=[v.version_number for v in versions].index(current_version),
            format_func=lambda x: f"V{x} ({next(v.created_at.strftime('%Y-%m-%d %H:%M') for v in versions if v.version_number == x)})"
        )
        if selected_version != current_version:
            on_version_select(selected_version)
    
    with col2:
        # 版本删除（只有当不是当前版本且不是唯一版本时才显示删除按钮）
        if len(versions) > 1 and selected_version != current_version:
            if st.button("删除此版本", key=f"delete_version_{selected_version}"):
                on_version_delete(selected_version)
