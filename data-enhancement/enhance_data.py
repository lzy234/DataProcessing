"""
数据补全脚本 - 使用Wikipedia爬取和AI增强
针对空缺字段进行数据补全
"""

import csv
import json
import os
import time
from typing import Dict, List, Any
import requests
from urllib.parse import quote

class DataEnhancer:
    """数据增强器 - 通过Wikipedia和AI补全缺失数据"""

    def __init__(self, openai_api_key=None):
        self.openai_api_key = openai_api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_wikipedia_summary(self, entity_name: str) -> Dict[str, Any]:
        """从Wikipedia获取实体摘要信息"""
        try:
            # 使用Wikipedia API
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(entity_name)}"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'title': data.get('title', ''),
                    'extract': data.get('extract', ''),
                    'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                    'categories': data.get('categories', [])
                }
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def infer_political_party(self, person_data: Dict[str, str]) -> str:
        """
        推断人物的政党归属
        基于bio、currentRole等信息
        """
        bio = person_data.get('bio', '').lower()
        current_role = person_data.get('currentRole', '').lower()
        name = person_data.get('name', '')

        # 关键词匹配
        if 'republican' in bio or 'gop' in bio:
            return 'Republican Party'
        elif 'democrat' in bio or 'democratic party' in bio:
            return 'Democratic Party'
        elif 'independent' in bio:
            return 'Independent'

        # 如果有Wikipedia数据，可以进一步增强
        wiki_data = self.fetch_wikipedia_summary(name)
        if wiki_data.get('success'):
            extract = wiki_data.get('extract', '').lower()
            if 'republican' in extract:
                return 'Republican Party'
            elif 'democrat' in extract:
                return 'Democratic Party'

        return ''  # 无法确定

    def infer_organization_sector(self, org_data: Dict[str, str], sectors_map: Dict[str, str]) -> str:
        """
        推断组织的sector
        基于组织名称和描述
        """
        name = org_data.get('name', '').lower()
        description = org_data.get('description', '').lower()

        # 政府部门
        if any(keyword in name for keyword in ['department', 'state', 'city', 'u.s.', 'federal']):
            if 'state' in name and 'department' in name:
                return 'SEC002'  # Government - Executive
            elif any(keyword in name for keyword in ['city', 'mayor', 'fort worth', 'houston', 'georgia']):
                return 'SEC005'  # Government - Other

        # 司法
        if 'court' in name or 'supreme court' in name:
            return 'SEC004'  # Government - Judicial

        # 立法
        if 'senate' in name or 'house of representatives' in name or 'congress' in name:
            return 'SEC005'  # Government - Other

        return ''

    def infer_person_organization(self, person_data: Dict[str, str], organizations: List[Dict[str, str]]) -> str:
        """
        推断人物所属组织
        基于currentRole和bio
        """
        current_role = person_data.get('currentRole', '').lower()
        bio = person_data.get('bio', '').lower()

        # 创建组织名称到ID的映射
        org_map = {}
        for org in organizations:
            org_name = org.get('name', '').lower()
            org_id = org.get('id', '')
            org_map[org_name] = org_id

            # 添加常见缩写
            if 'white house' in org_name:
                org_map['白宫'] = org_id
                org_map['white house'] = org_id

        # 检查currentRole中是否包含组织关键词
        for org_name, org_id in org_map.items():
            if org_name in current_role or org_name in bio[:200]:  # 只检查bio的前200字符
                return org_id

        # 特殊角色映射
        role_org_map = {
            '总统': 'O051',  # White House
            'president': 'O051',
            '副总统': 'O051',
            'vice president': 'O051',
            'chief of staff': 'O051',
            '国务卿': 'O043',  # U.S. Department of State
            'secretary of state': 'O043',
            '国防部长': None,  # 需要在Organizations中查找
            'secretary of defense': None,
            '财政部长': 'O045',  # U.S. Department of the Treasury
            'secretary of the treasury': 'O045',
            '内政部长': 'O044',  # U.S. Department of the Interior
            'secretary of the interior': 'O044',
            '能源部长': 'O040',  # U.S. Department of Energy
            'secretary of energy': 'O040',
            '农业部长': 'O039',  # U.S. Department of Agriculture
            'secretary of agriculture': 'O039',
        }

        for role_keyword, org_id in role_org_map.items():
            if role_keyword in current_role and org_id:
                return org_id

        return ''

    def enhance_organizations(self, input_file: str, output_file: str):
        """增强Organizations数据"""
        print(f"\n[*] 正在增强 Organizations 数据...")
        print(f"    输入文件: {input_file}")
        print(f"    输出文件: {output_file}")

        # 读取sectors以便映射
        sectors = []
        with open('data/output/Sectors.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            sectors = list(reader)

        sectors_map = {s['id']: s['name'] for s in sectors}

        # 读取并处理数据
        rows = []
        enhanced_count = 0

        with open(input_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                original_sector = row.get('sector', '').strip()

                # 如果sector为空，尝试推断
                if not original_sector:
                    inferred_sector = self.infer_organization_sector(row, sectors_map)
                    if inferred_sector:
                        row['sector'] = inferred_sector
                        enhanced_count += 1
                        print(f"    [+] {row['id']} ({row['name']}): sector = {inferred_sector}")

                rows.append(row)

        # 写入增强后的数据
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

        print(f"    [OK] 完成! 增强了 {enhanced_count} 条记录")
        return enhanced_count

    def enhance_people(self, input_file: str, output_file: str):
        """增强People数据"""
        print(f"\n[*] 正在增强 People 数据...")
        print(f"    输入文件: {input_file}")
        print(f"    输出文件: {output_file}")

        # 读取organizations以便映射
        organizations = []
        with open('data/output/Organizations.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            organizations = list(reader)

        # 读取并处理数据
        rows = []
        party_enhanced = 0
        org_enhanced = 0

        with open(input_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 推断政党
                if not row.get('party', '').strip():
                    inferred_party = self.infer_political_party(row)
                    if inferred_party:
                        row['party'] = inferred_party
                        party_enhanced += 1
                        print(f"    [+] {row['id']} ({row['name']}): party = {inferred_party}")

                # 推断组织
                if not row.get('organization', '').strip():
                    inferred_org = self.infer_person_organization(row, organizations)
                    if inferred_org:
                        row['organization'] = inferred_org
                        org_enhanced += 1
                        print(f"    [+] {row['id']} ({row['name']}): organization = {inferred_org}")

                rows.append(row)

        # 写入增强后的数据
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

        print(f"    [OK] 完成! 增强了 party: {party_enhanced} 条, organization: {org_enhanced} 条")
        return party_enhanced + org_enhanced

def main():
    print("=" * 80)
    print("数据补全和增强脚本")
    print("=" * 80)

    # 创建输出目录
    output_dir = 'data-enhancement/enhanced_output'
    os.makedirs(output_dir, exist_ok=True)

    enhancer = DataEnhancer()

    # 增强Organizations
    org_count = enhancer.enhance_organizations(
        'data/output/Organizations.csv',
        f'{output_dir}/Organizations_enhanced.csv'
    )

    # 增强People
    people_count = enhancer.enhance_people(
        'data/output/People.csv',
        f'{output_dir}/People_enhanced.csv'
    )

    print("\n" + "=" * 80)
    print("增强完成!")
    print("=" * 80)
    print(f"Organizations: 增强了 {org_count} 条记录")
    print(f"People: 增强了 {people_count} 条记录")
    print(f"\n增强后的文件保存在: {output_dir}/")

    # 生成增强报告
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'organizations_enhanced': org_count,
        'people_enhanced': people_count,
        'output_directory': output_dir
    }

    with open(f'{output_dir}/enhancement_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"增强报告已保存: {output_dir}/enhancement_report.json")

if __name__ == '__main__':
    main()
