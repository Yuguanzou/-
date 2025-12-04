from DrissionPage import ChromiumPage, ChromiumOptions
import time
import random

class SearchExecutor:
    """搜索执行模块，使用drissionpage进行浏览器自动化搜索"""
    
    def __init__(self, interval=2):
        """
        初始化搜索执行器
        :param interval: 搜索关键词之间的时间间隔（秒）
        """
        self.interval = interval
        # 定义User-Agent列表，模拟不同浏览器访问
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Version/17.3 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0"
        ]
        # 初始化浏览器，随机选择User-Agent
        user_agent = random.choice(self.user_agents)
        co = ChromiumOptions()
        co.set_user_agent(user_agent)
        
        # 注意：DrissionPage 4.0.5版本的set_proxy方法不直接支持带账号密码的代理格式
        # 当前注释掉代理配置，如需使用带认证的代理，建议通过浏览器插件实现
        # proxy_url = "http://6OGZKJ5Y:B9FA65E6714E@overseas-us.tunnel.qg.net:17365"
        
        self.page = ChromiumPage(co)
        
    def search(self, keyword, search_engine="bing", pages=1, start_page=1):
        """
        执行单个关键词搜索
        :param keyword: 搜索关键词
        :param search_engine: 搜索引擎，默认必应
        :param pages: 需要获取的页数
        :param start_page: 起始页面，默认第1页
        :return: 搜索结果页面的HTML内容列表
        """
        try:
            html_contents = []
            
            # 从指定的起始页面开始爬取
            # 注意：page索引从0开始（0代表第1页，9代表第10页）
            start_index = start_page - 1
            for page in range(start_index, start_index + pages):
                
                # 构建搜索URL
                if search_engine == "baidu":
                    # 百度分页参数：pn=0(第1页), 10(第2页), 20(第3页)...
                    pn = page * 10
                    search_url = f"https://www.baidu.com/s?wd={keyword}&pn={pn}"
                elif search_engine == "google":
                    # 谷歌分页参数：start=0(第1页), 10(第2页), 20(第3页)...
                    start = page * 10
                    search_url = f"https://www.google.com/search?q={keyword}&start={start}"
                elif search_engine == "bing":
                    # 必应分页参数：first=1(第1页), 11(第2页), 21(第3页)...
                    first = page * 10 + 1
                    search_url = f"https://www.bing.com/search?q={keyword}&first={first}"
                else:
                    raise ValueError("不支持的搜索引擎")
                
                # 访问搜索页面
                self.page.get(search_url)
                
                # 等待搜索结果元素出现
                if search_engine == "bing":
                    self.page.ele("li.b_algo", timeout=10)
                elif search_engine == "baidu":
                    self.page.ele("div.result", timeout=10)
                elif search_engine == "google":
                    self.page.ele("div.g", timeout=10)
                
                # 添加页面HTML内容到列表
                html_contents.append(self.page.html)
                # 调试：打印页面HTML前500字符
                print(f"DEBUG: 第{page+1}页HTML内容前500字符: {self.page.html[:500]}...")
                
                # 如果不是最后一页，等待1-3秒内的随机时间再继续翻页，避免触发反爬
                if page < pages - 1:
                    wait_time = random.uniform(1, 3)
                    
                    # 在等待时间内进行1-2次随机滑动页面
                    scroll_count = random.randint(1, 2)
                    print(f"DEBUG: 开始等待 {wait_time:.2f} 秒，将进行 {scroll_count} 次随机滑动")
                    
                    # 计算总等待时间内的滑动间隔
                    total_scroll_time = wait_time * 0.7  # 滑动操作占用70%的等待时间
                    scroll_interval = total_scroll_time / scroll_count
                    
                    for i in range(scroll_count):
                        # 随机滑动距离（100-500像素）
                        scroll_distance = random.randint(100, 500)
                        # 随机滑动方向向下
                        direction = "down"
                        
                        print(f"DEBUG: 第{i+1}/{scroll_count}次滑动: {direction} {scroll_distance}像素")
                        
                        # 执行滑动
                        if direction == "down":
                            self.page.scroll(scroll_distance)
                        else:
                            self.page.scroll(-scroll_distance)
                        
                        # 滑动后等待一小段随机时间
                        time.sleep(random.uniform(0.3, 0.5))
                    
                    # 剩余时间继续等待
                    remaining_time = wait_time - total_scroll_time
                    if remaining_time > 0:
                        time.sleep(remaining_time)
                    
                    print(f"DEBUG: 翻页等待完成")
            
            return html_contents if len(html_contents) > 0 else None
            
        except Exception as e:
            print(f"搜索关键词 '{keyword}' 时出错: {str(e)}")
            return None
    
    def batch_search(self, keywords, search_engine="bing", pages=1, start_page=1):
        """
        批量执行关键词搜索
        :param keywords: 关键词列表
        :param search_engine: 搜索引擎
        :param pages: 需要获取的页数
        :param start_page: 起始页面，默认第1页
        :return: 搜索结果字典，key为关键词，value为页面HTML内容列表
        """
        results = {}
        
        for i, keyword in enumerate(keywords):
            print(f"正在搜索第 {i+1}/{len(keywords)} 个关键词: {keyword} (从第{start_page}页开始，共{pages}页)")
            html_contents = self.search(keyword, search_engine, pages, start_page)
            results[keyword] = html_contents
            
            # 不是最后一个关键词则等待指定时间间隔
            if i < len(keywords) - 1:
                time.sleep(self.interval)
        
        return results
    
    def close(self):
        """关闭浏览器"""
        self.page.close()