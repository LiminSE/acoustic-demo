import asyncio
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import time  # 用来增加等待时间

# 存储所有规范的列表
standards_data = []

# 定义将数据实时保存到 CSV 的函数
def save_data_to_csv():
    if standards_data:
        df = pd.DataFrame(standards_data, columns=["标准编号", "标准名称"])
        df.to_csv("iso_acoustics_standards.csv", index=False, encoding='utf-8-sig')
        print("数据已保存到 'iso_acoustics_standards.csv'")

# 定义抓取函数
def run_playwright():
    # 启动 Playwright
    with sync_playwright() as p:
        # 启动 Chromium 浏览器
        browser = p.chromium.launch(headless=True)  # 无头模式
        page = browser.new_page()

        # 基本网址
        base_url = "https://www.iso.org/search.html?PROD_isoorg_en%5Bquery%5D=Acoustics&PROD_isoorg_en%5Bmenu%5D%5Bfacet%5D=standard"
        
        # 访问搜索页面
        page.goto(base_url)  # 访问不带分页参数的第一页
        print("搜索页已加载，开始输入关键词...")

        # 等待页面加载并增加等待超时（最多等60秒）
        page.wait_for_selector('input#autocomplete-1-input', timeout=60000)  # 等待搜索框出现
        print("搜索框已找到，开始输入关键词...")

        # 在搜索框中输入“Acoustics”
        page.fill('input#autocomplete-1-input', 'Acoustics')
        print("输入关键词 'Acoustics'...")

        # 等待页面实时更新，确保搜索结果已经加载完毕
        time.sleep(5)  # 等待 5 秒，以确保页面更新完毕

        # 获取页面源代码
        page_source = page.content()

        # 解析HTML
        soup = BeautifulSoup(page_source, 'html.parser')

        # 处理第一页数据
        print("开始处理第一页数据...")

        # 找到所有标准卡片
        standards_cards = soup.find_all('div', class_='card shadow hover-zoom')
        print(f"找到 {len(standards_cards)} 个标准卡片")

        # 如果没有找到标准卡片，跳过当前页面
        if not standards_cards:
            print(f"第一页没有找到标准卡片，可能是页面结构改变。")
        
        # 遍历每个标准卡片，提取信息
        for card in standards_cards:
            title_tag = card.find('a')
            if title_tag:
                # 提取标准编号和标准名称
                standard_number = title_tag.text.strip()  # 获取标准编号
                standard_name = title_tag['title'].strip()  # 获取完整标准名称（a 标签的 title 属性）
                
                # 添加完整标准信息
                standards_data.append([standard_number, standard_name])

        # 实时保存第一页数据
        save_data_to_csv()

        # 处理后续页面（从第二页开始）
        for page_num in range(2, 19):  # 第二页到第18页
            print(f"点击页面 {page_num} 获取数据...")

            # 关闭可能的 Cookie 同意框（通过点击同意按钮或关闭按钮）
            try:
                cookie_close_button = page.locator('button#onetrust-accept-btn-handler')
                if cookie_close_button.is_visible():
                    cookie_close_button.click()  # 点击同意按钮
                    print("关闭 Cookie 同意框...")
                    time.sleep(2)  # 等待几秒钟，确保同意框关闭
            except:
                print("没有找到 Cookie 同意框，跳过...")

            # 定位“下一页”按钮
            next_page_button = page.locator(f'li.page-item a.page-link[data-page="{page_num}"]:not([aria-label="Last"])')
            
            # 确保该链接可见且可点击
            if next_page_button.is_visible():
                next_page_button.click()  # 点击页面链接
                print(f"点击了第 {page_num} 页链接...")
                time.sleep(15)  # 等待 15 秒，确保下一页加载完成

                # 获取页面源代码
                page_source = page.content()

                # 解析HTML
                soup = BeautifulSoup(page_source, 'html.parser')

                # 找到所有标准卡片
                standards_cards = soup.find_all('div', class_='card shadow hover-zoom')
                print(f"找到 {len(standards_cards)} 个标准卡片")

                # 如果没有找到标准卡片，跳过当前页面
                if not standards_cards:
                    print(f"第 {page_num} 页没有找到标准卡片，可能是页面结构改变。")
                    # 即使没有数据，也实时保存当前已抓取的数据
                    save_data_to_csv()
                    continue

                # 遍历每个标准卡片，提取信息
                for card in standards_cards:
                    title_tag = card.find('a')
                    if title_tag:
                        # 提取标准编号和标准名称
                        standard_number = title_tag.text.strip()  # 获取标准编号
                        standard_name = title_tag['title'].strip()  # 获取完整标准名称（a 标签的 title 属性）
                        
                        standards_data.append([standard_number, standard_name])

                # 实时保存数据
                save_data_to_csv()
            else:
                print(f"第 {page_num} 页链接不可见，终止抓取。")
                break

        # 关闭浏览器
        browser.close()
        print("所有数据已抓取完毕，关闭浏览器...")

# 运行 Playwright
run_playwright()

# 将提取的数据存入 DataFrame（如果程序结束时没有保存最后的数据）
save_data_to_csv()
