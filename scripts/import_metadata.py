#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将MetaData目录中的CSV数据导入到data.db数据库
"""

import sqlite3
import csv
import json
import os
from datetime import datetime, timezone

# 数据库和CSV文件路径
DB_PATH = 'data.db'
METADATA_DIR = 'MetaData'

def get_current_timestamp():
    """获取当前时间戳（ISO格式）"""
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

def import_sectors(cursor):
    """导入Sectors数据"""
    print("\n[1/3] 导入 Sectors...")

    csv_path = os.path.join(METADATA_DIR, 'Sectors.csv')
    if not os.path.exists(csv_path):
        print(f"[WARNING] 文件不存在: {csv_path}")
        return {}

    # 读取CSV数据
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        sectors = list(reader)

    # 创建ID映射（CSV的id -> 数据库的自增id）
    id_map = {}
    timestamp = get_current_timestamp()

    for sector in sectors:
        csv_id = sector['id']
        name = sector['name']
        category = sector.get('category', '')
        description = sector.get('description', '')

        cursor.execute("""
            INSERT INTO sectors (name, category, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (name, category, description, timestamp, timestamp))

        db_id = cursor.lastrowid
        id_map[csv_id] = db_id

    print(f"[OK] 导入 {len(sectors)} 条 Sectors 数据")
    return id_map

