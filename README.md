# FilterFusion

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Build](https://github.com/Chaniug/FilterFusion/actions/workflows/python-app.yml/badge.svg)](https://github.com/Chaniug/FilterFusion/actions)
[![Latest Release](https://img.shields.io/github/v/release/Chaniug/FilterFusion?include_prereleases)](https://github.com/Chaniug/FilterFusion/releases)
[![Visitors](https://visitor-badge.laobi.icu/badge?page_id=Chaniug.FilterFusion)](https://github.com/Chaniug/FilterFusion)

> 🚀 **FilterFusion：全自动的广告过滤规则聚合器！**

---

## ✨ 项目介绍

**FilterFusion** 是一个专为热爱净网和自动化的你打造的广告过滤规则聚合项目。它能自动从不同来源抓取、整合各类广告屏蔽规则，通过智能去重、合并，生成高质量的 Adblock 规则文件，供所有用户自由订阅和使用。

- **全自动更新**：每日定时自动抓取与聚合，规则永远保持最新！
- **多源融合**：支持多种主流规则源，想聚合多少就聚合多少。
- **智能去重**：自动去除重复与无效规则，保持规则精简高效。
- **一键订阅**：随时获取最新的 `adblock-latest.txt`，简单易用。
- **开箱即用**：MIT 开源协议，完全免费，欢迎任何人参与和改进！

---

## 📦 项目结构

```text
FilterFusion/
├── dist/         # 合并后的规则及摘要等发布文件
├── rules/        # 各个源抓取下来的原始规则
├── config/       # 配置与模板
├── scripts/      # 主要合并、抓取等脚本
└── README.md
```

---

## 🚩 快速开始

1. **克隆仓库**
   ```bash
   git clone https://github.com/Chaniug/FilterFusion.git
   cd FilterFusion
   ```
2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```
3. **运行规则合并脚本**
   ```bash
   python scripts/merge_rules.py
   ```
4. **获取最新规则**
   - 合并后的规则在 `dist/adblock-latest.txt`
   - 也可订阅特定日期版，例如 `dist/adblock-20250605.txt`

---

## 🛡️ 订阅方式

- **Adblock / uBlock Origin 用户**  
  直接添加原始链接订阅即可：
  ```
  https://raw.githubusercontent.com/Chaniug/FilterFusion/main/dist/adblock-latest.txt
  ```
- **每日日版**  
  ```
  https://raw.githubusercontent.com/Chaniug/FilterFusion/main/dist/adblock-YYYYMMDD.txt
  ```

---

## 🤖 自动化与贡献

- **持续集成**：已接入 GitHub Actions 自动构建和更新。
- **欢迎贡献**：PR、Issue 和建议欢迎随时提交！
- **自定义规则**：可自行添加或修改 `rules/` 文件夹内容，按需扩展规则源。

---

## 🌏 项目优势

- **低误报率**，高兼容性。
- 纯 Python 实现，代码精简可维护。
- 适合个人、组织、开源社区二次开发和自托管。

---

## 🙌 鸣谢

- 感谢各大规则源项目与广大社区贡献者。
- 本项目仅聚合公开可用的广告过滤规则。

---

## 📜 License

[MIT License](LICENSE)

---

> ⭐️ 如果你觉得这个项目有用，欢迎 Star & Fork 支持，谢谢！