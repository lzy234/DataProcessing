"""
使用MetaData目录下的CSV文件重新构建SQLite数据库
"""
import sqlite3
import csv
import os
from datetime import datetime
from pathlib import Path

# 数据库文件路径
DB_PATH = "nexus.db"
METADATA_DIR = Path("MetaData")

def create_database():
    """创建数据库表结构"""
    # 如果数据库已存在，先删除
    if os.path.exists(DB_PATH):
        print(f"[INFO] 删除现有数据库: {DB_PATH}")
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Sectors 表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sectors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        description TEXT,
        updatedAt TEXT NOT NULL,
        createdAt TEXT NOT NULL
    )
    """)

    # 2. Parties 表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        abbreviation TEXT,
        color TEXT NOT NULL,
        updatedAt TEXT NOT NULL,
        createdAt TEXT NOT NULL
    )
    """)

    # 3. Organizations 表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS organizations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        parentOrganization INTEGER,
        sector INTEGER NOT NULL,
        description TEXT,
        updatedAt TEXT NOT NULL,
        createdAt TEXT NOT NULL,
        FOREIGN KEY (parentOrganization) REFERENCES organizations(id),
        FOREIGN KEY (sector) REFERENCES sectors(id)
    )
    """)

    # 4. Tags 表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        updatedAt TEXT NOT NULL,
        createdAt TEXT NOT NULL
    )
    """)

    # 5. Media 表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS media (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alt TEXT,
        caption TEXT,
        url TEXT,
        filename TEXT,
        mimeType TEXT,
        filesize INTEGER,
        width INTEGER,
        height INTEGER,
        updatedAt TEXT NOT NULL,
        createdAt TEXT NOT NULL
    )
    """)

    # 6. People 表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS people (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        avatar INTEGER,
        name TEXT NOT NULL,
        ChineseName TEXT,
        dateOfBirth TEXT,
        gender TEXT,
        currentRole TEXT NOT NULL,
        organization INTEGER,
        party INTEGER,
        education TEXT,
        careerHistory TEXT,
        slug TEXT,
        bio TEXT,
        sources TEXT,
        _status TEXT DEFAULT 'published',
        updatedAt TEXT NOT NULL,
        createdAt TEXT NOT NULL,
        FOREIGN KEY (avatar) REFERENCES media(id),
        FOREIGN KEY (organization) REFERENCES organizations(id),
        FOREIGN KEY (party) REFERENCES parties(id)
    )
    """)

    # 7. People_rels 关系表（用于多对多关系，如 specialTags）
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS people_rels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_id INTEGER NOT NULL,
        path TEXT NOT NULL,
        tags_id INTEGER,
        FOREIGN KEY (parent_id) REFERENCES people(id),
        FOREIGN KEY (tags_id) REFERENCES tags(id)
    )
    """)

    # 8. Connections 表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS connections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_relationTo TEXT NOT NULL,
        source_value INTEGER NOT NULL,
        target_relationTo TEXT NOT NULL,
        target_value INTEGER NOT NULL,
        description TEXT,
        updatedAt TEXT NOT NULL,
        createdAt TEXT NOT NULL
    )
    """)

    # 9. Users 表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        username TEXT NOT NULL UNIQUE,
        email TEXT UNIQUE,
        password TEXT NOT NULL,
        updatedAt TEXT NOT NULL,
        createdAt TEXT NOT NULL
    )
    """)

    # 创建索引提升查询性能
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_people_slug ON people(slug)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_people_organization ON people(organization)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_people_party ON people(party)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_organizations_sector ON organizations(sector)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_connections_source ON connections(source_relationTo, source_value)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_connections_target ON connections(target_relationTo, target_value)")

    conn.commit()
    print("[OK] 数据库表结构创建完成")
    return conn

def get_timestamp():
    """获取ISO格式时间戳"""
    return datetime.now().isoformat() + "Z"

def import_sectors(conn):
    """导入Sectors数据"""
    cursor = conn.cursor()
    timestamp = get_timestamp()

    # 映射：原始ID -> 数据库ID
    id_map = {}

    csv_path = METADATA_DIR / "Sectors.csv"
    if not csv_path.exists():
        print(f"[WARNING] 文件不存在: {csv_path}")
        return id_map

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute("""
                INSERT INTO sectors (name, category, description, updatedAt, createdAt)
                VALUES (?, ?, ?, ?, ?)
            """, (
                row['name'],
                row.get('category', ''),
                row.get('description', ''),
                timestamp,
                timestamp
            ))

            id_map[row['id']] = cursor.lastrowid

    conn.commit()
    print(f"[OK] 导入 {len(id_map)} 条 Sectors 数据")
    return id_map

def import_organizations(conn, sector_map):
    """导入Organizations数据"""
    cursor = conn.cursor()
    timestamp = get_timestamp()

    id_map = {}

    csv_path = METADATA_DIR / "Organizations.csv"
    if not csv_path.exists():
        print(f"[WARNING] 文件不存在: {csv_path}")
        return id_map

    # 第一轮：导入所有组织（parentOrganization暂时为NULL）
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

        for row in rows:
            sector_id = sector_map.get(row['sector'])
            if not sector_id:
                print(f"[WARNING] 组织 {row['name']} 的sector {row['sector']} 未找到，跳过")
                continue

            cursor.execute("""
                INSERT INTO organizations (name, sector, description, updatedAt, createdAt)
                VALUES (?, ?, ?, ?, ?)
            """, (
                row['name'],
                sector_id,
                row.get('description', ''),
                timestamp,
                timestamp
            ))

            id_map[row['id']] = cursor.lastrowid

    # 第二轮：更新parentOrganization关系
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('parentOrganization'):
                parent_id = id_map.get(row['parentOrganization'])
                child_id = id_map.get(row['id'])

                if parent_id and child_id:
                    cursor.execute("""
                        UPDATE organizations SET parentOrganization = ? WHERE id = ?
                    """, (parent_id, child_id))

    conn.commit()
    print(f"[OK] 导入 {len(id_map)} 条 Organizations 数据")
    return id_map

def import_people(conn, org_map):
    """导入People数据"""
    cursor = conn.cursor()
    timestamp = get_timestamp()

    id_map = {}

    csv_path = METADATA_DIR / "People.csv"
    if not csv_path.exists():
        print(f"[WARNING] 文件不存在: {csv_path}")
        return id_map

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 处理关系字段
            org_id = org_map.get(row.get('organization', '')) if row.get('organization') else None

            # 处理sources字段
            sources = row.get('sources', '')

            cursor.execute("""
                INSERT INTO people (
                    name, ChineseName, dateOfBirth, gender, currentRole,
                    organization, party, education, careerHistory, slug, bio,
                    sources, _status, updatedAt, createdAt
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['name'],
                row.get('ChineseName', ''),
                row.get('dateOfBirth', ''),
                row.get('gender', ''),
                row.get('currentRole', ''),
                org_id,
                None,  # party field (not in current CSV)
                row.get('education', ''),
                row.get('careerHistory', ''),
                row.get('slug', ''),
                row.get('bio', ''),
                sources,
                'published',
                timestamp,
                timestamp
            ))

            id_map[row['id']] = cursor.lastrowid

    conn.commit()
    print(f"[OK] 导入 {len(id_map)} 条 People 数据")
    return id_map

