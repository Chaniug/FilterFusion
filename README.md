# 🚀 FilterFusion

<p align="center">
  <a href="https://github.com/Chaniug/FilterFusion">
    <img src="https://img.shields.io/github/stars/Chaniug/FilterFusion?style=social" alt="Stars" />
  </a>
  <a href="https://github.com/Chaniug/FilterFusion/fork">
    <img src="https://img.shields.io/github/forks/Chaniug/FilterFusion?style=social" alt="Forks" />
  </a>
  <a href="https://github.com/Chaniug/FilterFusion/issues">
    <img src="https://img.shields.io/github/issues/Chaniug/FilterFusion?color=yellow" alt="Issues" />
  </a>
  <a href="https://github.com/Chaniug/FilterFusion/pulls">
    <img src="https://img.shields.io/github/issues-pr/Chaniug/FilterFusion?color=blue" alt="Pull Requests" />
  </a>
  <img src="https://img.shields.io/github/contributors/Chaniug/FilterFusion?color=orange" alt="Contributors" />
  <img src="https://img.shields.io/github/last-commit/Chaniug/FilterFusion?color=success" alt="Last Commit" />
</p>

---

## ✨ 关于 FilterFusion

FilterFusion 是一个专为开发者设计、自动聚合和融合多源广告过滤规则的高效工具集 🧩。  
本项目可以帮你自动抓取主流广告过滤规则，去重融合并输出标准格式，极大简化维护和更新自定义规则列表的流程。  
无论你是数据工程师、广告过滤规则爱好者还是希望维护自己的拦截列表，都能用 FilterFusion 实现一站式自动化处理！

### 🌈 项目核心亮点

- **极致性能** ⚡：大规模规则合并去重，高速输出
- **高度可定制** 🔧：支持自定义规则源、模板和输出格式
- **一键自动化** 🤖：一条命令即可完成规则的抓取、合并、发布
- **丰富场景适用** 🌍：支持广告拦截、内容过滤、家长控制等多种用途

---

## 📝 规则用法与流程

### 1. 规则格式支持

- 支持 Adblock Plus 通用规则、uBlock Origin、EasyList 等主流语法
- 规则示例（见 `rules/chaniug_adsuper.txt`）：
  ```
  ||example.com^
  www.example.com##.ad-banner
  @@||whitelist.com^$document
  ! 注释内容
  ```

### 2. 如何自动抓取和融合规则

FilterFusion 通过内置脚本自动抓取、处理和合并多源规则。  
只需简单几步，即可生成你自己的高质量、去重广告规则列表！

#### 步骤一：配置规则源

在 `config/sources.json` 中填写你需要聚合的规则源列表。

#### 步骤二：抓取规则

```bash
python scripts/fetch_rules.py
```
- 自动下载所有配置源的规则文件，并生成元数据

#### 步骤三：合并和去重规则

```bash
python scripts/merge_rules.py
```
- 自动去除重复、无效和注释行，融合所有规则，生成最终可用的标准规则文件（例如：`dist/adblock-latest.txt`）

#### 步骤四：在广告拦截软件中使用

- 直接将 `dist/adblock-latest.txt` 作为外部规则导入 uBlock Origin、AdGuard、Adblock Plus 等支持自定义规则的插件
- 也可将 `rules/chaniug_adsuper.txt` 作为本地自定义规则使用

---

## 💡 场景举例

- 构建自己的广告拦截、内容过滤、家长控制规则库
- 批量维护和自动更新自定义规则，不再手动合并
- 按需添加、禁用、定制规则源，快速适配新需求

---

## 🚀 快速开始

```bash
git clone https://github.com/Chaniug/FilterFusion.git
cd FilterFusion
pip install -r requirements.txt
python scripts/fetch_rules.py
python scripts/merge_rules.py
```

---

## 📊 贡献者统计

<p align="center">
  <img src="https://contrib.rocks/image?repo=Chaniug/FilterFusion" alt="Contributors" />
</p>
- 👥 查看所有 [贡献者名单](https://github.com/Chaniug/FilterFusion/graphs/contributors)
- 🏆 你也可以出现在这里，欢迎参与贡献！

---

## 🤝 如何参与

- 🌟 点亮 [Star](https://github.com/Chaniug/FilterFusion/stargazers) 支持项目
- 🐛 通过 [Issue](https://github.com/Chaniug/FilterFusion/issues) 反馈问题和建议
- ✨ 提交 [Pull Request](https://github.com/Chaniug/FilterFusion/pulls) 贡献你的代码
- 💬 在 [Discussions](https://github.com/Chaniug/FilterFusion/discussions) 区畅聊你的想法

---

<p align="center">
  <img src="https://github.githubassets.com/images/icons/emoji/unicorn.png" height="28" />
  <img src="https://github.githubassets.com/images/icons/emoji/rocket.png" height="28" />
  <img src="https://github.githubassets.com/images/icons/emoji/heart.png" height="28" />
  <img src="https://github.githubassets.com/images/icons/emoji/octocat.png" height="28" />
</p>