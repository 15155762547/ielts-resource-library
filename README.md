# 📚 雅思阅读智能高亮与双语对照语料库 / IELTS Reading Smart Highlighting & Bilingual Parallel Corpus

<p align="center">
  <img src="https://img.shields.io/badge/Language-HTML%20%7C%20JS%20%7C%20Python-blue.svg" alt="Languages">
  <img src="https://img.shields.io/badge/Data%20Source-Cambridge%20IELTS%204--19-orange.svg" alt="Cambridge IELTS 4-19">
  <img src="https://img.shields.io/badge/Vocabulary-7%2C413%20Words-green.svg" alt="7413 Vocabulary">
  <img src="https://img.shields.io/badge/License-Private-red.svg" alt="License Private">
</p>

[简体中文](#-中文介绍) | [English](#-english-description)

---

## 🇨🇳 中文介绍

这是一个专为雅思备考设计的智能交互式阅读语料库平台。系统对《剑桥雅思 4–19》全部官方阅读真题（共计 192 篇文章）进行了精准排版与对齐，并深度融合了 7,413 个大纲核心词汇的自动检索高亮、中文释义悬浮气泡以及多维度阅读模式。

### ✨ 核心功能亮点
1.  **📖 三向阅读视图无缝切换**：
    *   **英文原文**：专注英文浸入式阅读，采用美观舒适的 `Lora` 衬线学术字体，行高 2.0。
    *   **中文翻译**：纯中文精译排版，字间距与结构优化。
    *   **双语对照**：**最强特色功能**。宽屏设备采用 **左右分栏双列对齐** (左英右中)，段落高度在行内自适应同步对齐，阅读决不跑偏；窄屏或手机上自动响应式切换为 **上下段落交替**，中文部分附带淡蓝色雅致背景框。
2.  **🔍 全文大纲词汇自动高亮与词根还原 (Stemming)**：
    *   动态匹配内置词汇表（`合并单词表.csv`）。
    *   支持**智能词根变形匹配**：如词汇表中为 `reveal`，文章中出现的复数 `reveals`、过去式 `revealed`、进行时 `revealing` 都会被精准捕获并高亮。
3.  **📚 侧边栏词汇浏览器 (Vocabulary Sidebar)**：
    *   右侧抽屉式面板列出本篇文章涉及的全部高亮词汇及其**全文频次角标**与**中文释义**。
    *   支持输入过滤，支持**双向联动高亮**：点击侧边栏单词，文章所有匹配项闪烁并自动平滑滚动定位；点击文章中的单词可反向激活侧边栏。
4.  **💬 悬浮中文释义气泡 (Hover Tooltips)**：
    *   鼠标悬停在原文高亮词上时，会自动浮现深色毛玻璃交互气泡卡片，清晰呈现该词的**词根形式**和**中文翻译**。
    *   内置视口防溢出算法，自动避开屏幕边缘（顶部空间不足时自动翻转到下方显示）。
5.  **🎛️ 运行期辅助**：
    *   **全局词汇搜索**：主索引页拥有全局搜索引擎，输入单词立刻展示包含该词的全部真题文章并支持一键直达。
    *   **字号调节滑块**：阅读页支持 14px - 24px 动态无级字号调整。

### 📁 项目结构
```text
├── data/                  # 192篇官方真题原文与中文翻译数据源 (txt)
├── html_corpus/           # 自动生成的 HTML 交互平台 (用户使用主入口)
│   ├── index.html         # 资源库平台主页入口
│   ├── search_index.json  # 编译生成的全局检索词汇数据库
│   └── 剑桥雅思X/          # 各册书籍真题文章 HTML
├── build_html_v2.py       # 精排版与双语对齐 HTML 自动生成脚本
├── 合并单词表.csv           # 核心词汇中英对照数据库 (正面: 单词, 背面: 翻译)
├── wordlist_only.txt      # 纯单词表 (旧版备份)
└── README.md              # 项目文档
```

---

## 🇺🇸 English Description

An interactive, premium learning corpus designed specifically for IELTS candidates. It compiles, aligns, and styles all 192 reading passages from official **Cambridge IELTS books 4 to 19**, embedding advanced features such as automatic lemma-based vocabulary highlighting, inline interactive tooltips, a side vocabulary drawer, and a global search database mapping 7,413 key dictionary items.

### ✨ Key Features
1.  **📖 Three Multi-View Reading Layouts**:
    *   **English Original**: Deep immersion text styled with Lora serif fonts, 2.0 line-height, optimized for academic reading comfort.
    *   **Chinese Translation**: Pure translation views with custom line spacing.
    *   **Bilingual Parallel**: **Core feature**. Features a synchronized side-by-side column grid on desktop. Paragraph heights align dynamically. On mobile, it auto-collapses to alternating stacked paragraphs with soft-blue visual cards.
2.  **🔍 Lemma-Based Smart Highlighting (Stemming)**:
    *   Scans texts against the `合并单词表.csv` vocabulary database.
    *   Supports **rule-based stemming**: if `factor` is in the database, occurrences of `factors` will be highlighted; `reveal` matches `reveals`, `revealed`, and `revealing` correctly.
3.  **📚 Sidebar Vocabulary Drawer**:
    *   Displays all matched vocabulary in the current passage, including their **frequency counts** and **Chinese definitions**.
    *   Supports text search filtering and **two-way linking**: clicking a sidebar item scrolls the viewport to its first occurrence and pulses all matches; clicking words in the text selects them in the sidebar.
4.  **💬 Glassmorphic Tooltips on Hover**:
    *   Hovering over any highlighted word shows a modern translucent tooltip with the base lemma and translation.
    *   Auto-detects viewport boundaries to prevent screen overflow (flips to bottom if top space is tight).
5.  **🎛️ Real-Time Utilities**:
    *   **Global Search Engine**: Enter any vocab word on the index dashboard to immediately view all matching passages and jump to them.
    *   **Font Size Adjustment**: Slider control to scale article text sizes dynamically from 14px to 24px.

### 📁 Directory Layout
```text
├── data/                  # Original txt files of 192 IELTS articles
├── html_corpus/           # Generated HTML interactive platform (Learning Entrance)
│   ├── index.html         # Main dashboard page
│   ├── search_index.json  # Global search database compiled by Python
│   └── 剑桥雅思X/          # Generated HTML article pages per book
├── build_html_v2.py       # Compilation script for aligned paragraph formatting
├── 合并单词表.csv           # Vocabulary translation CSV database (word, definition)
├── wordlist_only.txt      # Word list backup
└── README.md              # Project Documentation
```

---

## ⚙️ 生成与构建指南 / Compilation Guide

如果您修改了 `data/` 里的真题文本，或者更新了 `合并单词表.csv` 词典，您可以重新运行生成脚本来编译整个语料库：

If you update the text files in `data/` or add words to `合并单词表.csv`, you can recompile the corpus using the following commands:

```bash
# 运行新版排版对齐与高亮编译脚本
# Run the alignment and formatting compiler script
python3 build_html_v2.py
```

*生成完成后，可以直接在浏览器中双击打开 `html_corpus/index.html` 进入学习主页。*  
*Once compiled, simply open `html_corpus/index.html` in your browser to start studying.*

---

## ⚠️ 版权与使用声明 / License & Copyright Disclaimer

本仓库存放的 `data/` 和 `html_corpus/` 包含**剑桥雅思官方真题阅读原文**及其翻译文本，版权归相关官方机构及原译者所有。

**请务必将本仓库保持在 GitHub 的 Private (私有仓库) 状态**，切勿将其公开 (Public) 上传至任何公共平台，以免发生版权或法律纠纷。

---

*祝您雅思备考顺利，取得理想成绩！*  
*Best of luck with your IELTS preparation!*
