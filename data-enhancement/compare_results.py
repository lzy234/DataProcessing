"""
对比增强前后的数据变化
"""

import csv
from typing import Dict, List

def compare_csv_files(original_file: str, enhanced_file: str, key_field: str = 'id'):
    """对比原始和增强后的CSV文件"""

    # 读取原始文件
    with open(original_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        original_data = {row[key_field]: row for row in reader}

    # 读取增强文件
    with open(enhanced_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        enhanced_data = {row[key_field]: row for row in reader}

    return original_data, enhanced_data

def show_changes(file_name: str, original_file: str, enhanced_file: str,
                 focus_fields: List[str], key_field: str = 'id'):
    """显示指定字段的变化"""

    print(f"\n{'='*80}")
    print(f"对比文件: {file_name}")
    print(f"{'='*80}")

    original_data, enhanced_data = compare_csv_files(original_file, enhanced_file, key_field)

    changes = []

    for record_id, enhanced_row in enhanced_data.items():
        original_row = original_data.get(record_id, {})

        for field in focus_fields:
            original_value = original_row.get(field, '').strip()
            enhanced_value = enhanced_row.get(field, '').strip()

            # 如果原始为空，增强后有值，则记录变化
            if not original_value and enhanced_value:
                name = enhanced_row.get('name', record_id)
                changes.append({
                    'id': record_id,
                    'name': name,
                    'field': field,
                    'old': original_value or '(空)',
                    'new': enhanced_value
                })

    if changes:
        print(f"\n发现 {len(changes)} 处改进:\n")

        for change in changes:
            print(f"  [{change['id']}] {change['name']}")
            print(f"    字段: {change['field']}")
            print(f"    变化: {change['old']} -> {change['new']}")
            print()
    else:
        print("\n未发现变化")

    return len(changes)

def main():
    print("="*80)
    print("数据增强对比报告")
    print("="*80)

    total_changes = 0

    # 对比Organizations
    changes = show_changes(
        "Organizations.csv",
        "data/output/Organizations.csv",
        "data-enhancement/enhanced_output/Organizations_enhanced.csv",
        focus_fields=['sector', 'parentOrganization']
    )
    total_changes += changes

    # 对比People
    changes = show_changes(
        "People.csv",
        "data/output/People.csv",
        "data-enhancement/enhanced_output/People_enhanced.csv",
        focus_fields=['party', 'organization']
    )
    total_changes += changes

    print("\n" + "="*80)
    print(f"总计: {total_changes} 处字段得到改进")
    print("="*80)

if __name__ == '__main__':
    main()
