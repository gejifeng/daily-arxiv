#!/bin/bash

# Daily arXiv 自动化部署脚本
# 作用：创建 Python 环境、安装依赖、生成本机 systemd 服务并启动

set -euo pipefail

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SERVICE_DIR="/etc/systemd/system"
SCHEDULER_UNIT_NAME="daily-arxiv-scheduler.service"
WEB_UNIT_NAME="daily-arxiv-web.service"
SCHEDULER_UNIT_PATH="$SERVICE_DIR/$SCHEDULER_UNIT_NAME"
WEB_UNIT_PATH="$SERVICE_DIR/$WEB_UNIT_NAME"

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

require_command() {
    local cmd="$1"
    local hint="$2"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        print_error "未找到命令 / Command not found: $cmd"
        echo "$hint"
        exit 1
    fi
}

read_web_port() {
    local config_file="$PROJECT_ROOT/config/config.yaml"

    if [ ! -f "$config_file" ]; then
        echo "5000"
        return
    fi

    local port
    port=$(awk '
        BEGIN { in_web = 0 }
        /^[^[:space:]]/ { in_web = ($1 == "web:") }
        in_web && $1 == "port:" { gsub(/"/, "", $2); print $2; exit }
    ' "$config_file")

    if [[ "$port" =~ ^[0-9]+$ ]]; then
        echo "$port"
    else
        echo "5000"
    fi
}

is_port_in_use() {
    local port="$1"
    if ss -ltn "( sport = :$port )" 2>/dev/null | tail -n +2 | grep -q .; then
        return 0
    fi
    return 1
}

create_conda_env() {
    require_command conda "请先安装 Conda，或选择 venv 模式。 / Please install Conda first, or choose venv mode."

    mapfile -t conda_envs < <(conda env list | awk 'NF && $1 !~ /^#/ {print $1}')

    echo ""
    echo "Conda 环境处理方式 / Conda environment mode:"
    echo "  1) 使用已有环境 / Use existing environment"
    echo "  2) 创建新环境 / Create new environment"

    if [ ${#conda_envs[@]} -eq 0 ]; then
        print_info "未扫描到已有 Conda 环境，将自动进入创建模式 / No existing Conda environment found; switching to create mode"
        conda_mode="2"
    else
        read -r -p "请选择 / Enter choice [1-2]: " conda_mode
    fi

    if [ "$conda_mode" = "1" ] && [ ${#conda_envs[@]} -gt 0 ]; then
        echo "可用 Conda 环境 / Available Conda environments:"
        for i in "${!conda_envs[@]}"; do
            echo "  $((i + 1))) ${conda_envs[$i]}"
        done
        read -r -p "请选择环境编号 / Select env number [1-${#conda_envs[@]}]: " conda_index
        if ! [[ "$conda_index" =~ ^[0-9]+$ ]] || [ "$conda_index" -lt 1 ] || [ "$conda_index" -gt ${#conda_envs[@]} ]; then
            print_error "无效编号 / Invalid selection"
            exit 1
        fi
        CONDA_ENV_NAME="${conda_envs[$((conda_index - 1))]}"
        print_info "已选择 Conda 环境 / Selected Conda environment: $CONDA_ENV_NAME"
    elif [ "$conda_mode" = "2" ]; then
        read -r -p "请输入新 Conda 环境名 / Enter new Conda env name [daily-arxiv]: " CONDA_ENV_NAME
        CONDA_ENV_NAME="${CONDA_ENV_NAME:-daily-arxiv}"

        if conda env list | awk '{print $1}' | grep -Fxq "$CONDA_ENV_NAME"; then
            print_info "Conda 环境已存在 / Conda environment already exists: $CONDA_ENV_NAME"
        else
            print_info "正在创建 Conda 环境 / Creating Conda environment: $CONDA_ENV_NAME (Python 3.12)"
            conda create -n "$CONDA_ENV_NAME" python=3.12 -y
            print_success "Conda 环境创建完成 / Conda environment created"
        fi
    else
        print_error "无效选项 / Invalid option"
        exit 1
    fi

    PYTHON_BIN=$(conda run -n "$CONDA_ENV_NAME" which python | tr -d '\r')
    if [ -z "$PYTHON_BIN" ] || [ ! -x "$PYTHON_BIN" ]; then
        print_error "无法定位 Conda 环境中的 python 可执行文件 / Unable to locate python executable in Conda environment"
        exit 1
    fi

    print_info "使用解释器 / Using interpreter: $PYTHON_BIN"
    conda run -n "$CONDA_ENV_NAME" python -m pip install --upgrade pip
    conda run -n "$CONDA_ENV_NAME" python -m pip install -r "$PROJECT_ROOT/requirements.txt"
}

create_venv_env() {
    require_command python3 "请先安装 Python 3。 / Please install Python 3 first."

    mapfile -t existing_venvs < <(find "$PROJECT_ROOT" -maxdepth 4 -type f -name "pyvenv.cfg" -printf '%h\n' 2>/dev/null | sort -u)

    echo ""
    echo "venv 环境处理方式 / venv mode:"
    echo "  1) 使用已有 venv / Use existing venv"
    echo "  2) 创建新 venv / Create new venv"

    if [ ${#existing_venvs[@]} -eq 0 ]; then
        print_info "未扫描到已有 venv，将自动进入创建模式 / No existing venv found; switching to create mode"
        venv_mode="2"
    else
        read -r -p "请选择 / Enter choice [1-2]: " venv_mode
    fi

    if [ "$venv_mode" = "1" ] && [ ${#existing_venvs[@]} -gt 0 ]; then
        echo "可用 venv 列表 / Available venv environments:"
        for i in "${!existing_venvs[@]}"; do
            echo "  $((i + 1))) ${existing_venvs[$i]}"
        done
        read -r -p "请选择环境编号 / Select venv number [1-${#existing_venvs[@]}]: " venv_index
        if ! [[ "$venv_index" =~ ^[0-9]+$ ]] || [ "$venv_index" -lt 1 ] || [ "$venv_index" -gt ${#existing_venvs[@]} ]; then
            print_error "无效编号 / Invalid selection"
            exit 1
        fi
        VENV_PATH="${existing_venvs[$((venv_index - 1))]}"
        print_info "已选择 venv / Selected venv: $VENV_PATH"
    elif [ "$venv_mode" = "2" ]; then
        read -r -p "请输入新 venv 目录名 / Enter new venv directory [.venv]: " VENV_INPUT
        VENV_INPUT="${VENV_INPUT:-.venv}"

        if [[ "$VENV_INPUT" = /* ]]; then
            VENV_PATH="$VENV_INPUT"
        else
            VENV_PATH="$PROJECT_ROOT/$VENV_INPUT"
        fi

        if [ -d "$VENV_PATH" ] && [ -x "$VENV_PATH/bin/python" ]; then
            print_info "venv 环境已存在 / venv already exists: $VENV_PATH"
        else
            print_info "正在创建 venv 环境 / Creating venv: $VENV_PATH"
            python3 -m venv "$VENV_PATH"
            print_success "venv 环境创建完成 / venv created"
        fi
    else
        print_error "无效选项 / Invalid option"
        exit 1
    fi

    PYTHON_BIN="$VENV_PATH/bin/python"
    if [ ! -x "$PYTHON_BIN" ]; then
        print_error "venv 中未找到 python 可执行文件 / Python executable not found in venv: $PYTHON_BIN"
        exit 1
    fi

    print_info "使用解释器 / Using interpreter: $PYTHON_BIN"
    "$PYTHON_BIN" -m pip install --upgrade pip
    "$PYTHON_BIN" -m pip install -r "$PROJECT_ROOT/requirements.txt"
}

generate_service_files() {
    local username="$1"
    local python_bin="$2"
    local python_dir
    python_dir="$(dirname "$python_bin")"

    local scheduler_log="$PROJECT_ROOT/logs/scheduler.log"
    local scheduler_error_log="$PROJECT_ROOT/logs/scheduler.error.log"
    local web_log="$PROJECT_ROOT/logs/web.log"
    local web_error_log="$PROJECT_ROOT/logs/web.error.log"

    local scheduler_tmp
    local web_tmp
    scheduler_tmp=$(mktemp)
    web_tmp=$(mktemp)

    cat > "$scheduler_tmp" <<EOF
[Unit]
Description=Daily arXiv Scheduler Service (auto-generated)
After=network.target

[Service]
Type=simple
User=$username
WorkingDirectory=$PROJECT_ROOT
Environment="PATH=$python_dir:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
EnvironmentFile=-$PROJECT_ROOT/.env
ExecStart=$python_bin $PROJECT_ROOT/scheduler.py
Restart=always
RestartSec=30
StandardOutput=append:$scheduler_log
StandardError=append:$scheduler_error_log

[Install]
WantedBy=multi-user.target
EOF

    cat > "$web_tmp" <<EOF
[Unit]
Description=Daily arXiv Web Service (auto-generated)
After=network.target

[Service]
Type=simple
User=$username
WorkingDirectory=$PROJECT_ROOT
Environment="PATH=$python_dir:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
EnvironmentFile=-$PROJECT_ROOT/.env
ExecStartPre=/bin/bash -c 'if /usr/bin/ss -ltn "( sport = :$WEB_PORT )" | /usr/bin/tail -n +2 | /usr/bin/grep -q .; then echo "Port $WEB_PORT is already in use"; exit 1; fi'
ExecStart=$python_bin $PROJECT_ROOT/src/web/app.py
Restart=always
RestartSec=10
StandardOutput=append:$web_log
StandardError=append:$web_error_log

[Install]
WantedBy=multi-user.target
EOF

    sudo cp "$scheduler_tmp" "$SCHEDULER_UNIT_PATH"
    sudo cp "$web_tmp" "$WEB_UNIT_PATH"
    rm -f "$scheduler_tmp" "$web_tmp"
}

echo -e "${BLUE}===================================================${NC}"
echo -e "${BLUE}  🚀 Daily arXiv 一键部署脚本 / One-click Deployment Script${NC}"
echo -e "${BLUE}===================================================${NC}"

require_command sudo "请安装 sudo 后重试。 / Please install sudo and try again."
require_command systemctl "当前系统不支持 systemd，无法使用该脚本部署服务。 / systemd is not available on this system."
require_command ss "请安装 iproute2（提供 ss 命令）后重试。 / Please install iproute2 (provides ss command)."

if [ ! -f "$PROJECT_ROOT/requirements.txt" ]; then
    print_error "未找到 requirements.txt，请确认在项目根目录执行。 / requirements.txt not found; run this script from project root."
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/config/config.yaml" ]; then
    print_error "未找到 config/config.yaml，请先准备配置文件。 / config/config.yaml not found."
    exit 1
fi

mkdir -p "$PROJECT_ROOT/logs" "$PROJECT_ROOT/data/papers" "$PROJECT_ROOT/data/summaries" "$PROJECT_ROOT/data/analysis"

WEB_PORT=$(read_web_port)
print_info "检测到 Web 端口 / Detected web port: $WEB_PORT"

if is_port_in_use "$WEB_PORT"; then
    print_error "端口 $WEB_PORT 已被占用，请释放端口或修改 config/config.yaml 中 web.port。 / Port $WEB_PORT is already in use."
    ss -ltnp "( sport = :$WEB_PORT )" || true
    exit 1
fi

echo ""
echo "请选择 Python 环境管理方式 / Select Python environment manager:"
echo "  1) Conda"
echo "  2) venv"
read -r -p "请输入选项 / Enter choice [1-2]: " ENV_CHOICE

case "$ENV_CHOICE" in
    1)
        create_conda_env
        ;;
    2)
        create_venv_env
        ;;
    *)
        print_error "无效选项，请输入 1 或 2。 / Invalid choice, please enter 1 or 2."
        exit 1
        ;;
esac

CURRENT_USER="$(id -un)"
print_info "将使用用户 / Running systemd services as user: $CURRENT_USER"

print_info "正在生成本机 service 文件 / Generating machine-specific service files..."
generate_service_files "$CURRENT_USER" "$PYTHON_BIN"
print_success "service 生成完成 / Services generated: $SCHEDULER_UNIT_PATH, $WEB_UNIT_PATH"

print_info "重载 systemd 配置 / Reloading systemd..."
sudo systemctl daemon-reload

print_info "设置开机自启并启动服务 / Enabling and starting services..."
sudo systemctl enable --now daily-arxiv-scheduler
sudo systemctl enable --now daily-arxiv-web

print_success "部署成功 / Deployment completed"
echo ""
echo "常用命令 / Useful commands:"
echo "  sudo systemctl status daily-arxiv-scheduler"
echo "  sudo systemctl status daily-arxiv-web"
echo "  tail -f $PROJECT_ROOT/logs/scheduler.log"
echo "  tail -f $PROJECT_ROOT/logs/web.log"
