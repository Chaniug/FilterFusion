<img src="https://github.com/Chaniug/FilterFusion/raw/main/assets/preview.png" alt="Project Preview" />

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
    <img src="https://img.shields.io/badge/Activity-Heatmap-orange?logo=github" alt="Activity Heatmap" />
  </a>
  <a href="https://github.com/Chaniug/FilterFusion/discussions">
    <img src="https://img.shields.io/badge/Chat-Discussions-blueviolet?logo=github" alt="Discussions" />
  </a>
  <a href="https://github.com/Chaniug/FilterFusion/issues/new?assignees=&labels=question&template=question.yml">
    <img src="https://img.shields.io/badge/Ask-Question-green?logo=github" alt="Ask Question" />
  </a>
</p>

**[中文 README](./README.md)** | **English** | **[日本語](./README_JP.md)** *(Coming Soon)*

---

## 📖 Table of Contents

- [About FilterFusion](#-about-filterfusion)
- [Subscription URLs](#-subscription-urls)
- [System Requirements](#-system-requirements)
- [Quick Start](#-quick-start)
- [How It Works](#-how-it-works)
- [Usage Guide](#-usage-guide)
- [Use Cases](#-use-cases)
- [FAQ](#-faq)
- [How to Contribute](#-how-to-contribute)
- [License](#-license)

---

## ✨ About FilterFusion

**FilterFusion** is an efficient toolkit designed for developers to automatically aggregate and merge multi-source ad-blocking filter rules 🧩.

This project helps you **automatically fetch mainstream ad-blocking filter rules**, remove duplicates, merge them, and output in standard formats, greatly simplifying the process of maintaining and updating custom blocklists.

Whether you're a data engineer, ad-blocking enthusiast, or someone who wants to maintain your own blocklist, FilterFusion enables one-stop automated processing!

### 🌈 Key Features

- **Lightning-Fast Performance** ⚡: Large-scale rule merging and deduplication with high-speed output
- **Highly Customizable** 🔧: Support for custom rule sources, templates, and output formats
- **One-Click Automation** 🤖: Fetch, merge, and publish rules with a single command
- **Multiple Use Cases** 🌍: Supports ad blocking, content filtering, parental controls, and more

---

## 📬 Subscription URLs

### AdBlock Rules (Browser Ad-Blocking)

Import any of the following links into your ad-blocking extension (uBlock Origin, AdGuard, etc.):

- **jsDelivr CDN** (Recommended for mainland China)  
  ```
  https://cdn.jsdelivr.net/gh/Chaniug/FilterFusion@main/dist/adblock-main.txt
  ```

- **GitHub Raw** (Available globally)  
  ```
  https://raw.githubusercontent.com/Chaniug/FilterFusion/main/dist/adblock-main.txt
  ```

- **gh.llkk.cc Acceleration** (Backup)  
  ```
  https://gh.llkk.cc/https://raw.githubusercontent.com/Chaniug/FilterFusion/main/dist/adblock-main.txt
  ```

### DNS Filtering Rules (Network-Level Ad-Blocking)

Import any of the following links into your DNS filtering tool (AdGuard Home, Pi-hole, Clash, etc.):

- **jsDelivr CDN** (Recommended for mainland China)  
  ```
  https://cdn.jsdelivr.net/gh/Chaniug/FilterFusion@main/dist/dns-blocklist.txt
  ```

- **GitHub Raw** (Available globally)  
  ```
  https://raw.githubusercontent.com/Chaniug/FilterFusion/main/dist/dns-blocklist.txt
  ```

- **gh.llkk.cc Acceleration** (Backup)  
  ```
  https://gh.llkk.cc/https://raw.githubusercontent.com/Chaniug/FilterFusion/main/dist/dns-blocklist.txt
  ```

### 📋 Report Filter Issues

<p align="center">
  <a href="https://github.com/Chaniug/AdSuper/issues/new?labels=%E8%A7%84%E5%88%99%E5%8F%8D%E9%A6%88&template=rule_report.yml" style="text-decoration:none;">
    <img src="https://img.shields.io/badge/Filter Feedback & Suggestions-Submit to @Chaniug/AdSuper-ff69b4?logo=github" alt="Report to AdSuper" />
  </a>
</p>

If you find **false positives, false negatives**, or want to suggest new rules, please submit an Issue to our sub-project [**@Chaniug/AdSuper**](https://github.com/Chaniug/AdSuper). We'll handle it promptly!

---

## 📦 System Requirements

Before using FilterFusion, ensure your system meets the following requirements:

### Minimum Requirements
- **Python**: 3.13 or higher (local development can use 3.14)
- **Operating System**: Windows, macOS, Linux
- **Network**: Internet connection required to fetch rule sources

### Dependencies
```
httpx[http2]>=0.27.0
```

### Check Python Version
```bash
python --version
# or
python3 --version
```

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Chaniug/FilterFusion.git
cd FilterFusion
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Fetch and Merge Rules

**AdBlock Rules**:
```bash
python scripts/fetch_rules.py    # Fetch all rule sources
python scripts/merge_rules.py    # Merge and deduplicate
```

**DNS Filtering Rules**:
```bash
python scripts/fetch_dns_rules.py    # Fetch DNS rule sources
python scripts/merge_dns_rules.py    # Merge and deduplicate DNS rules
```

### 4. Use the Generated Rules
- Generated rule files are located in the `dist/` directory
- Import directly into ad-blocking tools that support custom rules

---

## 🔧 How It Works

### Supported Rule Formats

FilterFusion supports mainstream ad-filtering rule formats:

- **Adblock Plus (ABP)** rules
- **uBlock Origin** rules
- **EasyList** rules
- Other ABP-compatible formats

### Rule Examples

```
||example.com^                          # Domain matching
www.example.com##.ad-banner             # Element hiding
@@||whitelist.com^$document             # Whitelist rule
! This is a comment
# This is also a comment
```

### Processing Pipeline

FilterFusion's workflow consists of four main stages:

```
Configure Sources → Fetch Rules → Merge & Deduplicate → Output Standard Format
```

---

## 📝 Usage Guide

### Step 1: Configure Rule Sources

#### AdBlock Rule Sources

Edit the `config/sources.txt` file to add the rule sources you want to aggregate:

```txt
# FilterFusion Rule Sources Configuration
# Format: Name > Subscription URL
# Enable: Write a line directly
# Disable: Add # at the beginning of the line

EasyList > https://easylist.to/easylist/easylist.txt
AdGuard Base > https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt

# Below are disabled sources (remove the leading # to enable):
# My Custom Rules > https://example.com/my-rules.txt
```

#### DNS Filtering Rule Sources

Edit the `config/dns_sources.txt` file to add the DNS filtering rule sources you want to aggregate:

```txt
# FilterFusion DNS Filtering Rule Sources Configuration
# Format: Name > Subscription URL
# Enable: Write a line directly
# Disable: Add # at the beginning of the line

AdGuard DNS > https://raw.githubusercontent.com/AdguardTeam/FiltersRegistry/master/filters/filter_15_DnsFilter/filter.txt
HaGeZi DNS > https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/dns.txt

# Below are disabled sources (remove the leading # to enable):
# StevenBlack Hosts > https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts
```

**Format Notes**:
- One rule source per line, separated by `>`
- Add `#` at the beginning to disable a source (keep config, skip fetching)
- Pure comment lines (with `#` but no `>`) are ignored
- URL must start with `http`

### Step 2: Fetch Rules

**AdBlock Rules**:
```bash
python scripts/fetch_rules.py
```

**DNS Filtering Rules**:
```bash
python scripts/fetch_dns_rules.py
```

**Features**:
- Download rule files from all configured sources
- Validate rule format validity
- Generate metadata (size, update time, etc.)
- Cache rule files for faster subsequent processing

### Step 3: Merge and Deduplicate Rules

**AdBlock Rules**:
```bash
python scripts/merge_rules.py
```

**DNS Filtering Rules**:
```bash
python scripts/merge_dns_rules.py
```

**Features**:
- Automatically remove duplicate rules
- Delete invalid and comment lines
- Merge all rules
- Output in standard format: `dist/adblock-main.txt` (AdBlock) or `dist/dns-blocklist.txt` (DNS)

### Step 4: Use in Filtering Tools

#### AdBlock Rules (Browser Ad-Blocking)

**Import Method (Example: uBlock Origin)**:

1. Open uBlock Origin extension options
2. Go to the "Filter lists" tab
3. Paste the subscription link in the "Import" field at the bottom
4. Click "Import"
5. Save settings

**Supported Tools**:
- uBlock Origin
- AdGuard (browser extension)
- Adblock Plus
- Brave Browser (Built-in)
- Safari ad-blocking extensions

#### DNS Filtering Rules (Network-Level Ad-Blocking)

**Import Method (Example: AdGuard Home)**:

1. Open AdGuard Home admin interface
2. Go to "Filters" → "DNS blocklists"
3. Click "Add a blocklist"
4. Paste the DNS rule subscription link
5. Click "Add"

**Supported Tools**:
- AdGuard Home
- Pi-hole
- Clash
- Surge
- Quantumult X
- Any tool that supports DNS filtering rules

---

## 💡 Use Cases

### Case 1: Build Personal Blocklist
```
Aggregate multiple sources → Merge & deduplicate → Generate custom blocklist
```

### Case 2: Enterprise Network Ad-Blocking
```
Configure enterprise-specific sources → Auto-update → Distribute to all devices
```

### Case 3: Content Filtering and Parental Controls
```
Select specialized filtering rules → Auto-update → Deploy in parental control system
```

### Case 4: Ad-Blocking Tool Development
```
Use FilterFusion to generate rules → Integrate into custom tools → Continuous maintenance
```

---

## ❓ FAQ

### Q1: How often are the rules updated?

**A**: The update frequency depends on:
- The update speed of configured rule sources
- How frequently you run the `fetch_rules.py` script

We recommend using GitHub Actions or cron jobs to automatically run the script. Suggested frequency: daily or weekly.

### Q2: How do I customize rule sources?

**A**: Edit the `config/sources.txt` file:

```txt
# Add a new rule source (one per line)
Your Rule Name > URL of the rule file

# Disable a rule source (add # at the beginning)
# Unwanted Source > https://example.com/filter.txt
```

- **Enable**: Write `Name > URL` directly
- **Disable**: Add `#` at the beginning of the line, no need to delete
- **URL Requirements**: Must be a directly accessible plain-text rule file (ABP/uBlock/AdGuard format compatible)

### Q3: What rule formats are supported?

**A**: FilterFusion supports:
- Adblock Plus (ABP) format
- uBlock Origin format
- EasyList/EasyPrivacy format
- Other ABP-compatible formats

### Q4: Where are the generated rule files?

**A**: After running the merge scripts, generated rule files are located in:

**AdBlock Rules**:
```
dist/adblock-main.txt       # Main rule file
dist/adblock-YYYYMMDD.txt   # Date-archived rule file
```

**DNS Filtering Rules**:
```
dist/dns-blocklist.txt       # Main rule file
dist/dns-blocklist-YYYYMMDD.txt   # Date-archived rule file
```

### Q5: What's the file size and performance?

**A**: 
- File size: Typically **2-5 MB** (depending on number of sources)
- Load performance: Modern browsers handle it easily
- Filter performance: Related to the complexity of rule sources

Regularly check file size and remove unnecessary rule sources for optimal performance.

### Q6: Why don't some rules work after importing?

**A**: Common reasons:
1. **Incompatible format** - Ensure your ad-blocking tool supports the rule format
2. **Rule syntax errors** - Check logs in `scripts/`
3. **Tool limitations** - Some tools limit the number of rules
4. **Cache issues** - Try restarting the browser or clearing extension cache

### Q7: Can I use multiple rule lists simultaneously?

**A**: **Yes**. Most ad-blocking tools support multiple rule lists. We recommend:
- Keep official rules (like EasyList) as the base
- Add FilterFusion-generated rules as supplements
- Use whitelist rules to avoid over-blocking

### Q8: I found false positives or false negatives, what should I do?

**A**: 
1. Record the specific URL with the issue
2. Submit an Issue to the [AdSuper project](https://github.com/Chaniug/AdSuper)
3. Provide detailed description (URL, blocking situation, etc.)
4. We'll process and update rules promptly

### Q9: Can I use this in commercial projects?

**A**: **Yes**. This project is licensed under MIT License, allowing commercial use. Just keep the original license and copyright notice in your project.

### Q10: How do I get technical support?

**A**: 
- 📖 Check [project documentation](https://github.com/Chaniug/FilterFusion/wiki)
- 🐛 Submit an [Issue](https://github.com/Chaniug/FilterFusion/issues)
- 💬 Ask in [Discussions](https://github.com/Chaniug/FilterFusion/discussions)
- 📧 Contact the maintainer (see contact info below)

---

## 📊 Contributors

<p align="center">
  <img src="https://contrib.rocks/image?repo=Chaniug/FilterFusion" alt="Contributors" />
</p>

[![Chaniug's github activity graph](https://github-readme-activity-graph.vercel.app/graph?username=Chaniug&theme=github-compact)](https://github.com/Ashutosh00710/github-readme-activity-graph)

- 👥 View all [contributors](https://github.com/Chaniug/FilterFusion/graphs/contributors)
- 🏆 You can appear here too. Welcome to contribute!

---

## 🤝 How to Contribute

![Chaniug's GitHub stats](https://github-readme-stats.vercel.app/api?username=Chaniug&show_icons=true&theme=tokyonight)
![Top Langs](https://github-readme-stats.vercel.app/api/top-langs/?username=Chaniug&layout=compact)

### Support the Project

- 🌟 [Star](https://github.com/Chaniug/FilterFusion/stargazers) the project to show your support
- 🍴 [Fork](https://github.com/Chaniug/FilterFusion/fork) the project
- 📢 Share with more people

### Participate in Development

- 🐛 Report issues and suggestions via [Issues](https://github.com/Chaniug/FilterFusion/issues)
- ✨ Submit [Pull Requests](https://github.com/Chaniug/FilterFusion/pulls) to contribute code
- 💬 Share ideas in [Discussions](https://github.com/Chaniug/FilterFusion/discussions)
- 📝 Improve documentation and examples

### Contributing Guidelines

1. Fork this project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](./LICENSE) file for details.

### License Summary

MIT License allows you to:
- ✅ Freely use, modify, and distribute this project
- ✅ Use in commercial and private projects
- ✅ Access and modify source code

You only need to:
- ⚠️ Keep the original license and copyright notice
- ⚠️ The project is provided "as-is" without any warranty

---

## 📧 Contact

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
  <b>Love this project? Please give it a Star ⭐ to support us!</b>
</p>
