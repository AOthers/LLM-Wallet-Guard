# DeepSeek UI

Windows 系统托盘应用，实时显示 DeepSeek API 的余额和 token 用量。

## 功能

- 💰 显示账户余额和月度消费
- 📊 展示 token 用量拆分：总消耗、输出、缓存命中、缓存未命中
- 🔄 每 30 秒自动刷新
- ⚠️ Token 过期弹窗提醒
- 🚀 支持开机自启

## 效果

```
┌────────────────────────────────┐
│ DeepSeek API 用量             ✕│
│                                │
│ ┌── 余额 ─────────────────────┐│
│ │ 余额  ¥3.71  (≈ 1.24M)     ││
│ │ 本月消费  ¥8.38            ││
│ └─────────────────────────────┘│
│                                │
│ ┌── 用量拆分（本月）──────────┐│
│ │ 总消耗      输出            ││
│ │ 16.41M      0.11M          ││
│ │ 缓存命中    缓存未命中      ││
│ │ 13.72M      2.47M          ││
│ └─────────────────────────────┘│
│                                │
│ 已刷新               [刷新]   │
└────────────────────────────────┘
```

## 使用方法

### 方式一：下载 exe（无需 Python，推荐）

1. 从 [Releases](https://github.com/AotherK/DeepSeekUI/releases) 下载 `DeepSeekUI.exe`
2. 复制 `config.example.json` 为 `config.json`，填入 token（见下方获取方式）
3. 两个文件放同一目录，双击 `DeepSeekUI.exe`

### 方式二：直接运行（需要 Python）

```bash
pip install PyQt6 requests pywin32
copy config.example.json config.json
# 编辑 config.json，填入 token
python main.py
```

### 方式三：自行打包

```bash
build.bat
# 输出在 dist\DeepSeekUI.exe
```

## 获取 Token

1. 浏览器打开 [platform.deepseek.com](https://platform.deepseek.com) 并登录
2. 按 `F12` → **Network** → 过滤 **XHR**
3. 找到 `get_user_summary` 请求
4. 复制 **Request Headers** 中的 `authorization` 字段
5. 粘贴到 `config.json` 的 `authorization` 字段

## 技术栈

- Python 3.9+
- PyQt6（系统托盘 + UI）
- requests（HTTP）
- pywin32（开机自启快捷方式）
- PyInstaller（打包）

## License

MIT
