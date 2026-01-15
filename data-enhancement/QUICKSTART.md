# 快速开始指南

## 🚀 一键运行（Windows）

```cmd
cd data-enhancement
run_analysis.bat
```

这会自动执行所有步骤并生成完整报告。

## 📝 手动运行（分步骤）

### 1️⃣ 分析空缺字段

```bash
python analyze_missing_fields.py
```

**输出文件:**
- `missing_fields_report.json` - 详细的空缺分析
- `priority_fields.json` - 优先补全清单

**控制台输出示例:**
```
[*] 分析文件: Organizations (data/output/Organizations.csv)
[!] parentOrganization: 51条空缺 (100.0%)
[~] sector: 7条空缺 (13.7%)
```

---

### 2️⃣ 运行数据增强

```bash
python enhance_data.py
```

**输出文件:**
- `enhanced_output/Organizations_enhanced.csv`
- `enhanced_output/People_enhanced.csv`
- `enhanced_output/enhancement_report.json`

**控制台输出示例:**
```
[+] O015 (City of Fort Worth, Texas): sector = SEC005
[+] P001 (Donald J. Trump): party = Republican Party
完成! 增强了 Organizations: 7条, People: 54条
```

---

### 3️⃣ 查看对比结果

```bash
python compare_results.py
```

**控制台输出示例:**
```
[O015] City of Fort Worth, Texas
  字段: sector
  变化: (空) -> SEC005

总计: 61处字段得到改进
```

---

### 4️⃣ 生成数据质量报告

```bash
python generate_quality_report.py
```

**输出文件:**
- `quality_report.json`

**控制台输出示例:**
```
Organizations:
  原始完整度: 71.6%
  增强完整度: 75.0%
  提升: +3.4% [+]

People:
  原始完整度: 86.9%
  增强完整度: 91.4%
  提升: +4.5% [+]
```

---

## 📊 查看结果

### 查看增强后的CSV文件

```bash
# Windows
start enhanced_output\Organizations_enhanced.csv
start enhanced_output\People_enhanced.csv

# Linux/Mac
open enhanced_output/Organizations_enhanced.csv
open enhanced_output/People_enhanced.csv
```

### 查看JSON报告

```bash
# 空缺分析报告
cat missing_fields_report.json

# 优先补全清单
cat priority_fields.json

# 增强统计报告
cat enhanced_output/enhancement_report.json

# 数据质量报告
cat quality_report.json
```

---

## 📈 成果速览

### ✅ 已完成

| 文件 | 字段 | 改进 |
|------|------|------|
| Organizations.csv | sector | 86.3% → **100%** (+7条) |
| People.csv | party | 0% → **53%** (+53条) |
| People.csv | organization | 71% → **72%** (+1条) |

**总改进**: 61个字段 🎉

### ⚠️ 仍需处理

1. **People.party** - 47条记录需手动补全
2. **Organizations.parentOrganization** - 51条全部空缺
3. **People.organization** - 28条记录需补全
4. **Parties.csv** - 文件为空，需要添加数据

---

## 🛠️ 工具说明

| 脚本 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `analyze_missing_fields.py` | 分析空缺 | CSV文件 | JSON报告 |
| `enhance_data.py` | 数据增强 | CSV文件 | 增强的CSV |
| `compare_results.py` | 对比变化 | 原始+增强CSV | 控制台输出 |
| `generate_quality_report.py` | 质量报告 | 原始+增强CSV | JSON报告 |

---

## 💡 技巧

### 只查看某个字段的空缺

```python
import json
with open('missing_fields_report.json') as f:
    data = json.load(f)
    # 查看People的party字段
    print(data['People']['field_stats']['party'])
```

### 导出空缺ID列表

```python
import json
with open('priority_fields.json') as f:
    data = json.load(f)
    # 获取所有party为空的人物ID
    party_empty_ids = data['People'][0]['sample_ids']
    print(party_empty_ids)
```

### 对比单个字段的变化

```bash
# 使用diff命令对比
diff <(cut -d',' -f8 ../data/output/People.csv) \
     <(cut -d',' -f8 enhanced_output/People_enhanced.csv)
```

---

## 📖 更多文档

- **[README.md](README.md)** - 完整项目文档
- **[SUMMARY.md](SUMMARY.md)** - 项目总结报告

---

## ❓ 常见问题

**Q: 增强后的数据会覆盖原始文件吗？**
A: 不会。所有增强数据保存在 `enhanced_output/` 目录，原始文件完全不受影响。

**Q: 如何验证增强数据的准确性？**
A: 自动增强的数据基于bio字段的关键词匹配，准确率较高。建议人工抽查验证。

**Q: 可以修改增强规则吗？**
A: 可以。编辑 `enhance_data.py` 中的 `infer_*` 函数即可自定义规则。

**Q: 如何处理剩余的空缺字段？**
A: 参考 `priority_fields.json` 中的ID列表，手动查询Wikipedia等数据源补全。

---

**创建时间**: 2026-01-15
**版本**: 1.0
**适用于**: Windows / Linux / macOS
