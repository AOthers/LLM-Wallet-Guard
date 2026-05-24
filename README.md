# DeepSeek UI

Windows 系统托盘应用，用于实时查看 DeepSeek API 余额。默认使用官方 API Key，不再需要每次从网页复制 authorization。

## 功能

- 首次启动可直接在软件内填写配置
- 使用 DeepSeek API Key 查询账户余额
- 托盘悬浮提示显示当前余额
- 默认每 30 秒自动刷新
- 凭据无效时弹窗提醒
- 支持开机自启
- 兼容旧版网页 authorization，可额外显示本月消费和 token 用量拆分

## 使用方法

### 下载 exe（无需 Python）

1. 从 Releases 下载 `DeepSeekUI.exe`
2. 双击运行 `DeepSeekUI.exe`
3. 首次启动时在配置页填入 DeepSeek API Key

## 配置

推荐配置：

```json
{
    "api_key": "sk-...",
    "authorization": "",
    "cookie": "",
    "refresh_seconds": 30
}
```

`api_key` 可在 DeepSeek 平台创建。程序会使用官方 `GET /user/balance` 接口查询余额。
配置可在软件面板右下角点击“设置”修改，保存后会写入本地 `config.json`。

兼容旧版网页数据：

```json
{
    "api_key": "sk-...",
    "authorization": "Bearer 从浏览器复制的 authorization",
    "cookie": "可选 Cookie",
    "refresh_seconds": 30
}
```

DeepSeek 官方 API Key 当前可直接查询余额；本月消费和 token 用量拆分仍依赖网页端接口，所以只有配置旧版 `authorization` 时才显示。

## 获取网页 Authorization 和 Cookie

这一步是可选的。只填写 API Key 时，软件可以正常显示余额；如果还想显示本月消费和 token 用量拆分，需要额外填写网页端 `authorization`，必要时再填写 `cookie`。

1. 浏览器打开 [platform.deepseek.com](https://platform.deepseek.com) 并登录
2. 按 `F12` 打开开发者工具或右键进入检查页面
3. 进入 **Network** （网络）面板
4. 过滤 **Fetch/XHR** 请求
5. 找到 `get_user_summary` 请求
6. 点击该请求，打开 **Headers**（标头）
7. 在 **Request Headers** 中复制 `authorization` 的完整值
8. 如果接口请求失败，再复制同一位置的 `cookie` 完整值
9. 回到软件，点击“设置”，粘贴到对应输入框并保存

注意：网页 `authorization` 和 `cookie` 属于敏感信息，不要提交到仓库或发给他人。

## 技术栈

- Python 3.9+
- PyQt6：系统托盘和界面
- requests：HTTP 请求
- pywin32：创建开机自启快捷方式
- PyInstaller：打包 exe

## License

MIT
