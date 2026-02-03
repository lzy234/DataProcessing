#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清空data.db中从MetaData导入的数据
"""

import sqlite3
import os

DB_PATH = 'data.db'

def clear_data():
    """清空导入的数据"""
    print("=" * 60)
    print("清空data.db中的MetaData数据")
    print("=" * 60)

    if not os.path.exists(DB_PATH):
        print(f"\n[ERROR] 数据库文件不存在: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 先显示当前数据量
        print("\n【清空前的数据统计】")
        cursor.execute("SELECT COUNT(*) FROM sectors")
        print(f"  Sectors: {cursor.fetchone()[0]} 条")

        cursor.execute("SELECT COUNT(*) FROM organizations")
        print(f"  Organizations: {cursor.fetchone()[0]} 条")

        cursor.execute("SELECT COUNT(*) FROM people")
        print(f"  People: {cursor.fetchone()[0]} 条")

        cursor.execute("SELECT COUNT(*) FROM people_sources")
        print(f"  People Sources: {cursor.fetchone()[0]} 条")

        cursor.execute("SELECT COUNT(*) FROM _people_v")
        print(f"  People Versions: {cursor.fetchone()[0]} 条")

        cursor.execute("SELECT COUNT(*) FROM _people_v_version_sources")
        print(f"  People Version Sources: {cursor.fetchone()[0]} 条")

        # 确认清空
        print("\n准备清空以下表的数据：")
        print("  - _people_v_version_sources (人物版本来源)")
        print("  - _people_v (人物版本)")
        print("  - people_sources (人物来源)")
        print("  - people (人物)")
        print("  - organizations (组织)")
        print("  - sectors (领域)")

        # 按照外键依赖顺序删除
        print("\n开始清空数据...")

        # 1. 删除people相关的版本数据
        cursor.execute("DELETE FROM _people_v_version_sources")
        cursor.execute("DELETE FROM _people_v")
        print("  [OK] 清空 _people_v 相关表")

        # 2. 删除people相关的关系数据
        cursor.execute("DELETE FROM people_rels")
        cursor.execute("DELETE FROM people_sources")
        print("  [OK] 清空 people 关系表")

        # 3. 删除people主表
        cursor.execute("DELETE FROM people")
        print("  [OK] 清空 people 主表")

        # 4. 删除organizations
        cursor.execute("DELETE FROM organizations")
        print("  [OK] 清空 organizations 表")

        # 5. 删除sectors
        cursor.execute("DELETE FROM sectors")
        print("  [OK] 清空 sectors 表")

        # 重置自增ID（如果sqlite_sequence表存在）
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'")
        if cursor.fetchone():
            cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('people', 'organizations', 'sectors', '_people_v', '_people_v_version_sources')")
            print("  [OK] 重置自增ID")

        # 提交事务
        conn.commit()

        # 显示清空后的数据量
        print("\n【清空后的数据统计】")
        cursor.execute("SELECT COUNT(*) FROM sectors")
        print(f"  Sectors: {cursor.fetchone()[0]} 条")

        cursor.execute("SELECT COUNT(*) FROM organizations")
        print(f"  Organizations: {cursor.fetchone()[0]} 条")

        cursor.execute("SELECT COUNT(*) FROM people")
        print(f"  People: {cursor.fetchone()[0]} 条")

        print("\n" + "=" * 60)
        print("[SUCCESS] 数据清空完成！")
        print("=" * 60)

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] 清空失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    clear_data()
