#!/usr/bin/env python3
"""从txt重新生成所有正确的HTML"""

import re, os

def is_chinese(line):
    return bool(re.search(r'[一-鿿]', line))


def parse_single_file(content):
    lines = content.strip().split('\n')
    title = lines[0].lstrip('#').strip() if lines else "Unknown"
    source = ""
    if len(lines) > 1 and lines[1].startswith('# 来源'):
        source = lines[1].replace('# 来源：', '').strip()

    content_lines = []
    for i in range(8, len(lines)):
        line = lines[i].strip()
        if not line or '© 2017-2026' in line or '京ICP备' in line:
            break
        if '老烤鸭' in line or 'laokaoya' in line.lower():
            continue
        if line == '---':
            continue
        if re.match(r'剑桥雅思\d+', line):
            if '阅读原文翻译' in line:
                break
            continue
        if line:
            content_lines.append(line)

    en_paras, zh_paras = [], []
    i = 0
    while i < len(content_lines):
        if is_chinese(content_lines[i]):
            zh_paras.append(content_lines[i])
        else:
            en_paras.append(content_lines[i])
        i += 1

    return title, source, en_paras, zh_paras


def build_both(en_paras, zh_paras):
    """交替 2-by-2 分组：每次取2个EN段落和2个ZH段落，各装入一个block"""
    blocks = []
    en_idx = zh_idx = 0

    while en_idx < len(en_paras) or zh_idx < len(zh_paras):
        group_en = en_paras[en_idx:en_idx+2]
        en_idx += 2
        group_zh = zh_paras[zh_idx:zh_idx+2]
        zh_idx += 2

        if group_en:
            blocks.append('<div class="en-block"><p>' + '</p><p>'.join(group_en) + '</p></div>')
        if group_zh:
            blocks.append('<div class="zh-block"><p>' + '</p><p>'.join(group_zh) + '</p></div>')

    return ''.join(blocks)


TEMPLATE = """<!DOCTYPE html>
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
        .both-c .en-block {{ background: #fafafa; border-radius: 8px; padding: 16px 20px; margin-bottom: 20px; }}
        .both-c .zh-block {{ background: #f0f4ff; border-radius: 8px; padding: 14px 20px; margin-bottom: 20px; border-left: 3px solid #6b9fff; }}
        .both-c .en-block p, .both-c .zh-block p {{ margin-bottom: 0; font-size: 15px; }}
        .both-c .en-block mark {{ background: #fef08a; padding: 1px 2px; border-radius: 2px; }}
        .both-c .zh-block p {{ color: #444; }}
        mark {{ background: #fef08a; padding: 1px 2px; border-radius: 2px; }}
        .nav-footer {{ margin-top: 32px; padding-top: 16px; border-top: 1px solid #eee; }}
        .nav-footer a {{ display: inline-block; padding: 8px 16px; background: #1c2b3a; color: #fff; text-decoration: none; border-radius: 6px; font-size: 14px; }}
        .nav-footer a:hover {{ background: #2d3e50; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <div class="meta">来源：{source}</div>
        </header>
        <div class="lang-nav">
            <button class="active" onclick="showLang('en')">English</button>
            <button onclick="showLang('zh')">中文翻译</button>
            <button onclick="showLang('both-c')">双语对照<span class="badge">C</span></button>
        </div>
        <div class="content">
            <div class="lang-section active" id="sec-en">
                <h2>English Original</h2>
                <div class="en">{en_section}</div>
            </div>
            <div class="lang-section" id="sec-zh">
                <h2>中文翻译</h2>
                <div class="zh">{zh_section}</div>
            </div>
            <div class="lang-section" id="sec-both-c">
                <h2>双语对照 C — 交替段落</h2>
                <div class="both-c">{both_c_section}</div>
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
</html>"""


def build_section(paras):
    return ''.join(f'<p>{p.replace("<","&lt;").replace(">", "&gt;")}</p>' for p in paras if p)


def generate(title, source, en_paras, zh_paras):
    return TEMPLATE.format(
        title=title,
        source=source,
        en_section=build_section(en_paras),
        zh_section=build_section(zh_paras),
        both_c_section=build_both(en_paras, zh_paras)
    )


def main():
    base = "/Volumes/奥睿科1TB/代码程序/剑雅资源库"
    data_dir = os.path.join(base, "data")
    html_dir = os.path.join(base, "html_corpus")
    total = fixed = 0

    for book in [f"剑桥雅思{i}" for i in range(4, 20)]:
        txt_book = os.path.join(data_dir, book)
        html_book = os.path.join(html_dir, book)
        if not os.path.isdir(txt_book):
            continue
        os.makedirs(html_book, exist_ok=True)

        for txt_file in sorted(os.listdir(txt_book)):
            if not txt_file.endswith('.txt'):
                continue
            txt_path = os.path.join(txt_book, txt_file)
            html_name = txt_file[:-4] + '.html'
            html_path = os.path.join(html_book, html_name)

            with open(txt_path, encoding='utf-8') as f:
                content = f.read()
            title, source, en_paras, zh_paras = parse_single_file(content)
            html_content = generate(title, source, en_paras, zh_paras)

            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            en_b = html_content.count('class="en-block"')
            zh_b = html_content.count('class="zh-block"')
            status = "✓" if en_b == zh_b else f"✗ en={en_b} zh={zh_b}"
            print(f"{book}/{txt_file}: en={len(en_paras)} zh={len(zh_paras)} {status}")
            total += 1
            if en_b == zh_b:
                fixed += 1

    print(f"\n完成: {fixed}/{total} 文件 blocks数相等")


if __name__ == "__main__":
    main()