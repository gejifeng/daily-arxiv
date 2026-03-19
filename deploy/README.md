# Daily arXiv 部署说明

本目录包含 Linux systemd 部署脚本与模板。

## 📂 文件说明

- `deploy_services.sh`: 一键部署脚本（推荐），支持选择 Conda/venv、扫描已有环境并选择“使用已有”或“创建新环境”、安装依赖、生成本机 service、开机自启。
- `start.sh`: 本地交互式脚本，支持前台/后台运行调度器、启动时询问是否初始化 Conda/venv、扫描已有环境并选择“使用已有”或“创建新环境”、以及调用 systemd 一键部署（菜单选项 8）。
- `uninstall_services.sh`: 一键卸载脚本，停止并禁用服务、删除 systemd service 文件、重载 systemd。
- `daily-arxiv-scheduler.service`: scheduler service 模板示例。
- `daily-arxiv-web.service`: web service 模板示例。

## 🚀 一键部署（推荐）

运行：

```bash
bash deploy/deploy_services.sh
```

脚本会自动完成：
1. 检查必要命令（`systemctl`、`sudo`、`ss` 等）。
2. 读取 `config/config.yaml` 中的 `web.port`，并在启动前检查端口占用。
3. 让你选择环境管理方式：Conda 或 venv。
4. 扫描已有环境，并让你选择“使用已有环境”或“创建新环境”。
5. 安装 `requirements.txt`。
6. 生成适配本机的 `/etc/systemd/system/daily-arxiv-scheduler.service` 与 `/etc/systemd/system/daily-arxiv-web.service`。
7. `daemon-reload` + `enable --now` 启动服务。

## ⚠️ 异常提示

脚本会在以下场景主动报错并退出：
- 未安装系统依赖命令（如 `systemctl`、`ss`）。
- `config/config.yaml` 或 `requirements.txt` 缺失。
- Web 端口已被占用。
- Python 环境创建失败，或无法找到可执行文件。

此外，生成的 web service 中含有 `ExecStartPre` 端口占用检查，防止服务重启时无提示失败。

## 🛠️ 常用管理命令

```bash
# 查看状态
sudo systemctl status daily-arxiv-scheduler
sudo systemctl status daily-arxiv-web

# 重启服务
sudo systemctl restart daily-arxiv-scheduler
sudo systemctl restart daily-arxiv-web

# 停止服务
sudo systemctl stop daily-arxiv-scheduler
sudo systemctl stop daily-arxiv-web

# 关闭开机自启
sudo systemctl disable daily-arxiv-scheduler
sudo systemctl disable daily-arxiv-web
```

## 🧹 卸载服务

```bash
bash deploy/uninstall_services.sh
```

脚本会交互确认后执行：
- 停止 `daily-arxiv-scheduler` 和 `daily-arxiv-web`
- 禁用开机自启
- 删除 `/etc/systemd/system/` 下对应 service 文件
- `daemon-reload` 并 `reset-failed`

## 📝 日志查看

```bash
tail -f logs/scheduler.log
tail -f logs/web.log
tail -f logs/scheduler.error.log
tail -f logs/web.error.log
```
