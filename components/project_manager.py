import streamlit as st
import os
import json
import shutil
from datetime import datetime
from .database import Database

class ProjectManager:
    def __init__(self, base_dir='projects'):
        """初始化项目管理器"""
        self.base_dir = base_dir
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
    
    def create_project(self, name, description=""):
        """创建新项目"""
        # 创建项目目录
        project_dir = os.path.join(self.base_dir, name)
        if os.path.exists(project_dir):
            raise ValueError(f"项目 '{name}' 已存在")
        
        os.makedirs(project_dir)
        
        # 创建项目配置文件
        config = {
            "name": name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "state": {
                "selected_clauses": [],
                "filters": {},
                "search_term": ""
            }
        }
        
        with open(os.path.join(project_dir, 'config.json'), 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        # 创建项目数据库
        db = Database(os.path.join(project_dir, 'clauses.db'))
        return project_dir
    
    def load_project(self, name):
        """加载项目"""
        project_dir = os.path.join(self.base_dir, name)
        if not os.path.exists(project_dir):
            raise ValueError(f"项目 '{name}' 不存在")
        
        # 加载项目配置
        with open(os.path.join(project_dir, 'config.json'), 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 更新session state
        st.session_state.project_name = name
        st.session_state.project_dir = project_dir
        st.session_state.selected_clauses = config['state']['selected_clauses']
        st.session_state.filters = config['state']['filters']
        st.session_state.search_term = config['state']['search_term']
        
        # 返回项目数据库路径
        return os.path.join(project_dir, 'clauses.db')
    
    def save_project_state(self, name):
        """保存项目状态"""
        project_dir = os.path.join(self.base_dir, name)
        if not os.path.exists(project_dir):
            raise ValueError(f"项目 '{name}' 不存在")
        
        # 读取现有配置
        config_path = os.path.join(project_dir, 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 更新状态
        config['updated_at'] = datetime.now().isoformat()
        config['state'] = {
            'selected_clauses': st.session_state.get('selected_clauses', []),
            'filters': st.session_state.get('filters', {}),
            'search_term': st.session_state.get('search_term', '')
        }
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def delete_project(self, name):
        """删除项目"""
        project_dir = os.path.join(self.base_dir, name)
        if not os.path.exists(project_dir):
            raise ValueError(f"项目 '{name}' 不存在")
        
        shutil.rmtree(project_dir)
    
    def list_projects(self):
        """列出所有项目"""
        if not os.path.exists(self.base_dir):
            return []
        
        projects = []
        for name in os.listdir(self.base_dir):
            project_dir = os.path.join(self.base_dir, name)
            if os.path.isdir(project_dir):
                config_path = os.path.join(project_dir, 'config.json')
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    projects.append(config)
        
        return sorted(projects, key=lambda x: x['updated_at'], reverse=True)

def render_project_manager():
    """渲染项目管理界面"""
    st.sidebar.title("项目管理")
    
    # 初始化项目管理器
    project_manager = ProjectManager()
    
    # 新建项目
    with st.sidebar.expander("新建项目", expanded=False):
        project_name = st.text_input("项目名称")
        project_desc = st.text_area("项目描述")
        if st.button("创建项目"):
            if project_name:
                try:
                    project_manager.create_project(project_name, project_desc)
                    st.success(f"项目 '{project_name}' 创建成功")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
            else:
                st.error("请输入项目名称")
    
    # 项目列表
    projects = project_manager.list_projects()
    if projects:
        st.sidebar.subheader("现有项目")
        for project in projects:
            col1, col2 = st.sidebar.columns([3, 1])
            with col1:
                if st.button(
                    project['name'],
                    key=f"load_{project['name']}",
                    help=f"最后更新: {datetime.fromisoformat(project['updated_at']).strftime('%Y-%m-%d %H:%M')}\n\n{project['description']}"
                ):
                    try:
                        db_path = project_manager.load_project(project['name'])
                        st.session_state.db_path = db_path
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
            
            with col2:
                if st.button("删除", key=f"delete_{project['name']}"):
                    try:
                        project_manager.delete_project(project['name'])
                        st.success(f"项目 '{project['name']}' 已删除")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
    else:
        st.sidebar.info("暂无项目，请创建新项目")
    
    # 保存当前项目状态
    if 'project_name' in st.session_state:
        project_manager.save_project_state(st.session_state.project_name)