def import_organizations(cursor, sector_id_map):
    """导入Organizations数据"""
    print("\n[2/3] 导入 Organizations...")

    csv_path = os.path.join(METADATA_DIR, 'Organizations.csv')
    if not os.path.exists(csv_path):
        print(f"[WARNING] 文件不存在: {csv_path}")
        return {}

    # 读取CSV数据
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        organizations = list(reader)

    # 创建ID映射
    id_map = {}
    timestamp = get_current_timestamp()

    # 第一轮：插入所有组织（不设置父组织）
    for org in organizations:
        csv_id = org['id']
        name = org['name']
        description = org.get('description', '')

        # 映射sector
        sector_csv_id = org.get('tor', '').strip()  # CSV中sector字段名为'tor'
        sector_db_id = sector_id_map.get(sector_csv_id) if sector_csv_id else None

        cursor.execute("""
            INSERT INTO organizations (name, description, sector_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (name, description, sector_db_id, timestamp, timestamp))

        db_id = cursor.lastrowid
        id_map[csv_id] = db_id

    # 第二轮：更新父组织关系
    for org in organizations:
        csv_id = org['id']
        parent_csv_id = org.get('parentOrganization', '').strip()

        if parent_csv_id and parent_csv_id in id_map:
            db_id = id_map[csv_id]
            parent_db_id = id_map[parent_csv_id]

            cursor.execute("""
                UPDATE organizations
                SET parent_organization_id = ?
                WHERE id = ?
            """, (parent_db_id, db_id))

    print(f"[OK] 导入 {len(organizations)} 条 Organizations 数据")
    return id_map

def import_people(cursor, org_id_map):
    """导入People数据"""
    print("\n[3/3] 导入 People...")

    csv_path = os.path.join(METADATA_DIR, 'People.csv')
    if not os.path.exists(csv_path):
        print(f"[WARNING] 文件不存在: {csv_path}")
        return {}

    # 读取CSV数据
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        people = list(reader)

    timestamp = get_current_timestamp()
    count = 0

    for person in people:
        csv_id = person.get('id', '')
        name = person.get('name', '')
        chinese_name = person.get('ChineseName', '')
        date_of_birth = person.get('dateOfBirth', '')
        gender = person.get('gender', '')
        current_role = person.get('currentRole', '')
        education = person.get('education', '')
        career_history = person.get('careerHistory', '')
        bio = person.get('bio', '')
        slug = person.get('slug', '')

        # 映射organization
        org_csv_id = person.get('organization', '').strip()
        org_db_id = org_id_map.get(org_csv_id) if org_csv_id else None

        # party暂时设为NULL（MetaData中没有party数据）
        party_db_id = None

        # 插入people主表
        cursor.execute("""
            INSERT INTO people (
                name, chinese_name, date_of_birth, gender, current_role,
                organization_id, party_id, education, career_history, bio, slug,
                created_at, updated_at, _status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, chinese_name, date_of_birth, gender, current_role,
            org_db_id, party_db_id, education, career_history, bio, slug,
            timestamp, timestamp, 'published'
        ))

        people_id = cursor.lastrowid

        # 插入到_people_v版本表（创建初始版本）
        cursor.execute("""
            INSERT INTO _people_v (
                parent_id,
                version_name, version_chinese_name, version_date_of_birth,
                version_gender, version_current_role, version_organization_id,
                version_party_id, version_education, version_career_history,
                version_bio, version_slug, version_updated_at, version_created_at,
                version__status, created_at, updated_at, latest
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            people_id,
            name, chinese_name, date_of_birth,
            gender, current_role, org_db_id,
            party_db_id, education, career_history,
            bio, slug, timestamp, timestamp,
            'published', timestamp, timestamp, 1
        ))

        version_id = cursor.lastrowid

        # 处理sources（如果有）
        sources_str = person.get('sources', '')
        if sources_str:
            try:
                sources = json.loads(sources_str)
                if isinstance(sources, list):
                    # 为主表添加sources
                    for idx, source in enumerate(sources):
                        source_name = source.get('sourceName', '')
                        source_url = source.get('sourceUrl', '')
                        reliability = source.get('reliability', '')

                        # 生成UUID格式的id (使用people_id确保唯一性)
                        source_id = f"ps-{people_id}-{idx}"

                        cursor.execute("""
                            INSERT INTO people_sources (
                                _order, _parent_id, id, source_name, source_url, reliability
                            )
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (idx, people_id, source_id, source_name, source_url, reliability))

                    # 为版本表添加sources
                    for idx, source in enumerate(sources):
                        source_name = source.get('sourceName', '')
                        source_url = source.get('sourceUrl', '')
                        reliability = source.get('reliability', '')

                        # 生成UUID (使用version_id确保唯一性)
                        cursor.execute("""
                            INSERT INTO _people_v_version_sources (
                                _order, _parent_id, source_name, source_url, reliability, _uuid
                            )
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (idx, version_id, source_name, source_url, reliability, f"pvs-{version_id}-{idx}"))

            except json.JSONDecodeError:
                pass  # 忽略JSON解析错误

        count += 1

    print(f"[OK] 导入 {count} 条 People 数据")
    return {}

def main():
    """主函数"""
    print("=" * 60)
    print("开始导入MetaData到data.db数据库")
    print("=" * 60)

    # 检查数据库文件是否存在
    if not os.path.exists(DB_PATH):
        print(f"\n[ERROR] 数据库文件不存在: {DB_PATH}")
        print("请先确保data.db数据库已创建并包含正确的表结构。")
        return

    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 导入数据
        sector_id_map = import_sectors(cursor)
        org_id_map = import_organizations(cursor, sector_id_map)
        import_people(cursor, org_id_map)

        # 提交事务
        conn.commit()

        print("\n" + "=" * 60)
        print("[SUCCESS] 数据导入完成!")
        print("=" * 60)

        # 显示统计信息
        print("\n数据统计:")
        cursor.execute("SELECT COUNT(*) FROM sectors")
        print(f"  - Sectors: {cursor.fetchone()[0]} 条")

        cursor.execute("SELECT COUNT(*) FROM organizations")
        print(f"  - Organizations: {cursor.fetchone()[0]} 条")

        cursor.execute("SELECT COUNT(*) FROM people")
        print(f"  - People: {cursor.fetchone()[0]} 条")

        cursor.execute("SELECT COUNT(*) FROM people_sources")
        print(f"  - People Sources: {cursor.fetchone()[0]} 条")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] 导入失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
