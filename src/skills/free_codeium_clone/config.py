"""
Free Codeium Clone 配置文件
"""

import os
from typing import Dict, Any, List
from enum import Enum
from dataclasses import dataclass


class Environment(str, Enum):
    """运行环境枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class ApiProvider(str, Enum):
    """API提供商枚举"""
    DEEPSEEK = "deepseek"
    MINIMAX = "minimax"
    KIMI = "kimi"
    TONGYI = "tongyi"


@dataclass
class ApiConfig:
    """API配置"""
    provider: ApiProvider
    api_key: str
    base_url: str
    model: str
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout_seconds: int = 30
    max_retries: int = 3
    
    # 成本配置（美元/百万tokens）
    cost_per_million_tokens: float = 0.85  # 默认DeepSeek价格
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """计算API调用成本"""
        total_tokens = input_tokens + output_tokens
        return (total_tokens / 1_000_000) * self.cost_per_million_tokens


@dataclass
class ProbeConfig:
    """探针配置"""
    enabled: bool = True
    collect_metrics: bool = True
    send_to_central_service: bool = True
    
    # 数据采集配置
    collect_user_behavior: bool = True
    collect_performance_data: bool = True
    collect_error_details: bool = True
    
    # 探针埋点
    probe_points: List[str] = None
    
    def __post_init__(self):
        if self.probe_points is None:
            self.probe_points = [
                "request_start",
                "api_call_start",
                "api_call_end",
                "response_generated",
                "quality_check_done",
                "request_complete"
            ]


@dataclass
class QualityCheckConfig:
    """质量检查配置"""
    enabled: bool = True
    min_score: int = 60
    max_line_length: int = 100
    
    # 各语言特定规则
    python_rules: List[str] = None
    javascript_rules: List[str] = None
    java_rules: List[str] = None
    
    def __post_init__(self):
        if self.python_rules is None:
            self.python_rules = [
                "遵循PEP8编码规范",
                "函数和方法使用小写字母和下划线分隔",
                "类名使用驼峰命名法",
                "导入语句放在文件顶部",
                "避免使用魔术数字"
            ]
        
        if self.javascript_rules is None:
            self.javascript_rules = [
                "使用严格模式 ('use strict')",
                "使用const和let而非var",
                "函数名使用驼峰命名法",
                "使用箭头函数而非function关键字",
                "添加JSDoc注释"
            ]
        
        if self.java_rules is None:
            self.java_rules = [
                "遵循Java编码规范",
                "类名使用驼峰命名法",
                "方法名使用驼峰命名法",
                "添加JavaDoc注释",
                "使用适当的访问修饰符"
            ]
    
    def get_rules_for_language(self, language: str) -> List[str]:
        """获取指定语言的规则"""
        language = language.lower()
        if language == "python":
            return self.python_rules
        elif language in ["javascript", "js"]:
            return self.javascript_rules
        elif language == "java":
            return self.java_rules
        else:
            return ["遵循通用的编程最佳实践"]


@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    default_ttl: int = 3600  # 1小时
    max_cache_size: int = 10000


@dataclass
class MetricsConfig:
    """指标配置"""
    enabled: bool = True
    flush_interval_seconds: int = 60
    retention_days: int = 30
    
    # 关键指标阈值
    max_response_time_ms: int = 5000
    min_success_rate_percent: float = 95.0
    max_token_cost_per_request_usd: float = 0.01


class Config:
    """主配置类"""
    
    def __init__(self, env: Environment = None):
        self.environment = env or self._detect_environment()
        self.version = "1.0.0"
        self.debug = self.environment == Environment.DEVELOPMENT
        
        # API配置
        self.api_configs = self._init_api_configs()
        
        # 探针配置
        self.probe_config = ProbeConfig()
        
        # 质量检查配置
        self.quality_config = QualityCheckConfig()
        
        # 缓存配置
        self.cache_config = CacheConfig()
        
        # 指标配置
        self.metrics_config = MetricsConfig()
        
        # 应用配置
        self.supported_languages = ["python", "javascript", "java", "typescript", "cpp", "go", "rust", "php"]
        self.max_request_length = 4000
        self.max_concurrent_requests = 100
        
        # 初始化完成
        print(f"配置初始化完成 - 环境: {self.environment.value}")
    
    def _detect_environment(self) -> Environment:
        """检测运行环境"""
        env = os.getenv("APP_ENV", "").lower()
        
        if env == "production":
            return Environment.PRODUCTION
        elif env == "testing":
            return Environment.TESTING
        else:
            return Environment.DEVELOPMENT
    
    def _init_api_configs(self) -> Dict[ApiProvider, ApiConfig]:
        """初始化API配置"""
        api_configs = {}
        
        # DeepSeek配置
        api_configs[ApiProvider.DEEPSEEK] = ApiConfig(
            provider=ApiProvider.DEEPSEEK,
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            base_url="https://api.deepseek.com",
            model="deepseek-coder",
            max_tokens=4096,
            temperature=0.8,
            cost_per_million_tokens=0.85
        )
        
        # MiniMax配置（基于之前的测试）
        api_configs[ApiProvider.MINIMAX] = ApiConfig(
            provider=ApiProvider.MINIMAX,
            api_key=os.getenv("MINIMAX_API_KEY", ""),
            base_url="https://api.minimax.chat",
            model="abab6.5s-chat",
            max_tokens=2048,
            temperature=0.7,
            cost_per_million_tokens=0.75  # 注：MiniMax分开计价，这里为平均价
        )
        
        # Kimi配置
        api_configs[ApiProvider.KIMI] = ApiConfig(
            provider=ApiProvider.KIMI,
            api_key=os.getenv("KIMI_API_KEY", ""),
            base_url="https://api.moonshot.cn",
            model="moonshot-v1-8k",
            max_tokens=8192,
            temperature=0.7,
            cost_per_million_tokens=0.80
        )
        
        # 通义千问配置
        api_configs[ApiProvider.TONGYI] = ApiConfig(
            provider=ApiProvider.TONGYI,
            api_key=os.getenv("TONGYI_API_KEY", ""),
            base_url="https://dashscope.aliyuncs.com",
            model="qwen-plus",
            max_tokens=2048,
            temperature=0.8,
            cost_per_million_tokens=0.90
        )
        
        return api_configs
    
    def get_available_providers(self) -> List[ApiProvider]:
        """获取可用的API提供商（有API密钥的）"""
        available = []
        for provider, config in self.api_configs.items():
            if config.api_key:
                available.append(provider)
        return available
    
    def get_provider_cost(self, provider: ApiProvider) -> float:
        """获取提供商成本"""
        config = self.api_configs.get(provider)
        if config:
            return config.cost_per_million_tokens
        return 1.0  # 默认成本
    
    def validate(self) -> List[str]:
        """验证配置，返回错误列表"""
        errors = []
        
        # 检查至少一个API提供商可用
        available_providers = self.get_available_providers()
        if not available_providers:
            errors.append("至少需要一个API提供商配置有效的API密钥")
        
        # 检查环境变量
        if self.environment == Environment.PRODUCTION and self.debug:
            errors.append("生产环境不应启用调试模式")
        
        # 检查请求长度限制
        if self.max_request_length < 100:
            errors.append("最大请求长度至少为100字符")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "environment": self.environment.value,
            "version": self.version,
            "debug": self.debug,
            "api_configs": {
                provider.value: {
                    "api_key": "***" if config.api_key else "",
                    "base_url": config.base_url,
                    "model": config.model,
                    "max_tokens": config.max_tokens,
                    "temperature": config.temperature,
                    "cost_per_million_tokens": config.cost_per_million_tokens
                }
                for provider, config in self.api_configs.items()
            },
            "probe_config": {
                "enabled": self.probe_config.enabled,
                "collect_metrics": self.probe_config.collect_metrics,
                "send_to_central_service": self.probe_config.send_to_central_service
            },
            "quality_config": {
                "enabled": self.quality_config.enabled,
                "min_score": self.quality_config.min_score,
                "max_line_length": self.quality_config.max_line_length
            },
            "cache_config": {
                "enabled": self.cache_config.enabled,
                "redis_host": self.cache_config.redis_host,
                "redis_port": self.cache_config.redis_port
            },
            "metrics_config": {
                "enabled": self.metrics_config.enabled,
                "flush_interval_seconds": self.metrics_config.flush_interval_seconds
            },
            "supported_languages": self.supported_languages,
            "max_request_length": self.max_request_length,
            "max_concurrent_requests": self.max_concurrent_requests
        }


# 全局配置实例
config = Config()

# 导出常用配置项
ENVIRONMENT = config.environment
DEBUG = config.debug
SUPPORTED_LANGUAGES = config.supported_languages
MAX_REQUEST_LENGTH = config.max_request_length