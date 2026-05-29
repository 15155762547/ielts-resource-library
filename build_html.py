#!/usr/bin/env python3
"""
雅思语料库 HTML 生成脚本
- 高亮词汇表里的所有单词（黄底色）
- 按书籍/Test/Passage 组织成 HTML 文件
- 英文段落 + 中文翻译对照
"""

import os
import re

DATA_DIR = "/Volumes/奥睿科1TB/代码程序/剑雅资源库/data"
VOCAB_FILE = "/Volumes/奥睿科1TB/代码程序/单词表计划/wordlist_only.txt"
OUTPUT_DIR = "/Volumes/奥睿科1TB/代码程序/剑雅资源库/html_corpus"

# ----------------- 工具函数 -----------------

def build_vocab_set():
    vocab = set()
    with open(VOCAB_FILE, 'r', encoding='utf-8') as f:
        for word in f:
            word = word.strip().lower()
            if word:
                vocab.add(word)
    print(f"词汇表加载: {len(vocab)} 个词")
    return vocab


def highlight_text(text: str, vocab: set) -> str:
    """
    在文本中高亮词汇表里的单词（大写也算）。
    用 <mark> 标签包裹匹配单词（大小写不敏感）。
    """
    if not text.strip():
        return ""

    # 按单词边界拆分，保留标点
    tokens = re.split(r'(\b|[,;:.!?()""\'\-–\s]+)', text)

    result = []
    for token in tokens:
        if token.strip():
            if token.lower() in vocab:
                result.append(f'<mark style="background:#fef08a;">{token}</mark>')
            else:
                result.append(token)
        else:
            result.append(token)

    return ''.join(result)


def split_paragraphs_lines(content: str) -> tuple[list[str], list[str]]:
    """
    从交替格式的 txt 文件中提取英文段落和中文段落并配对。

    格式: [文件头 meta]
         [英文段落1]
         [中文段落1]
         [英文段落2]
         [中文段落2]
         ...
         ---
         [英文段落A]   ← 后半部分，继续交替
         [中文段落A]
         ...

    返回 (english_paras, chinese_paras)，两组等长列表，
    同一索引的英中段落互相配对。
    """
    chinese_meta_patterns = [
        r'^来源：',
        r'^©\s*\d{4}',
        r'^京ICP备',
        r'^隐私政策',
        r'^网站地图',
        r'老烤鸭雅思$',   # 以"老烤鸭雅思"结尾的行（通常是版权 footer）
        r'^老烤鸭雅思',   # 以"老烤鸭雅思"开头的行
        r'整篇文章大体可以',
        r'后七段讲述',
        r'以下(是|每|每段)',
    ]

    def is_meta_en(line: str) -> bool:
        """判断英文行是否为 meta/header 行"""
        line = line.strip()
        if not line:
            return True
        if line.startswith('#'):
            return True
        if '阅读答案解析' in line or '阅读原文翻译' in line:
            return True
        # 纯中文行混入英文部分
        if len(re.findall(r'[\u4e00-\u9fff]', line)) > 5:
            return True
        return False

    def is_meta_zh(line: str) -> bool:
        """判断中文行是否为 meta/header 行"""
        line = line.strip()
        if not line:
            return True
        if line.startswith('#'):
            return True
        for p in chinese_meta_patterns:
            if re.search(p, line):
                return True
        return False

    def is_valid_zh(line: str) -> bool:
        """判断是否为有效中文段落（含量足够的中文）"""
        line = line.strip()
        return len(re.findall(r'[\u4e00-\u9fff]', line)) >= 10

    lines = content.split('\n')
    english_paras = []
    chinese_paras = []

    i = 0
    while i < len(lines):
        raw = lines[i].strip()

        # 遇到 --- 分隔符：继续处理后面所有内容
        if raw == '---':
            i += 1
            continue

        # 跳过空行
        if not raw:
            i += 1
            continue

        # 跳过英文 meta 行
        if is_meta_en(raw):
            i += 1
            continue

        # 此时 raw 是英文段落内容
        en_text = raw

        # 找下一个有效中文段落
        zh_text = ''
        j = i + 1
        while j < len(lines):
            next_raw = lines[j].strip()
            if next_raw == '---':
                # 遇到分隔符，说明这个英文段落没有配对中文
                break
            if not next_raw:
                j += 1
                continue
            if is_meta_zh(next_raw):
                j += 1
                continue
            if is_valid_zh(next_raw):
                zh_text = next_raw
                i = j + 1   # 跳过英文行 + 中文行
                break
            else:
                # 不是有效中文，可能是纯英文继续段落
                break

        if not zh_text:
            # 没找到配对中文，只前进当前英文行
            i += 1

        english_paras.append(en_text)
        chinese_paras.append(zh_text)

    return english_paras, chinese_paras


