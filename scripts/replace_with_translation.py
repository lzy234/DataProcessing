#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将翻译后的中文内容替换回原始CSV文件
不增加新列，直接用中文替换英文内容
特殊处理：People文件保留英文名和中文名
"""

import pandas as pd
import os
from pathlib import Path


def replace_translations(original_file, translated_file, output_file, keep_name_in_english=False):
    """
    用翻译文件的中文内容替换原始文件的英文内容

    Args:
        original_file: 原始CSV文件路径
        translated_file: 翻译后的CSV文件路径
        output_file: 输出文件路径
        keep_name_in_english: 是否保留name列为英文（仅用于People文件）
    """
    print(f"正在处理: {os.path.basename(original_file)}")

    # 读取文件
    df_original = pd.read_csv(original_file, encoding='utf-8-sig')
    df_translated = pd.read_csv(translated_file, encoding='utf-8-sig')

    # 确保两个文件有相同的行数和ID
    if len(df_original) != len(df_translated):
        print(f"警告: 原始文件和翻译文件行数不匹配！原始: {len(df_original)}, 翻译: {len(df_translated)}")

    # 创建结果DataFrame，从原始文件开始
    df_result = df_original.copy()

    # 遍历翻译文件的列，查找带_zh后缀的列
    for col in df_translated.columns:
        if col.endswith('_zh'):
            # 获取对应的英文列名（去掉_zh后缀）
            original_col = col[:-3]

            # 如果原始文件中存在该列，则用中文替换
            if original_col in df_result.columns:
                # 特殊处理：如果是People文件且是name列，跳过（保留英文名）
                if keep_name_in_english and original_col == 'name':
                    # 但是添加ChineseName列
                    if 'ChineseName' not in df_result.columns:
                        # 在name列后面插入ChineseName列
                        name_col_idx = df_result.columns.get_loc('name')
                        df_result.insert(name_col_idx + 1, 'ChineseName', df_translated[col])
                    continue

                # 用翻译的中文内容替换原始英文内容
                df_result[original_col] = df_translated[col]
                print(f"  - 已替换列: {original_col}")

    # 如果是People文件，确保保留ChineseName列
    if keep_name_in_english and 'ChineseName' in df_translated.columns:
        if 'ChineseName' not in df_result.columns:
            name_col_idx = df_result.columns.get_loc('name')
            df_result.insert(name_col_idx + 1, 'ChineseName', df_translated['ChineseName'])
            print(f"  - 已添加列: ChineseName（保留英文名和中文名）")

    # 保存结果
    df_result.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"[OK] 已保存到: {output_file}\n")

    return df_result


def main():
    # 定义路径
    base_dir = Path(__file__).parent
    original_dir = base_dir / 'data' / 'output'
    translated_dir = base_dir / 'data' / 'output' / 'translated'
    output_dir = base_dir / 'data' / 'output' / 'chinese'

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)

    # 定义要处理的文件
    files_to_process = [
        ('Organizations.csv', 'Organizations_zh.csv', False),
        ('Parties.csv', 'Parties_zh.csv', False),
        ('People.csv', 'People_zh.csv', True),  # People文件特殊处理
        ('Sectors.csv', 'Sectors_zh.csv', False),
    ]

    print("=" * 60)
    print("开始替换翻译内容")
    print("=" * 60)
    print()

    # 处理每个文件
    for original_name, translated_name, keep_english_name in files_to_process:
        original_file = original_dir / original_name
        translated_file = translated_dir / translated_name
        output_file = output_dir / original_name

        # 检查文件是否存在
        if not original_file.exists():
            print(f"[SKIP] 跳过: {original_name} (原始文件不存在)")
            continue

        if not translated_file.exists():
            print(f"[SKIP] 跳过: {translated_name} (翻译文件不存在)")
            continue

        # 执行替换
        try:
            replace_translations(original_file, translated_file, output_file, keep_english_name)
        except Exception as e:
            print(f"[ERROR] 处理 {original_name} 时出错: {str(e)}\n")

    print("=" * 60)
    print("处理完成！")
    print(f"结果已保存到: {output_dir}")
    print("=" * 60)


if __name__ == '__main__':
    main()
