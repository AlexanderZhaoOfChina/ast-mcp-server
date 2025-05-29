#!/usr/bin/env python
"""Test script for tree-sitter-languages."""
# tree-sitter-languages模块测试脚本。

import tree_sitter_languages
from tree_sitter import Parser

# Test a simple Python code snippet
# 测试一个简单的Python代码片段
code = b"""
def hello():
    print("Hello, world!")
"""
# 待解析的Python代码

# Get a parser for Python
# 获取Python的解析器（tree_sitter_languages自带的便捷方法）
parser = tree_sitter_languages.get_parser('python')
tree = parser.parse(code)
root = tree.root_node

print(f"Python root node type: {root.type}")
print(f"S-expression: {root.sexp()}")
# 打印根节点类型和S表达式（树结构的简洁表示）

# Alternative way using get_language and Parser
# 另一种方式：手动获取Language对象并创建Parser
python_lang = tree_sitter_languages.get_language('python')
custom_parser = Parser()
custom_parser.set_language(python_lang)

# 用自定义解析器解析同一段代码
# 这样可以灵活控制parser的行为
tree2 = custom_parser.parse(code)
print(f"Tree2 root node type: {tree2.root_node.type}")
# 打印自定义解析器的根节点类型
