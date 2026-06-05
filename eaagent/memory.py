"""
SQLite 持久化 Memory 模块（A计划）
支持 GitHub CI，完全基于标准库 sqlite3
"""

import os
import sqlite3
from datetime import datetime
from typing import Dict, Optional, List


class MemoryManager:
    def __init__(self, db_file: str = "eaagent_memory.db"):
        self.db_file = db_file
        self.conn = sqlite3.connect(db_file)
        self._create_table()

    def _create_table(self):
        """创建记忆表"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def remember(self, key: str, value: str):
        """记住或更新一条记忆"""
        now = datetime.now().isoformat()
        self.conn.execute("""
            INSERT INTO memory (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET 
                value = excluded.value,
                updated_at = excluded.updated_at
        """, (key, value, now))
        self.conn.commit()
        print(f"[Memory] 已记住: {key} = {value}")

    def recall(self, key: str = None) -> Dict[str, str] | str:
        """取出记忆"""
        if key:
            cursor = self.conn.execute("SELECT value FROM memory WHERE key=?", (key,))
            row = cursor.fetchone()
            return row[0] if row else ""
        else:
            cursor = self.conn.execute("SELECT key, value FROM memory")
            return {row[0]: row[1] for row in cursor.fetchall()}

    def list_all(self) -> List[Dict]:
        """列出所有记忆"""
        cursor = self.conn.execute("""
            SELECT key, value, updated_at 
            FROM memory 
            ORDER BY updated_at DESC
        """)
        return [
            {"key": row[0], "value": row[1], "updated_at": row[2]}
            for row in cursor.fetchall()
        ]

    def clear(self):
        """清空所有记忆"""
        self.conn.execute("DELETE FROM memory")
        self.conn.commit()
        print("[Memory] 已清空所有记忆")

    def close(self):
        self.conn.close()


# 全局单例
memory_manager = MemoryManager()
