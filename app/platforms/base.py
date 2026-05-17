from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass

from fastapi import APIRouter, Request


@dataclass
class QuotaInfo:
    remaining: float  # 0.0 ~ 1.0，剩余额度比例
    raw: Optional[dict] = None  # 原始响应数据


@dataclass
class UpstreamTarget:
    url: str
    is_rest: bool = False


class PlatformPlugin(ABC):
    """平台插件基类。每个平台实现此接口即可接入 KeyPool。"""

    @property
    @abstractmethod
    def name(self) -> str:
        """平台标识，如 'tavily'。"""
        ...

    @property
    def supports_quota(self) -> bool:
        """是否支持余额查询。子类可覆盖。"""
        return False

    @abstractmethod
    def get_router(self) -> APIRouter:
        """返回平台专属路由。"""
        ...

    @abstractmethod
    def resolve_upstream(self, path: str) -> UpstreamTarget:
        """根据请求子路径解析上游地址。

        path 是 /api/{platform}/ 之后的部分，直接拼接到上游根地址。
        插件自行决定 MCP 和 REST 的路由规则。
        """
        ...

    @abstractmethod
    def inject_key_for_request(
        self, target: UpstreamTarget, key: str, request: Request
    ) -> tuple[str, Optional[dict]]:
        """为请求注入 API key。

        返回 (upstream_url, extra_headers)。
        插件根据 target.is_rest 和请求特征决定注入方式。
        """
        ...

    @abstractmethod
    async def check_quota(self, key: str) -> QuotaInfo:
        """查询指定 key 的剩余额度。"""
        ...

    @abstractmethod
    def is_key_exhausted(self, status_code: int, response_body: bytes) -> bool:
        """根据上游响应判断 key 额度是否耗尽。"""
        ...

    @abstractmethod
    def is_key_invalid(self, status_code: int, response_body: bytes) -> bool:
        """根据上游响应判断 key 是否失效/被封禁。"""
        ...
