# 实用脚本说明

本目录包含项目的辅助脚本和监控工具。

## 脚本列表

### check_progress.py
检查数据处理进度的工具。

**功能：**
- 检查各个处理阶段的完成情况
- 显示已处理的人物数量
- 报告当前处理状态

**使用方法：**
```bash
python scripts/check_progress.py
```

---

### live_monitor.py
实时监控数据处理流程。

**功能：**
- 实时显示处理进度
- 监控API调用状态
- 显示错误和警告信息
- 动态刷新显示

**使用方法：**
```bash
python scripts/live_monitor.py
```

---

### monitor_pipeline.py
管道式监控工具，跟踪整个数据处理管道。

**功能：**
- 监控各个处理阶段
- 显示管道流转状态
- 记录处理时间和性能指标

**使用方法：**
```bash
python scripts/monitor_pipeline.py
```

---

### quick_status.bat
Windows批处理脚本，快速查看项目状态。

**功能：**
- 快速检查项目状态
- 显示关键指标
- 一键查看处理结果

**使用方法（Windows）：**
```cmd
scripts\quick_status.bat
```

或者双击运行该文件。

## 使用场景

- **开发阶段**：使用 `live_monitor.py` 实时查看处理进度
- **调试问题**：使用 `check_progress.py` 快速定位处理卡在哪个阶段
- **性能分析**：使用 `monitor_pipeline.py` 分析各阶段耗时
- **快速检查**：使用 `quick_status.bat` 一键查看状态

## 注意事项

1. 所有脚本都应该从项目根目录运行
2. 确保已安装所有必需的依赖（见 `requirements.txt`）
3. 某些脚本可能需要正在运行的处理任务才能显示有意义的信息
