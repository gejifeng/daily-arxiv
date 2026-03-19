#!/bin/bash

# Daily arXiv 启动脚本 / Launcher Script

set -e

# 项目目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PY_CMD="python"

setup_env_and_install_dependencies() {
    echo -e "\n${BLUE}环境初始化 / Environment bootstrap${NC}"
    echo "  1) Conda"
    echo "  2) venv"
    read -r -p "请选择 / Enter choice [1-2]: " env_choice

    case "$env_choice" in
        1)
            if ! command -v conda &> /dev/null; then
                echo -e "${RED}❌ 未找到 Conda / Conda not found${NC}"
                return 1
            fi

            mapfile -t conda_envs < <(conda env list | awk 'NF && $1 !~ /^#/ {print $1}')

            echo ""
            echo "Conda 环境处理方式 / Conda environment mode:"
            echo "  1) 使用已有环境 / Use existing environment"
            echo "  2) 创建新环境 / Create new environment"
            if [ ${#conda_envs[@]} -eq 0 ]; then
                echo -e "${YELLOW}⚠️  未扫描到已有 Conda 环境，将自动进入创建模式 / No existing Conda environments found; switching to create mode${NC}"
                conda_mode="2"
            else
                read -r -p "请选择 / Enter choice [1-2]: " conda_mode
            fi

            if [ "$conda_mode" = "1" ] && [ ${#conda_envs[@]} -gt 0 ]; then
                echo ""
                echo "可用 Conda 环境 / Available Conda environments:"
                for i in "${!conda_envs[@]}"; do
                    echo "  $((i + 1))) ${conda_envs[$i]}"
                done
                read -r -p "请选择环境编号 / Select env number [1-${#conda_envs[@]}]: " conda_index
                if ! [[ "$conda_index" =~ ^[0-9]+$ ]] || [ "$conda_index" -lt 1 ] || [ "$conda_index" -gt ${#conda_envs[@]} ]; then
                    echo -e "${RED}❌ 无效编号 / Invalid selection${NC}"
                    return 1
                fi
                conda_env_name="${conda_envs[$((conda_index - 1))]}"
                echo -e "${GREEN}✅ 已选择 Conda 环境 / Selected Conda env: $conda_env_name${NC}"
            elif [ "$conda_mode" = "2" ]; then
                read -r -p "请输入新 Conda 环境名 / Enter new Conda env name [daily-arxiv]: " conda_env_name
                conda_env_name="${conda_env_name:-daily-arxiv}"

                if conda env list | awk '{print $1}' | grep -Fxq "$conda_env_name"; then
                    echo -e "${GREEN}✅ Conda 环境已存在 / Conda env exists: $conda_env_name${NC}"
                else
                    echo -e "${YELLOW}正在创建 Conda 环境 / Creating Conda env: $conda_env_name${NC}"
                    conda create -n "$conda_env_name" python=3.12 -y
                fi
            else
                echo -e "${RED}❌ 无效选项 / Invalid option${NC}"
                return 1
            fi

            echo -e "${YELLOW}安装依赖 / Installing dependencies...${NC}"
            conda run -n "$conda_env_name" python -m pip install --upgrade pip
            conda run -n "$conda_env_name" python -m pip install -r requirements.txt

            conda_python=$(conda run -n "$conda_env_name" which python | tr -d '\r')
            if [ -n "$conda_python" ] && [ -x "$conda_python" ]; then
                PY_CMD="$conda_python"
                echo -e "${GREEN}✅ 后续将使用 / Will use Python: $PY_CMD${NC}"
            else
                echo -e "${YELLOW}⚠️  未能定位 Conda Python，继续使用当前 python / Failed to resolve Conda python, using current python${NC}"
            fi
            ;;
        2)
            mapfile -t existing_venvs < <(find "$PROJECT_DIR" -maxdepth 4 -type f -name "pyvenv.cfg" -printf '%h\n' 2>/dev/null | sort -u)

            echo ""
            echo "venv 环境处理方式 / venv mode:"
            echo "  1) 使用已有 venv / Use existing venv"
            echo "  2) 创建新 venv / Create new venv"
            if [ ${#existing_venvs[@]} -eq 0 ]; then
                echo -e "${YELLOW}⚠️  未扫描到已有 venv，将自动进入创建模式 / No existing venv found; switching to create mode${NC}"
                venv_mode="2"
            else
                read -r -p "请选择 / Enter choice [1-2]: " venv_mode
            fi

            if [ "$venv_mode" = "1" ] && [ ${#existing_venvs[@]} -gt 0 ]; then
                echo ""
                echo "可用 venv 列表 / Available venv environments:"
                for i in "${!existing_venvs[@]}"; do
                    echo "  $((i + 1))) ${existing_venvs[$i]}"
                done
                read -r -p "请选择环境编号 / Select venv number [1-${#existing_venvs[@]}]: " venv_index
                if ! [[ "$venv_index" =~ ^[0-9]+$ ]] || [ "$venv_index" -lt 1 ] || [ "$venv_index" -gt ${#existing_venvs[@]} ]; then
                    echo -e "${RED}❌ 无效编号 / Invalid selection${NC}"
                    return 1
                fi
                venv_path="${existing_venvs[$((venv_index - 1))]}"
            elif [ "$venv_mode" = "2" ]; then
                if ! command -v python3 &> /dev/null; then
                    echo -e "${RED}❌ 未找到 python3 / python3 not found${NC}"
                    return 1
                fi

                read -r -p "请输入新 venv 目录名 / Enter new venv directory [.venv]: " venv_input
                venv_input="${venv_input:-.venv}"

                if [[ "$venv_input" = /* ]]; then
                    venv_path="$venv_input"
                else
                    venv_path="$PROJECT_DIR/$venv_input"
                fi

                if [ -d "$venv_path" ] && [ -x "$venv_path/bin/python" ]; then
                    echo -e "${GREEN}✅ venv 已存在 / venv exists: $venv_path${NC}"
                else
                    echo -e "${YELLOW}正在创建 venv / Creating venv: $venv_path${NC}"
                    python3 -m venv "$venv_path"
                fi
            else
                echo -e "${RED}❌ 无效选项 / Invalid option${NC}"
                return 1
            fi

            PY_CMD="$venv_path/bin/python"
            if [ ! -x "$PY_CMD" ]; then
                echo -e "${RED}❌ 选定 venv 中未找到 python / Python not found in selected venv: $venv_path${NC}"
                return 1
            fi

            echo -e "${YELLOW}安装依赖 / Installing dependencies...${NC}"
            "$PY_CMD" -m pip install --upgrade pip
            "$PY_CMD" -m pip install -r requirements.txt
            echo -e "${GREEN}✅ 后续将使用 / Will use Python: $PY_CMD${NC}"
            ;;
        *)
            echo -e "${RED}❌ 无效选项 / Invalid option${NC}"
            return 1
            ;;
    esac
}

deploy_systemd_services() {
    echo -e "\n${GREEN}🚀 开始部署 systemd 服务 / Deploying systemd services...${NC}"
    bash "$PROJECT_DIR/deploy/deploy_services.sh"
}

prompt_env_setup_if_needed() {
    echo ""
    echo "是否立即配置 Python 虚拟环境并安装依赖？ / Configure Python environment and install dependencies now?"
    echo "  1) 是 / Yes"
    echo "  2) 否，稍后在菜单中选择 / No, choose later from menu"
    read -r -p "请选择 / Enter choice [1-2] (default: 1): " auto_env_choice
    auto_env_choice="${auto_env_choice:-1}"

    case "$auto_env_choice" in
        1)
            setup_env_and_install_dependencies
            ;;
        2)
            echo -e "${YELLOW}ℹ️  已跳过环境初始化 / Environment setup skipped${NC}"
            ;;
        *)
            echo -e "${YELLOW}⚠️  无效选项，默认跳过 / Invalid choice, skipping by default${NC}"
            ;;
    esac
}

echo -e "${BLUE}"
echo "============================================================"
echo "  🚀 Daily arXiv Scheduler Launcher / 调度器启动器"
echo "============================================================"
echo -e "${NC}"

# 检查 Python 环境
if ! command -v "$PY_CMD" &> /dev/null; then
    echo -e "${RED}❌ Python 未找到 / Python not found!${NC}"
    exit 1
fi

PYTHON_VERSION=$($PY_CMD --version 2>&1)
echo -e "${GREEN}✅ Python 环境 / Python environment: $PYTHON_VERSION${NC}"

# 检查依赖
echo -e "\n${YELLOW}📦 检查依赖 / Checking dependencies...${NC}"
if $PY_CMD -c "import apscheduler" 2>/dev/null; then
    echo -e "${GREEN}✅ APScheduler 已安装 / APScheduler is installed${NC}"
else
    echo -e "${YELLOW}⚠️  APScheduler 未安装 / APScheduler is not installed${NC}"
    echo -e "${YELLOW}提示 / Tip: 选择菜单 7 初始化环境并安装依赖 / Use menu option 7 to bootstrap environment and install dependencies${NC}"

    read -r -p "是否现在进入环境初始化流程？ / Start environment setup now? [y/N]: " setup_now
    setup_now="${setup_now:-N}"
    if [[ "$setup_now" =~ ^[Yy]$ ]]; then
        setup_env_and_install_dependencies
    fi
fi

# 检查配置文件
echo -e "\n${YELLOW}⚙️  检查配置 / Checking configuration...${NC}"
if [ -f "config/config.yaml" ]; then
    echo -e "${GREEN}✅ 配置文件存在 / Config file found${NC}"
else
    echo -e "${RED}❌ 配置文件不存在 / Config file not found!${NC}"
    exit 1
fi

if [ -f ".env" ]; then
    echo -e "${GREEN}✅ 环境变量文件存在 / .env file found${NC}"
else
    echo -e "${YELLOW}⚠️  .env 文件不存在，使用默认配置 / .env not found, using default settings${NC}"
fi

# 启动后先给一次环境初始化入口
prompt_env_setup_if_needed

# 检查数据目录
echo -e "\n${YELLOW}📁 检查数据目录 / Checking data directories...${NC}"
mkdir -p data/papers data/summaries data/analysis logs
echo -e "${GREEN}✅ 数据目录已就绪 / Data directories ready${NC}"

# 检查日志目录
mkdir -p logs
echo -e "${GREEN}✅ 日志目录已就绪 / Log directory ready${NC}"

# 启动选项
echo -e "\n${BLUE}启动选项 / Startup options:${NC}"
echo "  1) 启动调度器 (前台运行) / Start scheduler (foreground)"
echo "  2) 启动调度器 (后台运行) / Start scheduler (background)"
echo "  3) 运行一次任务 / Run once"
echo "  4) 测试邮件通知 / Test email notification"
echo "  5) 查看调度器状态 / Show scheduler status"
echo "  6) 停止调度器 / Stop scheduler"
echo "  7) 初始化环境并安装依赖 / Setup env and install dependencies"
echo "  8) 部署 systemd 服务 / Deploy systemd services"
echo "  0) 退出 / Exit"
echo ""
read -p "请选择 / Enter choice [0-8]: " choice

case $choice in
    1)
        echo -e "\n${GREEN}🚀 启动调度器 (前台运行) / Starting scheduler (foreground)...${NC}"
        "$PY_CMD" scheduler.py
        ;;
    2)
        echo -e "\n${GREEN}🚀 启动调度器 (后台运行) / Starting scheduler (background)...${NC}"
        nohup "$PY_CMD" scheduler.py > logs/scheduler.log 2>&1 &
        PID=$!
        echo $PID > logs/scheduler.pid
        echo -e "${GREEN}✅ 调度器已启动 / Scheduler started, PID: $PID${NC}"
        echo -e "${YELLOW}查看日志 / View logs: tail -f logs/scheduler.log${NC}"
        echo -e "${YELLOW}停止调度器 / Stop scheduler: ./deploy/start.sh (选项 / option 6)${NC}"
        ;;
    3)
        echo -e "\n${GREEN}🔄 运行一次任务 / Running once...${NC}"
        "$PY_CMD" main.py
        ;;
    4)
        echo -e "\n${GREEN}📧 测试邮件通知 / Testing email notification...${NC}"
        "$PY_CMD" -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from src.utils import load_config, load_env
from src.notifier import send_test_email

load_env()
config = load_config()
notification_config = config.get('scheduler', {}).get('notification', {})
if notification_config.get('enabled', False):
    email_config = notification_config.get('email', {})
    send_test_email(email_config)
else:
    print('⚠️  邮件通知未启用 / Email notification is disabled')
"
        ;;
    5)
        echo -e "\n${YELLOW}📊 调度器状态 / Scheduler status:${NC}"
        if [ -f "logs/scheduler.pid" ]; then
            PID=$(cat logs/scheduler.pid)
            if ps -p $PID > /dev/null 2>&1; then
                echo -e "${GREEN}✅ 调度器运行中 / Scheduler is running, PID: $PID${NC}"
                echo ""
                ps -f -p $PID
            else
                echo -e "${RED}❌ 调度器未运行 (PID 文件存在但进程不存在) / Scheduler not running (stale PID file)${NC}"
                rm logs/scheduler.pid
            fi
        else
            echo -e "${YELLOW}⚠️  未找到 PID 文件 / PID file not found${NC}"
        fi
        ;;
    6)
        echo -e "\n${YELLOW}🛑 停止调度器 / Stopping scheduler...${NC}"
        if [ -f "logs/scheduler.pid" ]; then
            PID=$(cat logs/scheduler.pid)
            if ps -p $PID > /dev/null 2>&1; then
                kill $PID
                echo -e "${GREEN}✅ 调度器已停止 / Scheduler stopped (PID: $PID)${NC}"
                rm logs/scheduler.pid
            else
                echo -e "${YELLOW}⚠️  进程不存在 / Process not found${NC}"
                rm logs/scheduler.pid
            fi
        else
            echo -e "${YELLOW}⚠️  未找到 PID 文件 / PID file not found${NC}"
        fi
        ;;
    7)
        setup_env_and_install_dependencies
        ;;
    8)
        deploy_systemd_services
        ;;
    0)
        echo -e "\n${BLUE}👋 再见 / Bye!${NC}"
        exit 0
        ;;
    *)
        echo -e "\n${RED}❌ 无效选项 / Invalid option${NC}"
        exit 1
        ;;
esac

echo ""
