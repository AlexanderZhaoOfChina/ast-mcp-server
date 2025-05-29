"""
AST/ASG resources for the MCP server.

This module defines the resources that provide code structure and semantic information
through the Model Context Protocol.
"""
# MCP服务器的AST/ASG资源模块。
# 本模块通过Model Context Protocol定义了提供代码结构和语义信息的资源。

import os
import json
from typing import Dict, Optional, List, Any
import tempfile
import hashlib
from .tools import parse_code_to_ast, create_asg_from_ast, analyze_code_structure

# Directory to store cached ASTs and ASGs
CACHE_DIR = os.path.join(tempfile.gettempdir(), "ast_mcp_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
# 用于存储AST和ASG缓存的目录，使用系统临时目录。
# 若目录不存在则自动创建。

def get_cache_path(code_hash: str, resource_type: str) -> str:
    """Get the cache file path for a given code hash and resource type."""
    # 获取指定代码哈希和资源类型的缓存文件路径。
    return os.path.join(CACHE_DIR, f"{code_hash}_{resource_type}.json")

def get_code_hash(code: str) -> str:
    """Generate a hash for the code to use as a cache key."""
    # 生成代码的哈希值，用作缓存键。
    return hashlib.md5(code.encode('utf-8')).hexdigest()

def cache_resource(code: str, resource_type: str, data: Dict) -> None:
    """Cache a resource for faster retrieval."""
    # 缓存资源，加快后续检索速度。
    code_hash = get_code_hash(code)
    cache_path = get_cache_path(code_hash, resource_type)
    
    try:
        with open(cache_path, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error caching resource: {e}")
    # 写入缓存文件，若失败则打印错误。

def get_cached_resource(code: str, resource_type: str) -> Optional[Dict]:
    """Get a cached resource if available."""
    # 获取已缓存的资源（如存在）。
    code_hash = get_code_hash(code)
    cache_path = get_cache_path(code_hash, resource_type)
    
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading cached resource: {e}")
    # 若缓存文件存在则读取，否则返回None。
    return None

def register_resources(mcp_server):
    """Register all resources with the MCP server."""
    # 向MCP服务器注册所有资源。
    
    @mcp_server.resource("ast://{code_hash}")
    def ast_resource(code_hash: str) -> Dict:
        """
        Resource that provides the Abstract Syntax Tree for a piece of code.
        
        The code_hash is used to locate the cached AST. If not found, this will
        return an error - the AST should be created first using the parse_to_ast tool.
        
        Args:
            code_hash: Hash of the code to retrieve AST for
            
        Returns:
            The cached AST data
        """
        # 提供指定代码哈希的AST资源。
        # 若缓存不存在则提示需先生成AST。
        cache_path = get_cache_path(code_hash, "ast")
        
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                return {"error": f"Error reading cached AST: {e}"}
        
        return {"error": "AST not found. Please use parse_to_ast tool first."}
    
    @mcp_server.resource("asg://{code_hash}")
    def asg_resource(code_hash: str) -> Dict:
        """
        Resource that provides the Abstract Semantic Graph for a piece of code.
        
        The code_hash is used to locate the cached ASG. If not found, this will
        return an error - the ASG should be created first using the generate_asg tool.
        
        Args:
            code_hash: Hash of the code to retrieve ASG for
            
        Returns:
            The cached ASG data
        """
        # 提供指定代码哈希的ASG资源。
        # 若缓存不存在则提示需先生成ASG。
        cache_path = get_cache_path(code_hash, "asg")
        
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                return {"error": f"Error reading cached ASG: {e}"}
        
        return {"error": "ASG not found. Please use generate_asg tool first."}
    
    @mcp_server.resource("analysis://{code_hash}")
    def analysis_resource(code_hash: str) -> Dict:
        """
        Resource that provides code structure analysis.
        
        The code_hash is used to locate the cached analysis. If not found, this will
        return an error - the analysis should be created first using the analyze_code tool.
        
        Args:
            code_hash: Hash of the code to retrieve analysis for
            
        Returns:
            The cached analysis data
        """
        # 提供指定代码哈希的结构分析资源。
        # 若缓存不存在则提示需先生成分析。
        cache_path = get_cache_path(code_hash, "analysis")
        
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                return {"error": f"Error reading cached analysis: {e}"}
        
        return {"error": "Analysis not found. Please use analyze_code tool first."}
    
    # Custom resource handler for AST node detail
    @mcp_server.resource("ast://{code_hash}/node/{node_id}")
    def ast_node_resource(code_hash: str, node_id: str) -> Dict:
        """
        Resource that provides details about a specific AST node.
        
        Args:
            code_hash: Hash of the code containing the AST
            node_id: ID of the node to retrieve
            
        Returns:
            The node details
        """
        # 提供指定AST节点的详细信息。
        # 先获取AST缓存，再递归查找目标节点。
        # 若AST不存在则提示需先生成。
        # 若节点未找到则返回错误。
        # 递归查找节点时，节点ID格式为 type_startByte_endByte。
        # 该方法适合用于定位和展示AST的具体节点信息。
        # Get the full AST
        cache_path = get_cache_path(code_hash, "ast")
        
        if not os.path.exists(cache_path):
            return {"error": "AST not found. Please use parse_to_ast tool first."}
        
        try:
            with open(cache_path, 'r') as f:
                ast_data = json.load(f)
            
            # Find the node by its ID
            def find_node(node, target_id):
                # Generate this node's ID
                current_id = f"{node['type']}_{node['start_byte']}_{node['end_byte']}"
                
                if current_id == target_id:
                    return node
                
                # Search in children
                for child in node.get("children", []):
                    result = find_node(child, target_id)
                    if result:
                        return result
                
                return None
            
            node = find_node(ast_data["ast"], node_id)
            
            if node:
                return node
            else:
                return {"error": f"Node with ID {node_id} not found in the AST"}
            
        except Exception as e:
            return {"error": f"Error retrieving AST node: {e}"}
        # 若读取或查找节点出错则返回错误信息。
