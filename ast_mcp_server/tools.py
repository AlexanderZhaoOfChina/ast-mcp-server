"""
AST/ASG analysis tools for the MCP server.

This module defines the tools that provide code structure and semantic analysis
capabilities through the Model Context Protocol.
"""
# MCP服务器的AST/ASG分析工具模块。
# 本模块通过Model Context Protocol定义了提供代码结构和语义分析能力的工具。

from typing import Dict, List, Optional, Union, Any
import os
import json
import importlib
from tree_sitter import Parser, Node

# Try to import language modules
LANGUAGE_MODULES = {
    "python": "tree_sitter_python",
    "javascript": "tree_sitter_javascript",
    "java": "tree_sitter_java",
}
# 支持的语言模块映射表。

# Path to the parsers availability marker
PARSERS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parsers")
PARSERS_AVAILABLE_FILE = os.path.join(PARSERS_DIR, "parsers_available.txt")
# 解析器目录及可用性标记文件路径。

# Language identifiers mapping
LANGUAGE_MAP = {
    "py": "python",
    "python": "python",
    "js": "javascript", 
    "javascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
    "tsx": "tsx",
    "go": "go",
    "golang": "go",
    "rs": "rust",
    "rust": "rust",
    "c": "c",
    "cpp": "cpp",
    "c++": "cpp",
    "java": "java"
}
# 语言标识符映射表，支持多种常见缩写。

# Initialize parser and languages
languages = {}
# 用于存储已初始化的语言解析器。

def init_parsers():
    """Initialize the tree-sitter parsers."""
    # 初始化tree-sitter解析器。
    global languages
    
    # Check if parsers are marked as available
    if not os.path.exists(PARSERS_AVAILABLE_FILE):
        return False
    
    try:
        # Check which language modules are available
        available_languages = []
        for lang_name, module_name in LANGUAGE_MODULES.items():
            try:
                module = importlib.import_module(module_name)
                from tree_sitter import Language
                languages[lang_name] = Language(module.language())
                available_languages.append(lang_name)
            except ImportError:
                print(f"Module {module_name} not found. Some language support may be limited.")
            except Exception as e:
                print(f"Error initializing {lang_name} language: {e}")
        # 动态导入各语言的tree-sitter模块，初始化解析器。
        if available_languages:
            print(f"Successfully initialized parsers for: {', '.join(available_languages)}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error initializing parsers: {e}")
        return False
    # 若初始化失败则返回False。

def node_to_dict(node: Node, source_bytes: bytes, include_children: bool = True) -> Dict:
    """Convert a tree-sitter Node to a dictionary representation."""
    # 将tree-sitter的Node节点转换为字典结构，便于序列化和后续处理。
    result = {
        "type": node.type,
        "start_byte": node.start_byte,
        "end_byte": node.end_byte,
        "start_point": {
            "row": node.start_point[0],
            "column": node.start_point[1]
        },
        "end_point": {
            "row": node.end_point[0],
            "column": node.end_point[1]
        },
        "text": source_bytes[node.start_byte:node.end_byte].decode('utf-8')
    }
    
    if include_children and node.child_count > 0:
        result["children"] = [node_to_dict(child, source_bytes, include_children) 
                             for child in node.children]
    # 递归处理所有子节点。
    return result

def create_field_edges(node: Dict, parent_id: Optional[str] = None) -> List[Dict]:
    """Create field edges for the ASG (connecting nodes with their named fields)."""
    # 为ASG创建字段边，将节点与其命名字段连接。
    edges = []
    node_id = f"{node['type']}_{node['start_byte']}_{node['end_byte']}"
    
    if parent_id:
        edges.append({
            "source": parent_id,
            "target": node_id,
            "type": "contains"
        })
    
    if "children" in node:
        for child in node.get("children", []):
            edges.extend(create_field_edges(child, node_id))
    # 递归处理所有子节点。
    return edges

def detect_language(code: str, filename: Optional[str] = None) -> str:
    """Detect the programming language from code content and/or filename."""
    # 根据文件名或代码内容简单推断编程语言。
    if filename:
        ext = filename.split('.')[-1].lower()
        if ext in LANGUAGE_MAP:
            return LANGUAGE_MAP[ext]
    
    # Simple heuristics for language detection
    if "def " in code and ":" in code and "import " in code:
        return "python"
    elif "func " in code and "{" in code and "}" in code and "package " in code:
        return "go"
    elif "fn " in code and "let " in code and "->" in code:
        return "rust"
    elif "const " in code and "function" in code and "=>" in code:
        return "typescript"
    elif "function" in code and "var " in code and ";" in code:
        return "javascript"
    elif "class " in code and "public " in code and "void " in code:
        return "java"
    elif "int " in code and "#include" in code:
        return "c"
    elif "std::" in code or "template<" in code:
        return "cpp"
    
    # Default to Python if we can't detect
    return "python"
    # 默认返回python。

