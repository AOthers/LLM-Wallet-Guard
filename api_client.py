from dataclasses import dataclass
from typing import Optional

import requests

API_BALANCE_URL = "https://api.deepseek.com/user/balance"
SUMMARY_URL = "https://platform.deepseek.com/api/v0/users/get_user_summary"
USAGE_URL = "https://platform.deepseek.com/api/v0/usage/cost"

# 人民币定价：每 100 万 token 价格（元）。按 DeepSeek 平台当前 V4 Pro / V4 Flash 价格填写。
PRICE_CNY_PER_1M = {
    "deepseek-v4-pro": {
        "PROMPT_TOKEN": 3.00,
        "PROMPT_CACHE_HIT_TOKEN": 0.025,
        "PROMPT_CACHE_MISS_TOKEN": 3.00,
        "RESPONSE_TOKEN": 6.00,
    },
    "deepseek-v4-flash": {
        "PROMPT_TOKEN": 1.00,
        "PROMPT_CACHE_HIT_TOKEN": 0.02,
        "PROMPT_CACHE_MISS_TOKEN": 1.00,
        "RESPONSE_TOKEN": 2.00,
    },
}


@dataclass
class BalanceData:
    normal_balance: float = 0.0
    normal_token_est: int = 0
    monthly_cost: Optional[float] = None
    input_tokens: int = 0
    cache_hit_tokens: int = 0
    cache_miss_tokens: int = 0
    output_tokens: int = 0
    usage_available: bool = False
    source: str = "api_key"
    is_available: bool = True
    error: Optional[str] = None


def _bearer(value: str) -> str:
    value = value.strip()
    if value.lower().startswith("bearer "):
        return value
    return f"Bearer {value}"


def _api_headers(api_key: str) -> dict:
    return {
        "Accept": "application/json",
        "Authorization": _bearer(api_key),
        "User-Agent": "LLMWalletGuard/1.2",
    }


