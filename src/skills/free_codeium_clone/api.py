"""
Free Codeium Clone API 接口
提供RESTful API供外部调用
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from .main import CodeAssistant, CodeRequestType, CodeLanguage


# 创建FastAPI应用
app = FastAPI(
    title="Free Codeium Clone API",
    description="免费的多语言代码生成助手API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化代码助手
code_assistant = CodeAssistant()

# 日志配置
logger = logging.getLogger(__name__)


# 请求/响应模型
class CodeCompletionRequest(BaseModel):
    """代码补全请求"""
    language: str = Field(..., description="编程语言: python, javascript, java, typescript, cpp, go, rust, php")
    code_context: str = Field(..., description="代码上下文，用于补全")
    style_guide: Optional[str] = Field(None, description="编码规范")
    user_id: Optional[str] = Field("anonymous", description="用户ID（用于监控）")
    
    @validator("language")
    def validate_language(cls, v):
        try:
            CodeLanguage(v.lower())
        except ValueError:
            raise ValueError(f"不支持的语言: {v}")
        return v.lower()


class FunctionGenerationRequest(BaseModel):
    """函数生成请求"""
    language: str = Field(..., description="编程语言")
    description: str = Field(..., description="功能描述")
    requirements: Optional[str] = Field("", description="具体需求")
    style_guide: Optional[str] = Field(None, description="编码规范")
    user_id: Optional[str] = Field("anonymous", description="用户ID（用于监控）")
    
    @validator("language")
    def validate_language(cls, v):
        try:
            CodeLanguage(v.lower())
        except ValueError:
            raise ValueError(f"不支持的语言: {v}")
        return v.lower()


class CodeExplanationRequest(BaseModel):
    """代码解释请求"""
    language: str = Field(..., description="编程语言")
    code_context: str = Field(..., description="需要解释的代码")
    user_id: Optional[str] = Field("anonymous", description="用户ID（用于监控）")
    
    @validator("language")
    def validate_language(cls, v):
        try:
            CodeLanguage(v.lower())
        except ValueError:
            raise ValueError(f"不支持的语言: {v}")
        return v.lower()


class GenericResponse(BaseModel):
    """通用响应模型"""
    status: str = Field(..., description="状态: success 或 error")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")
    error_type: Optional[str] = Field(None, description="错误类型（仅当status=error）")
    error_message: Optional[str] = Field(None, description="错误信息（仅当status=error）")
    response_time_ms: Optional[float] = Field(None, description="响应时间（毫秒）")
    timestamp: Optional[str] = Field(None, description="时间戳")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="API版本")
    uptime_seconds: float = Field(..., description="运行时间（秒）")
    total_requests: int = Field(..., description="总请求数")
    success_rate_percent: float = Field(..., description="成功率（百分比）")
    timestamp: str = Field(..., description="时间戳")


# 中间件：请求日志记录
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # 记录请求信息
    logger.info(f"Request: {request.method} {request.url}")
    
    # 处理请求
    response = await call_next(request)
    
    # 计算响应时间
    response_time = time.time() - start_time
    
    # 记录响应信息
    logger.info(f"Response: {response.status_code} - {response_time:.3f}s")
    
    return response


# 异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error_type": exc.__class__.__name__,
            "error_message": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_type": "InternalServerError",
            "error_message": "内部服务器错误",
            "timestamp": datetime.now().isoformat()
        }
    )


# API端点
@app.get("/", response_model=GenericResponse)
async def root():
    """根端点"""
    return GenericResponse(
        status="success",
        data={
            "service": "Free Codeium Clone API",
            "version": "1.0.0",
            "description": "免费的多语言代码生成助手",
            "endpoints": {
                "health": "/health",
                "completion": "/api/completion",
                "function": "/api/function",
                "explanation": "/api/explanation",
                "metrics": "/api/metrics"
            }
        },
        timestamp=datetime.now().isoformat()
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查端点"""
    metrics = code_assistant.get_metrics_summary()
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime_seconds=time.time() - app_start_time,
        total_requests=metrics["total_requests"],
        success_rate_percent=metrics["success_rate_percent"],
        timestamp=datetime.now().isoformat()
    )


