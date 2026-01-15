"""
生成数据质量可视化报告
"""

import csv
import json
from collections import defaultdict

def calculate_completeness(csv_file: str) -> dict:
    """计算CSV文件的完整度"""
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

        if not rows:
            return {'total_rows': 0, 'fields': {}, 'overall': 0}

        fieldnames = reader.fieldnames
        total_rows = len(rows)

        field_completeness = {}
        for field in fieldnames:
            filled = sum(1 for row in rows if row.get(field, '').strip())
            completeness = (filled / total_rows * 100) if total_rows > 0 else 0
            field_completeness[field] = {
                'filled': filled,
                'total': total_rows,
                'completeness': completeness
            }

        # 计算整体完整度（排除id字段）
        non_id_fields = [f for f in fieldnames if f != 'id']
        if non_id_fields:
            overall = sum(field_completeness[f]['completeness'] for f in non_id_fields) / len(non_id_fields)
        else:
            overall = 100

        return {
            'total_rows': total_rows,
            'fields': field_completeness,
            'overall': overall
        }

def generate_progress_bar(percentage: float, width: int = 30) -> str:
    """生成文本进度条"""
    filled = int(width * percentage / 100)
    bar = '#' * filled + '-' * (width - filled)
    return f"[{bar}] {percentage:.1f}%"

def main():
    print("=" * 100)
    print("数据质量报告")
    print("=" * 100)

    files = {
        'Organizations': {
            'original': '../data/output/Organizations.csv',
            'enhanced': 'enhanced_output/Organizations_enhanced.csv'
        },
        'People': {
            'original': '../data/output/People.csv',
            'enhanced': 'enhanced_output/People_enhanced.csv'
        },
        'Sectors': {
            'original': '../data/output/Sectors.csv',
            'enhanced': None
        }
    }

    report = {}

    for name, paths in files.items():
        print(f"\n{'='*100}")
        print(f"[*] {name}.csv")
        print(f"{'='*100}")

        # 原始数据质量
        original = calculate_completeness(paths['original'])
        report[name] = {'original': original}

        print(f"\n原始数据 (共{original['total_rows']}条记录):")
        print(f"  整体完整度: {generate_progress_bar(original['overall'])}")
        print(f"\n  各字段完整度:")

        for field, stats in sorted(original['fields'].items(),
                                   key=lambda x: x[1]['completeness']):
            status = "[OK]" if stats['completeness'] == 100 else "[~]" if stats['completeness'] > 50 else "[!]"
            print(f"    {status} {field:25s} {generate_progress_bar(stats['completeness'])}")

        # 如果有增强数据，显示对比
        if paths.get('enhanced'):
            enhanced = calculate_completeness(paths['enhanced'])
            report[name]['enhanced'] = enhanced

            improvement = enhanced['overall'] - original['overall']

            if improvement > 0:
                print(f"\n增强后数据:")
                print(f"  整体完整度: {generate_progress_bar(enhanced['overall'])} (提升 +{improvement:.1f}%)")
                print(f"\n  改进的字段:")

                improvements = []
                for field in enhanced['fields']:
                    orig_comp = original['fields'][field]['completeness']
                    enh_comp = enhanced['fields'][field]['completeness']
                    if enh_comp > orig_comp:
                        improvements.append({
                            'field': field,
                            'original': orig_comp,
                            'enhanced': enh_comp,
                            'improvement': enh_comp - orig_comp
                        })

                for imp in sorted(improvements, key=lambda x: x['improvement'], reverse=True):
                    print(f"    [+] {imp['field']:25s} {imp['original']:5.1f}% -> {imp['enhanced']:5.1f}% (提升 +{imp['improvement']:.1f}%)")
            else:
                print(f"\n增强后数据: 无改进")

    # 生成总结
    print(f"\n{'='*100}")
    print("总体数据质量总结")
    print(f"{'='*100}")

    for name, data in report.items():
        if 'enhanced' in data:
            orig = data['original']['overall']
            enh = data['enhanced']['overall']
            improvement = enh - orig

            print(f"\n{name}:")
            print(f"  原始完整度: {orig:.1f}%")
            print(f"  增强完整度: {enh:.1f}%")
            if improvement > 0:
                print(f"  提升: +{improvement:.1f}% [+]")
            else:
                print(f"  提升: 无变化")
        else:
            print(f"\n{name}:")
            print(f"  原始完整度: {data['original']['overall']:.1f}%")
            print(f"  状态: 未增强")

    # 保存JSON报告
    output_file = 'quality_report.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*100}")
    print(f"[OK] 数据质量报告已保存: {output_file}")
    print(f"{'='*100}")

if __name__ == '__main__':
    main()
