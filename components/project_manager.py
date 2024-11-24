import streamlit as st
import os
import json
import shutil
import zipfile
import io
from datetime import datetime
from .database import Database, Base, ClauseVersion
import sqlite3

class ProjectManager:
    def __init__(self, base_dir='projects'):
        self.base_dir = base_dir
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        
        if 'last_save_time' not in st.session_state:
            st.session_state.last_save_time = datetime.now()
    
    def create_project(self, name, description=""):
        """创建项目或打开已存在的项目"""
        project_dir = os.path.join(self.base_dir, name)
        
        # 如果项目已存在
        if os.path.exists(project_dir):
            try:
                # 尝试加载已存在的项目
                self.load_project(name)
                # 更新session state
                st.session_state.project_name = name
                return True, f"项目 '{name}' 已存在，已为您打开"
            except Exception as e:
                return False, f"打开已存在的项目失败: {str(e)}"
        
        try:
            # 创建新项目
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
            
            # 创建数据库并初始化保险方案
            db = Database(os.path.join(project_dir, 'clauses.db'))
            policy = db.create_policy(name, description)
            st.session_state.current_policy_id = policy.id
            
            return True, f"项目 '{name}' 创建成功"
        except Exception as e:
            return False, f"创建项目失败: {str(e)}"
    
    def load_project(self, name):
        """加载项目"""
        project_dir = os.path.join(self.base_dir, name)
        if not os.path.exists(project_dir):
            raise ValueError(f"目 '{name}' 不存在")
        
        # 获取数据库实例
        db = Database(os.path.join(project_dir, 'clauses.db'))
        
        # 加载配置文件
        with open(os.path.join(project_dir, 'config.json'), 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 获取或创建保险方案
        policies = db.session.query(db.InsurancePolicy).all()
        st.write(f"找到的保险方案数量：{len(policies)}")
        
        if policies:
            policy = policies[0]  # 使用第一个保险方案
            st.write(f"使用现有保险方案，ID：{policy.id}")
        else:
            policy = db.create_policy(name, config.get('description', ''))
            st.write(f"创建新保险方案，ID：{policy.id}")
        
        st.session_state.current_policy_id = policy.id
        
        # 获取保险方案关联的条款UUID列表
        clause_uuids = db.get_policy_clause_uuids(policy.id)
        st.write(f"从数据库加载的条款数量：{len(clause_uuids)}")
        
        # 根据UUID列表构建selected_clauses
        updated_selected_clauses = []
        for uuid in clause_uuids:
            # 获取条款的最新版本
            latest_version = db.get_clause_version_by_clause_uuid(uuid)
            if latest_version:
                clause = db.session.query(db.Clause).filter_by(uuid=uuid).first()
                if clause:
                    updated_clause = {
                        'UUID': uuid,
                        '序号': len(updated_selected_clauses) + 1,
                        '扩展条款标题': latest_version.title,
                        '扩展条款正文': latest_version.content,
                        'PINYIN': clause.pinyin,
                        'QUANPIN': clause.quanpin,
                        '险种': clause.insurance_type,
                        '保险公司': clause.company,
                        '年度版本': clause.version,
                        '版本号': latest_version.version_number
                    }
                    updated_selected_clauses.append(updated_clause)
        
        st.write(f"成功加载的条款数量：{len(updated_selected_clauses)}")
        
        # 初始化 version_info
        if 'version_info' not in st.session_state:
            st.session_state.version_info = {}
        
        # 更新 version_info
        for clause in updated_selected_clauses:
            st.session_state.version_info[clause['UUID']] = clause['版本号']
        
        # 更新session state
        st.session_state.project_name = name
        st.session_state.project_dir = project_dir
        st.session_state.insurance_data = config['state']['insurance_data']
        st.session_state.selected_clauses = updated_selected_clauses
        st.session_state.filters = config['state'].get('filters', {})
        st.session_state.search_term = config['state'].get('search_term', '')
        st.session_state.db_path = os.path.join(project_dir, 'clauses.db')
        st.session_state.last_save_time = datetime.now()
        
        # 加载其他信息选项卡配置
        st.session_state.other_info_tabs = config['state'].get('other_info_tabs', [])
        
        # 如果insurance_data存在，确保other_info_data也被加载
        if st.session_state.insurance_data:
            if 'other_info_data' not in st.session_state.insurance_data:
                st.session_state.insurance_data['other_info_data'] = config['state'].get('other_info_data', {})
        
        return os.path.join(project_dir, 'clauses.db')
    
    def save_project(self, name):
        """保存项目"""
        project_dir = os.path.join(self.base_dir, name)
        if not os.path.exists(project_dir):
            raise ValueError(f"项目 '{name}' 不存在")
        
        # 获取数据库实例
        db = Database(os.path.join(project_dir, 'clauses.db'))
        
        # 保存已选条款到数据库
        if 'current_policy_id' in st.session_state:
            clause_uuids = []
            version_info = {}  # 用于存储每个条款的当前版本号
            
            for clause in st.session_state.get('selected_clauses', []):
                clause_uuids.append(clause['UUID'])
                version_info[clause['UUID']] = clause.get('版本号', 1)
            
            db.save_policy_clauses(st.session_state.current_policy_id, clause_uuids)
        
        # 更新配置文件
        config_path = os.path.join(project_dir, 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        config['updated_at'] = datetime.now().isoformat()
        config['state'] = {
            'insurance_data': st.session_state.get('insurance_data', {}),
            'selected_clauses': st.session_state.get('selected_clauses', []),
            'filters': st.session_state.get('filters', {}),
            'search_term': st.session_state.get('search_term', ''),
            'version_info': version_info,
            'other_info_tabs': st.session_state.get('other_info_tabs', []),
            'other_info_data': (st.session_state.get('insurance_data', {}) or {}).get('other_info_data', {})
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        # 导出项目数据
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
        """导入项目"""
        project_dir = os.path.join(self.base_dir, name)
        
        # 如果目录存在，先尝试关闭所有可能的文件句柄
        if os.path.exists(project_dir):
            try:
                # 如果存在数据库连接，先关闭它
                if hasattr(self, 'db') and self.db:
                    self.db.session.close()
                    self.db.engine.dispose()
                
                # 在 Windows 上等待一小段时间以确保文件句柄被释放
                import time
                time.sleep(0.1)
                
                # 使用 force 选项删除目录
                import stat
                def remove_readonly(func, path, excinfo):
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                
                shutil.rmtree(project_dir, onerror=remove_readonly)
            except Exception as e:
                st.error(f"无法删除现有项目目录: {str(e)}")
                return None
        
        try:
            # 创建新的项目目录
            os.makedirs(project_dir)
            
            # 解压项目文件
            memory_zip = io.BytesIO(project_data)
            with zipfile.ZipFile(memory_zip, 'r') as zf:
                zf.extractall(project_dir)
            
            # 处理数据库升级
            db_path = os.path.join(project_dir, 'clauses.db')
            if os.path.exists(db_path):
                # 备份原数据库
                shutil.copy2(db_path, f"{db_path}.bak")
                
                # 创建新数据库
                from .database import Database, Base
                db = Database(db_path)
                Base.metadata.create_all(db.engine)
                
                try:
                    # 迁移数据
                    old_db = sqlite3.connect(f"{db_path}.bak")
                    new_db = sqlite3.connect(db_path)
                    
                    # 复制数据
                    old_db.backup(new_db)
                    
                    # 关闭连接
                    old_db.close()
                    new_db.close()
                    
                    # 删除备份
                    os.remove(f"{db_path}.bak")
                except Exception as e:
                    st.error(f"数据库升级失败: {str(e)}")
                    # 恢复备份
                    if os.path.exists(f"{db_path}.bak"):
                        shutil.copy2(f"{db_path}.bak", db_path)
                        os.remove(f"{db_path}.bak")
            
            # 加载项目
            return self.load_project(name)
        except Exception as e:
            st.error(f"导入项目失败: {str(e)}")
            # 如果导入失败，清理目录
            if os.path.exists(project_dir):
                try:
                    shutil.rmtree(project_dir, onerror=remove_readonly)
                except:
                    pass
            return None

def render_project_manager():
    st.sidebar.title("🗂️ 项目管理")
    
    project_manager = ProjectManager()
    
    if 'last_auto_save' not in st.session_state:
        st.session_state.last_auto_save = datetime.now()
    
    if 'project_name' in st.session_state and st.session_state.project_name is not None:
        now = datetime.now()
        if (now - st.session_state.last_auto_save).total_seconds() > 300:
            project_manager.save_project(st.session_state.project_name)
            st.session_state.last_auto_save = now
            st.sidebar.success("✨ 项目已自动保存")
    
    with st.sidebar.expander("✨ 新建项目", expanded=False):
        project_name = st.text_input("📝 项目名称")
        project_desc = st.text_area("📋 项目描述")
        if st.button("🎯 创建项目"):
            if project_name:
                success, message = project_manager.create_project(project_name, project_desc)
                if success:
                    st.success(f"🎉 {message}")
                    st.session_state.project_name = project_name
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
            else:
                st.error("⚠️ 请输入项目名称")
    
    with st.sidebar.expander("📥 导入项目", expanded=False):
        uploaded_file = st.file_uploader("📂 选择项目文件", type=['zip'])
        import_name = st.text_input("📝 项目名称（导入）")
        if uploaded_file is not None and import_name:
            try:
                project_manager.import_project(import_name, uploaded_file.read())
                st.session_state.project_name = import_name
                st.success(f"🎉 项目 '{import_name}' 导入成功")
            except ValueError as e:
                st.error(f"❌ {str(e)}")
    
    if 'project_name' in st.session_state and st.session_state.project_name is not None:
        if st.sidebar.button("💾 手动保存当前项目"):
            project_manager.save_project(st.session_state.project_name)
            st.sidebar.success("✨ 项目已手动保存")
    
    if 'project_name' in st.session_state and st.session_state.project_name is not None:
        if st.sidebar.button("📤 导出当前项目"):
            project_data = project_manager.export_project(st.session_state.project_name)
            st.download_button(
                "⬇️ 点击下载项目文件",
                project_data,
                file_name=f"{st.session_state.project_name}.zip",
                mime="application/zip"
            )
    
    if 'show_startup_message' not in st.session_state:
        st.session_state.show_startup_message = True
    
    if st.session_state.show_startup_message:
        st.info("💡 项目文件每隔5分钟自动保存，默认保存在浏览器缓存中。如果导出了项目数据，则将自动保存在选择的导出位置。")
        st.session_state.show_startup_message = False
