# eNSP MCP Server

eNSP（Enterprise Network Simulation Platform）设备管理 MCP 服务器，提供 Web UI 界面和 MCP 接口两种方式管理 eNSP 虚拟设备。

## 功能特性

- **设备扫描**：扫描指定端口范围的 eNSP 虚拟设备
- **设备连接**：通过 Telnet 协议连接设备
- **多终端 CLI**：每个连接的设备拥有独立的 CLI 终端，支持 tab 切换
- **设备管理**：重命名设备、断开连接
- **拓扑管理**：上传和保存网络拓扑文件
- **MCP 接口**：支持 AI 助手通过 MCP 协议调用所有功能
- **实时同步**：Web UI 与 MCP 数据实时同步

## 项目结构

```
mcpensp1/
├── app.py              # Flask 主服务器（Web UI + HTTP API）
├── mcp_server.py       # MCP 服务器
├── mcp.json            # MCP 配置文件
├── requirements.txt    # Python 依赖
├── templates/
│   └── index.html      # Web UI 页面
└── uploads/            # 拓扑文件上传目录
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

要使用两个终端启动两个服务器，首先启动主服务器再启动MCP服务器

### 2. 启动主服务器

```bash
python app.py
```

服务器启动后访问 <http://127.0.0.1:5000>

3，启动MCP服务器

<br />

```shellscript
python mcp_server.py
```

### 3. 配置 MCP（可选）

如需使用 MCP 接口，将 `mcp.json` 配置到你的 MCP 客户端：

```json
{
  "mcpServers": {
    "ensp": {
      "command": "python",
      "args": ["E:\\Trae CN\\code\\code\\mcpensp1\\mcp_server.py"],
      "env": {},
      "description": "eNSP Device MCP Server"
    }
  }
}
```

```json
"args": ["E:\\Trae CN\\code\\code\\mcpensp1\\mcp_server.py"],这个地方要修改为你的mcpserver.py的绝对路径
```

<br />

## Web UI 使用指南

### 扫描设备

1. 设置端口范围（默认 2000-2050）
2. 点击「扫描」按钮
3. 扫描结果显示在左侧设备列表

### 连接设备

1. 在设备列表点击设备对应的「连接」按钮
2. 连接成功后，左侧显示绿色边框，右侧显示该设备的 CLI 终端
3. 在终端输入框输入命令，按 Enter 发送

### 多终端管理

- 每个连接的设备在右侧区域有独立的 tab 标签页
- 点击 tab 切换不同设备的终端
- 点击 tab 上的 × 按钮断开该设备
- 点击侧边栏的「已连接」可快速切换到该设备终端

### 设备重命名

1. 鼠标悬停在设备名称上，点击 \[✎] 图标
2. 在弹窗中输入新名称
3. 点击「确定」保存

### 拓扑管理

点击「上传拓扑」按钮，可上传 JSON 或 TXT 格式的拓扑文件。

## MCP 工具列表

| 工具名                     | 说明        | 参数                          |
| ----------------------- | --------- | --------------------------- |
| `scan_devices`          | 扫描设备      | `start`, `end`（端口范围）        |
| `connect_device`        | 连接设备      | `port`（端口号）                 |
| `send_command`          | 发送命令      | `path`（设备路径）, `command`（命令） |
| `disconnect_device`     | 断开设备      | `path`（设备路径）                |
| `get_connected_devices` | 获取已连接设备列表 | 无                           |
| `rename_device`         | 重命名设备     | `path`, `name`              |
| `get_topology`          | 获取拓扑数据    | 无                           |
| `save_topology`         | 保存拓扑数据    | `data`（拓扑对象）                |

## 技术栈

- **后端**：Flask + Flask-SocketIO + eventlet
- **前端**：原生 JavaScript + Socket.IO 客户端
- **协议**：Telnet（设备通信）、Socket.IO（实时通信）、MCP（AI 接口）
- **样式**：Catppuccin Mocha 主题

## 注意事项

1. 确保 eNSP 虚拟设备已在本地运行
2. 默认端口范围 2000-2050 对应 eNSP 设备端口
3. MCP 服务器需要主服务器先启动
4. 页面刷新后会自动恢复已连接的设备终端

