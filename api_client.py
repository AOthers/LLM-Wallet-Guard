import json
import requests
from dataclasses import dataclass
from typing import Optional

SUMMARY_URL = "https://platform.deepseek.com/api/v0/users/get_user_summary"
USAGE_URL = "https://platform.deepseek.com/api/v0/usage/cost"

# 人民币定价：每百万 token 价格（元）— 中文官方页面
PRICE_CNY_PER_1M = {
    "deepseek-v4-pro": {
        "PROMPT_TOKEN":             3.00,   # 缓存未命中价
        "PROMPT_CACHE_HIT_TOKEN":   0.025,
        "PROMPT_CACHE_MISS_TOKEN":  3.00,
        "RESPONSE_TOKEN":           6.00,
    },
    "deepseek-v4-flash": {
        "PROMPT_TOKEN":             1.00,
        "PROMPT_CACHE_HIT_TOKEN":   0.02,
        "PROMPT_CACHE_MISS_TOKEN":  1.00,
        "RESPONSE_TOKEN":           2.00,
    },
}


@dataclass
class BalanceData:
    normal_balance: float = 0.0
    normal_token_est: int = 0
    monthly_cost: float = 0.0
    # 拆分用量（token 数）
    input_tokens: int = 0
    cache_hit_tokens: int = 0
    cache_miss_tokens: int = 0
    output_tokens: int = 0
    is_available: bool = True
    error: Optional[str] = None


def _headers(auth: str, cookie: str) -> dict:
    h = {
        "Accept": "application/json",
        "Authorization": auth.strip(),
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    if cookie.strip():
        h["Cookie"] = cookie.strip()
    return h


def fetch_balance(auth: str, cookie: str = "") -> BalanceData:
    resp = requests.get(SUMMARY_URL, headers=_headers(auth, cookie), timeout=15)
    if resp.status_code in (401, 403):
        return BalanceData(is_available=False, error="Token 已过期")
    resp.raise_for_status()
    data = resp.json()
    if data.get("code", -1) != 0:
        return BalanceData(is_available=False, error=f"接口错误: {data.get('msg','')}")
    biz = data.get("data", {}).get("biz_data", {})
    if not biz:
        return BalanceData(is_available=False, error="返回数据为空")
    nw = biz.get("normal_wallets", [])
    nb = float(nw[0].get("balance", 0)) if nw else 0.0
    nt = int(nw[0].get("token_estimation", 0)) if nw else 0
    mc = biz.get("monthly_costs", [])
    mca = float(mc[0].get("amount", 0)) if mc else 0.0
    return BalanceData(normal_balance=nb, normal_token_est=nt, monthly_cost=mca, is_available=True)


def _cost_to_tokens(cost_yuan: float, price_per_1m: float) -> int:
    if price_per_1m <= 0:
        return 0
    return int(cost_yuan / price_per_1m * 1_000_000)


def fetch_usage_detail(auth: str, cookie: str = "",
                       month: int = None, year: int = None) -> dict:
    """返回 {"input": int, "cache_hit": int, "cache_miss": int, "output": int}（token 数）"""
    from datetime import datetime
    now = datetime.now()
    m = month or now.month
    y = year or now.year
    resp = requests.get(USAGE_URL, headers=_headers(auth, cookie), timeout=15,
                        params={"month": str(m), "year": str(y)})
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
        for u in model.get("usage", []):
            amt_yuan = float(u.get("amount", 0))
            tp = u.get("type", "")
            price = prices.get(tp, 0)
            tokens = _cost_to_tokens(amt_yuan, price)
            if tp == "PROMPT_TOKEN":
                result["input"] += tokens
            elif tp == "PROMPT_CACHE_HIT_TOKEN":
                result["cache_hit"] += tokens
            elif tp == "PROMPT_CACHE_MISS_TOKEN":
                result["cache_miss"] += tokens
            elif tp == "RESPONSE_TOKEN":
                result["output"] += tokens
    return result
