#!/usr/bin/env python3
import os
import re
import json

DATA_DIR = "/Volumes/奥睿科1TB/代码程序/剑雅资源库/data"
VOCAB_FILE = "/Volumes/奥睿科1TB/代码程序/剑雅资源库/wordlist_only.txt"
OUTPUT_DIR = "/Volumes/奥睿科1TB/代码程序/剑雅资源库/html_corpus"

# ----------------- 词汇处理 -----------------

def build_vocab_set():
    vocab = set()
    if not os.path.exists(VOCAB_FILE):
        print(f"警告: 找不到词汇文件 {VOCAB_FILE}，将尝试读取当前目录下的文件")
        local_vocab = "wordlist_only.txt"
        if os.path.exists(local_vocab):
            vocab_path = local_vocab
        else:
            raise FileNotFoundError("未找到 wordlist_only.txt 文件")
    else:
        vocab_path = VOCAB_FILE
        
    with open(vocab_path, 'r', encoding='utf-8') as f:
        for word in f:
            word = word.strip().lower()
            if word:
                vocab.add(word)
    print(f"成功加载词汇表: {len(vocab)} 个单词")
    return vocab


def find_stem(word: str, vocab: set) -> str:
    word_lower = word.lower()
    if word_lower in vocab:
        return word_lower
        
    # Suffix rules for IELTS vocabulary
    # 1. Plural -s (decades -> decade)
    if word_lower.endswith('s') and len(word_lower) > 3:
        stem = word_lower[:-1]
        if stem in vocab:
            return stem
            
    # 2. Plural -es (boxes -> box)
    if word_lower.endswith('es') and len(word_lower) > 4:
        stem = word_lower[:-2]
        if stem in vocab:
            return stem
            
    # 3. Past/Passive -ed (revealed -> reveal, used -> use)
    if word_lower.endswith('ed') and len(word_lower) > 4:
        stem1 = word_lower[:-2]
        if stem1 in vocab:
            return stem1
        stem2 = word_lower[:-1]
        if stem2 in vocab:
            return stem2
            
    # 4. Continuous -ing (playing -> play, making -> make)
    if word_lower.endswith('ing') and len(word_lower) > 5:
        stem1 = word_lower[:-3]
        if stem1 in vocab:
            return stem1
        stem2 = word_lower[:-3] + 'e'
        if stem2 in vocab:
            return stem2
            
    # 5. Adverb -ly (slowly -> slow)
    if word_lower.endswith('ly') and len(word_lower) > 4:
        stem = word_lower[:-2]
        if stem in vocab:
            return stem
            
    return None


def highlight_text(text: str, vocab: set, word_counts: dict) -> tuple[str, set]:
    if not text.strip():
        return "", set()

    # Split by non-alphabetic chars, preserving hyphens inside words
    tokens = re.split(r'([^A-Za-z\-]+)', text)
    
    result = []
    matched_words = set()
    
    for token in tokens:
        if re.search(r'[A-Za-z]', token):
            vocab_word = find_stem(token, vocab)
            if vocab_word:
                # Wrap matching vocabulary in interactive mark tags
                result.append(f'<mark class="vocab-word" data-word="{vocab_word}">{token}</mark>')
                matched_words.add(vocab_word)
                word_counts[vocab_word] = word_counts.get(vocab_word, 0) + 1
            else:
                result.append(token)
        else:
            result.append(token)
            
    return ''.join(result), matched_words

# ----------------- 数据清洗与对齐 -----------------

def is_chinese(line):
    return bool(re.search(r'[\u4e00-\u9fff]', line))


def clean_text(line):
    line = line.strip()
    line = re.sub(r'文章来自老烤鸭雅思', '', line)
    line = re.sub(r'老烤鸭雅思', '', line)
    line = re.sub(r'laokaoya', '', line, flags=re.IGNORECASE)
    return line.strip()


def has_sentence_terminator(text, lang):
    if not text:
        return True
    last_char = text[-1]
    if lang == 'ZH':
        return last_char in ('。', '？', '！', '”', '；', '）', '’')
    else:
        return last_char in ('.', '?', '!', '"', "'", ')', '’', '”')


def split_mixed_line(line):
    """If a line contains both a long English part and a Chinese part, split them."""
    match = re.search(r'[\u4e00-\u9fff]', line)
    if not match:
        return None, None
        
    idx = match.start()
    en_part = line[:idx].strip()
    zh_part = line[idx:].strip()
    
    en_clean = re.sub(r'\s+', '', en_part)
    zh_chars = len(re.findall(r'[\u4e00-\u9fff]', zh_part))
    
    if len(en_clean) >= 15 and zh_chars >= 5:
        return en_part, zh_part
        
    return None, None


def extract_title_from_content(content: str, default_title: str) -> str:
    lines = content.split('\n')
    for line in lines[:6]:
        line = line.strip()
        match = re.search(r'(?:原文翻译|答案解析)\s*(.+)$', line)
        if match:
            title_text = match.group(1).strip()
            if title_text:
                return title_text
    return default_title


