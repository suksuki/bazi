"""
逻辑格式转换器 (Logic Adapter)
将Python表达式字符串转换为JSONLogic格式

用于处理小模型（如qwen2.5:3b）输出的Python表达式格式
"""

import ast
import json
from typing import Any, Dict, Union


class PythonToJSONLogic(ast.NodeVisitor):
    """
    将Python表达式字符串转换为JSONLogic格式
    例如: "(ten_gods.ZS > 0) & (ten_gods.ZR == 1)"
      -> {"and": [{" >": [{"var": "ten_gods.ZS"}, 0]}, {"==": [{"var": "ten_gods.ZR"}, 1]}]}
    """
    
    def translate(self, expression_str: str) -> Union[Dict[str, Any], str]:
        """
        将Python表达式字符串转换为JSONLogic格式
        
        Args:
            expression_str: Python表达式字符串
            
        Returns:
            JSONLogic格式的字典，如果转换失败则返回原始字符串
        """
        try:
            # 清理输入：去掉可能存在的markdown标记和空白
            clean_str = expression_str.strip()
            clean_str = clean_str.replace("```python", "").replace("```json", "").replace("```", "").strip()
            
            # 如果已经是字典格式（JSON字符串），尝试解析
            if clean_str.startswith("{") and clean_str.endswith("}"):
                try:
                    return json.loads(clean_str)
                except:
                    pass
            
            # 解析为AST
            tree = ast.parse(clean_str, mode='eval')
            result = self.visit(tree.body)
            
            # 确保返回的是JSONLogic格式（必须有根节点）
            if isinstance(result, dict):
                # 如果已经有and/or根节点，直接返回
                if "and" in result or "or" in result:
                    return result
                # 否则包装在and中
                return {"and": [result]}
            
            return result
            
        except Exception as e:
            print(f"⚠️  Logic Adapter转换失败: {e}")
            print(f"   输入: {expression_str[:100]}...")
            # 转换失败，返回原始字符串，交由后续验证器处理
            return expression_str
    
    def visit_BoolOp(self, node: ast.BoolOp) -> Dict[str, list]:
        """处理 and, or 操作"""
        op = "and" if isinstance(node.op, ast.And) else "or"
        values = [self.visit(value) for value in node.values]
        return {op: values}
    
    def visit_BinOp(self, node: ast.BinOp) -> Dict[str, list]:
        """
        处理二元操作
        注意：Python中 & 和 | 是位运算，但模型可能用来表示逻辑运算
        """
        # 处理位运算 & (模型常把and写成&)
        if isinstance(node.op, ast.BitAnd):
            return {
                "and": [self.visit(node.left), self.visit(node.right)]
            }
        elif isinstance(node.op, ast.BitOr):
            return {
                "or": [self.visit(node.left), self.visit(node.right)]
            }
        else:
            # 其他二元运算（+、-等），这里简化处理
            # 实际使用中很少遇到，返回原始结构
            return {
                "and": [self.visit(node.left), self.visit(node.right)]
            }
    
    def visit_Compare(self, node: ast.Compare) -> Dict[str, list]:
        """处理比较操作 >, <, ==, !=, >=, <="""
        left = self.visit(node.left)
        
        ops_map = {
            ast.Gt: ">",
            ast.Lt: "<",
            ast.GtE: ">=",
            ast.LtE: "<=",
            ast.Eq: "==",
            ast.NotEq: "!=",
        }
        
        # 简化处理：通常只有一个比较符
        if len(node.ops) == 1:
            op_node = node.ops[0]
            op_str = ops_map.get(type(op_node), "==")
            right = self.visit(node.comparators[0])
            return {op_str: [left, right]}
        else:
            # 多个比较符（如 a < b < c），转换为and链
            conditions = []
            conditions.append({ops_map.get(type(node.ops[0]), "=="): [left, self.visit(node.comparators[0])]})
            for i in range(1, len(node.ops)):
                conditions.append({
                    ops_map.get(type(node.ops[i]), "=="): [
                        self.visit(node.comparators[i-1]),
                        self.visit(node.comparators[i])
                    ]
                })
            return {"and": conditions}
    
    def visit_Attribute(self, node: ast.Attribute) -> Dict[str, str]:
        """处理属性访问 ten_gods.ZS"""
        value = self.visit(node.value)
        # value通常是字符串（如"ten_gods"），组合成"ten_gods.ZS"
        if isinstance(value, str):
            return {"var": f"{value}.{node.attr}"}
        elif isinstance(value, dict) and "var" in value:
            return {"var": f"{value['var']}.{node.attr}"}
        else:
            return {"var": f"{value}.{node.attr}"}
    
    def visit_Name(self, node: ast.Name) -> Union[str, Dict[str, str]]:
        """处理变量名"""
        # 对于简单变量名，返回字符串（后续会包装为var）
        return node.id
    
    def visit_Subscript(self, node: ast.Subscript) -> Dict[str, str]:
        """处理下标访问 ten_gods['ZS'] 或 self_energy['ZS']"""
        value = self.visit(node.value)
        
        # 提取索引值
        if isinstance(node.slice, ast.Index):  # Python < 3.9
            slice_value = node.slice.value
        else:  # Python >= 3.9
            slice_value = node.slice
        
        if isinstance(slice_value, ast.Str):  # Python < 3.8
            idx = slice_value.s
        elif isinstance(slice_value, ast.Constant):  # Python >= 3.8
            idx = slice_value.value
        else:
            idx = self.visit(slice_value)
        
        # 构建var表达式
        if isinstance(value, str):
            return {"var": f"{value}.{idx}"}
        elif isinstance(value, dict) and "var" in value:
            # 如果value已经是var结构，尝试合并
            return {"var": f"{value['var']}.{idx}"}
        else:
            return {"var": f"{value}.{idx}"}
    
    def visit_Constant(self, node: ast.Constant) -> Any:
        """处理常量（Python 3.8+）"""
        return node.value
    
    def visit_Num(self, node: ast.Num) -> Union[int, float]:
        """处理数字（Python < 3.8兼容）"""
        return node.n
    
    def visit_Str(self, node: ast.Str) -> str:
        """处理字符串（Python < 3.8兼容）"""
        return node.s
    
    def visit_NameConstant(self, node: ast.NameConstant) -> Any:
        """处理None, True, False（Python < 3.8兼容）"""
        return node.value
    
    def generic_visit(self, node: ast.AST) -> Any:
        """处理其他未覆盖的节点类型"""
        raise ValueError(f"不支持的AST节点类型: {type(node).__name__}")


def convert_python_to_jsonlogic(expression_str: str) -> Union[Dict[str, Any], str]:
    """
    便捷函数：将Python表达式转换为JSONLogic
    
    Args:
        expression_str: Python表达式字符串
        
    Returns:
        JSONLogic格式的字典，如果转换失败则返回原始字符串
    """
    adapter = PythonToJSONLogic()
    return adapter.translate(expression_str)


# --- 单元测试 ---
if __name__ == "__main__":
    adapter = PythonToJSONLogic()
    
    # 测试模型常输出的格式
    test_cases = [
        "(ten_gods.ZS > 0) & (ten_gods.ZR == 1)",
        "(ten_gods['PC'] > ten_gods['ZS'])",
        "self_energy['ZS'] > 0",
        "(exist(ten_gods.PC) and exist(ten_gods.ZS)) > (exist(ten_gods.ZC))",
    ]
    
    print("=" * 60)
    print("逻辑格式转换器测试")
    print("=" * 60)
    print()
    
    for i, case in enumerate(test_cases, 1):
        print(f"测试 {i}: {case}")
        try:
            result = adapter.translate(case)
            print(f"输出: {json.dumps(result, indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"❌ 转换失败: {e}")
        print("-" * 60)
        print()

