#!/bin/bash
# Git 历史问题彻底解决脚本
# 目标：解决所有冲突，清理历史，同步本地和远程

set -e  # 遇到错误立即退出

cd /home/jin/bazi_predict || exit 1

echo "=========================================="
echo "🔧 Git 历史问题彻底解决"
echo "=========================================="
echo ""

# 步骤 1: 检查并拉取远程最新状态
echo "📥 步骤 1: 获取远程最新状态..."
git fetch origin
echo ""

# 步骤 2: 检查是否有冲突
echo "🔍 步骤 2: 检查合并冲突..."
if git merge-base --is-ancestor HEAD origin/main 2>/dev/null; then
    echo "   ✅ 本地分支是远程分支的祖先，可以安全合并"
    NEED_MERGE=false
elif git merge-base --is-ancestor origin/main HEAD 2>/dev/null; then
    echo "   ⚠️  本地分支领先远程分支"
    NEED_MERGE=false
else
    echo "   ⚠️  本地和远程分支已分叉，需要合并"
    NEED_MERGE=true
fi
echo ""

# 步骤 3: 如果有分叉，先尝试合并
if [ "$NEED_MERGE" = true ]; then
    echo "🔄 步骤 3: 合并远程更改..."
    if git merge origin/main --no-edit; then
        echo "   ✅ 合并成功"
    else
        echo "   ❌ 合并冲突！需要手动解决"
        echo "   冲突文件:"
        git diff --name-only --diff-filter=U
        exit 1
    fi
    echo ""
fi

# 步骤 4: 添加所有修改的文件
echo "📝 步骤 4: 添加修改的文件..."
git add controllers/bazi_controller.py
git add core/config_schema.py
git add core/engine_v88.py
git add core/engine_v91.py
git add core/engines/flow_engine.py
git add core/processors/domains.py
git add core/processors/physics.py
git add core/processors/strength_judge.py
git add docs/ARCHITECTURE.md
git add facade/bazi_facade.py
git add requirements.txt
git add scripts/run_batch_calibration.py
git add services/calibration_service.py
git add tests/test_controller_facade.py
git add tests/test_flux_engine.py
git add ui/components/unified_input_panel.py
git add ui/pages/prediction_dashboard.py
git add ui/pages/quantum_lab.py
git add ui/pages/zeitgeist.py
git add ui/sidebar.py
git add utils/constants_manager.py
git add utils/notification_manager.py
echo "   ✅ 已添加 22 个修改的文件"
echo ""

# 步骤 5: 添加重要的新文件（Graph Engine 相关）
echo "📦 步骤 5: 添加重要的新文件..."
# Graph Engine 核心文件
git add core/engine_graph.py
git add core/engine_adapter.py
git add ui/components/graph_visualizer.py

# 重要的配置和文档
git add config/parameters.json
git add config/parameters_v49_golden.json
git add WSL_PATH_WARNING.md

# 重要的脚本
git add scripts/auto_evolve.py
git add scripts/train_model_optuna.py
git add scripts/batch_verify.py
git add scripts/analyze_failures.py
git add scripts/debug_outliers.py
git add scripts/auto_tune_val005.py

# 重要的文档
git add docs/GRAPH_NETWORK_ENGINE_ARCHITECTURE.md
git add docs/GRAPH_ENGINE_INTEGRATION_V33.md
git add docs/ANTIGRAVITY_OPTIMIZATION_CONSTITUTION_V1.0.md
git add scripts/AUTO_EVOLVE_README.md

# 辅助脚本
git add scripts/preflight_check.sh
git add scripts/start_evolution.sh
git add scripts/check_evolution_status.sh
git add scripts/monitor_evolution.sh
git add scripts/view_evolution.sh
git add scripts/train_wrapper.sh
git add scripts/run_without_warning.sh

echo "   ✅ 已添加重要的新文件"
echo ""

# 步骤 6: 检查暂存区状态
echo "📊 步骤 6: 检查暂存区状态..."
git status --short | head -30
echo ""

# 步骤 7: 提交更改
echo "💾 步骤 7: 提交更改..."
COMMIT_MSG="feat: Graph Network Engine V50.0 - Auto-Evolution Meta-Optimizer

- 实现图网络引擎 (GraphNetworkEngine) 核心算法
- 添加化气逻辑 (Stem Transformation) 和特殊格局检测
- 实现相对抑制机制 (Relative Suppression) 解决能量通胀
- 集成 Optuna AI 训练器进行超参数优化
- 实现自动进化元优化器 (Auto-Evolve) 无人值守训练
- 添加网络拓扑可视化组件
- 优化参数配置和批量验证系统
- 达到 72.7% 黄金平衡准确率 (Strong/Balanced/Weak 均衡)

V50.0 Features:
- V39.0: Stem Transformation (化气) Logic
- V40.0: Special Pattern Detector (专旺格)
- V42.1: System Entropy & Output Drain
- V43.0: Relative Suppression Mechanism
- V44.0: Optuna AI Trainer Integration
- V45.0: Cyclic Optimization Strategy
- V49.0: Precision Drain for Weak Cases
- V50.0: Unattended Auto-Evolution Meta-Optimizer"

if git commit -m "$COMMIT_MSG"; then
    echo "   ✅ 提交成功"
else
    echo "   ⚠️  提交失败或没有更改需要提交"
fi
echo ""

# 步骤 8: 推送到远程
echo "🚀 步骤 8: 推送到远程服务器..."
if git push origin main; then
    echo "   ✅ 推送成功"
else
    echo "   ❌ 推送失败，可能需要先拉取远程更改"
    echo "   尝试: git pull --rebase origin main"
    exit 1
fi
echo ""

echo "=========================================="
echo "✅ Git 历史问题已彻底解决！"
echo "=========================================="
echo ""
echo "📊 最终状态:"
git status --short | head -20
echo ""
echo "🎉 所有更改已同步到远程服务器"

