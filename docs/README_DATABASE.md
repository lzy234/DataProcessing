# CSV转SQLite数据库使用指南

## 概述

本项目提供了将CSV格式的政治人物和组织数据转换为Payload CMS所需的SQLite数据库的工具。

## 文件说明

### 核心脚本

1. **csv_to_sqlite.py** - CSV转SQLite转换脚本
   - 读取 `data/output/chinese/` 目录下的CSV文件
   - 生成符合Payload CMS结构的SQLite数据库
   - 输出文件：`nexus.db`

2. **verify_database.py** - 数据库验证脚本
   - 检查数据库表结构和数据完整性
   - 生成数据统计报告
   - 识别数据质量问题

### 数据文件

输入CSV文件（位于 `data/output/chinese/`）：
- `People.csv` - 政治人物数据（100条）
- `Organizations.csv` - 组织机构数据（51条）
- `Sectors.csv` - 领域分类数据（9条）
- `Parties.csv` - 政党数据（当前为空）

## 使用步骤

### 1. 准备环境

确保已安装Python 3.x，无需额外依赖包。

### 2. 运行转换

```bash
python csv_to_sqlite.py
```

**输出示例：**
```
==================================================
开始转换CSV到SQLite数据库
==================================================

[1/6] 创建数据库表结构...
[2/6] 导入 Sectors...
[OK] 导入 9 条 Sectors 数据
[3/6] 导入 Parties...
[OK] 导入 0 条 Parties 数据
[4/6] 导入 Organizations...
[OK] 导入 44 条 Organizations 数据
[5/6] 导入 People...
[OK] 导入 100 条 People 数据
[6/6] 创建默认用户...
[OK] 创建默认管理员用户

[DONE] 转换完成! 数据库文件: nexus.db
```

### 3. 验证数据

```bash
python verify_database.py
```

这将显示：
- 各表的记录数统计
- 数据预览（前5条）
- 关系检查（外键关联情况）
- 数据质量报告（缺失值统计）

## 数据库结构

### 核心表

| 表名 | 记录数 | 说明 |
|------|--------|------|
| **people** | 100 | 政治人物档案 |
| **organizations** | 44 | 组织机构（支持层级） |
| **sectors** | 18 | 行业领域分类 |
| **parties** | 0 | 政党数据（待补充） |
| **users** | 1 | 管理员账户 |

### 关系映射

- People → Organizations (多对一，通过 `organization` 字段)
- People → Parties (多对一，通过 `party` 字段)
- Organizations → Sectors (多对一，通过 `sector` 字段)
- Organizations → Organizations (自引用，通过 `parentOrganization` 字段)

## 当前数据统计

转换后的数据库包含：
- ✓ 100位政治人物
- ✓ 44个组织机构
- ✓ 18个领域分类
- ✓ 50人已关联组织
- ⚠ 0个政党数据（Parties.csv为空）

## 已知问题与待办

### 1. 缺失数据

- **Parties.csv为空**：需要补充政党数据（如Republican Party, Democratic Party等）
- **部分Organizations缺少sector**：7个组织的sector字段为空

### 2. 字段映射问题

CSV中的关系字段（如 `organization`, `party`）使用原始ID（如 "O001", "P001"），已通过脚本自动映射到数据库的自增ID。

### 3. 需要手动处理的部分

#### a) 用户密码加密

当前users表中的密码是占位符，需要使用bcrypt加密：

```python
import bcrypt

# 生成密码哈希
password = "your_password"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print(hashed.decode('utf-8'))
```

然后更新数据库：
```sql
UPDATE users SET password = '$2a$10$...' WHERE username = 'admin';
```

#### b) 补充Parties数据

创建 `data/output/chinese/Parties.csv` 并添加数据：

```csv
id,name,abbreviation,color
PAR001,Republican Party,GOP,#E81B23
PAR002,Democratic Party,DEM,#0015BC
PAR003,Independent,IND,#808080
```

然后重新运行 `csv_to_sqlite.py`。

#### c) 补充Connections关系数据

如需添加人物/组织间的关系网络，需要：
1. 创建 `Connections.csv`
2. 修改脚本添加导入逻辑

## 进阶使用

### 查询示例

```python
import sqlite3

conn = sqlite3.connect('nexus.db')
cursor = conn.cursor()

# 查询所有共和党成员
cursor.execute("""
    SELECT p.name, p.ChineseName, p.currentRole
    FROM people p
    JOIN parties pa ON p.party = pa.id
    WHERE pa.name = 'Republican Party'
""")

# 查询某个组织的所有成员
cursor.execute("""
    SELECT p.name, p.currentRole
    FROM people p
    JOIN organizations o ON p.organization = o.id
    WHERE o.name = '美国参议院'
""")

# 查询组织层级
cursor.execute("""
    SELECT
        child.name as 子组织,
        parent.name as 父组织
    FROM organizations child
    LEFT JOIN organizations parent ON child.parentOrganization = parent.id
    WHERE child.parentOrganization IS NOT NULL
""")
```

### 在Payload CMS中使用

1. 将生成的 `nexus.db` 文件复制到Payload CMS项目根目录
2. 确保 `payload.config.ts` 中的数据库配置正确：

```typescript
import { sqliteAdapter } from '@payloadcms/db-sqlite'

export default buildConfig({
  db: sqliteAdapter({
    client: {
      url: process.env.DATABASE_URI || 'file:./nexus.db',
    },
  }),
  // ...其他配置
})
```

3. 启动Payload CMS：
```bash
npm run dev
```

## 技术细节

### 自动化功能

脚本已实现：
- ✓ ID自动映射（CSV中的自定义ID → 数据库自增ID）
- ✓ 时间戳自动生成（createdAt, updatedAt）
- ✓ 外键关系自动建立
- ✓ 索引自动创建（提升查询性能）
- ✓ UTF-8编码处理（支持中文）

### 数据约束

- 必填字段校验（name, currentRole等）
- 外键约束（保证引用完整性）
- 唯一性约束（username）

## 故障排除

### 问题1：编码错误

**症状：** 运行时出现 `UnicodeEncodeError`

**解决：** 确保终端支持UTF-8编码，或修改脚本中的print语句移除特殊字符。

### 问题2：找不到CSV文件

**症状：** `FileNotFoundError: data/output/chinese/xxx.csv`

**解决：** 确认CSV文件存在且路径正确。

### 问题3：数据库已存在

**解决：** 删除现有的 `nexus.db` 文件后重新运行脚本。

```bash
rm nexus.db
python csv_to_sqlite.py
```

## 下一步建议

1. **补充Parties数据** - 创建完整的政党信息
2. **添加Media表数据** - 导入人物头像图片
3. **创建Connections关系** - 建立人物/组织关系网络
4. **添加Tags** - 创建特殊标签（如"2028 Candidate"）
5. **完善People数据** - 补充缺失的出生日期、教育背景等
6. **实现Hooks** - 在Payload CMS中配置自动化规则（职位推荐、标签自动添加等）

## 参考文档

- [数据库结构分析报告](docs/数据库结构分析报告.md)
- [Payload CMS官方文档](https://payloadcms.com/docs)
- [SQLite文档](https://www.sqlite.org/docs.html)

---

**最后更新：** 2026-01-15
**作者：** DataProcessing Team
