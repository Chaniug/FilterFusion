---
name: readme-premium-upgrade
overview: 将 README.md 从"模板风格"升级为高级感设计：重组 Hero 区域、ASCII 图升级为 Mermaid、精简 FAQ、优化视觉节奏和信息架构。
todos:
  - id: hero-rewrite
    content: 重写 Hero 区域：添加一行价值主张 tagline、badge 精简到 5 个核心、语言切换链接保留
    status: completed
  - id: about-restructure
    content: 重写「关于」section：保留项目简介和 4 点亮点，末尾插入 Why FilterFusion 对比表
    status: completed
    dependencies:
      - hero-rewrite
  - id: mermaid-diagrams
    content: Mermaid 替代 ASCII 图：工作原理四阶段流水线图 + 应用场景双管道图
    status: completed
    dependencies:
      - about-restructure
  - id: faq-consolidate
    content: 精简 FAQ：10 条合并为 6 条核心问答，删除 Q9/Q10，Q6/Q7 合并入 Q3
    status: completed
  - id: stats-merge
    content: 归拢统计区块：将 contrib.rocks / activity graph / GitHub Stats 合并到「如何参与」section
    status: completed
    dependencies:
      - faq-consolidate
  - id: visual-polish
    content: 全局视觉降噪：标题 emoji 削减至 5 个、--- 分隔线减至 5 条、目录锚点同步更新、指令步骤号改为加粗标题
    status: completed
    dependencies:
      - mermaid-diagrams
      - stats-merge
---

## 用户需求

将 README.md 从当前模板化、视觉噪杂的风格重写为更有高级感的文档，提升项目在 GitHub 上的第一印象。

## 核心改进维度

### Hero 区域重组

当前顶部预览图后堆叠 11 个 badge，缺少一句凝练的价值主张。重写为：预览图 + 一行强有力的项目 tagline + badge 精简到单行（stars / license / release / last-commit），其余 badge（forks / issues / PRs / contributors / activity / discussions / question）移动到「参与」section 中。

### Mermaid 图表替代 ASCII 图

- **工作原理**：当前 `配置规则源 → 抓取规则 → 合并去重 → 输出标准格式` 的箭头图升级为 Mermaid flowchart LR，展示四条流水线阶段
- **应用场景**：当前 4 个 `───` 框场景改为双列 Mermaid flowchart，展示 adblock 和 DNS 双管道

### FAQ 精简

当前 10 条精简到 6 条核心，删除凑数条目：

- 保留：Q1（更新频率）、Q2（自定义规则源）、Q3（支持的格式）、Q4（文件位置）、Q5（性能）、Q8（误拦截反馈）
- 合并 Q6+Q7 到 Q3 扩展说明
- 删除：Q9（商业使用，已在许可证说明）、Q10（技术支持，已在联系方式）

### 视觉噪音降低

- 标题 emoji 从每行一个减少到仅 5 个核心 section 保留（Hero、订阅地址、快速开始、工作原理、FAQ）
- `---` 分隔线从 11 条减少到 5 条
- ASCII 文本装饰全部移除

### 新增 Why FilterFusion 对比表

在「关于」section 末尾插入一个简洁的对比表，展示 FilterFusion vs 手动维护的差异（自动化、去重、多源聚合、CDN 分发）

### 统计区块归拢

将 contrib.rocks + activity graph + GitHub Stats + Top Langs 合并到「如何参与」section 内，作为统一展示区

### 其他微调

- 目录锚点从 10 条调整为新结构
- 系统要求中最低 Python 版本号提示统一
- 指令步骤数字改为加粗标题减少视觉干扰

## 技术方案

### 实现策略

纯 Markdown 重写，不涉及代码逻辑变更。所有改动集中在 `README.md` 单一文件，按照从上到下的顺序逐 section 替换，确保没有残留旧格式。

### Mermaid 图表设计（2 张）

**图 1：四阶段流水线（替代工作原理 ASCII 箭头）**

```
flowchart LR
    A[配置规则源<br/>sources.txt] --> B[异步并发抓取<br/>fetch_rules.py]
    B --> C[分类去重合并<br/>merge_rules.py]
    C --> D[输出 dist/<br/>发布 CDN]
```

用 `flowchart LR` 横向展示四个阶段，四色标注。

**图 2：双管道应用场景（替代 4 个 ASCII 框）**

```
flowchart LR
    subgraph AD[AdBlock 管道]
        S1[多源规则] --> M1[去重融合] --> O1[adblock-main.txt]
    end
    subgraph DNS[DNS 管道]
        S2[多源 DNS 列表] --> M2[合并输出] --> O2[dns-blocklist.txt]
    end
```

双列并排展示 adblock 和 DNS 两条独立管道。

### Badge 精简策略

Hero 区 badge 从 11 个精简到 5 个核心（stars / license / release / last-commit / python-version），其余 6 个 badge 下移到「参与」section 尾部。

### FAQ 合并与删除映射表

| 原条目 | 处理 |
| --- | --- |
| Q1 更新频率 | 保留，精简措辞 |
| Q2 自定义规则源 | 保留 |
| Q3 支持格式 | 保留，扩展涵盖 Q6+Q7 |
| Q4 文件位置 | 保留 |
| Q5 性能大小 | 保留 |
| Q6 规则不生效 | 合并到 Q3 扩展说明 |
| Q7 多列表同时使用 | 合并到 Q3 扩展说明 |
| Q8 误拦截反馈 | 保留 |
| Q9 商业使用 | 删除，LICENSE 已说明 |
| Q10 技术支持 | 删除，联系方式已覆盖 |


### 保留不变的内容

- 所有订阅地址 URL（adblock 3 条 + DNS 3 条 + 规则反馈链接）
- 所有 CLI 命令（git clone、pip install、fetch/merge 脚本）
- 配置格式说明（sources.txt / dns_sources.txt 格式注释）
- 导入工具的详细步骤（uBlock Origin、AdGuard Home）
- MIT License 声明
- 联系方式（GitHub / Issues / Discussions）
- 底部 Star 呼吁和 emoji 行