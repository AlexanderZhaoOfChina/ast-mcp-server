# AST MCP 服务器

本项目是一个基于 MCP（模型上下文协议，Model Context Protocol）的服务器，能够通过抽象语法树（AST）和抽象语义图（ASG）为代码提供结构和语义分析能力。

## 功能特性

- 将代码解析为抽象语法树（AST）
- 从代码生成抽象语义图（ASG）
- 分析代码结构和复杂度
- 支持多种编程语言（目前支持 Python、JavaScript）
- 兼容 Claude Desktop 及其他 MCP 客户端
- 支持增量解析，加速大文件处理
- 增强作用域处理和更完整的语义分析
- AST 差异分析，识别代码版本间的变化

## 安装方法

1. 克隆本仓库：

```bash
git clone https://github.com/yourusername/ast-mcp-server.git
cd ast-mcp-server
```

2. 使用 `uv` 设置环境：

```bash
# 如果未安装 uv，请先安装
# pip install uv

# 创建并激活虚拟环境
uv venv
source .venv/bin/activate  # Windows 下为 .venv\Scripts\activate

# 安装依赖
uv pip install -r requirements.txt
```

3. 构建解析器：

```bash
uv run build_parsers.py
```

## 与 Claude Desktop 配合使用

1. 配置 Claude Desktop 使用本服务器。推荐使用项目自带的 `claude_desktop_config.json` 文件：

```json
{
  "mcpServers": {
    "AstAnalyzer": {
      "command": "uv",
      "args": [
        "--directory", "/absolute/path/to/ast-mcp-server",
        "run", "server.py"
      ]
    }
  }
}
```

2. 将 `/absolute/path/to/ast-mcp-server` 替换为你本地的实际路径。

3. 将该配置文件添加到 Claude Desktop 配置目录：
   - macOS: `~/Library/Application Support/claude-desktop/claude_desktop_config.json`
   - Linux: `~/.config/claude-desktop/claude_desktop_config.json`
   - Windows: `%APPDATA%\claude-desktop\claude_desktop_config.json`

4. 重启 Claude Desktop 以加载新的 MCP 服务器。

5. 现在你可以在 Claude Desktop 中使用基于 AST 的代码分析工具。

## 功能验证

- **AST 解析**：可正确解析 Python 代码为详细的 AST，结构层次分明。
- **ASG 生成**：可生成包含节点和边的抽象语义图，正确反映代码组件间关系。
- **代码分析**：可识别函数、类、复杂度等结构信息。
- **资源缓存**：`parse_and_cache` 等函数可生成并返回可复用的资源 URI。
- **多语言支持**：已验证 Python 和 JavaScript 均可正常解析。
- **与 Claude Desktop 集成**：配置正确后可在 Claude Desktop 内使用所有功能。

## 开发与测试

开发模式下可使用 MCP inspector：

```bash
# 推荐使用脚本
./dev_server.sh

# 或手动运行
uv run -m mcp dev server.py
```

## 可用工具

### 基础工具
- `parse_to_ast`：将代码解析为 AST
- `generate_asg`：从代码生成 ASG
- `analyze_code`：分析代码结构和复杂度
- `supported_languages`：获取支持的编程语言列表
- `parse_and_cache`：解析并缓存 AST
- `generate_and_cache_asg`：生成并缓存 ASG
- `analyze_and_cache`：分析并缓存结构信息

### 增强工具
- `parse_to_ast_incremental`：支持增量解析
- `generate_enhanced_asg`：生成增强版 ASG
- `diff_ast`：对比两份代码的 AST 差异
- `find_node_at_position`：定位指定行列的节点
- `parse_and_cache_incremental`：增量解析并缓存
- `generate_and_cache_enhanced_asg`：生成并缓存增强版 ASG
- `ast_diff_and_cache`：生成并缓存 AST 差异

## 增加更多语言支持

1. 安装对应的 tree-sitter 语言包：

```bash
uv pip install tree-sitter-<language>
```

2. 在 `build_parsers.py` 和 `ast_mcp_server/tools.py` 的 `LANGUAGE_MODULES` 字典中添加新语言。

3. 运行 `uv run build_parsers.py` 初始化新语言。

## 工作原理

AST MCP 服务器通过 MCP 协议与 Claude Desktop 连接。启动流程如下：

1. Claude Desktop 使用 `uv run` 启动服务器，并指定工作目录
2. 服务器加载 tree-sitter 语言模块，支持多种编程语言解析
3. 注册所有工具和资源到 MCP 协议
4. Claude 可通过 MCP 工具分析你在聊天中分享的代码

所有工具的执行均在本地完成，结果返回给 Claude 进行展示和解释。

## 许可证

MIT 