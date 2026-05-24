# LLM Wallet Guard

LLM Wallet Guard is a lightweight Windows tray app for monitoring LLM API balances and usage costs.

当前 v1.2 以 DeepSeek 为首个可用平台，支持 API Key 查询余额、低余额提醒、软件内配置、托盘常驻和可选网页用量拆分。MiMo / OpenAI 已预留平台入口，会在后续版本接入。

## 功能

- 首次启动可直接在软件内填写配置
- 使用 DeepSeek API Key 查询账户余额
- 余额低于阈值时弹窗提醒，托盘图标变红
- 仅有 API Key 时显示余额
- 同时配置网页 Authorization 时显示本月消费和 token 用量拆分
- 默认每 30 秒自动刷新
- 支持窗口拖动、开机自启和原创托盘图标

## 使用方法

### 下载 exe

1. 从 Releases 下载 `LLMWalletGuard.exe`
2. 双击运行
3. 首次启动时选择 `DeepSeek`，填写 API Key
4. 如需完整用量，再填写网页 Authorization / Cookie

### 直接运行源码

```bash
pip install PyQt6 requests pywin32
python main.py
```

## 配置示例

```json
{
    "provider": "deepseek",
    "api_key": "sk-...",
    "authorization": "",
    "cookie": "",
    "refresh_seconds": 30,
    "low_balance_threshold": 10
}
```

字段说明：

- `provider`：当前可用值为 `deepseek`
- `api_key`：DeepSeek API Key，用于官方余额查询
- `authorization`：网页端 Authorization，可选，用于完整用量
- `cookie`：网页 Cookie，可选
- `refresh_seconds`：自动刷新间隔，最低 10 秒
- `low_balance_threshold`：低余额提醒阈值，单位元

## 获取网页 Authorization 和 Cookie

这一步是可选的。只填写 API Key 时，软件可以正常显示余额；如果还想显示本月消费和 token 用量拆分，需要额外填写网页端 `authorization`，必要时再填写 `cookie`。

1. 浏览器打开 [platform.deepseek.com](https://platform.deepseek.com) 并登录
2. 按 `F12` 打开开发者工具或右键进入检查页面
3. 进入 **Network** 面板
4. 过滤 **Fetch/XHR** 请求
5. 找到 `get_user_summary` 请求
6. 点击该请求，打开 **Headers**（标头）
7. 在 **Request Headers** 中复制 `authorization` 的完整值
8. 如果接口请求失败，再复制同一位置的 `cookie` 完整值

注意：网页 `authorization` 和 `cookie` 属于敏感信息，不要提交到仓库或发给他人。

## 参赛定位

一句话：

> 一个面向个人开发者的 LLM API 余额与成本监控工具，支持桌面托盘、API Key 配置、余额提醒、用量拆分和多模型平台扩展。

后续计划：

- 接入 MiMo / OpenAI
- 每日消费趋势图
- 异常用量提醒
- 一键导出用量报告
- 英文界面切换
- Demo 视频和截图

## 技术栈

- Python 3.9+
- PyQt6
- requests
- pywin32
- PyInstaller

## License

MIT
