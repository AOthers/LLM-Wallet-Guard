# DeepSeek UI 开发记录

## 接口

| 接口 | 认证 | 用途 |
|---|---|---|
| `api.deepseek.com/user/balance` | `Authorization: Bearer <api_key>` | 官方余额查询 |
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
├── api_client.py        # 官方 API 与旧版网页接口
├── tray_ui.py           # PyQt6 托盘和面板
├── config.example.json  # 配置模板
├── build.bat            # PyInstaller 打包脚本
├── .gitignore
├── README.md
└── LICENSE
```

## 功能

- 系统托盘常驻，双击弹出面板
- API Key 查询余额
- 可选显示月消费和用量拆分
- 自动刷新，默认 30 秒
- 凭据无效弹窗提醒
- 右键菜单：显示面板、立即刷新、开机自启、退出

## 打包

运行 `build.bat`，通过 PyInstaller 生成单文件程序：

```text
dist\DeepSeekUI.exe
```
