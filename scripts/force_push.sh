#!/bin/bash
# 强制推送脚本 - 从最安全到最暴力

echo "=== Git 强制推送工具 ==="
echo ""
echo "请选择推送方式："
echo "1. --force-with-lease (推荐，相对安全)"
echo "2. --force (暴力覆盖)"
echo "3. 先 fetch 再 --force-with-lease"
echo "4. 先 fetch 再 --force (最暴力)"
echo ""
read -p "请选择 (1-4): " choice

case $choice in
    1)
        echo "执行: git push --force-with-lease origin main"
        git push --force-with-lease origin main
        ;;
    2)
        echo "执行: git push --force origin main"
        git push --force origin main
        ;;
    3)
        echo "先执行: git fetch origin"
        git fetch origin
        echo "再执行: git push --force-with-lease origin main"
        git push --force-with-lease origin main
        ;;
    4)
        echo "先执行: git fetch origin"
        git fetch origin
        echo "再执行: git push --force origin main"
        git push --force origin main
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac

