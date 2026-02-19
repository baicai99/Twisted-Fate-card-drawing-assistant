# 免责声明（Disclaimer）

本项目及其代码仅供个人学习、参考和研究使用。任何用户在使用本项目及代码时，应当自行承担所有风险和责任。作者不对由本项目产生的任何直接或间接损失承担任何责任，包括但不限于：

1. **商业使用**：本项目及其代码**严禁用于任何形式的商业用途或盈利活动**。包括但不限于产品销售、广告推广、收取费用的服务等。如果你希望将该项目用于商业用途，请事先与作者联系，并取得正式授权。
2. **合法性**：用户有责任确保本项目及代码在其所在地的法律法规下是合法的。在任何可能产生法律争议或违规行为的情况下，**作者不承担任何责任**。
3. **项目修改和分发**：用户可以在本项目基础上进行修改、二次开发或重构，但**不得删除或更改本声明内容**。同时，任何形式的修改版本或衍生项目不得用于违反相关法律法规的行为中。
4. **不提供技术支持**：作者仅为个人学习提供参考代码，**不对代码使用中出现的任何错误、缺陷、或漏洞提供技术支持**。用户使用本项目的过程中产生的一切问题，均需自行解决。
5. **与第三方产品或服务的集成**：本项目可能会涉及到与其他第三方产品或服务的集成（如外部 API 调用、数据库访问等）。作者**不对这些第三方服务的可用性、安全性、或数据隐私性承担任何责任**。
6. **损坏和数据丢失**：用户在使用本项目时应自行备份数据，并进行充分测试。作者不对任何由于使用本代码引起的硬件损坏、数据丢失、或系统崩溃承担任何责任。
7. **项目停止维护**：作者有权随时停止对该项目的维护、更新或下线，且**无义务通知使用者**。

请务必仔细阅读并理解本免责声明。如果您无法接受这些条款，请勿使用本项目及其代码。

# Copyright © 2024 baicai99 · Card Master Assistant. All Rights Reserved.

# 卡牌大师助手
英雄联盟中崔斯特（卡牌大师）的自动选牌助手。

### 使用方法
- 鼠标中键在卡牌大师 W 技能栏按一下。
- `W` = 蓝牌，`E` = 黄牌，`A` = 红牌。
- `R` 第二段落地自动黄牌。
- 仅支持 `pynput` 输入后端（`TF_INPUT_BACKEND=legacy` 已弃用并自动回退）。

### 工具链（uv）
- 先安装 `uv`：[https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)
- 安装依赖（含打包组）：
```powershell
uv sync --group build
```

### 运行
```powershell
uv run python main.py
```
兼容入口（等价）：
```powershell
uv run python twist.py
```
性能统计（可选，PowerShell）：
```powershell
$env:TF_PERF_STATS = "1"
uv run python main.py
```
性能统计（可选，CMD）：
```cmd
set TF_PERF_STATS=1
uv run python main.py
```

### Windows 打包
在 PowerShell 中执行：
```powershell
.\build_windows.ps1
```
产物路径：`dist\twist.exe`

### 依赖定义
- 主依赖与分组定义：`pyproject.toml`
- 锁文件：`uv.lock`
- 旧 `requirements*.txt` 已移除，不再维护。

## 目录结构（重构后）
```text
app/
  config.py
  state.py
  color_detector.py
  window_guard.py
  selector.py
  input_handlers.py
  input_backend.py
  win_input.py
main.py
twist.py
pyproject.toml
uv.lock
```

# Disclaimer

This project and its code are intended for personal learning, reference, and research purposes only. Any user who uses this project and its code assumes all risks and responsibilities. The author is not responsible for any direct or indirect losses arising from this project, including but not limited to:

1. **Commercial Use**: This project and its code are **strictly prohibited for any form of commercial use or profit-making activities**. This includes, but is not limited to, product sales, advertising promotions, paid services, etc. If you wish to use this project for commercial purposes, please contact the author in advance and obtain formal authorization.
2. **Legality**: Users are responsible for ensuring that this project and its code comply with the laws and regulations of their respective locations. In any situation that may lead to legal disputes or violations, **the author assumes no responsibility**.
3. **Project Modification and Distribution**: Users may modify, redevelop, or restructure this project, but **must not delete or alter this disclaimer**. Additionally, any modified versions or derivative projects must not be used for actions that violate relevant laws and regulations.
4. **No Technical Support**: The author provides reference code solely for personal learning and **does not offer technical support for any errors, defects, or vulnerabilities that may occur during the use of the code**. All issues arising from the use of this project must be resolved by the user.
5. **Integration with Third-Party Products or Services**: This project may involve integration with other third-party products or services (such as external API calls, database access, etc.). The author **is not responsible for the availability, security, or data privacy of these third-party services**.
6. **Damage and Data Loss**: Users should back up their data and conduct thorough testing when using this project. The author is not responsible for any hardware damage, data loss, or system crashes resulting from the use of this code.
7. **Project Maintenance Termination**: The author reserves the right to cease maintenance, updates, or decommissioning of this project at any time and **has no obligation to notify users**.

Please read and understand this disclaimer carefully. If you cannot accept these terms, please do not use this project and its code.

# Copyright © 2024 baicai99 · Card Master Assistant. All Rights Reserved.

# Card Master Assistant
Automatic card selection assistant for Twisted Fate in League of Legends.

### How to Use
- Click the middle mouse button once on Twisted Fate's W skill icon.
- `W` = Blue Card, `E` = Yellow Card, `A` = Red Card.
- `R` second activation upon landing will automatically select Yellow Card.
- Only `pynput` backend is supported (`TF_INPUT_BACKEND=legacy` is deprecated and falls back to `pynput`).

### Tooling (uv)
- Install `uv` first: [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)
- Install dependencies (including build group):
```powershell
uv sync --group build
```

### Run
```powershell
uv run python main.py
```
Compatibility entrypoint (equivalent):
```powershell
uv run python twist.py
```
Optional perf stats (PowerShell):
```powershell
$env:TF_PERF_STATS = "1"
uv run python main.py
```
Optional perf stats (CMD):
```cmd
set TF_PERF_STATS=1
uv run python main.py
```

### Windows Build
Run in PowerShell:
```powershell
.\build_windows.ps1
```
Build artifact: `dist\twist.exe`

### Dependency Source of Truth
- Project dependencies and groups: `pyproject.toml`
- Lock file: `uv.lock`
- Legacy `requirements*.txt` files have been removed and are no longer maintained.