def _platform_headers(auth: str, cookie: str) -> dict:
    headers = {
        "Accept": "application/json",
        "Authorization": _bearer(auth),
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    if cookie.strip():
        headers["Cookie"] = cookie.strip()
    return headers


def fetch_api_balance(api_key: str) -> BalanceData:
    """使用官方 API Key 查询账号余额。"""
    resp = requests.get(API_BALANCE_URL, headers=_api_headers(api_key), timeout=15)
    if resp.status_code in (401, 403):
        return BalanceData(is_available=False, error="API Key 无效或已过期", source="api_key")

    resp.raise_for_status()
    data = resp.json()
    balance_infos = data.get("balance_infos", [])
    if not balance_infos:
        return BalanceData(is_available=False, error="返回余额数据为空", source="api_key")

    balance = next((item for item in balance_infos if item.get("currency") == "CNY"), balance_infos[0])
    total_balance = float(balance.get("total_balance", 0) or 0)
    is_available = bool(data.get("is_available", total_balance > 0))
    return BalanceData(
        normal_balance=total_balance,
        is_available=is_available,
        error=None if is_available else "余额不足",
        source="api_key",
    )


def fetch_platform_balance(auth: str, cookie: str = "") -> BalanceData:
    """兼容旧版网页 authorization 查询方式。"""
    resp = requests.get(SUMMARY_URL, headers=_platform_headers(auth, cookie), timeout=15)
    if resp.status_code in (401, 403):
        return BalanceData(is_available=False, error="Token 已过期", source="platform")

    resp.raise_for_status()
    data = resp.json()
    if data.get("code", -1) != 0:
        return BalanceData(is_available=False, error=f"接口错误: {data.get('msg', '')}", source="platform")

    biz = data.get("data", {}).get("biz_data", {})
    if not biz:
        return BalanceData(is_available=False, error="返回数据为空", source="platform")

    normal_wallets = biz.get("normal_wallets", [])
    normal_balance = float(normal_wallets[0].get("balance", 0)) if normal_wallets else 0.0
    normal_token_est = int(normal_wallets[0].get("token_estimation", 0)) if normal_wallets else 0

    monthly_costs = biz.get("monthly_costs", [])
    monthly_cost = float(monthly_costs[0].get("amount", 0)) if monthly_costs else 0.0

    return BalanceData(
        normal_balance=normal_balance,
        normal_token_est=normal_token_est,
        monthly_cost=monthly_cost,
        usage_available=True,
        source="platform",
        is_available=True,
    )


def _cost_to_tokens(cost_yuan: float, price_per_1m: float) -> int:
    if price_per_1m <= 0:
        return 0
    return int(cost_yuan / price_per_1m * 1_000_000)


def fetch_usage_detail(auth: str, cookie: str = "", month: int = None, year: int = None) -> dict:
    """返回 {"input": int, "cache_hit": int, "cache_miss": int, "output": int}（token 数）。"""
    from datetime import datetime

    now = datetime.now()
    m = month or now.month
    y = year or now.year
    resp = requests.get(
        USAGE_URL,
        headers=_platform_headers(auth, cookie),
        timeout=15,
        params={"month": str(m), "year": str(y)},
    )
    if resp.status_code in (401, 403):
        return {}

    resp.raise_for_status()
    data = resp.json()
    if data.get("code", -1) != 0:
        return {}

    biz_data = data.get("data", {}).get("biz_data", [])
    if not biz_data:
        return {}

    total_list = biz_data[0].get("total", [])
    result = {"input": 0, "cache_hit": 0, "cache_miss": 0, "output": 0}
    for model in total_list:
        model_name = model.get("model", "")
        prices = PRICE_CNY_PER_1M.get(model_name, {})
        for usage in model.get("usage", []):
            amount_yuan = float(usage.get("amount", 0))
            usage_type = usage.get("type", "")
            price = prices.get(usage_type, 0)
            tokens = _cost_to_tokens(amount_yuan, price)
            if usage_type == "PROMPT_TOKEN":
                result["input"] += tokens
            elif usage_type == "PROMPT_CACHE_HIT_TOKEN":
                result["cache_hit"] += tokens
            elif usage_type == "PROMPT_CACHE_MISS_TOKEN":
                result["cache_miss"] += tokens
            elif usage_type == "RESPONSE_TOKEN":
                result["output"] += tokens

    return result


# ── 第三方中转站 ──────────────────────────────────────────

PROXY_ACTIVE_SUBSCRIPTION_URL = "https://viptoken.top/api/v1/subscriptions/active"


@dataclass
class SubscriptionData:
    plan_name: str = ""
    status: str = ""
    expires_at_display: str = ""
    daily_usage_usd: float = 0.0
    weekly_usage_usd: float = 0.0
    monthly_usage_usd: float = 0.0
    daily_limit_usd: float = 0.0
    weekly_limit_usd: float = 0.0
    monthly_limit_usd: float = 0.0
    remaining_usd: float = 0.0
    usage_ratio: Optional[float] = None
    is_available: bool = True
    error: Optional[str] = None


def _proxy_proxies(proxy_url: str) -> Optional[dict]:
    proxy_url = (proxy_url or "").strip()
    if not proxy_url:
        return None
    return {"http": proxy_url, "https": proxy_url}


def _proxy_headers(authorization: str) -> dict:
    return {
        "Accept": "application/json",
        "Authorization": _bearer(authorization),
        "User-Agent": "LLMWalletGuard/1.2",
    }


def _money(value) -> float:
    return round(float(value or 0), 4)


def _format_datetime(value: str) -> str:
    if not value:
        return ""
    try:
        from datetime import datetime
        return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return value


def build_subscription_error(error: str) -> SubscriptionData:
    return SubscriptionData(is_available=False, error=error)


def parse_subscription_response(payload: dict) -> SubscriptionData:
    if payload.get("code", 0) != 0:
        return build_subscription_error(f"接口错误: {payload.get('message', '')}".strip())

    subscriptions = payload.get("data", [])
    active = next((item for item in subscriptions if item.get("status") == "active"), None)
    if not active:
        return build_subscription_error("未找到有效订阅")

    group = active.get("group", {}) or {}
    monthly_usage = _money(active.get("monthly_usage_usd"))
    monthly_limit = _money(group.get("monthly_limit_usd"))
    remaining = round(monthly_limit - monthly_usage, 4)
    ratio = round(monthly_usage / monthly_limit, 3) if monthly_limit > 0 else None

    return SubscriptionData(
        plan_name=group.get("name", ""),
        status=active.get("status", ""),
        expires_at_display=_format_datetime(active.get("expires_at", "")),
        daily_usage_usd=_money(active.get("daily_usage_usd")),
        weekly_usage_usd=_money(active.get("weekly_usage_usd")),
        monthly_usage_usd=monthly_usage,
        daily_limit_usd=_money(group.get("daily_limit_usd")),
        weekly_limit_usd=_money(group.get("weekly_limit_usd")),
        monthly_limit_usd=monthly_limit,
        remaining_usd=remaining,
        usage_ratio=ratio,
    )


def fetch_proxy_subscription(authorization: str, proxy_url: str = "") -> SubscriptionData:
    try:
        resp = requests.get(
            PROXY_ACTIVE_SUBSCRIPTION_URL,
            headers=_proxy_headers(authorization),
            params={"timezone": "Asia/Shanghai"},
            timeout=20,
            proxies=_proxy_proxies(proxy_url),
        )
    except requests.RequestException as e:
        return build_subscription_error(f"网络错误: {e}")

    if resp.status_code in (401, 403):
        return build_subscription_error("Authorization 无效或已过期")

    try:
        resp.raise_for_status()
    except requests.RequestException as e:
        return build_subscription_error(f"接口错误: {e}")

    return parse_subscription_response(resp.json())
