import os
from datetime import datetime
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json

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
        for _, row in df.iterrows():
            clause = Clause(
                uuid=row['UUID'],
                title=row['扩展条款标题'],
                content=row['扩展条款正文'],
                pinyin=row['PINYIN'],
                quanpin=row['QUANPIN'],
                insurance_type=row['险种'],
                company=row['保险公司'],
                version=row['年度版本']
            )
            existing_clause = self.session.query(Clause).filter_by(uuid=row['UUID']).first()
            if existing_clause:
                # 创建新版本
                version = ClauseVersion(
                    clause_uuid=existing_clause.uuid,
                    version_number=existing_clause.version_number + 1,
                    title=existing_clause.title,
                    content=existing_clause.content
                )
                self.session.add(version)
                # 更新现有条款
                existing_clause.title = row['扩展条款标题']
                existing_clause.content = row['扩展条款正文']
                existing_clause.version_number += 1
                existing_clause.updated_at = datetime.utcnow()
            else:
                self.session.add(clause)
        self.session.commit()

    def export_clauses(self, format='xlsx'):
        """导出条款数据"""
        clauses = self.session.query(Clause).filter_by(is_active=True).all()
        data = []
        for clause in clauses:
            data.append({
                'UUID': clause.uuid,
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
            for clause in clauses:
                data.append({
                    'UUID': clause.uuid,
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
            for clause in clauses:
                doc.add_heading(clause.title, level=1)
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
            for clause in clauses:
                content += f"# {clause.title}\n\n"
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
            with open(self.db_path, 'wb') as f:
                f.write(db_data)
            return True
        except Exception as e:
            print(f"导入数据库失败：{str(e)}")
            return False

    def __del__(self):
        """关闭数据库连接"""
        self.session.close()