def parse_code_to_ast(code: str, language: Optional[str] = None, filename: Optional[str] = None, include_children: bool = True) -> Dict:
    """
    Parse code into an Abstract Syntax Tree (AST) using tree-sitter.
    
    Args:
        code: Source code to parse
        language: Programming language identifier (optional)
        filename: Source file name (optional, used for language detection)
        include_children: Whether to include child nodes in the result
        
    Returns:
        Dictionary representation of the AST
    """
    # 使用tree-sitter将代码解析为AST。
    # Initialize parsers if not done already
    if not languages and not init_parsers():
        return {"error": "Tree-sitter language parsers not available. Run build_parsers.py first."}
    # 若未初始化解析器则先初始化。
    
    # Detect language if not provided
    if not language:
        language = detect_language(code, filename)
    # 未指定语言时自动检测。
    
    # Normalize language identifier
    language = LANGUAGE_MAP.get(language.lower(), language.lower())
    # 规范化语言标识符。
    
    # Check if language is supported
    if language not in languages:
        return {"error": f"Unsupported language: {language}"}
    # 检查语言是否受支持。
    
    try:
        # Create a parser and set the language
        parser = Parser()
        parser.language = languages[language]
        # 创建解析器并设置语言。
        
        # Parse the code
        source_bytes = bytes(code, 'utf-8')
        tree = parser.parse(source_bytes)
        # 解析代码为语法树。
        
        # Convert to dictionary
        root_node = tree.root_node
        ast = node_to_dict(root_node, source_bytes, include_children)
        # 转换为字典结构。
        
        return {
            "language": language,
            "ast": ast
        }
    except Exception as e:
        return {"error": f"Error parsing code: {e}"}
    # 捕获异常并返回错误信息。

def create_asg_from_ast(ast_data: Dict) -> Dict:
    """
    Create an Abstract Semantic Graph (ASG) from an AST.
    
    This is a simplified version that extracts some basic semantic information.
    A production version would have more sophisticated analysis.
    
    Args:
        ast_data: AST data from parse_code_to_ast
        
    Returns:
        Dictionary representation of the ASG
    """
    # 从AST生成ASG（抽象语义图），本实现为简化版。
    if "error" in ast_data:
        return ast_data
    
    ast = ast_data["ast"]
    language = ast_data["language"]
    
    # Extract nodes and edges from the AST
    nodes = []
    edges = []
    
    def extract_nodes(node, parent_id=None):
        node_id = f"{node['type']}_{node['start_byte']}_{node['end_byte']}"
        
        # Add the node
        nodes.append({
            "id": node_id,
            "type": node["type"],
            "text": node["text"],
            "start_byte": node["start_byte"],
            "end_byte": node["end_byte"],
            "start_line": node["start_point"]["row"],
            "start_col": node["start_point"]["column"],
            "end_line": node["end_point"]["row"],
            "end_col": node["end_point"]["column"]
        })
        # 添加节点信息。
        
        # Add edge to parent if exists
        if parent_id:
            edges.append({
                "source": parent_id,
                "target": node_id,
                "type": "contains"
            })
        # 如有父节点则添加包含关系边。
        
        # Process children
        if "children" in node:
            for child in node["children"]:
                extract_nodes(child, node_id)
        # 递归处理所有子节点。
        
        return node_id
    
    # Start extraction from the root
    root_id = extract_nodes(ast)
    # 从根节点开始提取。
    
    # Add semantic edges based on language-specific rules
    if language == "python":
        add_python_semantic_edges(ast, edges)
    elif language in ["javascript", "typescript"]:
        add_js_ts_semantic_edges(ast, edges)
    # 按语言类型添加语义边。
    
    return {
        "language": language,
        "nodes": nodes,
        "edges": edges,
        "root": root_id
    }
    # 返回ASG结构。

