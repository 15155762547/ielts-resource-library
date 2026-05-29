#!/usr/bin/env python3
"""
雅思阅读语料库索引生成脚本
输入: /Volumes/奥睿科1TB/代码程序/剑雅资源库/data/ 下的所有 txt 文章
输出: /Volumes/奥睿科1TB/代码程序/剑雅资源库/vocab_index.csv

格式: 单词,句子原文,书籍,Test,Passage,段落序号
"""

import os
import re
import csv
import sys

DATA_DIR = "/Volumes/奥睿科1TB/代码程序/剑雅资源库/data"
OUTPUT_CSV = "/Volumes/奥睿科1TB/代码程序/剑雅资源库/vocab_index.csv"
VOCAB_FILE = "/Volumes/奥睿科1TB/代码程序/单词表计划/wordlist_only.txt"

# ----------------- 工具函数 -----------------

def split_sentences(paragraph: str) -> list[str]:
    """按 .!? 分割英文句子，过滤空字符串"""
    # 匹配句号/感叹号/问号后跟空格或直接结束
    raw = re.split(r'(?<=[.!?])\s+(?=[A-Z])', paragraph)
    return [s.strip() for s in raw if s.strip() and len(s.strip()) > 3]


def parse_filename(fname: str):
    """
    从文件名提取书籍信息。
    支持两种格式:
    - 剑桥雅思4 剑桥雅思4 Test 1阅读原文翻译 Passage 1 独家.txt
    - 剑桥雅思19 Test1Passage1.txt
    """
    fname_clean = fname.replace('.txt', '')

    # 提取书籍编号
    book_match = re.search(r'剑桥雅思\s*(\d+)', fname_clean)
    if not book_match:
        return None
    book = f"剑桥雅思{book_match.group(1)}"

    # 提取 Test 和 Passage
    test_match = re.search(r'Test\s*(\d+)', fname_clean, re.IGNORECASE)
    passage_match = re.search(r'Passage\s*(\d+)', fname_clean, re.IGNORECASE)
    if not test_match or not passage_match:
        return None

    return {
        'book': book,
        'test': f"Test {test_match.group(1)}",
        'passage': f"Passage {passage_match.group(1)}"
    }


def extract_english_paragraphs(content: str) -> list[tuple[int, str]]:
    """
    提取纯英文段落，返回 [(段落序号, 段落文本), ...]
    只取 --- 分隔符之前的英文部分
    """
    if '---' in content:
        english_part = content.split('---')[0]
    else:
        english_part = content

    lines = english_part.strip().split('\n')
    paragraphs = []
    para_num = 0
    buffer = []

    for line in lines:
        line = line.strip()
        # 跳过文件头（# 开头）和介绍性中文段落
        if line.startswith('#'):
            continue
        # 跳过纯中文介绍段落（不包含英文字母）
        if line and not re.search(r'[A-Za-z]', line):
            # 如果 buffer 有内容，说明是英文段落结束了
            if buffer:
                para_num += 1
                paragraphs.append((para_num, ' '.join(buffer)))
                buffer = []
            continue
        # 跳过太短的行（可能是标题碎片）
        if line and len(line) < 20:
            continue
        # 包含英文的行，加入段落
        if re.search(r'[A-Za-z]', line):
            # 如果是纯中文行跳过
            chinese_ratio = len(re.findall(r'[\u4e00-\u9fff]', line)) / max(len(line), 1)
            if chinese_ratio > 0.3:
                if buffer:
                    para_num += 1
                    paragraphs.append((para_num, ' '.join(buffer)))
                    buffer = []
                continue
            buffer.append(line)

    if buffer:
        para_num += 1
        paragraphs.append((para_num, ' '.join(buffer)))

    return paragraphs


# ----------------- 主程序 -----------------

def build_vocab_set():
    """加载词汇表"""
    vocab = set()
    with open(VOCAB_FILE, 'r', encoding='utf-8') as f:
        for word in f:
            word = word.strip().lower()
            if word:
                vocab.add(word)
    print(f"词汇表加载: {len(vocab)} 个词")
    return vocab


def main():
    vocab = build_vocab_set()
    total_files = 0
    total_sentences = 0
    matched_sentences = 0

    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['单词', '句子原文', '书籍', 'Test', 'Passage', '段落序号'])

        for book_dir in sorted(os.listdir(DATA_DIR)):
            book_path = os.path.join(DATA_DIR, book_dir)
            if not os.path.isdir(book_path):
                continue

            for fname in sorted(os.listdir(book_path)):
                if not fname.endswith('.txt'):
                    continue
                total_files += 1
                fpath = os.path.join(book_path, fname)

                meta = parse_filename(fname)
                if not meta:
                    print(f"  [跳过] 无法解析文件名: {fname}")
                    continue

                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()

                paragraphs = extract_english_paragraphs(content)

                for para_num, para_text in paragraphs:
                    sentences = split_sentences(para_text)
                    for sent in sentences:
                        total_sentences += 1
                        sent_lower = sent.lower()
                        # 检查句子里包含哪些词汇表里的词
                        found_words = []
                        for w in vocab:
                            # 单词边界匹配，防止 match 匹配到单词内部
                            pattern = r'\b' + re.escape(w) + r'\b'
                            if re.search(pattern, sent_lower):
                                found_words.append(w)

                        for word in found_words:
                            matched_sentences += 1
                            writer.writerow([
                                word,
                                sent,
                                meta['book'],
                                meta['test'],
                                meta['passage'],
                                para_num
                            ])

        print(f"\n处理完成:")
        print(f"  文章总数: {total_files}")
        print(f"  句子总数: {total_sentences}")
        print(f"  匹配记录数: {matched_sentences}")
        print(f"  输出文件: {OUTPUT_CSV}")


if __name__ == '__main__':
    main()