# -*- coding: utf-8 -*-
"""
Created on Thu Mar  6 22:36:28 2025

@author: Administrator
"""

import requests
from datetime import datetime
import time
from difflib import SequenceMatcher

# 配置参数
INPUT_FILE = 'ref.txt'
OUTPUT_HTML = 'literature_index.html'
CROSSREF_API = 'https://api.crossref.org/works'
HEADERS = {
    'User-Agent': 'LiteratureIndexBot/1.0 (mailto:your@email.com)'
}

def get_similarity(a, b):
    """计算两个字符串的相似度"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def parse_crossref_date(date_parts):
    """解析Crossref的日期格式"""
    try:
        if not date_parts or not date_parts[0]:
            return None
        parts = date_parts[0]
        year = int(parts[0]) if len(parts) >= 1 else None
        month = int(parts[1]) if len(parts) >= 2 else 1
        day = int(parts[2]) if len(parts) >= 3 else 1
        return datetime(year, month, day) if year else None
    except Exception as e:
        print(f"日期解析错误: {e}")
        return None

def fetch_articles():
    # 读取文献列表
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        titles = [line.strip() for line in f if line.strip()]

    articles = []
    
    for title in titles:
        time.sleep(1)  # 遵守API速率限制
        
        try:
            params = {'query.title': title, 'rows': 5}
            response = requests.get(CROSSREF_API, params=params, headers=HEADERS)
            response.raise_for_status()
            data = response.json()
            items = data.get('message', {}).get('items', [])
            
            if not items:
                print(f"未找到结果：{title}")
                continue

            # 寻找最佳匹配
            best_match = None
            max_sim = 0
            for item in items:
                item_title = ' '.join(item.get('title', ['']))
                sim = get_similarity(title, item_title)
                if sim > max_sim:
                    max_sim = sim
                    best_match = item

            if max_sim < 0.6:  # 相似度阈值
                print(f"低相似度（{max_sim:.2f}）：{title} -> {item_title}")
                continue

            # 提取信息
            doi = best_match.get('DOI')
            url = f"https://doi.org/{doi}" if doi else None
            date_parts = best_match.get('issued', {}).get('date-parts')
            date = parse_crossref_date(date_parts)
            
            articles.append({
                'title': title,
                'url': url,
                'date': date
            })

        except Exception as e:
            print(f"获取文献失败：{title} - {str(e)}")
    
    return articles

def generate_html(articles):
    # 排序：有日期的在前，按日期降序；无日期的在后
    articles_sorted = sorted(articles, 
        key=lambda x: x['date'] or datetime.min, 
        reverse=True
    )

    html = """<!DOCTYPE html>
<html>
<head>
    <title>文献索引</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 20px auto; }
        h1 { color: #2c3e50; }
        ul { list-style-type: none; padding: 0; }
        li { margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 5px; }
        a { text-decoration: none; color: #2980b9; }
        .date { float: right; color: #7f8c8d; }
        .no-date { color: #e74c3c; }
    </style>
</head>
<body>
    <h1>文献索引（按时间排序）</h1>
    <ul>
"""

    for article in articles_sorted:
        date = article['date']
        date_str = date.strftime("%Y-%m-%d") if date else '<span class="no-date">日期未知</span>'
        url = article['url'] or '#'
        
        html += f"""
        <li>
            <a href="{url}" target="_blank">{article['title']}</a>
            <span class="date">{date_str}</span>
        </li>
        """

    html += """
    </ul>
</body>
</html>
"""

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)

if __name__ == '__main__':
    articles = fetch_articles()
    generate_html(articles)
    print(f"生成完成！请查看 {OUTPUT_HTML}")