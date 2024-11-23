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
        self.base_dir = base_dir
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        
        if 'last_save_time' not in st.session_state:
            st.session_state.last_save_time = datetime.now()
    
    def create_project(self, name, description=""):
        project_dir = os.path.join(self.base_dir, name)
        if os.path.exists(project_dir):
            raise ValueError(f"项目 '{name}' 已存在")
        
        os.makedirs(project_dir)
        
        config = {
            "name": name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "state": {
                "insurance_data": None,
                "selected_clauses": [],
                "filters": {},
                "search_term": ""
            }
        }
        
        with open(os.path.join(project_dir, 'config.json'), 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        db = Database(os.path.join(project_dir, 'clauses.db'))
        
        return self.load_project(name)
    
    def load_project(self, name):
        project_dir = os.path.join(self.base_dir, name)
        if not os.path.exists(project_dir):
            raise ValueError(f"项目 '{name}' 不存在")
        
        with open(os.path.join(project_dir, 'config.json'), 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        st.session_state.project_name = name
        st.session_state.project_dir = project_dir
        st.session_state.insurance_data = config['state']['insurance_data']
        st.session_state.selected_clauses = config['state']['selected_clauses']
        st.session_state.filters = config['state']['filters']
        st.session_state.search_term = config['state']['search_term']
        st.session_state.db_path = os.path.join(project_dir, 'clauses.db')
        st.session_state.last_save_time = datetime.now()
        
        return os.path.join(project_dir, 'clauses.db')
    
    def save_project(self, name):
        project_dir = os.path.join(self.base_dir, name)
        if not os.path.exists(project_dir):
            raise ValueError(f"项目 '{name}' 不存在")
        
        config_path = os.path.join(project_dir, 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        config['updated_at'] = datetime.now().isoformat()
        config['state'] = {
            'insurance_data': st.session_state.get('insurance_data', None),
            'selected_clauses': st.session_state.get('selected_clauses', []),
            'filters': st.session_state.get('filters', {}),
            'search_term': st.session_state.get('search_term', '')
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        project_data = self.export_project(name)
        
        return project_data
    
    def export_project(self, name):
        project_dir = os.path.join(self.base_dir, name)
        if not os.path.exists(project_dir):
            raise ValueError(f"项目 '{name}' 不存在")
        
        memory_zip = io.BytesIO()
        with zipfile.ZipFile(memory_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            config_path = os.path.join(project_dir, 'config.json')
            zf.write(config_path, 'config.json')
            
            db_path = os.path.join(project_dir, 'clauses.db')
            if os.path.exists(db_path):
                zf.write(db_path, 'clauses.db')
        
        memory_zip.seek(0)
        return memory_zip.getvalue()
    
    def import_project(self, name, project_data):
        project_dir = os.path.join(self.base_dir, name)
        
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
        
        os.makedirs(project_dir)
        
        memory_zip = io.BytesIO(project_data)
        with zipfile.ZipFile(memory_zip, 'r') as zf:
            zf.extractall(project_dir)
        
        return self.load_project(name)

def render_project_manager():
    st.sidebar.title("项目管理")
    
    project_manager = ProjectManager()
    
    if 'last_auto_save' not in st.session_state:
        st.session_state.last_auto_save = datetime.now()
    
    if 'project_name' in st.session_state and st.session_state.project_name is not None:
        now = datetime.now()
        if (now - st.session_state.last_auto_save).total_seconds() > 300:
            project_manager.save_project(st.session_state.project_name)
            st.session_state.last_auto_save = now
            st.sidebar.success("项目已自动保存")
    
    with st.sidebar.expander("新建项目", expanded=False):
        project_name = st.text_input("项目名称")
        project_desc = st.text_area("项目描述")
        if st.button("创建项目"):
            if project_name:
                try:
                    project_manager.create_project(project_name, project_desc)
                    st.success(f"项目 '{project_name}' 创建成功")
                    st.session_state.project_name = project_name
                except ValueError as e:
                    st.error(str(e))
            else:
                st.error("请输入项目名称")
    
    with st.sidebar.expander("导入项目", expanded=False):
        uploaded_file = st.file_uploader("选择项目文件", type=['zip'])
        import_name = st.text_input("项目名称（导入）")
        if uploaded_file is not None and import_name:
            try:
                project_manager.import_project(import_name, uploaded_file.read())
                st.session_state.project_name = import_name
                st.success(f"项目 '{import_name}' 导入成功")
            except ValueError as e:
                st.error(str(e))
    
    if 'project_name' in st.session_state and st.session_state.project_name is not None:
        if st.sidebar.button("手动保存当前项目"):
            project_manager.save_project(st.session_state.project_name)
            st.sidebar.success("项目已手动保存")
    
    if 'project_name' in st.session_state and st.session_state.project_name is not None:
        if st.sidebar.button("导出当前项目"):
            project_data = project_manager.export_project(st.session_state.project_name)
            st.download_button(
                "点击下载项目文件",
                project_data,
                file_name=f"{st.session_state.project_name}.zip",
                mime="application/zip"
            )
    
    if 'show_startup_message' not in st.session_state:
        st.session_state.show_startup_message = True
    
    if st.session_state.show_startup_message:
        st.info("项目文件每隔5分钟自动保存，默认保存在浏览器缓存中。如果导出了项目数据，则将自动保存在选择的导出位置。")
        st.session_state.show_startup_message = False
