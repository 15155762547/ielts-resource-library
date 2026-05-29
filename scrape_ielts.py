#!/usr/bin/env python3
"""
剑桥雅思阅读爬虫
从 laokaoya.com 爬取剑桥雅思4-19所有阅读文章
"""

import os
import re
import random
import time
import requests
from bs4 import BeautifulSoup

BASE_DIR = "/Volumes/奥睿科1TB/代码程序/剑雅资源库/data"
ENTRY_URL = "https://www.laokaoya.com/43981.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

TIMEOUT = 30
DELAY_MIN = 2
DELAY_MAX = 3
MAX_RETRIES = 1
RETRY_DELAY = 5


def extract_article_links(html_content):
    """从入口页提取所有子链接"""
    soup = BeautifulSoup(html_content, 'html.parser')
    links = []

    for a in soup.find_all('a', href=True):
        href = a['href']
        if re.match(r'https://www\.laokaoya\.com/\d+\.html', href):
            title = a.get_text(strip=True)
            if '剑桥雅思' in title and '阅读' in title:
                links.append({'url': href, 'title': title})

    return links


def download_page(url):
    """下载单个页面，支持重试"""
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()
            return response.text
        except Exception as e:
            if attempt < MAX_RETRIES:
                print(f"  重试中 ({attempt + 1}/{MAX_RETRIES}): {e}")
                time.sleep(RETRY_DELAY)
            else:
                raise


def parse_article(html_content, source_url):
    """解析文章页面，提取英文和中文内容"""
    soup = BeautifulSoup(html_content, 'html.parser')

    title = None
    for h2 in soup.find_all('h2'):
        text = h2.get_text(strip=True)
        if 'Test' in text and 'Passage' in text:
            title = text
            break

    if not title:
        for h1 in soup.find_all('h1'):
            text = h1.get_text(strip=True)
            if 'Test' in text and 'Passage' in text:
                title = text
                break

    paragraphs = []
    for p in soup.find_all('p'):
        text = p.get_text(strip=True)
        if text and len(text) > 20:
            paragraphs.append(text)

    if len(paragraphs) < 2:
        return None, None, None

    mid = len(paragraphs) // 2
    english_paras = paragraphs[:mid]
    chinese_paras = paragraphs[mid:]

    return title, english_paras, chinese_paras


def extract_book_and_passage(title):
    """从标题提取书籍名和文章名"""
    match = re.search(r'剑桥雅思\d+', title)
    book = match.group(0) if match else "未知书籍"

    match = re.search(r'Test\s*\d+\s*Passage\s*\d+', title)
    passage = match.group(0) if match else title

    return book, passage


def save_article(book, passage, english_paras, chinese_paras, source_url):
    """保存文章到文件"""
    book_dir = os.path.join(BASE_DIR, book)
    os.makedirs(book_dir, exist_ok=True)

    filename = f"{book} {passage}.txt"
    filepath = os.path.join(book_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# {book} {passage}\n")
        f.write(f"# 来源：{source_url}\n")
        f.write("\n")

        for para in english_paras:
            f.write(f"{para}\n")

        f.write("\n---\n\n")

        for para in chinese_paras:
            f.write(f"{para}\n")

    return filepath


def run():
    """主流程"""
    print("=" * 50)
    print("  剑桥雅思阅读爬虫")
    print("=" * 50)

    print(f"\n[1/4] 获取入口页: {ENTRY_URL}")
    try:
        entry_html = download_page(ENTRY_URL)
    except Exception as e:
        print(f"获取入口页失败: {e}")
        return

    print("[2/4] 提取子链接...")
    links = extract_article_links(entry_html)
    print(f"找到 {len(links)} 篇文章")

    print("[3/4] 开始爬取...")
    success_count = 0
    fail_count = 0
    failed_list = []
    consecutive_failures = 0

    for i, link in enumerate(links, 1):
        print(f"\n[{i}/{len(links)}] {link['title']}")
        print(f"  URL: {link['url']}")

        try:
            html = download_page(link['url'])
            title, english_paras, chinese_paras = parse_article(html, link['url'])

            if not title or not english_paras:
                raise ValueError("内容解析失败")

            book, passage = extract_book_and_passage(title)
            filepath = save_article(book, passage, english_paras, chinese_paras, link['url'])

            print(f"  保存成功: {filepath}")
            success_count += 1
            consecutive_failures = 0

        except Exception as e:
            print(f"  失败: {e}")
            fail_count += 1
            failed_list.append((link['url'], str(e)))
            consecutive_failures += 1

            if consecutive_failures >= 3:
                print("\n警告：连续3次失败，暂停爬虫")
                break

        delay = random.uniform(DELAY_MIN, DELAY_MAX)
        time.sleep(delay)

    print("\n" + "=" * 50)
    print("  爬虫完成")
    print("=" * 50)
    print(f"\n成功: {success_count} 篇 / 总数 {len(links)} 篇")
    print(f"失败: {fail_count} 篇")

    if failed_list:
        print("\n失败列表:")
        for i, (url, reason) in enumerate(failed_list, 1):
            print(f"  {i}. {url} - {reason}")

    print(f"\n文件保存位置: {BASE_DIR}")
    print("=" * 50)


if __name__ == "__main__":
    run()