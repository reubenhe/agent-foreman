# 牛马监工台 · Agent Foreman

**中文** | [English](#english)

> 一个为 AI 编程 Agent 设计的浏览器监控面板。实时掌握本地和远程 Codex / Claude Code 的工作状态，支持从浏览器直接发话催活。

![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![No dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)

---

## 功能特性

- **实时监控** 本地及远程 Codex / Claude Code Agent 状态（1秒后台刷新）
- **三状态分组**：等回话 / 开工 / 摸鱼，一眼看全局
- **发话催活**：直接从网页向 Agent 发消息，支持多种注入方式
  - Linux：ptrace TIOCSTI 注入（无需 tmux）
  - macOS：tmux send-keys（需要在 tmux 里运行）
  - 远程服务器：通过 SSH 执行注入脚本
- **多机器支持**：同时监控本地 + 多台远程服务器 + Mac
- **发话方式**：直接按 Enter 发送，Shift+Enter 换行
- **花名系统**：给每个 Agent 起别名
- **统计卡片**：点击可按状态筛选 Agent
- **凭据安全**：密码 AES-256 加密存储，master password 保护
- **零依赖**：纯 Python 标准库，无需 pip install

---

## 截图

> *(可在此处添加截图)*

---

## 快速开始

### 环境要求

| 平台 | 要求 |
|------|------|
| Linux | Python 3.9+，OpenSSL，OpenSSH |
| macOS | Python 3.9+，tmux（发话功能），psutil（自动安装） |

### 安装

```bash
git clone https://github.com/YOUR_USERNAME/agent-foreman.git
cd agent-foreman
cp config.example.json config.json
```

### 启动

**推荐在 tmux 里启动，防止关闭终端后服务停止：**

```bash
tmux new-session -s foreman
python3 monitor_server.py --host 0.0.0.0 --port 8787
```

**首次启动**会提示设置 master password（用于加密远程主机密码，自己记住即可）。

之后每次启动输入同一密码。按 `Ctrl+B` 然后 `D` 挂到后台。

浏览器访问：

```
http://<your-server-ip>:8787
```

---

## 连接远程服务器

在网页「管工地」→「登记新工地」添加远程主机。

工地地址支持直接粘贴 SSH 格式，自动解析：

```
user@192.168.1.100
```

### 认证方式 A：SSH 密钥（推荐）

先配好免密登录：

```bash
ssh-copy-id username@remote-ip
```

然后在表单中选「SSH 密钥（免密）」，无需输入密码。

### 认证方式 B：SSH 密码

在表单中选「SSH 密码」，输入登录密码（加密保存）。

> 远程机器只需有 `python3`，无需预装任何包。探针脚本通过 SSH 自动推送执行。

---

## 连接 Mac

1. **开启远程登录**：系统设置 → 通用 → 共享 → 远程登录

2. **安装 tmux**（Mac 上发话需要）：
   ```bash
   brew install tmux
   ```

3. **在 tmux 里启动 Agent**：
   ```bash
   tmux
   claude   # 或 codex --yolo
   ```

4. 在网页添加工地（同上）

---

## 发话功能说明

每张 Agent 卡片底部有输入框：

- **Enter** = 发送消息
- **Shift+Enter** = 换行
- **留空发送** = 发送「继续」，催 Agent 继续干活

### 各平台发话原理

| 平台 | 方式 | 前提 |
|------|------|------|
| Linux 本地 | ptrace TIOCSTI | 同用户，ptrace_scope ≤ 1 |
| Linux 远程 | SSH + ptrace TIOCSTI | SSH 可达，同用户 |
| macOS | SSH + tmux send-keys | Agent 在 tmux 里运行 |

### Linux ptrace 权限

部分系统需要调整：

```bash
# 临时允许（重启失效）
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope

# 永久允许
echo 'kernel.yama.ptrace_scope = 0' | sudo tee /etc/sysctl.d/10-ptrace.conf
sudo sysctl -p /etc/sysctl.d/10-ptrace.conf
```

> ⚠️ 降低 ptrace_scope 允许同用户进程相互调试，请在可信环境中使用。

---

## Agent 状态说明

| 状态 | 含义 |
|------|------|
| 🔴 等回话 | 最近输出疑似在等待用户回复 |
| 🟡 开工 | 进程活跃或有 CPU 消耗 |
| ⚪ 摸鱼 | 进程存活但无活跃信号 |
| 🔘 失联 | 进程存活但心跳已过期 |

点击顶部统计卡片可按状态筛选。

---

## 配置说明

```bash
cp config.example.json config.json
```

主要配置项（`config.json`）：

```jsonc
{
  // 服务端轮询间隔（秒）
  "refresh_interval_sec": 10,

  // 发话方式：stdin（推荐）
  "send_mode": "stdin",

  // 静态主机列表（通常只保留 local）
  "hosts": [
    {"name": "local", "mode": "local"}
  ],

  // 通过网页 UI 添加的远程主机（自动维护）
  "managed_hosts": [],

  // Agent 会话文件路径
  "paths": {
    "codex_sessions": "~/.codex/sessions",
    "claude_projects": "~/.claude/projects"
  },

  // 状态判定参数
  "status": {
    "busy_cpu_threshold": 20.0,
    "active_heartbeat_sec": 120,
    "stale_heartbeat_sec": 900
  }
}
```

---

## 项目结构

```
agent-foreman/
├── monitor_server.py     # 主服务（单文件，零外部依赖）
├── static/
│   ├── index.html        # 页面结构
│   ├── app.js            # 前端逻辑
│   └── styles.css        # 样式
├── config.example.json   # 配置示例
├── tests/                # 测试
└── docs/                 # 文档
```

无需构建步骤，直接运行即可。

---

## 安全说明

- 远程密码通过 AES-256-CBC + PBKDF2（390,000 次迭代）加密存储
- 密码不出现在 `config.json` 或任何 API 响应中
- vault 仅在启动时输入 master password 后解锁
- **开源/分享时确保以下文件不被提交**（已在 .gitignore 中）：
  - `config.json`（含主机 IP）
  - `credentials.enc.json`（加密凭据）
  - `session_aliases.json`（花名记录）

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

---

<a name="english"></a>

# Agent Foreman

**[中文](#牛马监工台--agent-foreman)** | English

> A browser dashboard for monitoring Codex / Claude Code AI agents. See who's working, who's idle, and send messages directly from your browser — in real time.

---

## Features

- **Real-time monitoring** of local and remote Codex / Claude Code agents (1s background refresh)
- **Three status groups**: Needs Input / Working / Slacking
- **Send messages** directly to agents from the browser
  - Linux: ptrace TIOCSTI injection (no tmux required)
  - macOS: tmux send-keys (agent must run inside tmux)
  - Remote: SSH-based injection script
- **Multi-machine**: monitor local + multiple remote servers + Macs simultaneously
- **Keyboard-friendly**: press Enter to send, Shift+Enter for newline
- **Nicknames**: give each agent a custom alias
- **Clickable stats**: filter agents by status with one click
- **Secure credentials**: AES-256 encrypted storage, master password protected
- **Zero dependencies**: pure Python stdlib, no pip install needed

---

## Quick Start

### Requirements

| Platform | Requirements |
|----------|--------------|
| Linux | Python 3.9+, OpenSSL, OpenSSH |
| macOS | Python 3.9+, tmux (for send), psutil (auto-installed) |

### Install

```bash
git clone https://github.com/YOUR_USERNAME/agent-foreman.git
cd agent-foreman
cp config.example.json config.json
```

### Start

**Recommended: run inside tmux so the server survives terminal close:**

```bash
tmux new-session -s foreman
python3 monitor_server.py --host 0.0.0.0 --port 8787
```

On **first run**, you'll be asked to set a master password (used to encrypt remote host credentials). Enter the same password on subsequent runs.

Press `Ctrl+B` then `D` to detach from tmux. Open your browser:

```
http://<your-server-ip>:8787
```

---

## Connect Remote Servers

In the dashboard, click **「管工地」(Manage Sites)** → **「登记新工地」(Add Site)**.

You can paste SSH format directly into the address field — it auto-parses:

```
user@192.168.1.100
```

### Method A: SSH Key (Recommended)

```bash
ssh-copy-id username@remote-ip
```

Select **「SSH 密钥（免密）」** in the form. No password needed.

### Method B: SSH Password

Select **「SSH 密码」**, enter your login password (stored encrypted).

> The remote machine only needs `python3`. No packages need to be pre-installed — the probe script is pushed over SSH automatically.

---

## Connect macOS Machines

1. **Enable Remote Login**: System Settings → General → Sharing → Remote Login

2. **Install tmux** (required for send feature):
   ```bash
   brew install tmux
   ```

3. **Start your agent inside tmux**:
   ```bash
   tmux
   claude   # or: codex --yolo
   ```

4. Add the Mac as a remote site in the dashboard.

---

## Sending Messages

Each agent card has an input box at the bottom:

- **Enter** = send message
- **Shift+Enter** = newline
- **Send empty** = sends "继续" (continue), nudging the agent to keep working

### How injection works

| Platform | Method | Requirement |
|----------|--------|-------------|
| Linux local | ptrace TIOCSTI | Same user, ptrace_scope ≤ 1 |
| Linux remote | SSH + ptrace TIOCSTI | SSH access, same user |
| macOS | SSH + tmux send-keys | Agent running inside tmux |

### Linux ptrace permission

Some systems need:

```bash
# Temporary (reset on reboot)
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope

# Permanent
echo 'kernel.yama.ptrace_scope = 0' | sudo tee /etc/sysctl.d/10-ptrace.conf
sudo sysctl -p /etc/sysctl.d/10-ptrace.conf
```

> ⚠️ Lowering ptrace_scope allows same-user processes to debug each other. Use in trusted environments only.

---

## Agent Status

| Status | Meaning |
|--------|---------|
| 🔴 Needs Input | Recent output looks like the agent is waiting for a reply |
| 🟡 Working | Process is active or consuming CPU |
| ⚪ Slacking | Process alive but no strong activity signal |
| 🔘 Stale | Process alive but heartbeat has expired |

Click any stat card at the top to filter agents by status.

---

## Configuration

```bash
cp config.example.json config.json
```

Key fields in `config.json`:

```jsonc
{
  "refresh_interval_sec": 10,   // server-side poll interval
  "send_mode": "stdin",          // message injection mode
  "hosts": [
    {"name": "local", "mode": "local"}
  ],
  "managed_hosts": [],           // managed by the UI
  "paths": {
    "codex_sessions": "~/.codex/sessions",
    "claude_projects": "~/.claude/projects"
  },
  "status": {
    "busy_cpu_threshold": 20.0,
    "active_heartbeat_sec": 120,
    "stale_heartbeat_sec": 900
  }
}
```

---

## Project Structure

```
agent-foreman/
├── monitor_server.py     # Main server (single file, zero external deps)
├── static/
│   ├── index.html        # Page structure
│   ├── app.js            # Frontend logic
│   └── styles.css        # Styles
├── config.example.json   # Config template
├── tests/                # Tests
└── docs/                 # Documentation
```

No build step required. Just run `monitor_server.py`.

---

## Security

- Remote passwords encrypted with AES-256-CBC + PBKDF2 (390,000 iterations)
- Passwords never appear in `config.json` or any API response
- Vault is unlocked only after master password entry at startup
- **Do NOT commit these files** (already in `.gitignore`):
  - `config.json` (contains host IPs)
  - `credentials.enc.json` (encrypted credentials)
  - `session_aliases.json` (agent nicknames)

---

## License

MIT License. See [LICENSE](LICENSE) for details.