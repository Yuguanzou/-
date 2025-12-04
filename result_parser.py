from bs4 import BeautifulSoup
import urllib.parse
import base64

class ResultParser:
    """搜索结果解析模块，提取标题、部分内容和链接"""
    
    def __init__(self):
        pass
    
    def parse_baidu_results(self, html_content):
        """
        解析百度搜索结果
        :param html_content: 搜索结果页面的HTML内容
        :return: 解析后的结果列表，每个元素包含title、content、url
        """
        if not html_content:
            return []
        
        results = []
        soup = BeautifulSoup(html_content, "html.parser")
        
        # 定位百度搜索结果项
        search_items = soup.find_all("div", class_="result")
        
        for item in search_items:
            try:
                # 提取标题和链接
                title_elem = item.find("h3")
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link_elem = title_elem.find("a")
                    if link_elem:
                        url = link_elem["href"]
                        # 检查是否为必应跳转链接，提取实际URL
                        parsed_url = urllib.parse.urlparse(url)
                        if parsed_url.netloc == "www.bing.com" and parsed_url.path == "/ck/a":
                            query_params = urllib.parse.parse_qs(parsed_url.query)
                            if "u" in query_params:
                                u_param = query_params["u"][0]
                                # 查找base64编码的URL部分（以aHR0cHM6开头表示https）
                                base64_start = u_param.find("aHR0cHM6")
                                if base64_start != -1:
                                    base64_part = u_param[base64_start:]
                                    # 补全base64编码的填充字符
                                    base64_part += "=" * ((4 - len(base64_part) % 4) % 4)
                                    try:
                                        actual_url = base64.b64decode(base64_part).decode('utf-8')
                                        url = actual_url
                                    except Exception as e:
                                        print(f"解码必应跳转链接失败: {str(e)}")
                                        pass
                    else:
                        url = ""
                else:
                    title = ""
                    url = ""
                
                # 提取部分内容
                content_elem = item.find("div", class_="c-abstract")
                content = content_elem.get_text(strip=True) if content_elem else ""
                
                if title and url:
                    results.append({
                        "title": title,
                        "content": content,
                        "url": url
                    })
            
            except Exception as e:
                print(f"解析百度搜索结果时出错: {str(e)}")
                continue
        
        return results
    
    def parse_google_results(self, html_content):
        """
        解析谷歌搜索结果
        :param html_content: 搜索结果页面的HTML内容
        :return: 解析后的结果列表，每个元素包含title、content、url
        """
        if not html_content:
            print("DEBUG: html_content为空")
            return []
        
        results = []
        soup = BeautifulSoup(html_content, "html.parser")
        
        # 调试：查看页面标题
        page_title = soup.title.text if soup.title else "无标题"
        print(f"DEBUG: 页面标题: {page_title}")
        
        # 定位谷歌搜索结果项
        search_items = soup.find_all("div", class_="g")
        print(f"DEBUG: 找到div.g元素数量: {len(search_items)}")
        
        # 如果没找到div.g，尝试查找其他可能的搜索结果容器
        if len(search_items) == 0:
            # 尝试查找新的Google搜索结果结构
            search_items = soup.find_all("div", class_="tF2Cxc")
            print(f"DEBUG: 找到div.tF2Cxc元素数量: {len(search_items)}")
            
            # 查看所有div元素的class
            all_divs = soup.find_all("div")
            print(f"DEBUG: 所有div元素数量: {len(all_divs)}")
            
            # 收集所有div的class
            div_classes = set()
            for div in all_divs:
                classes = div.get("class")
                if classes:
                    div_classes.update(classes)
            
            print("DEBUG: 页面中所有div的class列表:")
            print(sorted(list(div_classes))[:20])  # 只打印前20个
        
        for item in search_items:
            try:
                # 调试：打印当前搜索项的HTML
                print(f"DEBUG: 当前搜索项HTML: {str(item)[:300]}...")
                
                # 提取标题和链接
                title_elem = item.find("h3")
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link_elem = item.find("a")
                    if link_elem:
                        url = link_elem.get("href", "")
                        # 检查是否为Google的重定向链接
                        if url.startswith("/url?q="):
                            # 提取实际URL
                            from urllib.parse import urlparse, parse_qs
                            parsed_url = urlparse(url)
                            if "q" in parse_qs(parsed_url.query):
                                url = parse_qs(parsed_url.query)["q"][0]
                    else:
                        url = ""
                else:
                    # 尝试查找其他标题元素
                    title_elem = item.find("h2")
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link_elem = item.find("a")
                        url = link_elem.get("href", "") if link_elem else ""
                    else:
                        title = ""
                        url = ""
                
                # 提取部分内容
                content_elem = item.find("div", class_="VwiC3b")
                if not content_elem:
                    content_elem = item.find("div", class_="IsZvec")
                    if not content_elem:
                        content_elem = item.find("span", class_="aCOpRe")
                
                content = content_elem.get_text(strip=True) if content_elem else ""
                
                print(f"DEBUG: 提取到 - 标题: {title[:50]}..., URL: {url}, 内容: {content[:50]}...")
                
                if title and url:
                    results.append({
                        "title": title,
                        "content": content,
                        "url": url
                    })
                    print(f"DEBUG: 添加搜索结果成功")
            
            except Exception as e:
                print(f"DEBUG: 解析谷歌搜索结果时出错: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"DEBUG: 解析完成，共获取 {len(results)} 条谷歌搜索结果")
        return results
    
    def parse_bing_results(self, html_content):
        """
        解析必应搜索结果
        :param html_content: 搜索结果页面的HTML内容
        :return: 解析后的结果列表，每个元素包含title、content、url、redirect_url
        """
        if not html_content:
            return []
        results = []
        soup = BeautifulSoup(html_content, "html.parser")
        
        # 定位必应搜索结果项
        search_items = soup.find_all("li", class_="b_algo")
        
        for item in search_items:
            try:
                # 提取标题
                title_elem = item.find("h2")
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                
                # 提取必应跳转链接
                redirect_url = ""
                link_elem = title_elem.find("a")
                if link_elem:
                    redirect_url = link_elem["href"]
                
                # 从<cite>标签提取实际URL
                actual_url = ""
                attribution_div = item.find("div", class_="b_attribution")
                if attribution_div:
                    cite_tag = attribution_div.find("cite")
                    if cite_tag:
                        actual_url = cite_tag.get_text(strip=True)
                
                # 如果<cite>标签没有找到URL，使用跳转链接作为实际URL
                if not actual_url:
                    actual_url = redirect_url
                
                if not actual_url:
                    continue
                
                # 提取部分内容
                content_elem = item.find("div", class_="b_caption")
                content = ""
                if content_elem:
                    # 移除标题部分
                    if content_elem.find("h2"):
                        content_elem.find("h2").extract()
                    content = content_elem.get_text(strip=True)
                
                results.append({
                    "title": title,
                    "content": content,
                    "url": actual_url,
                    "redirect_url": redirect_url
                })
            
            except Exception as e:
                print(f"解析必应搜索结果时出错: {str(e)}")
                continue
        
        return results
    
    def parse(self, html_content, search_engine="bing"):
        """
        根据搜索引擎类型解析结果
        :param html_content: 搜索结果页面的HTML内容或HTML内容列表
        :param search_engine: 搜索引擎类型
        :return: 解析后的结果列表
        """
        all_results = []
        
        # 如果是HTML内容列表，则遍历处理每个页面
        if isinstance(html_content, list):
            for page_html in html_content:
                if search_engine == "baidu":
                    all_results.extend(self.parse_baidu_results(page_html))
                elif search_engine == "google":
                    all_results.extend(self.parse_google_results(page_html))
                elif search_engine == "bing":
                    all_results.extend(self.parse_bing_results(page_html))
                else:
                    raise ValueError("不支持的搜索引擎")
        else:
            # 单页面处理
            if search_engine == "baidu":
                all_results = self.parse_baidu_results(html_content)
            elif search_engine == "google":
                all_results = self.parse_google_results(html_content)
            elif search_engine == "bing":
                all_results = self.parse_bing_results(html_content)
            else:
                raise ValueError("不支持的搜索引擎")
        
        return all_results