def create_default_user(conn):
    """创建默认管理员用户"""
    cursor = conn.cursor()
    timestamp = get_timestamp()

    # 检查是否已存在用户
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        print("[OK] 用户已存在，跳过创建")
        return

    # 注意：这里的密码需要使用bcrypt加密
    # 临时使用占位符，实际使用时需要加密
    cursor.execute("""
        INSERT INTO users (name, username, email, password, updatedAt, createdAt)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "管理员",
        "admin",
        "admin@nexus.local",
        "$2a$10$placeholder_hash_replace_with_real_bcrypt_hash",
        timestamp,
        timestamp
    ))

    conn.commit()
    print("[OK] 创建默认管理员用户（密码需要手动加密）")

def verify_database(conn):
    """验证数据库内容"""
    cursor = conn.cursor()

    print("\n" + "=" * 50)
    print("数据库内容验证")
    print("=" * 50)

    tables = ['sectors', 'organizations', 'people', 'users']

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table.ljust(20)}: {count} 条记录")

    # 显示部分数据示例
    print("\n" + "=" * 50)
    print("数据示例（前3条People记录）")
    print("=" * 50)

    cursor.execute("""
        SELECT p.id, p.name, p.ChineseName, o.name as org_name
        FROM people p
        LEFT JOIN organizations o ON p.organization = o.id
        LIMIT 3
    """)

    for row in cursor.fetchall():
        print(f"ID: {row[0]}, Name: {row[1]}, Chinese: {row[2]}, Org: {row[3]}")

def main():
    """主函数"""
    print("=" * 50)
    print("使用MetaData重新构建SQLite数据库")
    print("=" * 50)

    # 创建数据库
    print("\n[1/5] 创建数据库表结构...")
    conn = create_database()

    # 按依赖顺序导入数据
    print("\n[2/5] 导入 Sectors...")
    sector_map = import_sectors(conn)

    print("\n[3/5] 导入 Organizations...")
    org_map = import_organizations(conn, sector_map)

    print("\n[4/5] 导入 People...")
    people_map = import_people(conn, org_map)

    print("\n[5/5] 创建默认用户...")
    create_default_user(conn)

    # 验证数据库
    verify_database(conn)

    # 关闭连接
    conn.close()

    print("\n" + "=" * 50)
    print(f"[DONE] 数据库重建完成: {DB_PATH}")
    print("=" * 50)
    print("\n统计信息:")
    print(f"  - Sectors: {len(sector_map)} 条")
    print(f"  - Organizations: {len(org_map)} 条")
    print(f"  - People: {len(people_map)} 条")
    print("\n[NOTE] 注意:")
    print("  1. 数据库已使用MetaData目录下的数据重建")
    print("  2. 旧数据库已被删除")
    print("  3. 用户密码需要手动更新为bcrypt加密值")

if __name__ == "__main__":
    main()
