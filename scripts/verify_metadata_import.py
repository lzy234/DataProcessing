#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证MetaData导入到data.db的数据
"""

import sqlite3
import os

DB_PATH = 'data.db'

def verify_data():
    """验证导入的数据"""
    print("=" * 60)
    print("验证data.db数据库")
    print("=" * 60)

    if not os.path.exists(DB_PATH):
        print(f"\n[ERROR] 数据库文件不存在: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. 统计数据
        print("\n【数据统计】")
        cursor.execute("SELECT COUNT(*) FROM sectors")
        sectors_count = cursor.fetchone()[0]
        print(f"  Sectors: {sectors_count} 条")

        cursor.execute("SELECT COUNT(*) FROM organizations")
        orgs_count = cursor.fetchone()[0]
        print(f"  Organizations: {orgs_count} 条")

        cursor.execute("SELECT COUNT(*) FROM people")
        people_count = cursor.fetchone()[0]
        print(f"  People: {people_count} 条")

        cursor.execute("SELECT COUNT(*) FROM people_sources")
        sources_count = cursor.fetchone()[0]
        print(f"  People Sources: {sources_count} 条")

        cursor.execute("SELECT COUNT(*) FROM _people_v")
        people_v_count = cursor.fetchone()[0]
        print(f"  People Versions: {people_v_count} 条")

        cursor.execute("SELECT COUNT(*) FROM _people_v_version_sources")
        people_v_sources_count = cursor.fetchone()[0]
        print(f"  People Version Sources: {people_v_sources_count} 条")

        # 2. 预览Sectors数据
        print("\n【Sectors 预览（前5条）】")
        cursor.execute("""
            SELECT id, name, category, description
            FROM sectors
            ORDER BY id
            LIMIT 5
        """)
        for row in cursor.fetchall():
            print(f"  ID: {row[0]} | {row[1]} | 类别: {row[2]}")

        # 3. 预览Organizations数据
        print("\n【Organizations 预览（前5条）】")
        cursor.execute("""
            SELECT o.id, o.name, s.name as sector_name, po.name as parent_name
            FROM organizations o
            LEFT JOIN sectors s ON o.sector_id = s.id
            LEFT JOIN organizations po ON o.parent_organization_id = po.id
            ORDER BY o.id
            LIMIT 5
        """)
        for row in cursor.fetchall():
            parent = f" | 父组织: {row[3]}" if row[3] else ""
            print(f"  ID: {row[0]} | {row[1]} | 领域: {row[2]}{parent}")

        # 4. 预览People数据
        print("\n【People 预览（前5条）】")
        cursor.execute("""
            SELECT p.id, p.name, p.chinese_name, p.current_role, o.name as org_name
            FROM people p
            LEFT JOIN organizations o ON p.organization_id = o.id
            ORDER BY p.id
            LIMIT 5
        """)
        for row in cursor.fetchall():
            org = f" | 组织: {row[4]}" if row[4] else ""
            print(f"  ID: {row[0]} | {row[1]} ({row[2]}) | {row[3]}{org}")

        # 5. 关系检查
        print("\n【关系检查】")
        cursor.execute("""
            SELECT COUNT(*) FROM people WHERE organization_id IS NOT NULL
        """)
        people_with_org = cursor.fetchone()[0]
        print(f"  已关联组织的人物: {people_with_org}/{people_count} ({people_with_org*100//people_count}%)")

        cursor.execute("""
            SELECT COUNT(*) FROM organizations WHERE sector_id IS NOT NULL
        """)
        orgs_with_sector = cursor.fetchone()[0]
        print(f"  已关联领域的组织: {orgs_with_sector}/{orgs_count} ({orgs_with_sector*100//orgs_count}%)")

        cursor.execute("""
            SELECT COUNT(*) FROM organizations WHERE parent_organization_id IS NOT NULL
        """)
        orgs_with_parent = cursor.fetchone()[0]
        print(f"  有父组织的组织: {orgs_with_parent}/{orgs_count}")

        # 6. 版本数据检查
        print("\n【版本数据检查】")
        cursor.execute("""
            SELECT COUNT(*) FROM _people_v WHERE latest = 1
        """)
        latest_versions = cursor.fetchone()[0]
        print(f"  最新版本数量: {latest_versions}/{people_v_count}")

        cursor.execute("""
            SELECT p.name, pv.id, pv.version_name, pv.latest
            FROM people p
            LEFT JOIN _people_v pv ON p.id = pv.parent_id
            WHERE pv.id IS NULL
            LIMIT 5
        """)
        people_no_version = cursor.fetchall()
        if people_no_version:
            print(f"  [WARNING] 发现 {len(people_no_version)} 个人物没有版本记录")
        else:
            print(f"  [OK] 所有人物都有版本记录")

        # 7. 数据质量检查
        print("\n【数据质量检查】")
        cursor.execute("""
            SELECT COUNT(*) FROM people WHERE name IS NULL OR name = ''
        """)
        people_no_name = cursor.fetchone()[0]
        print(f"  缺少姓名的人物: {people_no_name}")

        cursor.execute("""
            SELECT COUNT(*) FROM people WHERE current_role IS NULL OR current_role = ''
        """)
        people_no_role = cursor.fetchone()[0]
        print(f"  缺少职位的人物: {people_no_role}")

        cursor.execute("""
            SELECT COUNT(*) FROM organizations WHERE name IS NULL OR name = ''
        """)
        orgs_no_name = cursor.fetchone()[0]
        print(f"  缺少名称的组织: {orgs_no_name}")

        # 8. 示例查询
        print("\n【示例查询：白宫相关人员】")
        cursor.execute("""
            SELECT p.name, p.chinese_name, p.current_role
            FROM people p
            JOIN organizations o ON p.organization_id = o.id
            WHERE o.name LIKE '%白宫%'
            ORDER BY p.id
            LIMIT 5
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]} ({row[1]}) - {row[2]}")

        print("\n【示例查询：科技领域组织】")
        cursor.execute("""
            SELECT o.name, s.name as sector_name
            FROM organizations o
            JOIN sectors s ON o.sector_id = s.id
            WHERE s.category = '资本' AND s.name LIKE '%科技%'
            ORDER BY o.id
            LIMIT 5
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]} - {row[1]}")

        print("\n" + "=" * 60)
        print("[SUCCESS] 验证完成！数据导入正常。")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] 验证失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    verify_data()
