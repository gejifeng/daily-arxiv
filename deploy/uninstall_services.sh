#!/bin/bash

# Daily arXiv 服务卸载脚本 / Service uninstall script
# 作用：停止、禁用并删除 daily-arxiv 的 systemd 服务文件

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

SERVICE_DIR="/etc/systemd/system"
SCHEDULER_UNIT_NAME="daily-arxiv-scheduler.service"
WEB_UNIT_NAME="daily-arxiv-web.service"

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

run_systemctl() {
    if command -v sudo >/dev/null 2>&1; then
        sudo systemctl "$@"
    else
        systemctl "$@"
    fi
}

remove_file() {
    local file_path="$1"
    if [ -f "$file_path" ] || [ -L "$file_path" ]; then
        if command -v sudo >/dev/null 2>&1; then
            sudo rm -f "$file_path"
        else
            rm -f "$file_path"
        fi
        print_success "已删除 / Removed: $file_path"
    else
        print_info "文件不存在，跳过 / File not found, skipped: $file_path"
    fi
}

echo -e "${BLUE}===================================================${NC}"
echo -e "${BLUE}  🧹 Daily arXiv 服务卸载脚本 / Service Uninstall${NC}"
echo -e "${BLUE}===================================================${NC}"

if ! command -v systemctl >/dev/null 2>&1; then
    print_error "未找到 systemctl，无法卸载 systemd 服务 / systemctl not found"
    exit 1
fi

echo ""
echo "将执行以下操作 / This script will:"
echo "  1) 停止服务 / Stop services"
echo "  2) 禁用开机自启 / Disable autostart"
echo "  3) 删除 service 文件 / Remove service files"
echo "  4) 重载 systemd / Reload systemd"
echo ""

read -r -p "确认继续？ / Continue? [y/N]: " confirm
confirm="${confirm:-N}"
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    print_info "已取消 / Cancelled"
    exit 0
fi

print_info "停止服务 / Stopping services..."
run_systemctl stop daily-arxiv-scheduler || true
run_systemctl stop daily-arxiv-web || true

print_info "禁用开机自启 / Disabling services..."
run_systemctl disable daily-arxiv-scheduler || true
run_systemctl disable daily-arxiv-web || true

print_info "删除 service 文件 / Removing unit files..."
remove_file "$SERVICE_DIR/$SCHEDULER_UNIT_NAME"
remove_file "$SERVICE_DIR/$WEB_UNIT_NAME"

print_info "重载 systemd / Reloading systemd..."
run_systemctl daemon-reload
run_systemctl reset-failed || true

print_success "卸载完成 / Uninstall completed"
echo ""
echo "可选检查命令 / Optional checks:"
echo "  systemctl status daily-arxiv-scheduler"
echo "  systemctl status daily-arxiv-web"
