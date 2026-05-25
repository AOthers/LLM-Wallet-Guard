# 更新日志

## v1.3 (2026-05-25)

### 新增

- **第三方中转站平台**：平台下拉新增"第三方中转站"选项，支持接入任意 API 中转服务
- **订阅额度监控**：查看月度已用额度、剩余额度、使用率和到期时间
- **配置页动态切换**：选择不同平台时配置表单字段自动显隐，无需重启
- **数据页双布局**：DeepSeek 显示余额+用量拆分，中转站显示订阅额度卡片

### 优化

- 配置页高度从 440px 压缩至 210px（中转站）/ 340px（DeepSeek）
- 输入框内边距从 `7px 9px` 缩小至 `4px 8px`，高度从 30px 降至 26px
- 全局边距和间距收窄（root margins 12→6、spacing 8→4）
- 数据页高度同步收窄（285→270 / 132→118 / 205→190）

### 配置

- 新增 `proxy_authorization` 字段（第三方中转站 Authorization）
- `provider` 合法值新增 `proxy`

### 内部

- API 层新增 `SubscriptionData` 数据类与 `fetch_proxy_subscription()` 函数
- 代理字段从 UI 中移除，API URL 保留 `viptoken.top`

---

## v1.2 (2025-03)

- 首个可用平台 DeepSeek，支持 API Key 查余额
- 低余额弹窗提醒 + 托盘图标变红
- 可选网页 Authorization 查看本月消费和 token 用量拆分
- 软件内填写配置、托盘常驻、开机自启
- MiMo / OpenAI 预留平台入口
