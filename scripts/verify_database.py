"""
验证SQLite数据库内容
"""
import sqlite3

DB_PATH = "nexus.db"

def verify_database():
    """验证数据库内容"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 60)
    print("数据库验证报告")
    print("=" * 60)

    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()

    print(f"\n[数据表] 共 {len(tables)} 个表:")
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  - {table_name}: {count} 条记录")

    # 详细查看各表数据
    print("\n" + "=" * 60)
    print("详细数据预览")
    print("=" * 60)

    # Sectors
    print("\n[Sectors 表]")
    cursor.execute("SELECT id, name, category FROM sectors LIMIT 5")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} ({row[2]})")

    # Organizations
    print("\n[Organizations 表]")
    cursor.execute("""
        SELECT o.id, o.name, s.name as sector
        FROM organizations o
        LEFT JOIN sectors s ON o.sector = s.id
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} - {row[2]}")

    # People
    print("\n[People 表]")
    cursor.execute("""
        SELECT p.id, p.name, p.ChineseName, p.currentRole, o.name as org, pa.name as party
        FROM people p
        LEFT JOIN organizations o ON p.organization = o.id
        LEFT JOIN parties pa ON p.party = pa.id
        LIMIT 5
    """)
    for row in cursor.fetchall():
        org = row[4] if row[4] else "无"
        party = row[5] if row[5] else "无"
        print(f"  {row[0]}: {row[1]} ({row[2]}) - {row[3]}")
        print(f"      组织: {org}, 政党: {party}")

    # 检查关系
    print("\n" + "=" * 60)
    print("关系检查")
    print("=" * 60)

    # 有组织的人数
    cursor.execute("SELECT COUNT(*) FROM people WHERE organization IS NOT NULL")
    count = cursor.fetchone()[0]
    print(f"\n关联了组织的人物: {count} 人")

    # 有政党的人数
    cursor.execute("SELECT COUNT(*) FROM people WHERE party IS NOT NULL")
    count = cursor.fetchone()[0]
    print(f"关联了政党的人物: {count} 人")

    # 组织层级
    cursor.execute("SELECT COUNT(*) FROM organizations WHERE parentOrganization IS NOT NULL")
    count = cursor.fetchone()[0]
    print(f"有上级组织的组织: {count} 个")

    # 检查空值
    print("\n" + "=" * 60)
    print("数据质量检查")
    print("=" * 60)

    # People表空字段统计
    cursor.execute("SELECT COUNT(*) FROM people WHERE ChineseName IS NULL OR ChineseName = ''")
    count = cursor.fetchone()[0]
    print(f"\nPeople表缺少中文名: {count} 条")

    cursor.execute("SELECT COUNT(*) FROM people WHERE dateOfBirth IS NULL OR dateOfBirth = ''")
    count = cursor.fetchone()[0]
    print(f"People表缺少出生日期: {count} 条")

    cursor.execute("SELECT COUNT(*) FROM people WHERE education IS NULL OR education = ''")
    count = cursor.fetchone()[0]
    print(f"People表缺少教育背景: {count} 条")

    # Organizations表缺少sector的记录
    cursor.execute("SELECT name FROM organizations WHERE sector IS NULL")
    orgs = cursor.fetchall()
    if orgs:
        print(f"\n[WARNING] Organizations表缺少sector的记录 ({len(orgs)} 条):")
        for org in orgs[:10]:  # 最多显示10条
            print(f"  - {org[0]}")

    conn.close()

    print("\n" + "=" * 60)
    print("验证完成")
    print("=" * 60)

if __name__ == "__main__":
    verify_database()