@app.post("/api/completion", response_model=GenericResponse)
async def code_completion(request: CodeCompletionRequest):
    """
    代码补全
    
    根据提供的代码上下文，生成后续代码
    """
    start_time = time.time()
    
    try:
        # 处理请求
        result = code_assistant.process_request(
            request_type=CodeRequestType.CODE_COMPLETION,
            language=request.language,
            code_context=request.code_context,
            style_guide=request.style_guide,
            user_id=request.user_id
        )
        
        response_time = (time.time() - start_time) * 1000
        
        if result["status"] == "success":
            return GenericResponse(
                status="success",
                data=result,
                response_time_ms=round(response_time, 2),
                timestamp=result["timestamp"]
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=result["error_message"]
            )
            
    except Exception as e:
        logger.error(f"代码补全失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.post("/api/function", response_model=GenericResponse)
async def function_generation(request: FunctionGenerationRequest):
    """
    函数生成
    
    根据功能描述，生成完整的函数代码
    """
    start_time = time.time()
    
    try:
        # 处理请求
        result = code_assistant.process_request(
            request_type=CodeRequestType.FUNCTION_GENERATION,
            language=request.language,
            description=request.description,
            requirements=request.requirements,
            style_guide=request.style_guide,
            user_id=request.user_id
        )
        
        response_time = (time.time() - start_time) * 1000
        
        if result["status"] == "success":
            return GenericResponse(
                status="success",
                data=result,
                response_time_ms=round(response_time, 2),
                timestamp=result["timestamp"]
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=result["error_message"]
            )
            
    except Exception as e:
        logger.error(f"函数生成失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.post("/api/explanation", response_model=GenericResponse)
async def code_explanation(request: CodeExplanationRequest):
    """
    代码解释
    
    解释提供的代码的功能和逻辑
    """
    start_time = time.time()
    
    try:
        # 处理请求
        result = code_assistant.process_request(
            request_type=CodeRequestType.CODE_EXPLANATION,
            language=request.language,
            code_context=request.code_context,
            user_id=request.user_id
        )
        
        response_time = (time.time() - start_time) * 1000
        
        if result["status"] == "success":
            return GenericResponse(
                status="success",
                data=result,
                response_time_ms=round(response_time, 2),
                timestamp=result["timestamp"]
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=result["error_message"]
            )
            
    except Exception as e:
        logger.error(f"代码解释失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/api/metrics", response_model=GenericResponse)
async def get_metrics():
    """获取服务指标"""
    try:
        metrics = code_assistant.get_metrics_summary()
        
        return GenericResponse(
            status="success",
            data={
                "metrics": metrics,
                "system_info": {
                    "version": "1.0.0",
                    "start_time": app_start_time,
                    "current_time": time.time()
                }
            },
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"获取指标失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.post("/api/metrics/reset")
async def reset_metrics():
    """重置指标（仅限调试）"""
    try:
        code_assistant.reset_metrics()
        
        return GenericResponse(
            status="success",
            data={"message": "指标已重置"},
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"重置指标失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/api/supported-languages")
async def get_supported_languages():
    """获取支持的编程语言列表"""
    languages = [lang.value for lang in CodeLanguage]
    
    return GenericResponse(
        status="success",
        data={"supported_languages": languages},
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/usage/{user_id}")
async def get_user_usage(user_id: str):
    """获取用户使用统计"""
    try:
        # 这里应该从数据库查询用户历史数据
        # 原型阶段返回模拟数据
        user_history = [
            {
                "timestamp": "2026-03-27T10:30:00",
                "request_type": "code_completion",
                "language": "python",
                "tokens_used": 150
            },
            {
                "timestamp": "2026-03-27T11:15:00",
                "request_type": "function_generation",
                "language": "javascript",
                "tokens_used": 280
            }
        ]
        
        total_tokens = sum(item["tokens_used"] for item in user_history)
        
        return GenericResponse(
            status="success",
            data={
                "user_id": user_id,
                "total_requests": len(user_history),
                "total_tokens_used": total_tokens,
                "history": user_history
            },
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"获取用户使用统计失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# 全局变量
app_start_time = None


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    global app_start_time
    app_start_time = time.time()
    
    logger.info("Free Codeium Clone API 启动完成")
    logger.info(f"服务版本: 1.0.0")
    logger.info(f"支持的编程语言: {', '.join([lang.value for lang in CodeLanguage])}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("Free Codeium Clone API 正在关闭")
    
    # 保存指标数据（原型阶段仅记录）
    metrics = code_assistant.get_metrics_summary()
    logger.info(f"最终指标: {metrics}")
    
    logger.info("Free Codeium Clone API 已关闭")


# 直接运行时的入口
if __name__ == "__main__":
    import uvicorn
    
    # 设置日志级别
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 启动服务器
    uvicorn.run(
        "src.skills.free_codeium_clone.api:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )