import requests
from bs4 import BeautifulSoup
import csv

# 定义获取Google Scholar页面内容的函数
def fetch_page(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    return response.text

# 提取学者的名称、机构和引用数的函数
def extract_scholar_info(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    scholars = []

    # 查找所有包含学者信息的div
    for div in soup.find_all('div', class_='gs_ai gs_scl gs_ai_chpr'):
        name = div.find('h3', class_='gs_ai_name').get_text(strip=True)
        institution = div.find('div', class_='gs_ai_aff').get_text(strip=True)
        citations = div.find('div', class_='gs_ai_cby').get_text(strip=True)
        citations_count = int(citations.replace('Cited by ', '').replace(',', ''))

        scholars.append({
            'Name': name,
            'Institution': institution,
            'Citations': citations_count
        })
    
    return scholars

# 提取下一页链接（after_author）的函数
def get_next_page_url(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    next_page = soup.find('button', {'aria-label': 'Next page'})
    if next_page:
        # 获取下一页的after_author参数
        after_author = next_page.get('data-astart', None)
        if after_author:
            return f'https://scholar.google.com/citations?hl=en&view_op=search_authors&mauthors=label:{label}&after_author={after_author}&astart={start_index+10}'
    return None

# 保存数据到CSV文件的函数
def save_to_csv(scholars, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Name', 'Institution', 'Citations']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for scholar in scholars:
            writer.writerow(scholar)

# 主爬取函数（递归处理分页）
def scrape_scholar_by_label(label, start_index=0, max_pages=2):
    url = f'https://scholar.google.com/citations?hl=en&view_op=search_authors&mauthors=label:{label}&astart={start_index}'
    page_content = fetch_page(url)
    scholars = extract_scholar_info(page_content)

    # 如果还有下一页，继续抓取
    next_page_url = get_next_page_url(page_content)
    if next_page_url and max_pages > 0:
        scholars += scrape_scholar_by_label(label, start_index + 10, max_pages - 1)
    
    return scholars

# 针对不同领域进行爬取并保存结果
def scrape_and_save_labels(labels):
    for label in labels:
        print(f'Scraping scholars for label: {label}')
        scholars = scrape_scholar_by_label(label)
        save_to_csv(scholars, f'{label}.csv')
        print(f'Finished saving data for {label}.')

# 要爬取的标签
labels = ['architectural_acoustics', 'environmental_acoustics', 'building_acoustics', 'soundscape']

# 执行爬取并保存数据
scrape_and_save_labels(labels)