def parse_into_blocks(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    lines = content.split('\n')
    
    # 1. Clean lines
    raw_paras = []
    for idx, line in enumerate(lines):
        cleaned = clean_text(line)
        if not cleaned:
            continue
        if cleaned.startswith('#'):
            continue
        if '©' in cleaned or '京ICP备' in cleaned or '隐私政策' in cleaned or '网站地图' in cleaned:
            continue
        if cleaned == '---' or cleaned == '===':
            continue
            
        # Classify
        if is_chinese(cleaned):
            zh_chars = len(re.findall(r'[\u4e00-\u9fff]', cleaned))
            if zh_chars > 3:
                raw_paras.append(('ZH', cleaned, idx + 1))
            else:
                raw_paras.append(('EN', cleaned, idx + 1))
        else:
            raw_paras.append(('EN', cleaned, idx + 1))

    # 2. Find first English body paragraph (>120 chars)
    first_en_idx = -1
    for i, (p_type, text, line_num) in enumerate(raw_paras):
        if p_type == 'EN' and len(text) > 120:
            first_en_idx = i
            break
            
    if first_en_idx == -1:
        for i, (p_type, text, line_num) in enumerate(raw_paras):
            if p_type == 'EN' and len(text) > 60:
                first_en_idx = i
                break
                
    if first_en_idx == -1:
        return None, "Unknown Title", []
        
    # Extract title from content
    title = extract_title_from_content(content, "IELTS Article")
    
    # Body candidates
    body_candidates = raw_paras[first_en_idx:]
    
    # 3. Filter footer links
    body_lines = []
    footer_started = False
    for p_type, text, line_num in body_candidates:
        is_footer = False
        if p_type == 'ZH' and len(text) < 150:
            if '原文翻译' in text or '答案解析' in text or '阅读词汇' in text or '真题词汇' in text or '点击查看' in text:
                is_footer = True
        
        if is_footer:
            footer_started = True
            
        if not footer_started:
            body_lines.append((p_type, text))
            
    # 4. Split mixed lines
    processed_body = []
    for p_type, text in body_lines:
        en_part, zh_part = split_mixed_line(text)
        if en_part and zh_part:
            processed_body.append(('EN', en_part))
            processed_body.append(('ZH', zh_part))
        else:
            processed_body.append((p_type, text))
            
    # 5. Merge split paragraphs
    merged_paras = []
    i = 0
    while i < len(processed_body):
        p_type, text = processed_body[i]
        
        while i + 1 < len(processed_body) and processed_body[i+1][0] == p_type and not has_sentence_terminator(text, p_type):
            text += " " + processed_body[i+1][1]
            i += 1
            
        merged_paras.append((p_type, text))
        i += 1
        
    # 6. Group into bilingual blocks
    blocks = []
    curr_en = []
    curr_zh = []
    
    for p_type, text in merged_paras:
        if p_type == 'EN':
            if curr_zh:
                blocks.append((curr_en, curr_zh))
                curr_en = [text]
                curr_zh = []
            else:
                curr_en.append(text)
        else:
            curr_zh.append(text)
            
    if curr_en or curr_zh:
        blocks.append((curr_en, curr_zh))
        
    return content, title, blocks


def parse_filename(fname: str):
    fname_clean = fname.replace('.txt', '')
    
    # Book
    book_match = re.search(r'剑桥雅思\s*(\d+)', fname_clean)
    if not book_match:
        return None
    book_num = int(book_match.group(1))
    book = f"剑桥雅思{book_num}"
    
    # Test
    test_match = re.search(r'Test\s*(\d+)', fname_clean, re.IGNORECASE)
    test = f"Test {test_match.group(1)}" if test_match else "Test 1"
    
    # Passage
    passage_match = re.search(r'Passage\s*(\d+)', fname_clean, re.IGNORECASE)
    passage = f"Passage {passage_match.group(1)}" if passage_match else "Passage 1"
    
    return {
        'book': book,
        'book_num': book_num,
        'test': test,
        'passage': passage
    }


def get_clean_html_name(fname: str, book_name: str) -> str:
    name_clean = fname.replace('.txt', '').replace('.html', '')
    pattern = rf'^({re.escape(book_name)})[\s\-–_]*({re.escape(book_name)})'
    if re.match(pattern, name_clean):
        name_clean = re.sub(pattern, r'\1', name_clean)
    return name_clean + '.html'


# ----------------- HTML 模板 -----------------

ARTICLE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - {book} {test} {passage} - 雅思阅读高亮资源库</title>
    <!-- Outfit & Lora Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400..700;1,400..700&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #f8fafc;
            --text-color: #1e293b;
            --primary: #1e3a8a;
            --primary-light: #eff6ff;
            --accent: #d97706;
            --accent-light: #fef3c7;
            --border-color: #e2e8f0;
            --card-bg: #ffffff;
            --sidebar-width: 320px;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg-color);
            color: var(--text-color);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}

        /* App Layout */
        .app-container {{
            display: flex;
            flex: 1;
            position: relative;
        }}

        /* Sidebar Style */
        aside {{
            width: var(--sidebar-width);
            background: var(--card-bg);
            border-right: 1px solid var(--border-color);
            position: fixed;
            top: 0;
            bottom: 0;
            left: 0;
            z-index: 100;
            display: flex;
            flex-direction: column;
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        .sidebar-header {{
            padding: 24px;
            border-bottom: 1px solid var(--border-color);
        }}

        .sidebar-header h2 {{
            font-size: 18px;
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .sidebar-header p {{
            font-size: 13px;
            color: #64748b;
        }}

        .vocab-search {{
            padding: 12px 24px;
            border-bottom: 1px solid var(--border-color);
            background: #fafafa;
        }}

        .vocab-search input {{
            width: 100%;
            padding: 8px 12px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            font-size: 13px;
            font-family: inherit;
            outline: none;
            transition: border-color 0.2s;
        }}

        .vocab-search input:focus {{
            border-color: var(--primary);
        }}

        .vocab-list-wrapper {{
            flex: 1;
            overflow-y: auto;
            padding: 16px 24px;
        }}

        .vocab-list {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}

        .vocab-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            background: var(--bg-color);
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
            border: 1px solid transparent;
        }}

        .vocab-item:hover {{
            background: var(--primary-light);
            border-color: #93c5fd;
        }}

        .vocab-item.active-filter {{
            background: var(--primary);
            color: white;
        }}

        .vocab-item.active-filter .badge {{
            background: rgba(255, 255, 255, 0.2);
            color: white;
        }}

        .vocab-item .word-name {{
            font-weight: 500;
        }}

        .vocab-item .badge {{
            font-size: 11px;
            background: #e2e8f0;
            color: #475569;
            padding: 2px 8px;
            border-radius: 99px;
            font-weight: 600;
        }}

        /* Main Workspace */
        main {{
            flex: 1;
            margin-left: var(--sidebar-width);
            padding: 40px;
            max-width: 1200px;
            width: calc(100% - var(--sidebar-width));
            display: flex;
            flex-direction: column;
            gap: 32px;
            transition: margin-left 0.3s;
        }}

        /* Header styling */
        header {{
            background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
            color: white;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            position: relative;
            overflow: hidden;
        }}

        header::after {{
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            bottom: 0;
            left: 0;
            background: radial-gradient(circle at top right, rgba(255, 255, 255, 0.1), transparent 60%);
            pointer-events: none;
        }}

        .back-link {{
            display: inline-flex;
            align-items: center;
            color: rgba(255, 255, 255, 0.8);
            text-decoration: none;
            font-size: 14px;
            margin-bottom: 20px;
            gap: 6px;
            transition: color 0.2s;
        }}

        .back-link:hover {{
            color: white;
        }}

        .badges {{
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
        }}

        .badge-tag {{
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(4px);
            color: white;
            padding: 4px 12px;
            border-radius: 99px;
            font-size: 12px;
            font-weight: 500;
            letter-spacing: 0.5px;
        }}

        header h1 {{
            font-size: 28px;
            font-weight: 700;
            line-height: 1.4;
            max-width: 900px;
        }}

        header .meta-source {{
            margin-top: 16px;
            font-size: 13px;
            color: rgba(255, 255, 255, 0.6);
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        header .meta-source a {{
            color: inherit;
            text-decoration: underline;
        }}

        /* Toolbar controls */
        .toolbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--card-bg);
            padding: 16px 24px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.05);
            flex-wrap: wrap;
            gap: 16px;
        }}

        /* Segmented Controller (Tabs) */
        .tabs-selector {{
            display: inline-flex;
            background: var(--bg-color);
            padding: 4px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}

        .tab-btn {{
            background: none;
            border: none;
            padding: 8px 20px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            color: #64748b;
            transition: all 0.2s;
            font-family: inherit;
        }}

        .tab-btn.active {{
            background: var(--card-bg);
            color: var(--primary);
            box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
            font-weight: 600;
        }}

        /* Font controls */
        .font-controls {{
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 13px;
            color: #64748b;
        }}

        .font-slider {{
            width: 100px;
            cursor: pointer;
            accent-color: var(--primary);
        }}

        /* Content Sections */
        .content-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.02);
            padding: 48px;
            min-height: 400px;
            transition: all 0.2s;
        }}

        .reading-section {{
            display: none;
        }}

        .reading-section.active {{
            display: block;
        }}

        /* Reading styles */
        .en-article, .zh-article {{
            max-width: 800px;
            margin: 0 auto;
        }}

        .en-article p {{
            font-family: 'Lora', Georgia, serif;
            font-size: var(--article-font-size, 18px);
            line-height: 2.0;
            color: var(--text-color);
            margin-bottom: 28px;
            text-align: justify;
        }}

        .zh-article p {{
            font-family: inherit;
            font-size: calc(var(--article-font-size, 18px) - 2px);
            line-height: 1.9;
            color: #334155;
            margin-bottom: 24px;
            text-align: justify;
        }}

        /* Parallel rows */
        .parallel-container {{
            display: flex;
            flex-direction: column;
        }}

        .parallel-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 48px;
            padding: 32px 0;
            border-bottom: 1px solid var(--border-color);
        }}

        .parallel-row:first-child {{
            padding-top: 0;
        }}

        .parallel-row:last-child {{
            border-bottom: none;
            padding-bottom: 0;
        }}

        .parallel-en p {{
            font-family: 'Lora', Georgia, serif;
            font-size: var(--article-font-size, 17px);
            line-height: 1.9;
            color: var(--text-color);
            margin-bottom: 16px;
            text-align: justify;
        }}

        .parallel-en p:last-child {{
            margin-bottom: 0;
        }}

        .parallel-zh p {{
            font-family: inherit;
            font-size: calc(var(--article-font-size, 17px) - 2px);
            line-height: 1.8;
            color: #475569;
            margin-bottom: 14px;
            text-align: justify;
        }}

        .parallel-zh p:last-child {{
            margin-bottom: 0;
        }}

        /* Vocabulary highlights */
        .vocab-word {{
            background-color: rgba(245, 158, 11, 0.12);
            border-bottom: 2px solid rgba(245, 158, 11, 0.5);
            color: inherit;
            cursor: pointer;
            padding: 1px 2px;
            border-radius: 2px;
            transition: all 0.15s ease-in-out;
            font-weight: 500;
        }}

        .vocab-word:hover {{
            background-color: var(--accent-light);
            border-bottom-color: var(--accent);
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}

        .vocab-word.highlighted-active {{
            background-color: var(--accent);
            color: white;
            border-bottom-color: var(--accent);
            border-radius: 4px;
            padding: 2px 4px;
            box-shadow: 0 4px 6px rgba(217, 87, 6, 0.3);
        }}

        /* Sidebar toggle button (Mobile) */
        .menu-toggle {{
            display: none;
            position: fixed;
            bottom: 24px;
            right: 24px;
            width: 56px;
            height: 56px;
            background: var(--primary);
            color: white;
            border-radius: 99px;
            border: none;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
            z-index: 999;
            cursor: pointer;
            justify-content: center;
            align-items: center;
            font-size: 20px;
        }}

        /* Responsive Design */
        @media (max-width: 992px) {{
            aside {{
                transform: translateX(-100%);
            }}
            
            aside.open {{
                transform: translateX(0);
                box-shadow: 10px 0 30px rgba(0, 0, 0, 0.15);
            }}

            main {{
                margin-left: 0;
                width: 100%;
                padding: 20px;
            }}

            .menu-toggle {{
                display: flex;
            }}
        }}

        @media (max-width: 768px) {{
            .parallel-row {{
                grid-template-columns: 1fr;
                gap: 20px;
                padding: 24px 0;
            }}
            
            .parallel-en {{
                border-bottom: 1px dashed var(--border-color);
                padding-bottom: 20px;
            }}

            .content-card {{
                padding: 24px;
            }}

            header {{
                padding: 24px;
            }}

            header h1 {{
                font-size: 22px;
            }}
        }}
    </style>
</head>
<body>
    <button class="menu-toggle" onclick="toggleSidebar()">☰</button>

    <div class="app-container">
        <!-- Sidebar containing vocab list -->
        <aside id="sidebar">
            <div class="sidebar-header">
                <h2>📚 词汇浏览器</h2>
                <p>本篇共识别出 <b id="vocab-total-count">0</b> 个高亮单词</p>
            </div>
            <div class="vocab-search">
                <input type="text" id="vocab-search-input" placeholder="搜索本篇高亮单词..." oninput="filterVocabList()">
            </div>
            <div class="vocab-list-wrapper">
                <ul class="vocab-list" id="vocab-list">
                    <!-- Dynamic vocab items will be inserted here -->
                </ul>
            </div>
        </aside>

        <!-- Main text view -->
        <main>
            <header>
                <a href="../index.html" class="back-link">
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                        <path fill-rule="evenodd" d="M15 8a.5.5 0 0 0-.5-.5H2.707l3.147-3.146a.5.5 0 1 0-.708-.708l-4 4a.5.5 0 0 0 0 .708l4 4a.5.5 0 0 0 .708-.708L2.707 8.5H14.5A.5.5 0 0 0 15 8z"/>
                    </svg>
                    返回总目录
                </a>
                <div class="badges">
                    <span class="badge-tag">{book}</span>
                    <span class="badge-tag">{test}</span>
                    <span class="badge-tag">{passage}</span>
                </div>
                <h1>{title}</h1>
                <div class="meta-source">
                    <svg width="12" height="12" fill="currentColor" viewBox="0 0 16 16" style="opacity: 0.8;">
                        <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM1.173 8a13.133 13.133 0 0 1 1.66-2.043C4.12 4.668 5.88 4 8 4c2.12 0 3.879.668 5.168 1.957A13.133 13.133 0 0 1 14.828 8c-.058.087-.122.183-.195.288-.335.48-.83 1.12-1.465 1.755C11.879 11.332 10.119 12 8 12c-2.12 0-3.879-.668-5.168-1.957A13.134 13.134 0 0 1 1.172 8z"/>
                        <path d="M8 5.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5zM4.5 8a3.5 3.5 0 1 1 7 0 3.5 3.5 0 0 1-7 0z"/>
                    </svg>
                    <span>{source}</span>
                </div>
            </header>

            <div class="toolbar">
                <div class="tabs-selector">
                    <button class="tab-btn active" onclick="switchTab('en')">English 原文</button>
                    <button class="tab-btn" onclick="switchTab('zh')">中文翻译</button>
                    <button class="tab-btn" onclick="switchTab('both')">双语对照</button>
                </div>
                <div class="font-controls">
                    <span>字号</span>
                    <input type="range" class="font-slider" id="font-size-slider" min="14" max="24" value="18" oninput="changeFontSize(this.value)">
                    <span id="font-size-val">18px</span>
                </div>
            </div>

            <div class="content-card">
                <!-- English section -->
                <div class="reading-section active" id="section-en">
                    <div class="en-article">
                        {en_paragraphs}
                    </div>
                </div>

                <!-- Chinese section -->
                <div class="reading-section" id="section-zh">
                    <div class="zh-article">
                        {zh_paragraphs}
                    </div>
                </div>

                <!-- Parallel section -->
                <div class="reading-section" id="section-both">
                    <div class="parallel-container">
                        {both_rows}
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        // Set vocabulary list and counts dynamically
        const wordCounts = {word_counts_json};
        let activeWord = null;

        // Initialize UI
        document.addEventListener('DOMContentLoaded', () => {{
            renderVocabList();
            setupWordClickListeners();
        }});

        function toggleSidebar() {{
            document.getElementById('sidebar').classList.toggle('open');
        }}

        function switchTab(tabId) {{
            document.querySelectorAll('.reading-section').forEach(sec => sec.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            
            document.getElementById('section-' + tabId).classList.add('active');
            
            // Find clicking button
            let btnIdx = tabId === 'en' ? 0 : (tabId === 'zh' ? 1 : 2);
            document.querySelectorAll('.tab-btn')[btnIdx].classList.add('active');
        }}

        function changeFontSize(val) {{
            document.documentElement.style.setProperty('--article-font-size', val + 'px');
            document.getElementById('font-size-val').textContent = val + 'px';
        }}

        function renderVocabList(filter = '') {{
            const listContainer = document.getElementById('vocab-list');
            listContainer.innerHTML = '';
            
            const words = Object.keys(wordCounts).sort();
            let totalMatch = 0;
            
            words.forEach(word => {{
                if (filter && !word.includes(filter.toLowerCase())) return;
                
                totalMatch += wordCounts[word];
                
                const li = document.createElement('li');
                li.className = 'vocab-item';
                if (activeWord === word) li.classList.add('active-filter');
                
                li.innerHTML = `
                    <span class="word-name">${{word}}</span>
                    <span class="badge">${{wordCounts[word]}}</span>
                `;
                
                li.onclick = (e) => {{
                    e.stopPropagation();
                    selectWord(word);
                }};
                listContainer.appendChild(li);
            }});
            
            document.getElementById('vocab-total-count').textContent = words.length;
        }}

        function filterVocabList() {{
            const query = document.getElementById('vocab-search-input').value;
            renderVocabList(query);
        }}

        function setupWordClickListeners() {{
            document.querySelectorAll('.vocab-word').forEach(element => {{
                element.onclick = (e) => {{
                    e.stopPropagation();
                    const word = element.getAttribute('data-word');
                    selectWord(word);
                }};
            }});
        }}

        function selectWord(word) {{
            if (activeWord === word) {{
                // De-select
                activeWord = null;
                document.querySelectorAll('.vocab-word').forEach(el => {{
                    el.classList.remove('highlighted-active');
                }});
                renderVocabList(document.getElementById('vocab-search-input').value);
                return;
            }}
            
            activeWord = word;
            
            // Re-render sidebar items to show active class
            renderVocabList(document.getElementById('vocab-search-input').value);
            
            // Highlight occurrences in document
            document.querySelectorAll('.vocab-word').forEach(el => {{
                if (el.getAttribute('data-word') === word) {{
                    el.classList.add('highlighted-active');
                }} else {{
                    el.classList.remove('highlighted-active');
                }}
            }});
            
            // Scroll to the first active instance
            const firstActive = document.querySelector('.vocab-word.highlighted-active');
            if (firstActive) {{
                // Determine if we need to switch tabs
                const parentSection = firstActive.closest('.reading-section');
                if (parentSection && !parentSection.classList.contains('active')) {{
                    const sectionId = parentSection.id.replace('section-', '');
                    switchTab(sectionId);
                }}
                
                setTimeout(() => {{
                    firstActive.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                }}, 100);
            }}
        }}
    </script>
</body>
</html>
"""

# ----------------- 总索引页面模板 -----------------

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>雅思阅读高亮资源库 - 剑桥雅思真语料</title>
    <!-- Outfit Font -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #f8fafc;
            --text-color: #0f172a;
            --primary: #1e3a8a;
            --primary-dark: #1e40af;
            --border-color: #e2e8f0;
            --card-bg: #ffffff;
            --accent: #d97706;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg-color);
            color: var(--text-color);
            min-height: 100vh;
            padding: 48px 24px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            gap: 40px;
        }}

        /* Hero Header */
        header {{
            background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%);
            color: white;
            padding: 56px 48px;
            border-radius: 24px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}

        header::after {{
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            bottom: 0;
            left: 0;
            background: radial-gradient(circle at top right, rgba(255, 255, 255, 0.15), transparent 70%);
            pointer-events: none;
        }}

        header h1 {{
            font-size: 36px;
            font-weight: 800;
            letter-spacing: -0.5px;
        }}

        header p {{
            font-size: 16px;
            color: rgba(255, 255, 255, 0.7);
            max-width: 600px;
            line-height: 1.6;
        }}

        /* Search Section */
        .search-section {{
            background: var(--card-bg);
            padding: 32px;
            border-radius: 20px;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}

        .search-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 12px;
        }}

        .search-title {{
            font-size: 18px;
            font-weight: 600;
            color: var(--primary);
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .search-bar {{
            position: relative;
            width: 100%;
        }}

        .search-bar input {{
            width: 100%;
            padding: 16px 20px;
            border-radius: 12px;
            border: 2px solid var(--border-color);
            outline: none;
            font-size: 16px;
            font-family: inherit;
            transition: all 0.2s;
        }}

        .search-bar input:focus {{
            border-color: var(--primary);
            box-shadow: 0 0 0 4px rgba(30, 58, 138, 0.1);
        }}

        /* Search Results Drawer */
        .search-results {{
            display: none;
            flex-direction: column;
            gap: 12px;
            max-height: 400px;
            overflow-y: auto;
            border-top: 1px solid var(--border-color);
            padding-top: 20px;
        }}

        .search-results.active {{
            display: flex;
        }}

        .result-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 20px;
            background: var(--bg-color);
            border-radius: 10px;
            text-decoration: none;
            color: inherit;
            transition: all 0.2s;
            border: 1px solid transparent;
        }}

        .result-item:hover {{
            background: var(--primary-light);
            border-color: #93c5fd;
            transform: translateX(4px);
        }}

        .result-title {{
            font-weight: 500;
            color: var(--primary-dark);
        }}

        .result-meta {{
            font-size: 13px;
            color: #64748b;
            display: flex;
            gap: 8px;
        }}

        /* Corpus Directory Grid */
        .corpus-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 24px;
        }}

        .book-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.01);
            transition: transform 0.2s, box-shadow 0.2s;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}

        .book-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
        }}

        .book-card h3 {{
            font-size: 18px;
            font-weight: 700;
            color: var(--primary);
            border-bottom: 2px solid var(--primary-light);
            padding-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .book-card .article-count {{
            font-size: 12px;
            background: var(--primary-light);
            color: var(--primary);
            padding: 2px 10px;
            border-radius: 99px;
            font-weight: 600;
        }}

        .article-list {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 8px;
            flex: 1;
        }}

        .article-link {{
            display: block;
            padding: 10px 12px;
            border-radius: 8px;
            background: var(--bg-color);
            color: #334155;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
        }}

        .article-link:hover {{
            background: var(--primary);
            color: white;
        }}

        .stat-banner {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}

        .stat-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            padding: 24px;
            border-radius: 16px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        }}

        .stat-card .val {{
            font-size: 28px;
            font-weight: 800;
            color: var(--primary);
        }}

        .stat-card .lbl {{
            font-size: 13px;
            color: #64748b;
            font-weight: 500;
        }}

        @media (max-width: 768px) {{
            body {{
                padding: 24px 16px;
            }}
            
            header {{
                padding: 32px 24px;
            }}

            header h1 {{
                font-size: 28px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Banner Header -->
        <header>
            <h1>雅思阅读高亮真题语料库</h1>
            <p>基于《剑桥雅思 4–19》全部官方文章构建，针对大纲核心词汇进行完美高亮与对齐，支持英文、中文与左右对照阅读模式。</p>
        </header>

        <!-- Stats Banner -->
        <div class="stat-banner">
            <div class="stat-card">
                <span class="val">{total_books} 本</span>
                <span class="lbl">剑雅书籍覆盖</span>
            </div>
            <div class="stat-card">
                <span class="val">{total_articles} 篇</span>
                <span class="lbl">经典学术阅读文章</span>
            </div>
            <div class="stat-card">
                <span class="val">{total_vocab} 词</span>
                <span class="lbl">高亮大纲词汇量</span>
            </div>
        </div>

        <!-- Word search box -->
        <div class="search-section">
            <div class="search-header">
                <span class="search-title">🔍 全文词汇检索</span>
                <span id="search-info" style="font-size: 13px; color: #64748b;">输入任意大纲单词，快速查找包含该词的真题文章</span>
            </div>
            <div class="search-bar">
                <input type="text" id="search-input" placeholder="输入大纲单词进行搜索 (例如: federal, evidence, logic)..." oninput="searchVocab()">
            </div>
            <div class="search-results" id="search-results-drawer">
                <!-- Search results will show here -->
            </div>
        </div>

        <!-- Main Corpus Grid -->
        <div class="corpus-grid">
            {grid_cards}
        </div>
    </div>

    <script>
        // Load the compiled search index
        let searchIndex = null;
        
        async function loadSearchIndex() {{
            try {{
                const res = await fetch('search_index.json');
                searchIndex = await res.json();
                console.log("搜索索引加载成功", Object.keys(searchIndex).length, "个单词");
            }} catch(e) {{
                console.error("加载搜索索引失败", e);
            }}
        }}

        // Trigger loading
        loadSearchIndex();

        function searchVocab() {{
            const query = document.getElementById('search-input').value.trim().toLowerCase();
            const drawer = document.getElementById('search-results-drawer');
            const info = document.getElementById('search-info');
            
            if (!query) {{
                drawer.classList.remove('active');
                drawer.innerHTML = '';
                info.textContent = '输入任意大纲单词，快速查找包含该词的真题文章';
                return;
            }}
            
            if (!searchIndex) {{
                info.textContent = '索引正在加载中，请稍后...';
                return;
            }}
            
            // Exact word search and suffix search
            // If the query exists as a key in searchIndex
            let matches = [];
            if (searchIndex[query]) {{
                matches = searchIndex[query];
            }} else {{
                // Fuzzy/prefix match keys
                const matchingKeys = Object.keys(searchIndex).filter(key => key.startsWith(query));
                // Gather articles
                const uniqueArticles = new Set();
                matchingKeys.slice(0, 10).forEach(key => {{
                    searchIndex[key].forEach(art => {{
                        const keyStr = art.path;
                        if (!uniqueArticles.has(keyStr)) {{
                            uniqueArticles.add(keyStr);
                            matches.push(art);
                        }}
                    }});
                }});
            }}
            
            if (matches.length === 0) {{
                drawer.classList.add('active');
                drawer.innerHTML = `<div style="text-align: center; color: #64748b; padding: 20px;">未找到包含单词 "${{query}}" 的文章</div>`;
                info.textContent = `找到 0 篇包含词汇的文章`;
                return;
            }}
            
            drawer.classList.add('active');
            drawer.innerHTML = '';
            
            matches.slice(0, 15).forEach(item => {{
                const a = document.createElement('a');
                a.className = 'result-item';
                a.href = item.path;
                a.innerHTML = `
                    <span class="result-title">${{item.book}} ${{item.test}} ${{item.passage}}</span>
                    <span class="result-meta">${{item.title}}</span>
                `;
                drawer.appendChild(a);
            }});
            
            info.textContent = `为您展示前 ${{Math.min(15, matches.length)}} 篇匹配的文章 (总共 ${{matches.length}} 篇)`;
        }}
    </script>
</body>
</html>
"""

# ----------------- 主程序 -----------------

def main():
    vocab = build_vocab_set()
    
    # Clean up old generated HTML and JSON files to prevent orphans
    if os.path.exists(OUTPUT_DIR):
        print("清理旧的 HTML 与 JSON 文件...")
        for root, dirs, files in os.walk(OUTPUT_DIR):
            for file in files:
                if file.endswith('.html') or file.endswith('.json'):
                    try:
                        os.remove(os.path.join(root, file))
                    except Exception as e:
                        print(f"删除 {file} 失败: {e}")
                        
    # Ensure Output Directories
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    
    total_files = 0
    total_books = 0
    total_highlights_count = 0
    
    # To store grid cards HTML
    books_data = []
    
    # Global search index mapping word -> list of matching passages
    global_search_index = {}
    
    # Loop books sorted numerically
    book_dirs = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))],
                       key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)
                       
    for book_dir in book_dirs:
        book_path = os.path.join(DATA_DIR, book_dir)
        meta_book = parse_filename(book_dir)
        book_name = meta_book['book'] if meta_book else book_dir
        
        # Create output dir for book
        html_book_dir = os.path.join(OUTPUT_DIR, book_dir)
        os.makedirs(html_book_dir, exist_ok=True)
        
        # Loop articles in book
        articles_in_book = []
        
        txt_files = sorted([f for f in os.listdir(book_path) if f.endswith('.txt')])
        if not txt_files:
            continue
            
        total_books += 1
        print(f"开始处理 {book_name} ...")
        
        for fname in txt_files:
            total_files += 1
            txt_path = os.path.join(book_path, fname)
            
            # Extract test/passage info from filename
            meta = parse_filename(fname)
            test = meta['test'] if meta else "Test"
            passage = meta['passage'] if meta else "Passage"
            
            # Parse paragraphs
            res = parse_into_blocks(txt_path)
            if not res:
                print(f"  [失败] 无法解析文章 {fname}")
                continue
                
            content, title, blocks = res
            
            # Word counts for current file
            file_word_counts = {}
            
            # Build sections html
            en_section_html = []
            zh_section_html = []
            both_rows_html = []
            
            for en_paras, zh_paras in blocks:
                # 1. Format EN paragraphs and highlight
                en_paras_html = []
                block_words = set()
                for en_p in en_paras:
                    highlighted_p, p_words = highlight_text(en_p, vocab, file_word_counts)
                    en_paras_html.append(f'<p>{highlighted_p}</p>')
                    block_words.update(p_words)
                    
                # 2. Format ZH paragraphs
                zh_paras_html = []
                for zh_p in zh_paras:
                    zh_paras_html.append(f'<p>{zh_p}</p>')
                    
                en_block_str = ''.join(en_paras_html)
                zh_block_str = ''.join(zh_paras_html)
                
                # Append to individual tab HTML
                en_section_html.append(en_block_str)
                zh_section_html.append(zh_block_str)
                
                # Append to bilingual parallel row
                both_rows_html.append(
                    f'<div class="parallel-row">'
                    f'  <div class="parallel-en">{en_block_str}</div>'
                    f'  <div class="parallel-zh">{zh_block_str}</div>'
                    f'</div>'
                )
                
            # Accumulate highlights for the book
            total_highlights_count += sum(file_word_counts.values())
            
            # Create Global Search Index mappings
            html_name = get_clean_html_name(fname, book_name)
            rel_html_path = f"{book_dir}/{html_name}"
            for word in file_word_counts.keys():
                if word not in global_search_index:
                    global_search_index[word] = []
                global_search_index[word].append({
                    "path": rel_html_path,
                    "title": title,
                    "book": book_name,
                    "test": test,
                    "passage": passage
                })

                
            # Extract source URL if present
            source_match = re.search(r'来源：(https?://[^\s]+)', content)
            source_url = source_match.group(1) if source_match else ''
            source_html = f'来源：<a href="{source_url}" target="_blank">{source_url}</a>' if source_url else '官方真题语料'
            
            # Format single article HTML
            article_html = ARTICLE_TEMPLATE.format(
                title=title,
                book=book_name,
                test=test,
                passage=passage,
                source=source_html,
                en_paragraphs=''.join(en_section_html),
                zh_paragraphs=''.join(zh_section_html),
                both_rows=''.join(both_rows_html),
                word_counts_json=json.dumps(file_word_counts, ensure_ascii=False)
            )
            
            # Write article page
            html_path = os.path.join(html_book_dir, html_name)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(article_html)
                
            # Save for book card info
            articles_in_book.append({
                "name": f"{test} {passage}",
                "title": title,
                "path": f"{book_dir}/{html_name}"
            })
            
        # Create book card HTML block
        li_items = []
        for art in articles_in_book:
            li_items.append(
                f'<li>'
                f'  <a href="{art["path"]}" class="article-link" title="{art["title"]}">'
                f'    <strong>{art["name"]}</strong>'
                f'    <div style="font-size: 11px; opacity: 0.8; margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{art["title"]}</div>'
                f'  </a>'
                f'</li>'
            )
            
        books_data.append(
            f'<div class="book-card">'
            f'  <h3>'
            f'    <span>📘 {book_name}</span>'
            f'    <span class="article-count">{len(articles_in_book)} 篇</span>'
            f'  </h3>'
            f'  <ul class="article-list">'
            f'    {"".join(li_items)}'
            f'  </ul>'
            f'</div>'
        )

    # 1. Write search_index.json
    with open(os.path.join(OUTPUT_DIR, 'search_index.json'), 'w', encoding='utf-8') as f:
        json.dump(global_search_index, f, ensure_ascii=False)
        
    # 2. Write global index.html
    index_html = INDEX_TEMPLATE.format(
        total_books=total_books,
        total_articles=total_files,
        total_vocab=len(global_search_index),
        grid_cards=''.join(books_data)
    )
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)
        
    print(f"\n生成流程圆满结束!")
    print(f"  已生成书籍数: {total_books}")
    print(f"  已生成文章数: {total_files}")
    print(f"  词汇高亮记录: ~{total_highlights_count} 处")
    print(f"  全局检索词汇数: {len(global_search_index)} 个")
    print(f"  成果主页: {OUTPUT_DIR}/index.html")


if __name__ == '__main__':
    main()
