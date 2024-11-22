import os
from datetime import datetime
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import io

# 创建基类
Base = declarative_base()

class Clause(Base):
    """条款模型"""
    __tablename__ = 'clauses'

    id = Column(Integer, primary_key=True)
    uuid = Column(String(50), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    pinyin = Column(String(200))
    quanpin = Column(String(500))
    insurance_type = Column(String(50))
    company = Column(String(100))
    version = Column(String(20))
    version_number = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ClauseVersion(Base):
    """条款版本历史"""
    __tablename__ = 'clause_versions'

    id = Column(Integer, primary_key=True)
    clause_uuid = Column(String(50), nullable=False)
    version_number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Database:
    def __init__(self, db_path='clauses.db'):
        """初始化数据库连接"""
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def import_clauses(self, df):
        """导入条款数据"""
        # 确保DataFrame包含所需的列
        required_columns = ['UUID', '扩展条款标题', '扩展条款正文', 'PINYIN', 'QUANPIN', '险种', '保险公司', '年度版本']
        if not all(col in df.columns for col in required_columns):
            raise ValueError("导入的数据缺少必要的列")

        # 验证UUID不为空且不重复
        if df['UUID'].isnull().any():
            raise ValueError("存在空的UUID")
        if df['UUID'].duplicated().any():
            raise ValueError("存在重复的UUID")

        # 记录新增和更新的条款数量
        new_count = 0
        update_count = 0

        for _, row in df.iterrows():
            uuid = row['UUID']
            existing_clause = self.session.query(Clause).filter_by(uuid=uuid).first()
            
            if existing_clause:
                # 只有当内容有变化时才创建新版本
                if existing_clause.content != row['扩展条款正文']:
                    # 创建新版本记录
                    version = ClauseVersion(
                        clause_uuid=existing_clause.uuid,
                        version_number=existing_clause.version_number + 1,
                        title=existing_clause.title,
                        content=existing_clause.content
                    )
                    self.session.add(version)
                    
                    # 更新条款
                    existing_clause.title = row['扩展条款标题']
                    existing_clause.content = row['扩展条款正文']
                    existing_clause.pinyin = row['PINYIN']
                    existing_clause.quanpin = row['QUANPIN']
                    existing_clause.insurance_type = row['险种']
                    existing_clause.company = row['保险公司']
                    existing_clause.version = row['年度版本']
                    existing_clause.version_number += 1
                    existing_clause.updated_at = datetime.utcnow()
                    update_count += 1
            else:
                # 创建新条款
                new_clause = Clause(
                    uuid=uuid,
                    title=row['扩展条款标题'],
                    content=row['扩展条款正文'],
                    pinyin=row['PINYIN'],
                    quanpin=row['QUANPIN'],
                    insurance_type=row['险种'],
                    company=row['保险公司'],
                    version=row['年度版本']
                )
                self.session.add(new_clause)
                new_count += 1

        self.session.commit()
        return new_count, update_count

    def export_clauses(self, format='dataframe'):
        """导出条款数据"""
        clauses = self.session.query(Clause).filter_by(is_active=True).all()
        data = []
        for i, clause in enumerate(clauses, 1):
            data.append({
                'UUID': clause.uuid,
                '序号': i,
                '扩展条款标题': clause.title,
                '扩展条款正文': clause.content,
                'PINYIN': clause.pinyin,
                'QUANPIN': clause.quanpin,
                '险种': clause.insurance_type,
                '保险公司': clause.company,
                '年度版本': clause.version,
                '版本号': clause.version_number
            })
        df = pd.DataFrame(data)
        
        if format == 'xlsx':
            output = io.BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)
            return output
        elif format == 'json':
            return df.to_json(orient='records', force_ascii=False)
        elif format == 'dataframe':
            return df
        else:
            return df

    def export_selected_clauses(self, clause_uuids, format='docx'):
        """导出选中的条款"""
        clauses = self.session.query(Clause).filter(
            Clause.uuid.in_(clause_uuids),
            Clause.is_active == True
        ).all()
        
        if format == 'xlsx':
            data = []
            for i, clause in enumerate(clauses, 1):
                data.append({
                    '序号': i,
                    '扩展条款标题': clause.title,
                    '扩展条款正文': clause.content,
                    '险种': clause.insurance_type,
                    '保险公司': clause.company,
                    '年度版本': clause.version
                })
            df = pd.DataFrame(data)
            output = io.BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)
            return output
        
        elif format == 'docx':
            from docx import Document
            doc = Document()
            for i, clause in enumerate(clauses, 1):
                doc.add_heading(f"{i}. {clause.title}", level=1)
                doc.add_paragraph(clause.content)
                doc.add_paragraph(f"险种：{clause.insurance_type}")
                doc.add_paragraph(f"保险公司：{clause.company}")
                doc.add_paragraph(f"版本：{clause.version}")
                doc.add_page_break()
            
            output = io.BytesIO()
            doc.save(output)
            output.seek(0)
            return output
        
        elif format == 'markdown':
            content = ""
            for i, clause in enumerate(clauses, 1):
                content += f"# {i}. {clause.title}\n\n"
                content += f"{clause.content}\n\n"
                content += f"险种：{clause.insurance_type}\n\n"
                content += f"保险公司：{clause.company}\n\n"
                content += f"版本：{clause.version}\n\n"
                content += "---\n\n"
            return content

    def update_clause(self, uuid, title=None, content=None):
        """更新条款内容"""
        clause = self.session.query(Clause).filter_by(uuid=uuid).first()
        if clause:
            # 创建新版本记录
            version = ClauseVersion(
                clause_uuid=clause.uuid,
                version_number=clause.version_number + 1,
                title=clause.title,
                content=clause.content
            )
            self.session.add(version)
            
            # 更新条款
            if title:
                clause.title = title
            if content:
                clause.content = content
            clause.version_number += 1
            clause.updated_at = datetime.utcnow()
            self.session.commit()
            return True
        return False

    def get_clause_versions(self, uuid):
        """获取条款的所有版本"""
        versions = self.session.query(ClauseVersion).filter_by(
            clause_uuid=uuid
        ).order_by(ClauseVersion.version_number.desc()).all()
        return versions

    def activate_clause_version(self, uuid, version_number):
        """激活指定版本的条款"""
        version = self.session.query(ClauseVersion).filter_by(
            clause_uuid=uuid,
            version_number=version_number
        ).first()
        
        if version:
            clause = self.session.query(Clause).filter_by(uuid=uuid).first()
            if clause:
                clause.title = version.title
                clause.content = version.content
                clause.version_number = version.version_number
                clause.updated_at = datetime.utcnow()
                self.session.commit()
                return True
        return False

    def clear_database(self):
        """清空数据库"""
        self.session.query(Clause).delete()
        self.session.query(ClauseVersion).delete()
        self.session.commit()

    def export_database(self):
        """导出数据库"""
        if os.path.exists(self.db_path):
            with open(self.db_path, 'rb') as f:
                return f.read()
        return None

    def import_database(self, db_data):
        """导入数据库"""
        try:
            # 先关闭当前会话
            self.session.close()
            
            # 备份现有数据库（如果存在）
            if os.path.exists(self.db_path):
                backup_path = f"{self.db_path}.bak"
                os.rename(self.db_path, backup_path)
            
            # 写入新数据库
            with open(self.db_path, 'wb') as f:
                f.write(db_data)
            
            # 重新创建会话
            self.engine = create_engine(f'sqlite:///{self.db_path}')
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
            
            return True
        except Exception as e:
            print(f"导入数据库失败：{str(e)}")
            # 恢复备份
            if os.path.exists(f"{self.db_path}.bak"):
                if os.path.exists(self.db_path):
                    os.remove(self.db_path)
                os.rename(f"{self.db_path}.bak", self.db_path)
            return False
        finally:
            # 清理备份文件
            if os.path.exists(f"{self.db_path}.bak"):
                os.remove(f"{self.db_path}.bak")

    def __del__(self):
        """关闭数据库连接"""
        self.session.close()