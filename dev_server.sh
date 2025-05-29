#!/bin/bash
# Start the AST MCP server in development mode with the inspector
# 以开发模式并带有inspector启动AST MCP服务器

# Kill any running instances
# 杀死所有正在运行的相关进程，避免端口冲突
pkill -f "mcp dev server.py" || true

# Current directory
# 获取当前脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Start the server with the MCP inspector using uv
# 切换到脚本目录并用uv启动带MCP inspector的开发服务器
cd "$DIR"
uv run -m mcp dev server.py
