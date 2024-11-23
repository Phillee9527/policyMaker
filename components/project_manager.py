import streamlit as st
import os
import json
import shutil
import zipfile
import io
from datetime import datetime
import uuid
import pandas as pd
from .database import Database

def handle_project_action(action, project_name, project_manager):
    """处理项目操作"""
    try:
        if action == 'load':
            db_path = project_manager.load_project(project_name)
            st.session_state.db_path = db_path
            st.rerun()
        
        elif action == 'save':
            # 让用户选择保存位置
            project_data = project_manager.save_project(project_name)
            st.download_button(
                "点击下载项目文件",
                project_data,
                file_name=f"{project_name}.zip",
                mime="application/zip",
                key=f"save_{project_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
            st.success("项目已保存")
        
        elif action == 'export':
            # 导出项目到用户选择的位置
            project_data = project_manager.export_project(project_name)
            st.download_button(
                "点击下载项目文件",
                project_data,
                file_name=f"{project_name}.zip",
                mime="application/zip",
                key=f"export_{project_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
        
        elif action == 'delete':
            if st.session_state.get('confirm_delete') == project_name:
                project_manager.delete_project(project_name)
                st.session_state.pop('confirm_delete', None)
                st.success("项目已删除")
                st.rerun()
            else:
                st.session_state.confirm_delete = project_name
                st.warning("确定要删除当前项目吗？再次点击删除按钮确认。")
    
    except Exception as e:
        st.error(str(e))

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
        
        # 自动加载新创建的项目
        return self.load_project(name)
    
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
    
    def save_project(self, name):
        """保存项目"""
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
            'insurance_data': st.session_state.get('insurance_data', None),
            'selected_clauses': st.session_state.get('selected_clauses', []),
            'filters': st.session_state.get('filters', {}),
            'search_term': st.session_state.get('search_term', '')
        }
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        # 创建项目文件
        project_data = self.export_project(name)
        
        return project_data
    
    def export_project(self, name):
        """导出项目"""
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
        
        # 如果删除的是当前项目，清除session state
        if st.session_state.get('project_name') == name:
            st.session_state.pop('project_name', None)
            st.session_state.pop('project_dir', None)
            st.session_state.pop('db_path', None)
            st.session_state.pop('insurance_data', None)
            st.session_state.pop('selected_clauses', None)
            st.session_state.pop('filters', None)
            st.session_state.pop('search_term', None)
    
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
        st.sidebar.subheader("项目列表")
        
        # 创建项目数据表格
        data = []
        for project in projects:
            data.append({
                "项目名称": project['name'],
                "描述": project['description'],
                "最后更新": datetime.fromisoformat(project['updated_at']).strftime('%Y-%m-%d %H:%M'),
                "操作": "选择"
            })
        
        # 显示项目表格
        edited_df = st.sidebar.data_editor(
            pd.DataFrame(data),
            hide_index=True,
            use_container_width=True,
            column_config={
                "项目名称": st.column_config.TextColumn(
                    "项目名称",
                    width="medium"
                ),
                "描述": st.column_config.TextColumn(
                    "描述",
                    width="medium"
                ),
                "最后更新": st.column_config.TextColumn(
                    "最后更新",
                    width="small"
                ),
                "操作": st.column_config.SelectboxColumn(
                    "操作",
                    help="选择操作",
                    width="small",
                    options=["选择", "保存", "导出", "删除"]
                )
            }
        )
        
        # 处理表格操作
        if edited_df is not None and len(edited_df) > 0:
            for idx, row in edited_df.iterrows():
                project_name = row["项目名称"]
                action = row["操作"]
                
                if action != "选择":
                    handle_project_action(action.lower(), project_name, project_manager)
                    # 重置操作
                    edited_df.at[idx, "操作"] = "选择"
                    st.rerun()
                
                # 如果是当前项目，高亮显示
                if project_name == st.session_state.get('project_name'):
                    edited_df.at[idx, "项目名称"] = f"**{project_name}**"
        
        # 显示当前项目信息
        if 'project_name' in st.session_state:
            st.sidebar.markdown("---")
            st.sidebar.markdown(f"**当前项目：** {st.session_state.project_name}")
            current_project = next((p for p in projects if p['name'] == st.session_state.project_name), None)
            if current_project:
                st.sidebar.markdown(f"**描述：** {current_project['description']}")
                st.sidebar.markdown(f"**最后更新：** {datetime.fromisoformat(current_project['updated_at']).strftime('%Y-%m-%d %H:%M')}")
    else:
        st.sidebar.info("暂无项目，请创建新项目")
