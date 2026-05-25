# v1.3

## 新增：第三方中转站平台

平台下拉新增「第三方中转站」，填入 Authorization 即可查看订阅的月度额度使用情况，无需再开浏览器。

## 功能亮点

- 🖥️ **多平台一键切换**：DeepSeek（余额+用量拆分）↔ 第三方中转站（订阅额度），配置页字段自动适配
- 💰 **订阅额度监控**：月度已用/剩余额度、使用率百分比、到期时间一目了然
- 📐 **页面大幅紧凑化**：配置页高度缩减约一半，视觉更清爽
- 🔧 **通用化命名**：所有 `viptoken` 字样替换为 `proxy`，不绑定任何具体服务商

## 配置示例

**第三方中转站：**
```json
{
    "provider": "proxy",
    "proxy_authorization": "Bearer ...",
    "refresh_seconds": 30
}
```

## 如何更新

- 下载新 `LLMWalletGuard.exe` 覆盖旧文件即可，`config.json` 格式兼容
- 源码运行：`pip install -r requirements.txt && python main.py`

---

### 详细变更 · Full Changelog

查看 [CHANGELOG.md](./CHANGELOG.md)
