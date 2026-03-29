"""
Free Codeium Clone - 主应用模块
提供多语言代码生成、智能补全、基础质量检查功能
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

from src.utils.multi_model_router import MultiModelRouter, RoutingStrategy
from src.code_assistant.config import ApiProvider


class CodeRequestType(str, Enum):
    """代码请求类型枚举"""
    CODE_COMPLETION = "code_completion"        # 代码补全
    FUNCTION_GENERATION = "function_generation" # 函数生成
    CODE_EXPLANATION = "code_explanation"      # 代码解释
    CODE_REFACTORING = "code_refactoring"      # 代码重构


class CodeLanguage(str, Enum):
    """支持的编程语言"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    TYPESCRIPT = "typescript"
    CPP = "cpp"
    GO = "go"
    RUST = "rust"
    PHP = "php"


class CodeAssistant:
    """免费代码助手核心类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.router = MultiModelRouter()
        
        # 性能监控指标
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens_used": 0,
            "total_cost_usd": 0.0,
            "request_history": []
        }
        
        # 语言特定提示模板
        self.language_templates = {
            CodeLanguage.PYTHON: {
                "completion": "Complete the Python code: {code_context}\n# Complete the code:",
                "function": "Generate a Python function based on the description: {description}\nRequirements: {requirements}\nGenerate a complete function with proper docstring:",
                "explanation": "Explain this Python code:\n{code}\nExplanation:"
            },
            CodeLanguage.JAVASCRIPT: {
                "completion": "Complete the JavaScript code: {code_context}\n// Complete the code:",
                "function": "Generate a JavaScript function based on the description: {description}\nRequirements: {requirements}\nGenerate a complete function with JSDoc:",
                "explanation": "Explain this JavaScript code:\n{code}\nExplanation:"
            },
            CodeLanguage.JAVA: {
                "completion": "Complete the Java code: {code_context}\n// Complete the code:",
                "function": "Generate a Java method based on the description: {description}\nRequirements: {requirements}\nGenerate a complete method with JavaDoc:",
                "explanation": "Explain this Java code:\n{code}\nExplanation:"
            }
        }
        
        # 质量检查规则
        self.quality_rules = {
            "python": [
                "遵循PEP8编码规范",
                "函数和方法使用小写字母和下划线分隔",
                "类名使用驼峰命名法",
                "导入语句放在文件顶部",
                "避免使用魔术数字"
            ],
            "javascript": [
                "使用严格模式 ('use strict')",
                "使用const和let而非var",
                "函数名使用驼峰命名法",
                "使用箭头函数而非function关键字",
                "添加JSDoc注释"
            ],
            "java": [
                "遵循Java编码规范",
                "类名使用驼峰命名法",
                "方法名使用驼峰命名法",
                "添加JavaDoc注释",
                "使用适当的访问修饰符"
            ]
        }
        
        self.logger.info("Free Codeium Clone 初始化完成")
    
    def process_request(self, 
                       request_type: str,
                       language: str,
                       code_context: str = "",
                       description: str = "",
                       requirements: str = "",
                       style_guide: str = "",
                       user_id: str = "anonymous") -> Dict[str, Any]:
        """
        处理代码请求
        
        Args:
            request_type: 请求类型 (code_completion/function_generation/code_explanation/code_refactoring)
            language: 编程语言
            code_context: 代码上下文（用于补全或解释）
            description: 功能描述（用于函数生成）
            requirements: 具体需求
            style_guide: 编码规范
            user_id: 用户ID（用于监控）
            
        Returns:
            处理结果字典
        """
        start_time = time.time()
        self.metrics["total_requests"] += 1
        
        try:
            # 验证请求参数
            self._validate_request(request_type, language, code_context, description)
            
            # 构建提示词
            prompt = self._build_prompt(
                request_type=request_type,
                language=language,
                code_context=code_context,
                description=description,
                requirements=requirements,
                style_guide=style_guide
            )
            
            # 预估token数（用于路由决策）
            estimated_input_tokens = len(prompt) // 4  # 近似估计
            estimated_output_tokens = 500  # 默认输出长度
            
            # 选择API提供商（成本优先策略）
            provider, selection_reason = self.router.select_provider(
                estimated_input_tokens=estimated_input_tokens,
                estimated_output_tokens=estimated_output_tokens,
                priority="cost"
            )
            
            # 记录请求开始时间
            request_start = time.time()
            
            # 这里应该调用实际的API客户端
            # 由于这是原型，我们模拟响应
            generated_code = self._simulate_api_call(
                prompt=prompt,
                request_type=request_type,
                language=language
            )
            
            # 模拟响应时间和token消耗
            response_time_ms = (time.time() - request_start) * 1000
            input_tokens = estimated_input_tokens
            output_tokens = len(generated_code) // 4
            
            # 更新路由器性能指标
            self.router.update_metrics(
                provider=provider,
                success=True,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                response_time_ms=response_time_ms
            )
            
            # 构建响应
            result = {
                "status": "success",
                "generated_code": generated_code,
                "language": language,
                "request_type": request_type,
                "tokens_used": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens
                },
                "provider": provider.value,
                "selection_reason": selection_reason,
                "quality_check": self._perform_quality_check(generated_code, language),
                "response_time_ms": round(response_time_ms, 2),
                "timestamp": datetime.now().isoformat()
            }
            
            # 更新本地指标
            self.metrics["successful_requests"] += 1
            self.metrics["total_tokens_used"] += input_tokens + output_tokens
            self.metrics["request_history"].append({
                "user_id": user_id,
                "request_type": request_type,
                "language": language,
                "tokens_used": input_tokens + output_tokens,
                "timestamp": datetime.now().isoformat(),
                "success": True
            })
            
            # 计算成本（探针功能）
            cost_estimate = self._estimate_cost(provider, input_tokens, output_tokens)
            self.metrics["total_cost_usd"] += cost_estimate
            result["estimated_cost_usd"] = round(cost_estimate, 6)
            
            return result
            
        except Exception as e:
            self.metrics["failed_requests"] += 1
            self.metrics["request_history"].append({
                "user_id": user_id,
                "request_type": request_type,
                "language": language,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "success": False
            })
            
            return {
                "status": "error",
                "error_type": e.__class__.__name__,
                "error_message": str(e),
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.now().isoformat()
            }
    
    def _validate_request(self, 
                         request_type: str,
                         language: str,
                         code_context: str,
                         description: str):
        """验证请求参数"""
        # 验证请求类型
        try:
            CodeRequestType(request_type)
        except ValueError:
            raise ValueError(f"无效的请求类型: {request_type}")
        
        # 验证语言
        try:
            CodeLanguage(language)
        except ValueError:
            raise ValueError(f"不支持的语言: {language}")
        
        # 验证内容
        if request_type == CodeRequestType.CODE_COMPLETION and not code_context:
            raise ValueError("代码补全需要提供代码上下文")
        
        if request_type == CodeRequestType.FUNCTION_GENERATION and not description:
            raise ValueError("函数生成需要提供功能描述")
        
        # 验证输入长度
        max_length = 4000
        if len(code_context) > max_length:
            raise ValueError(f"代码上下文过长（最大{max_length}字符）")
        
        if len(description) > max_length:
            raise ValueError(f"功能描述过长（最大{max_length}字符）")
    
    def _build_prompt(self,
                     request_type: str,
                     language: str,
                     code_context: str,
                     description: str,
                     requirements: str,
                     style_guide: str) -> str:
        """构建提示词"""
        lang_enum = CodeLanguage(language)
        
        if request_type == CodeRequestType.CODE_COMPLETION:
            template = self.language_templates[lang_enum]["completion"]
            return template.format(code_context=code_context)
        
        elif request_type == CodeRequestType.FUNCTION_GENERATION:
            template = self.language_templates[lang_enum]["function"]
            req_text = requirements if requirements else "功能正确、代码清晰、有适当的错误处理"
            return template.format(description=description, requirements=req_text)
        
        elif request_type == CodeRequestType.CODE_EXPLANATION:
            template = self.language_templates[lang_enum]["explanation"]
            return template.format(code=code_context)
        
        else:
            # 默认为代码补全
            template = self.language_templates[lang_enum]["completion"]
            return template.format(code_context=code_context)
    
    def _simulate_api_call(self,
                          prompt: str,
                          request_type: str,
                          language: str) -> str:
        """模拟API调用（原型阶段）"""
        # 在实际实现中，这里应该调用真正的API客户端
        
        # 基于请求类型和语言生成示例代码
        if request_type == CodeRequestType.CODE_COMPLETION:
            if language == CodeLanguage.PYTHON.value:
                return "def calculate_average(numbers):\n    \"\"\"计算数字列表的平均值\"\"\"\n    if not numbers:\n        return 0\n    return sum(numbers) / len(numbers)"
            elif language == CodeLanguage.JAVASCRIPT.value:
                return "function calculateAverage(numbers) {\n    // 计算数字数组的平均值\n    if (!numbers || numbers.length === 0) {\n        return 0;\n    }\n    const sum = numbers.reduce((acc, num) => acc + num, 0);\n    return sum / numbers.length;\n}"
            else:
                return "// 代码补全结果"
        
        elif request_type == CodeRequestType.FUNCTION_GENERATION:
            if language == CodeLanguage.PYTHON.value:
                return """def process_user_data(user_data):
    \"\"\"处理用户数据
    
    Args:
        user_data (dict): 用户数据字典
        
    Returns:
        dict: 处理后的用户数据
        
    Raises:
        ValueError: 如果用户数据无效
    \"\"\"
    if not isinstance(user_data, dict):
        raise ValueError("用户数据必须是字典类型")
    
    # 验证必需字段
    required_fields = ['id', 'name', 'email']
    for field in required_fields:
        if field not in user_data:
            raise ValueError(f"缺少必需字段: {field}")
    
    # 处理数据
    processed_data = {
        'user_id': str(user_data['id']),
        'username': user_data['name'].strip(),
        'email': user_data['email'].lower(),
        'processed_at': datetime.now().isoformat()
    }
    
    return processed_data"""
            else:
                return "// 生成的函数代码"
        
        else:
            return "// 生成的代码"
    
    def _perform_quality_check(self, code: str, language: str) -> Dict[str, Any]:
        """执行代码质量检查"""
        quality_result = {
            "passed": True,
            "issues": [],
            "suggestions": [],
            "score": 100
        }
        
        # 基础检查
        lines = code.split('\n')
        
        # 检查代码长度
        if len(lines) > 100:
            quality_result["issues"].append("代码过长，建议拆分为更小的函数")
            quality_result["score"] -= 10
        
        # 检查注释比例
        comment_lines = sum(1 for line in lines if line.strip().startswith(('#', '//', '/*', '*')))
        if len(lines) > 0:
            comment_ratio = comment_lines / len(lines)
            if comment_ratio < 0.1:
                quality_result["suggestions"].append("建议增加代码注释以提高可读性")
            elif comment_ratio > 0.4:
                quality_result["suggestions"].append("注释过多，建议简化代码逻辑")
        
        # 语言特定检查
        if language == CodeLanguage.PYTHON.value:
            if 'print(' in code and 'logging.' not in code:
                quality_result["suggestions"].append("建议使用logging模块而非print语句用于生产环境")
        
        elif language == CodeLanguage.JAVASCRIPT.value:
            if 'var ' in code:
                quality_result["issues"].append("建议使用const或let替代var声明变量")
                quality_result["score"] -= 5
        
        # 更新通过状态
        if len(quality_result["issues"]) > 0:
            quality_result["passed"] = False
            quality_result["score"] = max(60, quality_result["score"])  # 最低60分
        
        return quality_result
    
    def _estimate_cost(self, provider: ApiProvider, input_tokens: int, output_tokens: int) -> float:
        """估算API调用成本"""
        if provider == ApiProvider.MINIMAX:
            # MiniMax分开计价
            input_cost = (input_tokens / 1_000_000) * 0.30  # $0.30/百万输入tokens
            output_cost = (output_tokens / 1_000_000) * 1.20  # $1.20/百万输出tokens
            return input_cost + output_cost
        else:
            # 其他提供商统一价格
            total_tokens = input_tokens + output_tokens
            api_config = self.router.config.api_configs.get(provider)
            if api_config:
                return (total_tokens / 1_000_000) * api_config.cost_per_million_tokens
            return 0.0
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        total_requests = self.metrics["total_requests"]
        successful_requests = self.metrics["successful_requests"]
        
        success_rate = 0
        if total_requests > 0:
            success_rate = successful_requests / total_requests * 100
        
        avg_tokens_per_request = 0
        if successful_requests > 0:
            avg_tokens_per_request = self.metrics["total_tokens_used"] / successful_requests
        
        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": self.metrics["failed_requests"],
            "success_rate_percent": round(success_rate, 2),
            "total_tokens_used": self.metrics["total_tokens_used"],
            "avg_tokens_per_request": round(avg_tokens_per_request, 2),
            "total_cost_usd": round(self.metrics["total_cost_usd"], 6),
            "timestamp": datetime.now().isoformat()
        }
    
    def reset_metrics(self):
        """重置指标"""
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens_used": 0,
            "total_cost_usd": 0.0,
            "request_history": []
        }
        self.logger.info("指标已重置")


# 全局实例
code_assistant = CodeAssistant()