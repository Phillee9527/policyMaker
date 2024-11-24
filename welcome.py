import streamlit as st
import json
import requests
from streamlit_lottie import st_lottie

def load_lottie_url(url: str):
    """从URL加载Lottie动画"""
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

def show_welcome_screen():
    """显示欢迎页面"""
    # 设置页面配置
    st.set_page_config(
        page_title="🌟 欢迎使用保险方案生成平台",
        page_icon="🌟",
        layout="wide"
    )
    
    # 加载动画 - 使用数据分析相关的动画
    lottie_url = "https://assets9.lottiefiles.com/packages/lf20_qp1q7mct.json"  # 这是一个数据分析动画
    # 备用动画URLs，以防主URL不可用
    backup_urls = [
        "https://assets6.lottiefiles.com/packages/lf20_xyadoh9h.json",  # 备用数据分析动画1
        "https://assets5.lottiefiles.com/packages/lf20_qrf3xad8.json",  # 备用数据分析动画2
        "https://assets7.lottiefiles.com/packages/lf20_dwjqnr8o.json"   # 备用数据分析动画3
    ]
    
    # 尝试加载主动画，如果失败则尝试备用动画
    lottie_json = load_lottie_url(lottie_url)
    if not lottie_json:
        for backup_url in backup_urls:
            lottie_json = load_lottie_url(backup_url)
            if lottie_json:
                break
    
    # 显示欢迎信息
    st.markdown("""
    <style>
    .welcome-header {
        text-align: center;
        color: #1e3d59;
        font-size: 2.5rem;
        margin-bottom: 2rem;
    }
    .welcome-text {
        text-align: center;
        font-size: 1.2rem;
        line-height: 1.6;
        margin-bottom: 2rem;
    }
    .stLottie {
        margin: 0 auto;
        display: block;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="welcome-header">🌟 欢迎使用保险方案生成平台 🌟</h1>', unsafe_allow_html=True)
    
    # 使用列布局来居中显示内容
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # 显示动画，添加更多的自定义选项
        if lottie_json:
            st_lottie(
                lottie_json,
                speed=1,
                reverse=False,
                loop=True,
                quality="low",  # 降低质量以提高性能
                height=300,
                key="welcome_animation"
            )
        else:
            st.warning("⚠️ 动画加载失败，但这不影响系统的使用~")
        
        st.info("""
        👋 亲爱的用户，欢迎来到我们的保险方案生成平台！

        🎯 这是一个充满智慧的小助手，它可以帮您：
        
        📝 轻松管理保险方案
        📚 智能组织条款内容
        🎨 一键生成精美文档
        💾 安全保存项目数据
        
        🌈 让我们开始这段奇妙的旅程吧！
        """)
        
        # 添加一些有趣的统计数据
        st.success("""
        🎉 有趣的小知识：
        
        ⚡ 我们的平台可以在 3 秒内生成一份完整的保险方案
        🎯 支持多种格式的文档导出
        🔄 每 5 分钟自动保存您的工作进度
        """)
        
        # 添加操作提示
        st.warning("""
        💡 小贴士：
        
        1️⃣ 先创建或选择一个项目
        2️⃣ 填写基本信息
        3️⃣ 选择合适的条款
        4️⃣ 一键生成方案
        
        准备好了吗？让我们开始吧！ 🚀
        """)
        
        # 添加进入按钮
        if st.button("🎮 点击进入主程序", key="enter_button"):
            st.session_state.welcome_completed = True
            st.balloons()  # 放飞气球效果
            st.experimental_rerun()

def should_show_welcome():
    """判断是否应该显示欢迎页面"""
    return not st.session_state.get('welcome_completed', False) 