def add_python_semantic_edges(ast: Dict, edges: List[Dict]):
    """Add Python-specific semantic edges to the ASG."""
    # 为ASG添加Python特有的语义边。
    # This is a simplified implementation for demo purposes
    # A real implementation would do much deeper analysis
    
    # Find all function definitions
    functions = {}
    variables = {}
    
    def find_definitions(node, scope=None):
        if node["type"] == "function_definition":
            # Get function name
            for child in node.get("children", []):
                if child["type"] == "identifier":
                    func_name = child["text"]
                    func_id = f"{node['type']}_{node['start_byte']}_{node['end_byte']}"
                    functions[func_name] = func_id
                    
                    # New scope for this function
                    new_scope = func_id
                    
                    # Process the function body with this new scope
                    for body_child in node.get("children", []):
                        if body_child["type"] == "block":
                            find_definitions(body_child, new_scope)
        
        elif node["type"] == "assignment":
            # Track variable assignments
            for child in node.get("children", []):
                if child["type"] == "identifier":
                    var_name = child["text"]
                    var_id = f"{child['type']}_{child['start_byte']}_{child['end_byte']}"
                    
                    # Store in current scope
                    if scope not in variables:
                        variables[scope] = {}
                    variables[scope][var_name] = var_id
        
        # Process all children
        for child in node.get("children", []):
            find_definitions(child, scope)
    
    # Start analysis from the root
    find_definitions(ast)
    
    # Now scan for references
    def find_references(node, scope=None):
        if node["type"] == "call":
            # Check for function calls
            for child in node.get("children", []):
                if child["type"] == "identifier":
                    func_name = child["text"]
                    if func_name in functions:
                        caller_id = f"{child['type']}_{child['start_byte']}_{child['end_byte']}"
                        edges.append({
                            "source": caller_id,
                            "target": functions[func_name],
                            "type": "calls"
                        })
        
        elif node["type"] == "identifier":
            # Check for variable references
            var_name = node["text"]
            var_id = f"{node['type']}_{node['start_byte']}_{node['end_byte']}"
            
            # Check in current scope first, then parent scopes
            current_scope = scope
            while current_scope is not None:
                if current_scope in variables and var_name in variables[current_scope]:
                    target_id = variables[current_scope][var_name]
                    if var_id != target_id:  # Don't link to self
                        edges.append({
                            "source": var_id,
                            "target": target_id,
                            "type": "references"
                        })
                    break
                
                # Move up to parent scope
                # This is simplistic - real implementation would track scope hierarchy
                current_scope = None
        
        # Process all children
        for child in node.get("children", []):
            find_references(child, scope)
    
    # Start reference analysis from the root
    find_references(ast)

def add_js_ts_semantic_edges(ast: Dict, edges: List[Dict]):
    """Add JavaScript/TypeScript-specific semantic edges to the ASG."""
    # 为ASG添加JS/TS特有的语义边。
    # Similar to Python version but adapted for JS/TS syntax
    # This is also a simplified implementation for demo purposes
    
    # Functionality similar to the Python version would go here
    # Since this is a demo, we're keeping it simple
    pass

def analyze_code_structure(code: str, language: Optional[str] = None, filename: Optional[str] = None) -> Dict:
    """
    Analyze code structure and provide insights.
    
    Args:
        code: Source code to analyze
        language: Programming language identifier (optional)
        filename: Source file name (optional)
        
    Returns:
        Dictionary with code structure analysis
    """
    # 分析代码结构并给出洞见。
    # Parse code to AST
    ast_data = parse_code_to_ast(code, language, filename)
    if "error" in ast_data:
        return ast_data
    
    # Perform analysis based on the AST
    language = ast_data["language"]
    ast = ast_data["ast"]
    
    # Collect structure information
    structure = {
        "language": language,
        "code_length": len(code),
        "functions": [],
        "classes": [],
        "imports": [],
        "complexity_metrics": {
            "max_nesting_level": 0,
            "total_nodes": 0
        }
    }
    # 结构信息收集，包括函数、类、导入、复杂度等。
    
    # Calculate metrics based on language
    if language == "python":
        analyze_python_structure(ast, structure)
    elif language in ["javascript", "typescript"]:
        analyze_js_ts_structure(ast, structure)
    elif language == "go":
        analyze_go_structure(ast, structure)
    # Add more language analyzers as needed
    
    return structure