def extract_paragraphs(raw: str, lang: str) -> list[str]:
    """按行提取段落，过滤空行和元信息行（兼容旧接口，仍保留学籍处理）"""
    lines = raw.strip().split('\n')
    paras = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            continue
        if lang == 'zh' and not re.search(r'[\u4e00-\u9fff]', line):
            continue
        if lang == 'zh' and len(re.findall(r'[\u4e00-\u9fff]', line)) < 10:
            continue
        if lang == 'en':
            chinese_ratio = len(re.findall(r'[\u4e00-\u9fff]', line)) / max(len(line), 1)
            if chinese_ratio > 0.3:
                continue
            if len(line) < 30 and not re.search(r'[.!?]', line):
                continue
        paras.append(line)
    return paras


# ----------------- HTML 模板 -----------------

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; background: #f5f5f5; color: #1a1a1a; line-height: 1.8; }}
        .container {{ max-width: 1100px; margin: 0 auto; padding: 20px; }}
        header {{ background: #1c2b3a; color: #fff; padding: 24px 32px; border-radius: 12px 12px 0 0; }}
        header h1 {{ font-size: 20px; font-weight: 600; }}
        header .meta {{ margin-top: 8px; font-size: 14px; color: #c09a5b; }}
        .lang-nav {{ background: #2d3e50; padding: 12px 32px; display: flex; gap: 4px; flex-wrap: wrap; }}
        .lang-nav button {{ background: none; border: none; color: #fff; padding: 6px 16px; cursor: pointer; font-size: 14px; border-radius: 6px; }}
        .lang-nav button.active {{ background: #c09a5b; color: #1c2b3a; font-weight: 600; }}
        .lang-nav .badge {{ font-size: 11px; opacity: 0.7; margin-left: 4px; }}
        .content {{ background: #fff; padding: 32px; border-radius: 0 0 12px 12px; min-height: 400px; }}
        .lang-section {{ display: none; }}
        .lang-section.active {{ display: block; }}
        h2 {{ font-size: 13px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin: 28px 0 12px; }}
        h2:first-child {{ margin-top: 0; }}
        p {{ margin-bottom: 16px; font-size: 16px; }}
        .en p {{ font-size: 16px; line-height: 2; }}
        .zh p {{ font-size: 15px; line-height: 2; color: #444; }}

        /* 双语对照A: 左右分栏 */
        .both-a {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
        .pair-a {{ margin-bottom: 28px; }}
        .pair-a .pair-en {{ margin-bottom: 8px; padding-bottom: 12px; border-bottom: 1px solid #e8e8e8; }}
        .pair-a .pair-zh {{ font-size: 14px; color: #555; line-height: 1.9; }}

        /* 双语对照C: 交替段落 */
        .both-c .pair {{ margin-bottom: 28px; border-left: 3px solid #c09a5b; padding-left: 20px; }}
        .both-c .pair-en {{ margin-bottom: 10px; }}
        .both-c .pair-zh {{ margin-top: 6px; font-size: 15px; color: #555; line-height: 1.9; }}
        .both-c .en-block {{ background: #fafafa; border-radius: 8px; padding: 16px 20px; margin-bottom: 20px; }}
        .both-c .zh-block {{ background: #f0f4ff; border-radius: 8px; padding: 14px 20px; margin-bottom: 20px; border-left: 3px solid #6b9fff; }}
        .both-c .en-block p, .both-c .zh-block p {{ margin-bottom: 0; font-size: 15px; }}
        .both-c .en-block mark {{ background: #fef08a; padding: 1px 2px; border-radius: 2px; }}
        .both-c .zh-block p {{ color: #444; }}

        mark {{ background: #fef08a; padding: 1px 2px; border-radius: 2px; }}
        .stats {{ background: #fffef0; border: 1px solid #f0e080; border-radius: 8px; padding: 16px 20px; margin-bottom: 24px; font-size: 14px; color: #666; }}
        .stats span {{ color: #c09a5b; font-weight: 600; }}
        .nav-footer {{ margin-top: 32px; padding-top: 16px; border-top: 1px solid #eee; }}
        .nav-footer a {{ display: inline-block; padding: 8px 16px; background: #1c2b3a; color: #fff; text-decoration: none; border-radius: 6px; font-size: 14px; }}
        .nav-footer a:hover {{ background: #2d3e50; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <div class="meta">{source}</div>
        </header>
        <div class="lang-nav">
            <button class="active" onclick="showLang('en')">English</button>
            <button onclick="showLang('zh')">中文翻译</button>
            <button onclick="showLang('both-a')">双语对照<span class="badge">A</span></button>
            <button onclick="showLang('both-c')">双语对照<span class="badge">C</span></button>
        </div>
        <div class="content">
            <div class="stats">词汇表匹配: <span>{match_count}</span> 处高亮</div>
            <div class="lang-section active" id="sec-en">
                <h2>English Original</h2>
                {english_content}
            </div>
            <div class="lang-section" id="sec-zh">
                <h2>中文翻译</h2>
                {chinese_content}
            </div>
            <div class="lang-section" id="sec-both-a">
                <h2>双语对照 A — 左右分栏</h2>
                {both_a_html}
            </div>
            <div class="lang-section" id="sec-both-c">
                <h2>双语对照 C — 交替段落</h2>
                {both_c_html}
            </div>
        </div>
        <div class="nav-footer">
            <a href="index.html">← 返回总目录</a>
        </div>
    </div>
    <script>
        function showLang(lang) {{
            document.querySelectorAll('.lang-section').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.lang-nav button').forEach(el => el.classList.remove('active'));
            document.getElementById('sec-' + lang).classList.add('active');
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>'''


def make_paragraph_html(text: str, vocab: set, lang: str) -> str:
    """把一段文字转成 HTML，英文高亮单词"""
    if lang == 'en':
        text = highlight_text(text, vocab)
        # 英文按句子分段落，方便阅读
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        para_html = '<p>' + '</p><p>'.join(sentences) + '</p>'
    else:
        text = text.strip().replace('\n', '')
        para_html = f'<p>{text}</p>'
    return para_html


def build_index_page(data_dir: str, vocab: set) -> str:
    """生成分书籍的总索引页面"""
    books = sorted([d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))],
                   key=lambda x: int(re.search(r'\d+', x).group()))

    rows = []
    for book in books:
        book_path = os.path.join(data_dir, book)
        passages = sorted([f for f in os.listdir(book_path) if f.endswith('.txt')])
        items = []
        for p in passages:
            meta = parse_filename(p)
            if meta:
                # 生成相对路径
                html_rel = f"{book}/{p.replace('.txt', '.html')}"
                items.append(f'<li><a href="{html_rel}">{meta["test"]} {meta["passage"]}</a></li>')
        rows.append(f'<div class="book"><h3>{book}</h3><ul>{"".join(items)}</ul></div>')

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>雅思阅读语料库</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; background: #f5f5f5; color: #1a1a1a; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 24px; }}
        header {{ background: #1c2b3a; color: #fff; padding: 28px 32px; border-radius: 12px 12px 0 0; }}
        header h1 {{ font-size: 22px; font-weight: 600; }}
        header p {{ margin-top: 8px; color: #c09a5b; font-size: 14px; }}
        .content {{ background: #fff; padding: 32px; border-radius: 0 0 12px 12px; }}
        .book {{ margin-bottom: 28px; }}
        .book h3 {{ font-size: 16px; color: #1c2b3a; margin-bottom: 10px; padding-bottom: 6px; border-bottom: 2px solid #1c2b3a; }}
        .book ul {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 6px; list-style: none; }}
        .book li {{ background: #f8f8f8; border-radius: 6px; }}
        .book a {{ display: block; padding: 10px 14px; color: #333; text-decoration: none; font-size: 14px; }}
        .book a:hover {{ background: #1c2b3a; color: #fff; border-radius: 6px; }}
        .intro {{ background: #fffef0; border: 1px solid #f0e080; border-radius: 8px; padding: 20px 24px; margin-bottom: 28px; font-size: 14px; line-height: 1.8; color: #555; }}
        .intro strong {{ color: #c09a5b; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>雅思阅读语料库</h1>
            <p>剑桥雅思 4–19 · 192 篇阅读文章 · 支持词汇高亮检索</p>
        </header>
        <div class="content">
            <div class="intro">
                <strong>使用方法：</strong>点击下方任意一篇，进入文章页面。英文原文里已高亮标注词汇表里的所有单词（黄色背景）。
                可以切换 <strong>English</strong> / <strong>中文翻译</strong> / <strong>双语对照</strong> 三种视图。
                页面内使用 Ctrl+F（或 Command+F）搜索任意单词，高亮词一目了然。
            </div>
            {''.join(rows)}
        </div>
    </div>
</body>
</html>'''


def parse_filename(fname: str):
    fname_clean = fname.replace('.txt', '')
    book_match = re.search(r'剑桥雅思\s*(\d+)', fname_clean)
    if not book_match:
        return None
    book = f"剑桥雅思{book_match.group(1)}"
    test_match = re.search(r'Test\s*(\d+)', fname_clean, re.IGNORECASE)
    passage_match = re.search(r'Passage\s*(\d+)', fname_clean, re.IGNORECASE)
    if not test_match or not passage_match:
        return None
    return {
        'book': book,
        'test': f"Test {test_match.group(1)}",
        'passage': f"Passage {passage_match.group(1)}"
    }


# ----------------- 主程序 -----------------

def main():
    vocab = build_vocab_set()

    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    total_files = 0
    total_highlights = 0

    for book_dir in sorted(os.listdir(DATA_DIR)):
        book_path = os.path.join(DATA_DIR, book_dir)
        if not os.path.isdir(book_path):
            continue

        html_book_dir = os.path.join(OUTPUT_DIR, book_dir)
        os.makedirs(html_book_dir, exist_ok=True)

        for fname in sorted(os.listdir(book_path)):
            if not fname.endswith('.txt'):
                continue
            total_files += 1
            txt_path = os.path.join(book_path, fname)
            meta = parse_filename(fname)
            if not meta:
                print(f"  [跳过] {fname}")
                continue

            with open(txt_path, 'r', encoding='utf-8') as f:
                content = f.read()

            english_paras, chinese_paras = split_paragraphs_lines(content)

            # 生成英文 HTML（带高亮）
            en_parts = []
            highlight_count = 0
            for para in english_paras:
                para_html = make_paragraph_html(para, vocab, 'en')
                en_parts.append(para_html)

            # 生成中文 HTML
            zh_parts = []
            for para in chinese_paras:
                zh_parts.append(f'<p>{para.strip()}</p>')

            en_html = '<div class="en">' + ''.join(en_parts) + '</div>'
            zh_html = '<div class="zh">' + ''.join(zh_parts) + '</div>'

            # 双语对照A: 左右分栏（按段落配对，英文在上，中文在下，两列并排）
            both_a_parts = []
            en_count = len(english_paras)
            zh_count = len(chinese_paras)
            for i in range(min(en_count, zh_count)):
                en_seg = make_paragraph_html(english_paras[i], vocab, 'en')
                zh_seg = f'<p>{chinese_paras[i].strip()}</p>'
                both_a_parts.append(
                    f'<div class="pair-a">'
                    f'<div class="pair-en">{en_seg}</div>'
                    f'<div class="pair-zh">{zh_seg}</div>'
                    f'</div>'
                )
            both_a_html = '<div class="both-a">' + ''.join(both_a_parts) + '</div>'

            # 双语对照C: 交替段落（英文段落块 + 中文段落块交替，块内不配对）
            both_c_parts = []
            for i in range(en_count):
                en_seg = make_paragraph_html(english_paras[i], vocab, 'en')
                both_c_parts.append(f'<div class="en-block">{en_seg}</div>')
                if i < zh_count and chinese_paras[i].strip():
                    both_c_parts.append(f'<div class="zh-block"><p>{chinese_paras[i].strip()}</p></div>')
            both_c_html = '<div class="both-c">' + ''.join(both_c_parts) + '</div>'

            title = f"{meta['book']} {meta['test']} {meta['passage']}"
            source_url_match = re.search(r'来源：(https?://[^\s]+)', content)
            source = source_url_match.group(1) if source_url_match else ''

            html_content = HTML_TEMPLATE.format(
                title=title,
                source=f'来源：{source}' if source else '',
                english_content=en_html,
                chinese_content=zh_html,
                both_a_html=both_a_html,
                both_c_html=both_c_html,
                match_count=en_count
            )

            html_name = fname.replace('.txt', '.html')
            html_path = os.path.join(html_book_dir, html_name)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            total_highlights += highlight_count

    # 生成总索引页
    index_html = build_index_page(DATA_DIR, vocab)
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)

    print(f"\n生成完成:")
    print(f"  文章总数: {total_files}")
    print(f"  高亮处总数: ~{total_highlights}")
    print(f"  输出目录: {OUTPUT_DIR}")
    print(f"  入口文件: {OUTPUT_DIR}/index.html")


if __name__ == '__main__':
    main()