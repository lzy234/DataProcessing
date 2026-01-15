@echo off
chcp 65001 >nul
echo ================================================================================
echo 数据查漏补缺 - 分析工具
echo ================================================================================
echo.

echo [1/3] 正在分析CSV文件的空缺字段...
python analyze_missing_fields.py
echo.

echo [2/3] 正在运行数据增强...
python enhance_data.py
echo.

echo [3/3] 正在生成对比报告...
python compare_results.py
echo.

echo ================================================================================
echo 完成！
echo ================================================================================
echo.
echo 增强后的文件保存在: enhanced_output/
echo 详细报告:
echo   - missing_fields_report.json (空缺分析)
echo   - priority_fields.json (优先补全清单)
echo   - enhanced_output/enhancement_report.json (增强统计)
echo.
echo 查看完整文档: README.md 和 SUMMARY.md
echo.

pause