def analyze_python_structure(ast: Dict, structure: Dict):
    """Analyze Python code structure."""
    # 分析Python代码结构，提取函数、类、导入、复杂度等信息。
    # Track functions
    functions = []
    classes = []
    imports = []
    
    def count_nodes(node):
        count = 1  # Count this node
        for child in node.get("children", []):
            count += count_nodes(child)
        return count
    # 递归统计AST节点总数。
    
    def find_max_nesting(node, current_depth=0):
        max_depth = current_depth
        
        # Increase depth for nesting structures
        if node["type"] in ["if_statement", "for_statement", "while_statement", "try_statement", "with_statement"]:
            current_depth += 1
            max_depth = current_depth
        
        # Check children
        for child in node.get("children", []):
            child_max = find_max_nesting(child, current_depth)
            max_depth = max(max_depth, child_max)
            
        return max_depth
    # 递归查找最大嵌套层级。
    
    def extract_structures(node):
        if node["type"] == "function_definition":
            # Extract function name
            name = ""
            for child in node.get("children", []):
                if child["type"] == "identifier":
                    name = child["text"]
                    break
            
            # Get function parameters
            params = []
            for child in node.get("children", []):
                if child["type"] == "parameters":
                    for param_child in child.get("children", []):
                        if param_child["type"] == "identifier":
                            params.append(param_child["text"])
            
            functions.append({
                "name": name,
                "location": {
                    "start_line": node["start_point"]["row"] + 1,
                    "end_line": node["end_point"]["row"] + 1
                },
                "parameters": params
            })
            
        elif node["type"] == "class_definition":
            # Extract class name
            name = ""
            for child in node.get("children", []):
                if child["type"] == "identifier":
                    name = child["text"]
                    break
                    
            classes.append({
                "name": name,
                "location": {
                    "start_line": node["start_point"]["row"] + 1,
                    "end_line": node["end_point"]["row"] + 1
                }
            })
            
        elif node["type"] == "import_statement" or node["type"] == "import_from_statement":
            # Get imported module names
            module_names = []
            for child in node.get("children", []):
                if child["type"] == "dotted_name":
                    module_names.append(child["text"])
                    
            imports.append({
                "module": ".".join(module_names),
                "line": node["start_point"]["row"] + 1
            })
        
        # Process children
        for child in node.get("children", []):
            extract_structures(child)
    # 递归提取结构信息。
    
    # Process the AST
    extract_structures(ast)
    
    # Count total nodes
    total_nodes = count_nodes(ast)
    
    # Find maximum nesting level
    max_nesting = find_max_nesting(ast)
    
    # Update structure
    structure["functions"] = functions
    structure["classes"] = classes
    structure["imports"] = imports
    structure["complexity_metrics"]["total_nodes"] = total_nodes
    structure["complexity_metrics"]["max_nesting_level"] = max_nesting

def analyze_js_ts_structure(ast: Dict, structure: Dict):
    """Analyze JavaScript/TypeScript code structure."""
    # 分析JS/TS代码结构，方法类似Python。
    # Similar implementation as the Python version but adapted for JS/TS
    # Since this is a demo, we're keeping it simplified
    pass

def analyze_go_structure(ast: Dict, structure: Dict):
    """Analyze Go code structure."""
    # 分析Go代码结构，方法类似Python。
    # Similar implementation as the Python version but adapted for Go
    # Since this is a demo, we're keeping it simplified
    pass

def register_tools(mcp_server):
    """Register all tools with the MCP server."""
    # 向MCP服务器注册所有工具。
    @mcp_server.tool()
    def parse_to_ast(code: str, language: Optional[str] = None, filename: Optional[str] = None) -> Dict:
        """
        Parse code into an Abstract Syntax Tree (AST).
        
        This tool takes source code and returns its syntax tree representation.
        The AST provides structural information about the code, showing how
        different parts of the code relate to each other syntactically.
        
        Args:
            code: The source code to parse
            language: The programming language (e.g., 'python', 'javascript')
                     If not provided, the tool will attempt to detect it
            filename: Optional filename to help with language detection
            
        Returns:
            A dictionary containing the AST and language information
        """
        # 解析代码为AST，返回语法结构信息。
        return parse_code_to_ast(code, language, filename)
    
    @mcp_server.tool()
    def generate_asg(code: str, language: Optional[str] = None, filename: Optional[str] = None) -> Dict:
        """
        Generate an Abstract Semantic Graph (ASG) from code.
        
        This tool analyzes code and creates a semantic graph that captures not just
        syntax but also semantic relationships like variable references, function calls,
        type information, and data flow where possible.
        
        Args:
            code: The source code to analyze
            language: The programming language (e.g., 'python', 'javascript')
                     If not provided, the tool will attempt to detect it
            filename: Optional filename to help with language detection
            
        Returns:
            A dictionary containing the ASG nodes, edges, and metadata
        """
        # 生成ASG，包含语法和语义关系。
        ast_data = parse_code_to_ast(code, language, filename)
        return create_asg_from_ast(ast_data)
    
    @mcp_server.tool()
    def analyze_code(code: str, language: Optional[str] = None, filename: Optional[str] = None) -> Dict:
        """
        Analyze code structure and provide insights.
        
        This tool examines code and extracts structural information like functions,
        classes, complexity metrics, and other language-specific details.
        
        Args:
            code: The source code to analyze
            language: The programming language (e.g., 'python', 'javascript')
                     If not provided, the tool will attempt to detect it
            filename: Optional filename to help with language detection
            
        Returns:
            A dictionary with analysis results including structure and metrics
        """
        # 分析代码结构，返回结构和复杂度等信息。
        return analyze_code_structure(code, language, filename)
    
    @mcp_server.tool()
    def supported_languages() -> List[str]:
        """
        Get the list of supported programming languages.
        
        Returns:
            A list of programming language identifiers that can be parsed
        """
        # 获取支持的编程语言列表。
        # Initialize parsers if not done already
        if not languages and not init_parsers():
            return []
        
        return list(languages.keys())
