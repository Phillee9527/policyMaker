import streamlit as st
import os
import json
import shutil
import zipfile
import io
from datetime import datetime
from .database import Database

class ProjectManager:
    def __init__(self, base_dir='projects'):
        """初始化项目管理器"""
        self.base_dir = base_dir
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        
        # 初始化自动保存计时器
        if 'last_save_time' not in st.session_state:
            st.session_state.last_save_time = datetime.now()
    
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
                "insurance_data": None,  # 保单信息
                "selected_clauses": [],  # 已选条款
                "filters": {},           # 筛选条件
                "search_term": ""        # 搜索关键词
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
        st.session_state.insurance_data = config['state']['insurance_data']
        st.session_state.selected_clauses = config['state']['selected_clauses']
        st.session_state.filters = config['state']['filters']
        st.session_state.search_term = config['state']['search_term']
        st.session_state.db_path = os.path.join(project_dir, 'clauses.db')
        st.session_state.last_save_time = datetime.now()
        
        return os.path.join(project_dir, 'clauses.db')
    
    def save_project_state(self, name, force=False):
        """保存项目状态"""
        # 检查是否需要自动保存（每5分钟）
        now = datetime.now()
        if not force and (now - st.session_state.last_save_time).total_seconds() < 300:
            return
        
        project_dir = os.path.join(self.base_dir, name)
        if not os.path.exists(project_dir):
            raise ValueError(f"项目 '{name}' 不存在")
        
        # 读取现有配置
        config_path = os.path.join(project_dir, 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 更新状态
        config['updated_at'] = now.isoformat()
        config['state'] = {
            'insurance_data': st.session_state.get('insurance_data', None),
            'selected_clauses': st.session_state.get('selected_clauses', []),
            'filters': st.session_state.get('filters', {}),
            'search_term': st.session_state.get('search_term', '')
        }
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        # 更新最后保存时间
        st.session_state.last_save_time = now
        
        if force:
            st.success("项目已保存")
    
    def export_project(self, name):
        """导出项目"""
        # 先保存当前状态
        self.save_project_state(name, force=True)
        
        project_dir = os.path.join(self.base_dir, name)
        if not os.path.exists(project_dir):
            raise ValueError(f"项目 '{name}' 不存在")
        
        # 创建内存中的zip文件
        memory_zip = io.BytesIO()
        with zipfile.ZipFile(memory_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 添加配置文件
            config_path = os.path.join(project_dir, 'config.json')
            zf.write(config_path, 'config.json')
            
            # 添加数据库文件
            db_path = os.path.join(project_dir, 'clauses.db')
            if os.path.exists(db_path):
                zf.write(db_path, 'clauses.db')
        
        memory_zip.seek(0)
        return memory_zip.getvalue()
    
    def import_project(self, name, project_data):
        """导入项目"""
        project_dir = os.path.join(self.base_dir, name)
        if os.path.exists(project_dir):
            raise ValueError(f"项目 '{name}' 已存在")
        
        os.makedirs(project_dir)
        
        # 解压项目文件
        memory_zip = io.BytesIO(project_data)
        with zipfile.ZipFile(memory_zip, 'r') as zf:
            zf.extractall(project_dir)
        
        # 加载项目
        return self.load_project(name)
    
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
    
    # 导入项目
    with st.sidebar.expander("导入项目", expanded=False):
        uploaded_file = st.file_uploader("选择项目文件", type=['zip'])
        import_name = st.text_input("项目名称（导入）")
        if uploaded_file is not None and import_name:
            try:
                project_manager.import_project(import_name, uploaded_file.read())
                st.success(f"项目 '{import_name}' 导入成功")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
    
    # 项目列表
    projects = project_manager.list_projects()
    if projects:
        st.sidebar.subheader("现有项目")
        for project in projects:
            col1, col2, col3, col4 = st.sidebar.columns([2, 1, 1, 1])
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
                if st.button("保存", key=f"save_{project['name']}"):
                    try:
                        project_manager.save_project_state(project['name'], force=True)
                    except ValueError as e:
                        st.error(str(e))
            
            with col3:
                if st.button("导出", key=f"export_{project['name']}"):
                    try:
                        project_data = project_manager.export_project(project['name'])
                        st.download_button(
                            "下载项目文件",
                            project_data,
                            file_name=f"{project['name']}.zip",
                            mime="application/zip",
                            key=f"download_{project['name']}"
                        )
                    except ValueError as e:
                        st.error(str(e))
            
            with col4:
                if st.button("删除", key=f"delete_{project['name']}"):
                    try:
                        project_manager.delete_project(project['name'])
                        st.success(f"项目 '{project['name']}' 已删除")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
    else:
        st.sidebar.info("暂无项目，请创建新项目")
    
    # 自动保存当前项目状态
    if 'project_name' in st.session_state:
        project_manager.save_project_state(st.session_state.project_name)
