"""
CSV字段空缺分析脚本
分析data/output目录下的4个CSV文件，统计每个字段的空缺情况
"""

import csv
import os
from collections import defaultdict
import json

def analyze_csv_file(filepath):
    """分析单个CSV文件的空缺字段"""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        # 统计信息
        total_rows = 0
        field_stats = defaultdict(lambda: {'empty': 0, 'filled': 0, 'empty_ids': []})

        for row in reader:
            total_rows += 1
            row_id = row.get('id', f'row_{total_rows}')

            for field in fieldnames:
                value = row.get(field, '').strip()
                if value == '' or value is None:
                    field_stats[field]['empty'] += 1
                    field_stats[field]['empty_ids'].append(row_id)
                else:
                    field_stats[field]['filled'] += 1

        return {
            'total_rows': total_rows,
            'field_stats': dict(field_stats),
            'fieldnames': fieldnames
        }

def main():
    # CSV文件列表
    csv_files = {
        'Organizations': 'data/output/Organizations.csv',
        'People': 'data/output/People.csv',
        'Parties': 'data/output/Parties.csv',
        'Sectors': 'data/output/Sectors.csv'
    }

    results = {}

    print("=" * 80)
    print("CSV文件空缺字段分析报告")
    print("=" * 80)
    print()

    for name, filepath in csv_files.items():
        if not os.path.exists(filepath):
            print(f"[!] 文件不存在: {filepath}")
            continue

        print(f"\n[*] 分析文件: {name} ({filepath})")
        print("-" * 80)

        analysis = analyze_csv_file(filepath)
        results[name] = analysis

        total_rows = analysis['total_rows']
        print(f"总行数: {total_rows}")
        print(f"字段数: {len(analysis['fieldnames'])}")
        print(f"\n字段列表: {', '.join(analysis['fieldnames'])}")
        print("\n字段空缺统计:")

        # 按空缺率排序
        field_stats = analysis['field_stats']
        sorted_fields = sorted(
            field_stats.items(),
            key=lambda x: x[1]['empty'] / total_rows if total_rows > 0 else 0,
            reverse=True
        )

        for field, stats in sorted_fields:
            empty_count = stats['empty']
            filled_count = stats['filled']
            empty_rate = (empty_count / total_rows * 100) if total_rows > 0 else 0

            status = "[!]" if empty_rate > 50 else "[~]" if empty_rate > 10 else "[+]"

            print(f"  {status} {field:25s} - 空缺: {empty_count:4d} ({empty_rate:5.1f}%), 已填: {filled_count:4d}")

            # 如果空缺数量较少，显示具体的ID
            if 0 < empty_count <= 10:
                print(f"      空缺ID: {', '.join(stats['empty_ids'][:10])}")

    # 保存详细报告为JSON
    output_file = 'data-enhancement/missing_fields_report.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n\n{'=' * 80}")
    print(f"[OK] 详细报告已保存至: {output_file}")
    print(f"{'=' * 80}")

    # 生成需要补全的字段清单
    print("\n\n需要重点补全的字段清单（空缺率 > 10%）:")
    print("=" * 80)

    priority_fields = {}
    for name, analysis in results.items():
        total_rows = analysis['total_rows']
        if total_rows == 0:
            continue

        missing_fields = []
        for field, stats in analysis['field_stats'].items():
            empty_rate = (stats['empty'] / total_rows * 100)
            if empty_rate > 10 and field != 'id':  # 排除ID字段
                missing_fields.append({
                    'field': field,
                    'empty_count': stats['empty'],
                    'empty_rate': empty_rate,
                    'sample_ids': stats['empty_ids'][:5]
                })

        if missing_fields:
            priority_fields[name] = sorted(missing_fields, key=lambda x: x['empty_rate'], reverse=True)

    for name, fields in priority_fields.items():
        print(f"\n{name}:")
        for field_info in fields:
            print(f"  - {field_info['field']}: {field_info['empty_count']}条记录缺失 ({field_info['empty_rate']:.1f}%)")
            if field_info['sample_ids']:
                print(f"    示例ID: {', '.join(field_info['sample_ids'])}")

    # 保存优先补全清单
    priority_file = 'data-enhancement/priority_fields.json'
    with open(priority_file, 'w', encoding='utf-8') as f:
        json.dump(priority_fields, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] 优先补全清单已保存至: {priority_file}")

if __name__ == '__main__':
    main()
