# 🚀 FilterFusion · 自动聚合多源广告规则

<p align="center">
  <a href="https://github.com/Chaniug/FilterFusion/stargazers">
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

<p align="center">
  <a href="#订阅地址"><img src="https://img.shields.io/badge/订阅地址-Adblock--style-blue?logo=adblock-plus&labelColor=red" alt="订阅地址"></a>
  <a href="#反馈规则"><img src="https://img.shields.io/badge/规则反馈-AdSuper子项目-orange?logo=github" alt="规则反馈"></a>
</p>

---

## 🌟 项目简介

> 🧩 **FilterFusion** —— 一站式自动聚合多源广告过滤规则的高效工具集，让你轻松拥有属于自己的高质量广告拦截列表！

- 🚦 **多源聚合**：自动抓取主流规则源，融合去重，免手动维护
- ⚡ **极速处理**：十万级规则秒级合并，性能极致
- 🧰 **高度定制**：支持自定义源、模板、兼容主流语法
- 🤖 **全自动流程**：一键完成下载、合并、分发
- 💡 **丰富应用场景**：广告拦截、内容过滤、家长控制都能用

<p align="center">
  <img src="https://github.githubassets.com/images/icons/emoji/unicorn.png" height="28" />
  <img src="https://github.githubassets.com/images/icons/emoji/rocket.png" height="28" />
  <img src="https://github.githubassets.com/images/icons/emoji/heart.png" height="28" />
  <img src="https://github.githubassets.com/images/icons/emoji/octocat.png" height="28" />
</p>

---

## 🔗 订阅地址

> 🎉 **推荐直接使用项目自动聚合输出的订阅链接！**  
>
> ```
> https://cdn.jsdelivr.net/gh/Chaniug/FilterFusion/dist/adblock-latest.txt
> ```
>
> - 适用于 **uBlock Origin**、**AdGuard**、**Adblock Plus** 等支持自定义规则的拦截器
> - 规则每日自动更新，永远保持最新！

### 📥 如何使用订阅地址？

1. 复制上方链接
2. 打开你的广告拦截插件（如 uBlock Origin/AdGuard）
3. 找到“自定义过滤器”或“我的订阅”页面
4. 粘贴此订阅地址，点击“添加”或“订阅”
5. 刷新规则，即可生效！

> 💡 **也可以将 `dist/adblock-latest.txt` 作为本地规则导入使用**

---

## 📣 规则收集 & 反馈

- 🚩 **FilterFusion 仅做规则聚合与自动处理，原始规则收集与 issue 反馈请前往子项目 👉 [@Chaniug/AdSuper](https://github.com/Chaniug/AdSuper)**
- 💬 欢迎大家在 [AdSuper](https://github.com/Chaniug/AdSuper/issues) 提交你的规则、反馈广告漏拦等问题，帮助本聚合规则不断完善！
- 🛠️ 子项目专注于搜集、整理和维护高质量规则源，主项目则实现规则的高效融合与发布。

---

## 📝 支持的规则格式

- ✅ **Adblock Plus**、**uBlock Origin**、**EasyList**、**AdGuard** 等主流语法
- ✅ 支持屏蔽规则、例外规则、HTML/CSS/scriptlet 注入、正则规则、多种修饰符
- 示例：
  ```
  ||example.com^
  www.example.com##.ad-banner
  @@||whitelist.com^$document
  ! 注释内容
  ```

---

## 🛠️ 自动化使用流程

1. **配置规则源**  
   编辑 `config/sources.json`，添加你需要聚合的源
2. **自动抓取规则**  
   ```bash
   python scripts/fetch_rules.py
   ```
3. **合并去重规则**  
   ```bash
   python scripts/merge_rules.py
   ```
4. **导入拦截器**  
   使用 `dist/adblock-latest.txt` 的订阅地址，或本地导入

---

## 💡 应用场景

- 🛡️ 自建广告拦截/内容过滤/家长控制
- 🔄 批量维护和自动更新自定义规则
- 🛠️ 灵活适配新需求和自定义扩展

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

## 👥 贡献者

<p align="center">
  <img src="https://contrib.rocks/image?repo=Chaniug/FilterFusion" alt="Contributors" />
</p>
- 查看所有 [贡献者名单](https://github.com/Chaniug/FilterFusion/graphs/contributors)
- 你也可以出现在这里，欢迎参与贡献！

---

## 🤝 参与方式

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
