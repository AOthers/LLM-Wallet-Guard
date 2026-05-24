# LLM Wallet Guard 开发记录

## 产品定位

LLM Wallet Guard 是一个面向个人开发者的 LLM API 余额与成本监控工具，支持桌面托盘、API Key 配置、余额提醒、用量拆分和多模型平台扩展。

## 版本路线

### v1.2：参赛包装版

目标：从 DeepSeek 专用工具升级为 LLM Wallet Guard 的参赛原型。

- 改名为 `LLM Wallet Guard`
- 保留 DeepSeek 作为首个可用 provider
- 配置中新增 `provider`
- 配置中新增 `low_balance_threshold`
- 配置页增加平台选择
- 配置页增加余额提醒阈值
- 低余额时托盘图标变红并弹窗提醒一次
- 只填写 API Key 时显示余额
- 同时填写网页 Authorization 时显示完整用量
- 更新 README 为参赛介绍

### v1.3：多平台真实支持

目标：抽象多平台 provider，让项目从“包装”变成真正的多平台工具。

- 新增 `providers/` 目录
- 抽象统一返回结构：provider、balance、currency、monthly_cost、usage_available、error
- 拆分 DeepSeek provider
- 增加 MiMo provider
- 调研 OpenAI 余额/账单接口，确认权限和可用性后再接入
- 配置页按 provider 显示不同字段

### v1.4：趋势图与报告

目标：增强成本监控能力，形成完整产品体验。

- 本地保存每日余额快照
- 最近 7 天余额/消费趋势图
- 余额低于阈值提醒
- 异常用量提醒
- 一键导出 Markdown / CSV 报告
- 英文界面切换
- Demo 视频和截图素材

## 当前接口

| 接口 | 认证 | 用途 |
|---|---|---|
| `api.deepseek.com/user/balance` | `Authorization: Bearer <api_key>` | DeepSeek 官方余额查询 |
| `platform.deepseek.com/api/v0/users/get_user_summary` | 网页 `authorization` + 可选 Cookie | 旧版余额、月消费 |
| `platform.deepseek.com/api/v0/usage/cost?month=&year=` | 同上 | 按模型拆分的用量金额 |

## 当前数据策略

优先使用官方 API Key 查询余额，避免用户反复打开浏览器复制网页 authorization。

如果用户同时配置旧版 `authorization`，程序会额外请求网页端接口，用于显示本月消费和 token 用量拆分。DeepSeek 官方 API Key 当前只覆盖余额查询，暂未提供同等粒度的月度用量接口。

## 定价表

人民币定价，单位为元 / 100 万 token。当前代码按 V4 Pro 与 V4 Flash 两个模型反推 token 数。

| 类型 | V4 Pro | V4 Flash |
|---|---:|---:|
| 缓存命中 | ¥0.025 / 1M | ¥0.02 / 1M |
| 缓存未命中 | ¥3.00 / 1M | ¥1.00 / 1M |
| 输出 | ¥6.00 / 1M | ¥2.00 / 1M |

## 项目结构

```text
DeepseekUI/
├── main.py              # 入口和配置读取
├── api_client.py        # DeepSeek 官方 API 与旧版网页接口
├── tray_ui.py           # PyQt6 托盘、数据页和配置页
├── config.example.json  # 配置模板
├── build.bat            # PyInstaller 打包脚本
├── assets/              # 图标资产
├── tools/               # 工具脚本
├── README.md
└── LICENSE
```
