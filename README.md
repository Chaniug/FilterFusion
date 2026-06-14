<img src="https://github.com/Chaniug/FilterFusion/raw/main/assets/preview.png" alt="项目预览" />

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
  <a href="https://github.com/Chaniug/FilterFusion/releases">
    <img src="https://img.shields.io/github/v/release/Chaniug/FilterFusion?display_name=tag&color=brightgreen" alt="Latest Release" />
  </a>
  <a href="https://github.com/Chaniug/FilterFusion/graphs/commit-activity">
    <img src="https://img.shields.io/badge/活跃度-热力图-orange?logo=github" alt="活跃度热力图" />
  </a>
  <a href="https://github.com/Chaniug/FilterFusion/discussions">
    <img src="https://img.shields.io/badge/畅聊-Discussions-blueviolet?logo=github" alt="Discussions" />
  </a>
  <a href="https://github.com/Chaniug/FilterFusion/issues/new?assignees=&labels=question&template=question.yml">
    <img src="https://img.shields.io/badge/提问-Question-green?logo=github" alt="提问" />
  </a>
</p>

**中文** | **[English](./README_EN.md)** | **[日本語](./README_JP.md)** *(敬请期待)*

---

## 📖 目录

- [关于 FilterFusion](#-关于-filterfusion)
- [规则订阅地址](#-规则订阅地址)
- [系统要求](#-系统要求)
- [快速开始](#-快速开始)
- [工作原理](#-工作原理)
- [使用指南](#-使用指南)
- [实际应用场景](#-实际应用场景)
- [常见问题 FAQ](#-常见问题-faq)
- [如何参与](#-如何参与)
- [许可证](#-许可证)

---

## ✨ 关于 FilterFusion

FilterFusion 是一个专为开发者设计、自动聚合和融合多源广告过滤规则的高效工具集 🧩。

本项目可以帮你**自动抓取主流广告过滤规则**，通过去重、融合并输出标准格式，极大简化维护和更新自定义规则列表的流程。

无论你是数据工程师、广告过滤规则爱好者还是希望维护自己的拦截列表，都能用 FilterFusion 实现一站式自动化处理！

### 🌈 项目核心亮点

- **极致性能** ⚡：大规模规则合并去重，高速输出
- **高度可定制** 🔧：支持自定义规则源、模板和输出格式
- **一键自动化** 🤖：一条命令即可完成规则的抓取、合并、发布
- **丰富场景适用** 🌍：支持广告拦截、内容过滤、家长控制等多种用途

---

## 📬 规则订阅地址

将以下任一链接导入你的广告拦截工具（uBlock Origin、AdGuard 等）：

- **GitHub Raw**（全球可用）  
  ```
  https://raw.githubusercontent.com/Chaniug/FilterFusion/main/dist/adblock-main.txt
  ```

- **jsDelivr CDN**（中国大陆推荐使用）  
  ```
  https://cdn.jsdelivr.net/gh/Chaniug/FilterFusion@main/dist/adblock-main.txt
  ```

- **FastGit 加速**（部分可用）  
  ```
  https://raw.fastgit.org/Chaniug/FilterFusion/main/dist/adblock-main.txt
  ```

- **GitHub Proxy**（部分可用）  
  ```
  https://ghproxy.com/https://raw.githubusercontent.com/Chaniug/FilterFusion/main/dist/adblock-main.txt
  ```

### 📋 规则反馈

<p align="center">
  <a href="https://github.com/Chaniug/AdSuper/issues/new?labels=%E8%A7%84%E5%88%99%E5%8F%8D%E9%A6%88&template=rule_report.yml" style="text-decoration:none;">
    <img src="https://img.shields.io/badge/规则反馈&建议-点此前往@Chaniug/AdSuper-ff69b4?logo=github" alt="前往 AdSuper 反馈规则" />
  </a>
</p>

如需反馈**误拦截、漏拦截**或希望补充的新规则，请前往我们的子项目 [**@Chaniug/AdSuper**](https://github.com/Chaniug/AdSuper) 提交规则 Issue，我们会及时处理！

---

## 📦 系统要求

在使用 FilterFusion 前，请确保您的系统满足以下要求：

### 最低要求
- **Python**: 3.10 或更高版本
- **操作系统**: Windows、macOS、Linux
- **网络**: 需要互联网连接以抓取规则源

### 依赖库
```
requests>=2.31.0
```

### 检查 Python 版本
```bash
python --version
# 或
python3 --version
```

---

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/Chaniug/FilterFusion.git
cd FilterFusion
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 抓取并合并规则
```bash
python scripts/fetch_rules.py    # 抓取所有规则源
python scripts/merge_rules.py    # 合并并去重
```

### 4. 使用生成的规则
- 生成的规则文件位于 `dist/` 目录
- 直接导入到支持自定义规则的广告拦截工具中

---

## 🔧 工作原理

### 支持的规则格式

FilterFusion 支持主流的广告过滤规则格式：

- **Adblock Plus (ABP)** 通用规则
- **uBlock Origin** 规则
- **EasyList** 规则
- 其他兼容 ABP 的规则

### 规则示例

```
||example.com^                          # 完整域名匹配
www.example.com##.ad-banner             # 元素隐藏规则
@@||whitelist.com^$document             # 白名单规则
! 这是一条注释
# 这也是一条注释
```

### 处理流程

FilterFusion 的工作流程分为四个主要阶段：

```
配置规则源 → 抓取规则 → 合并去重 → 输出标准格式
```

---

## 📝 使用指南

### 第一步：配置规则源

编辑 `config/sources.json` 文件，添加你需要聚合的规则源列表：

```json
{
  "sources": [
    {
      "name": "EasyList",
      "url": "https://easylist.to/easylist/easylist.txt"
    },
    {
      "name": "AdGuard Base",
      "url": "https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt"
    }
  ]
}
```

### 第二步：抓取规则

自动下载所有配置源的规则文件：

```bash
python scripts/fetch_rules.py
```

**功能**：
- 下载所有配置源的规则文件
- 验证规则格式有效性
- 生成元数据（大小、更新时间等）
- 缓存规则文件以加快后续处理

### 第三步：合并和去重规则

融合所有规则，生成最终的标准规则文件：

```bash
python scripts/merge_rules.py
```

**功能**：
- 自动去除重复规则
- 删除无效和注释行
- 融合所有规则
- 输出标准格式：`dist/adblock-main.txt`

### 第四步：在广告拦截工具中使用

#### 导入方法（以 uBlock Origin 为例）

1. 打开 uBlock Origin 扩展选项
2. 进入「Filter lists」标签
3. 在底部「Import」输入框中粘贴订阅链接
4. 点击「Import」导入
5. 保存设置

#### 支持的工具
- uBlock Origin
- AdGuard
- Adblock Plus
- Brave Browser（内置）
- Safari 广告拦截插件

---

## 💡 实际应用场景

### 场景 1：构建个人规则库
```
快速聚合多个规则源 → 去重融合 → 生成个人定制规则库
```

### 场景 2：企业内网广告拦截
```
配置企业特定规则源 → 自动更新 → 分发到组织内所有设备
```

### 场景 3：内容过滤和家长控制
```
选择专用过滤规则 → 自动更新 → 用于家长控制系统
```

### 场景 4：广告过滤工具开发
```
使用 FilterFusion 生成规则 → 集成到自有工具 → 持续维护
```

---

## ❓ 常见问题 FAQ

### Q1: 多久更新一次规则？

**A**: 规则的更新频率取决于：
- 配置的规则源的更新速度
- 你执行 `fetch_rules.py` 脚本的频率

建议使用 GitHub Actions 或定时任务（cron）自动运行脚本，建议每天或每周执行一次。

### Q2: 如何自定义规则源？

**A**: 编辑 `config/sources.json` 文件：

```json
{
  "sources": [
    {
      "name": "你的规则名",
      "url": "规则文件的 URL",
      "enabled": true
    }
  ]
}
```

设置 `"enabled": false` 可禁用某个规则源而无需删除。

### Q3: 规则支持哪些格式？

**A**: FilterFusion 支持：
- Adblock Plus (ABP) 格式
- uBlock Origin 格式
- EasyList/EasyPrivacy 格式
- 其他兼容 ABP 的格式

### Q4: 生成的规则文件在哪里？

**A**: 运行 `merge_rules.py` 后，生成的规则文件位于：
```
dist/adblock-main.txt       # 主规则文件
```

### Q5: 规则文件多大？性能如何？

**A**: 
- 文件大小：通常 **2-5 MB**（取决于规则源数量）
- 加载性能：现代浏览器可轻松处理
- 过滤性能：与规则源的复杂度相关

建议定期检查规则文件大小，移除不需要的规则源以优化性能。

### Q6: 为什么有些规则导入后不生效？

**A**: 常见原因：
1. **格式不兼容** - 确保广告拦截工具支持该规则格式
2. **规则语法错误** - 检查 `scripts/` 中的日志输出
3. **工具限制** - 某些工具对规则数量有限制
4. **缓存问题** - 尝试重启浏览器或清除扩展缓存

### Q7: 可以同时使用多个规则列表吗？

**A**: **可以**。大多数广告拦截工具支持多个规则列表，建议：
- 保留官方规则（如 EasyList）作为基础
- 添加 FilterFusion 生成的规则作为补充
- 使用白名单规则避免过度拦截

### Q8: 我发现有误拦截或漏拦截，怎么办？

**A**: 
1. 记录具体的误拦截/漏拦截网址
2. 前往 [AdSuper 项目](https://github.com/Chaniug/AdSuper) 提交 Issue
3. 详细描述问题（网址、拦截情况等）
4. 我们会及时处理并更新规则

### Q9: 可以在商业项目中使用吗？

**A**: **可以**。本项目采用 MIT License，允许商业使用。只需在项目中保留原始许可证和版权声明即可。

### Q10: 如何获得技术支持？

**A**: 
- 📖 查看 [项目文档](https://github.com/Chaniug/FilterFusion/wiki)
- 🐛 提交 [Issue](https://github.com/Chaniug/FilterFusion/issues)
- 💬 在 [Discussions](https://github.com/Chaniug/FilterFusion/discussions) 区提问
- 📧 联系维护者（见下方联系方式）

---

## 📊 贡献者统计

<p align="center">
  <img src="https://contrib.rocks/image?repo=Chaniug/FilterFusion" alt="Contributors" />
</p>

[![Chaniug's github activity graph](https://github-readme-activity-graph.vercel.app/graph?username=Chaniug&theme=github-compact)](https://github.com/Ashutosh00710/github-readme-activity-graph)

- 👥 查看所有 [贡献者名单](https://github.com/Chaniug/FilterFusion/graphs/contributors)
- 🏆 你也可以出现在这里，欢迎参与贡献！

---

## 🤝 如何参与

![Chaniug's GitHub stats](https://github-readme-stats.vercel.app/api?username=Chaniug&show_icons=true&theme=tokyonight)
![Top Langs](https://github-readme-stats.vercel.app/api/top-langs/?username=Chaniug&layout=compact)

### 支持项目

- 🌟 点亮 [Star](https://github.com/Chaniug/FilterFusion/stargazers) 支持项目
- 🍴 [Fork](https://github.com/Chaniug/FilterFusion/fork) 项目
- 📢 分享给更多人

### 参与开发

- 🐛 通过 [Issue](https://github.com/Chaniug/FilterFusion/issues) 反馈问题和建议
- ✨ 提交 [Pull Request](https://github.com/Chaniug/FilterFusion/pulls) 贡献代码
- 💬 在 [Discussions](https://github.com/Chaniug/FilterFusion/discussions) 区分享想法
- 📝 完善文档和示例

### 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

---

## 📄 许可证

本项目采用 **MIT License** 开源协议。详见 [LICENSE](./LICENSE) 文件。

### 简要说明

MIT License 允许您：
- ✅ 自由使用、修改和分发本项目
- ✅ 用于商业和私人项目
- ✅ 获得源代码和修改代码

您只需：
- ⚠️ 保留原始许可证和版权声明
- ⚠️ 本项目按"原样"提供，作者不承担任何责任

---

## 📧 联系方式

- **GitHub**: [@Chaniug](https://github.com/Chaniug)
- **Project Issues**: [FilterFusion Issues](https://github.com/Chaniug/FilterFusion/issues)
- **Discussions**: [FilterFusion Discussions](https://github.com/Chaniug/FilterFusion/discussions)

---

<p align="center">
  <img src="https://github.githubassets.com/images/icons/emoji/unicorn.png" height="28" />
  <img src="https://github.githubassets.com/images/icons/emoji/rocket.png" height="28" />
  <img src="https://github.githubassets.com/images/icons/emoji/heart.png" height="28" />
  <img src="https://github.githubassets.com/images/icons/emoji/octocat.png" height="28" />
</p>

<p align="center">
  <b>喜欢这个项目？请点个 Star ⭐ 来支持我们！</b>
</p>
