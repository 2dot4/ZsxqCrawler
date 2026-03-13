#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
from typing import Dict, Any, Optional

class DatabasePathManager:
    """数据库路径管理器 - 统一管理所有数据库文件的存储位置"""
    
    def __init__(self, base_dir: str = "output/databases"):
        # 确保使用项目根目录的绝对路径
        if not os.path.isabs(base_dir):
            # 查找项目根目录（包含config.toml的目录）
            current_dir = os.path.abspath(os.getcwd())
            project_root = current_dir

            # 向上查找包含config.toml的目录
            while project_root != os.path.dirname(project_root):
                if os.path.exists(os.path.join(project_root, "config.toml")):
                    break
                project_root = os.path.dirname(project_root)

            self.base_dir = os.path.join(project_root, base_dir)
        else:
            self.base_dir = base_dir

        self._ensure_base_dir()
    
    def _ensure_base_dir(self):
        """确保基础目录存在"""
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir, exist_ok=True)
            print(f"📁 创建数据库目录: {self.base_dir}")
    
    def get_group_dir(self, group_id: str) -> str:
        """获取指定群组的数据库目录"""
        group_dir = os.path.join(self.base_dir, str(group_id))
        if not os.path.exists(group_dir):
            os.makedirs(group_dir, exist_ok=True)
            print(f"📁 创建群组目录: {group_dir}")
        return group_dir

    def get_group_data_dir(self, group_id: str):
        """获取指定群组的数据目录（返回Path对象）"""
        from pathlib import Path
        return Path(self.get_group_dir(group_id))
    
    def get_topics_db_path(self, group_id: str) -> str:
        """获取话题数据库路径"""
        group_dir = self.get_group_dir(group_id)
        return os.path.join(group_dir, f"zsxq_topics_{group_id}.db")
    
    def get_files_db_path(self, group_id: str) -> str:
        """获取文件数据库路径"""
        group_dir = self.get_group_dir(group_id)
        return os.path.join(group_dir, f"zsxq_files_{group_id}.db")
    
    def get_columns_db_path(self, group_id: str) -> str:
        """获取专栏数据库路径"""
        group_dir = self.get_group_dir(group_id)
        return os.path.join(group_dir, f"zsxq_columns_{group_id}.db")
    
    def get_config_db_path(self) -> str:
        """获取配置数据库路径（全局配置，不按群组分）"""
        return os.path.join(self.base_dir, "zsxq_config.db")
    
    def get_main_db_path(self, group_id: str) -> str:
        """获取主数据库路径（兼容旧版本）"""
        return self.get_topics_db_path(group_id)
    
    def list_group_databases(self, group_id: str) -> Dict[str, str]:
        """列出指定群组的所有数据库文件"""
        group_dir = self.get_group_dir(group_id)
        databases = {}
        
        # 话题数据库
        topics_db = self.get_topics_db_path(group_id)
        if os.path.exists(topics_db):
            databases['topics'] = topics_db
        
        # 文件数据库
        files_db = self.get_files_db_path(group_id)
        if os.path.exists(files_db):
            databases['files'] = files_db
        
        return databases
    
    def get_database_info(self, group_id: str) -> Dict[str, Any]:
        """获取数据库信息"""
        databases = self.list_group_databases(group_id)
        info = {
            'group_id': group_id,
            'group_dir': self.get_group_dir(group_id),
            'databases': {}
        }
        
        for db_type, db_path in databases.items():
            if os.path.exists(db_path):
                stat = os.stat(db_path)
                info['databases'][db_type] = {
                    'path': db_path,
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                }
        
        return info
    
    def migrate_old_databases(self, group_id: str, old_paths: Dict[str, str]) -> Dict[str, str]:
        """迁移旧的数据库文件到新的目录结构"""
        migration_results = {}
        
        for db_type, old_path in old_paths.items():
            if not os.path.exists(old_path):
                continue
            
            if db_type == 'topics':
                new_path = self.get_topics_db_path(group_id)
            elif db_type == 'files':
                new_path = self.get_files_db_path(group_id)
            else:
                continue
            
            try:
                # 如果新路径已存在，备份
                if os.path.exists(new_path):
                    backup_path = f"{new_path}.backup"
                    os.rename(new_path, backup_path)
                    print(f"📦 备份现有数据库: {backup_path}")
                
                # 移动文件
                os.rename(old_path, new_path)
                migration_results[db_type] = {
                    'old_path': old_path,
                    'new_path': new_path,
                    'status': 'success'
                }
                print(f"✅ 迁移数据库: {old_path} -> {new_path}")
                
            except Exception as e:
                migration_results[db_type] = {
                    'old_path': old_path,
                    'new_path': new_path,
                    'status': 'failed',
                    'error': str(e)
                }
                print(f"❌ 迁移失败: {old_path} -> {new_path}, 错误: {e}")
        
        return migration_results
    
    def list_all_groups(self) -> list:
        """列出所有存在的群组ID"""
        groups = []
        if not os.path.exists(self.base_dir):
            return groups
        
        for item in os.listdir(self.base_dir):
            item_path = os.path.join(self.base_dir, item)
            if os.path.isdir(item_path) and item.isdigit():  # 群组ID目录
                # 检查是否有数据库文件
                topics_db = self.get_topics_db_path(item)
                if os.path.exists(topics_db):
                    groups.append({
                        'group_id': item,
                        'group_dir': item_path,
                        'topics_db': topics_db
                    })
        
        return groups
    
    def cleanup_empty_dirs(self):
        """清理空的群组目录"""
        if not os.path.exists(self.base_dir):
            return

        for item in os.listdir(self.base_dir):
            item_path = os.path.join(self.base_dir, item)
            if os.path.isdir(item_path) and item.isdigit():  # 群组ID目录
                if not os.listdir(item_path):  # 空目录
                    os.rmdir(item_path)
                    print(f"🗑️ 删除空目录: {item_path}")

# 全局实例
db_path_manager = DatabasePathManager()

def get_db_path_manager() -> DatabasePathManager:
    """获取数据库路径管理器实例"""
    return db_path_manager


def get_root_download_dir() -> str:
    """返回项目根目录下的 download 目录路径（若不存在则创建）"""
    project_root = os.path.abspath(os.path.dirname(__file__))
    root_download_dir = os.path.join(project_root, "download")
    os.makedirs(root_download_dir, exist_ok=True)
    return root_download_dir


def mirror_file_to_root_downloads(source_path: str, filename: Optional[str] = None) -> Optional[str]:
    """将已下载文件复制一份到根目录 download 目录"""
    if not source_path or not os.path.isfile(source_path):
        return None

    target_dir = get_root_download_dir()
    target_name = filename or os.path.basename(source_path)
    dest_path = os.path.join(target_dir, target_name)

    shutil.copy2(source_path, dest_path)
    return dest_path
