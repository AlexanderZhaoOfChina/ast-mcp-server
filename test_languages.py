#!/usr/bin/env python
"""Test script for tree-sitter language modules."""
# tree-sitter语言模块测试脚本。

import tree_sitter_python
import tree_sitter_javascript
from tree_sitter import Language, Parser

# Test Python
print("Setting up Python language...")
# 设置并测试Python语言解析器
python_language = Language(tree_sitter_python.language())
python_parser = Parser()
# Use the language property instead of set_language method
# 使用language属性而不是set_language方法
python_parser.language = python_language

python_code = b"""
def hello():
    print("Hello, world!")
"""
# 待解析的Python代码片段

python_tree = python_parser.parse(python_code)
print("Python parsing successful!")
print(f"Root node type: {python_tree.root_node.type}")
# 检查节点有哪些属性
print("Node attributes:")
print(dir(python_tree.root_node))
# 打印树结构的字符串表示
print(f"Node representation: {python_tree.root_node}")
# 打印根节点的所有子节点
print("Children:")
for i, child in enumerate(python_tree.root_node.children):
    print(f"Child {i}: {child.type}")
print("-" * 50)

# Test JavaScript
print("Setting up JavaScript language...")
# 设置并测试JavaScript语言解析器
js_language = Language(tree_sitter_javascript.language())
js_parser = Parser()
# Use the language property instead of set_language method
# 使用language属性而不是set_language方法
js_parser.language = js_language

js_code = b"""
function hello() {
    console.log("Hello, world!");
}
"""
# 待解析的JavaScript代码片段

js_tree = js_parser.parse(js_code)
print("JavaScript parsing successful!")
print(f"Root node type: {js_tree.root_node.type}")
# 打印根节点的所有子节点
print("Children:")
for i, child in enumerate(js_tree.root_node.children):
    print(f"Child {i}: {child.type}")
