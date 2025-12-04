from search_executor import SearchExecutor
from result_parser import ResultParser
from output_formatter import OutputFormatter
from page_analyzer import PageAnalyzer
from llm_connector import LLMConnector
import datetime
import time

def main():
    """主程序入口"""
    print("==============================================")
    print("自动化储能信息源搜索工具")
    print("==============================================")
    

    # 示例储能关键词数组
    default_keywords = [
"에너지 저장 EPC",
"배터리 저장 EPC",
"BESS EPC 업체",
"마이크로그리드 EPC",
"태양광+저장 EPC",
"에너지 저장 소유자"
]
    
    # 用户输入配置
    print(f"\n默认搜索关键词: {default_keywords}")
    use_default = input("是否使用默认关键词？(y/n): ").lower()
    
    if use_default == "n":
        keywords_input = input("请输入搜索关键词，用逗号分隔: ")
        keywords = [kw.strip() for kw in keywords_input.split(",")]
    else:
        keywords = default_keywords
    
    interval_input = input("请输入关键词搜索时间间隔(秒，默认3秒): ")
    try:
        interval = int(interval_input) if interval_input else 3
    except ValueError:
        print("输入无效，使用默认时间间隔2秒")
        interval = 2
    
    search_engine_input = input("请选择搜索引擎(bing/baidu/google，默认bing): ").lower()
    search_engine = search_engine_input if search_engine_input in ["bing", "baidu", "google"] else "bing"
    
    pages_input = input("请输入搜索页数(默认1页): ")
    try:
        pages = int(pages_input) if pages_input else 1
        # 限制最大页数为10页
        pages = max(1, min(pages, 100))

    except ValueError:
        print("输入无效，使用默认页数1页")
        pages = 1
    
    # 添加起始页面配置项
    start_page_input = input("请输入起始页面(默认1页): ")
    try:
        start_page = int(start_page_input) if start_page_input else 1
        # 限制起始页面最小值为1
        start_page = max(1, start_page)
    except ValueError:
        print("输入无效，使用默认起始页面1页")
        start_page = 1
    
    # 设置URL过滤词
    default_filter_words = ["zhihu","news","PV magazine","PV new", "finance","law","worldbank","research","footanstey","noyapro","mckinsey","pcbaaa","enverus","exportsemi","PV Tech","digital","storm4","mtu solutions","modoenergy","amazon","renewablemirror","linkedin","eia","Wood Mackenzie","woodmac","report","search","growthmarketreports","energy-box","woodmac","storageawards","sciencedirect","orbit.dtu","arxiv","bclplaw","windfarmbop","strath.ac","saudigulfprojects","eqmagpro","aesindiana","adb","constructionreviewonline","carilec","windpowerengineering","ieeexplore","nature","ndxy","link springer","microgridknowledge","pmc ncbi nlm nih","canusaepc","runoob","developer baidu","c biancheng","w3school","cppreference","c-cpp","c-language","cainiaoplus","dotcpp","baike baidu","learn microsoft","blog csdn","cainiaoya","cainiaojc","imooc","bilibili","ruanyifeng","icourse163","nowcoder","visualstudio microsoft","bcg","gii","the innovation","ldescouncil","energypartnership","zenodo","lazard","sites ucmerced","power eng","sciencedirect","sandia","lexology","nidec conversion","nortonrosefulbright","fbm","energyindustryreview","bessfinder","batteriesinternational","energystorages tech","enfsolar","solarpro","pv magazine usa","cjoglobal","crugroup","PV tech","mordorintelligence"]
    filter_choice = input(f"是否使用默认URL过滤词({', '.join(default_filter_words)})？(y/n，默认y): ").lower()
    filter_words = default_filter_words.copy()  # 避免修改原列表
    if filter_choice not in ["y", ""]:
        filter_input = input("请输入过滤词，用逗号分隔: ")
        filter_words = [fw.strip().lower() for fw in filter_input.split(",")]
        # 移除空字符串
        filter_words = [fw for fw in filter_words if fw]
    
    # 初始化模块
    print("\n正在初始化搜索工具...")
    search_executor = SearchExecutor(interval=interval)
    result_parser = ResultParser()
    output_formatter = OutputFormatter()
    
    # 初始化页面分析器和LLM连接器
    page_analyzer = PageAnalyzer()
    llm_connector = LLMConnector()
    
    try:
        # 执行批量搜索
        print(f"\n开始搜索...从第{start_page}页开始，共搜索{pages}页")
        raw_results = search_executor.batch_search(keywords, search_engine, pages, start_page)
        
        # 解析搜索结果
        print("\n正在解析搜索结果...")
        parsed_results = {}
        for keyword, html_content in raw_results.items():
            if html_content:
                parsed_results[keyword] = result_parser.parse(html_content, search_engine)
            else:
                parsed_results[keyword] = []
    
        # 应用URL过滤词
        if filter_words:
            print(f"\n正在应用URL过滤词: {filter_words}")
            filtered_results = {}
            for keyword, results in parsed_results.items():
                filtered_results[keyword] = []
                for result in results:
                    url = result.get("url", "").lower()
                    # 检查URL是否包含任何过滤词
                    contains_filter = any(filter_word in url for filter_word in filter_words)
                    if not contains_filter:
                        filtered_results[keyword].append(result)
                    else:
                        print(f"已过滤URL: {result.get('url', '')}")
            parsed_results = filtered_results
        
        # 添加网站字段去重功能
        print("\n正在执行网站字段去重...")
        import urllib.parse
        unique_domain_results = {}
        processed_domains = set()
        
        for keyword, results in parsed_results.items():
            unique_domain_results[keyword] = []
            for result in results:
                url = result.get("url", "")
                try:
                    # 从URL中提取完整域名（保留www前缀）
                    parsed_url = urllib.parse.urlparse(url)
                    domain = parsed_url.netloc
                    
                    # 只保留每个域名的第一个结果
                    if domain not in processed_domains:
                        processed_domains.add(domain)
                        unique_domain_results[keyword].append(result)
                    else:
                        print(f"已去重URL (同域名): {url}")
                except Exception as e:
                    print(f"处理URL时出错 {url}: {str(e)}")
                    # 出错时保留该结果
                    unique_domain_results[keyword].append(result)
        
        # 统计去重效果
        original_count = sum(len(results) for results in parsed_results.values())
        unique_count = sum(len(results) for results in unique_domain_results.values())
        deduplicated_count = original_count - unique_count
        print(f"去重完成: 原结果 {original_count} 条，去重后 {unique_count} 条，减少 {deduplicated_count} 条重复结果")
        parsed_results = unique_domain_results
        
        # 整合所有结果到一个列表，便于处理
        all_results = []
        for keyword, results in parsed_results.items():
            for result in results:
                result['keyword'] = keyword  # 添加关键词信息
                all_results.append(result)
        
        # 询问是否进行页面分析和储能领域分类
        analyze_choice = input("\n是否对搜索结果进行页面分析和储能领域分类？(y/n，默认y): ").lower()
        if analyze_choice == "y" or analyze_choice == "":  # 空输入表示使用默认值y
            print("\n开始页面分析和储能领域分类...")
            print(f"共需处理 {len(all_results)} 个URL")
            
            # 分析页面并获取内容
            for i, result in enumerate(all_results):
                url = result.get("url", "")
                print(f"\n[{i+1}/{len(all_results)}] 分析URL: {url}")
                
                # 分析页面
                page_result = page_analyzer.analyze_page(url)
                
                if page_result['success']:
                    # 提取页面内容和元数据
                    result['page_content'] = page_result['content']
                    result['page_metadata'] = page_result['metadata']
                    
                    # 使用LLM进行储能领域分类
                    print(f"使用LLM分析内容...")
                    llm_result = llm_connector.analyze_content(page_result['content'], page_result['metadata'])
                    
                    if llm_result['success']:
                        # 将LLM分析结果添加到结果中
                        result['is_energy_storage'] = llm_result['is_energy_storage']
                        result['storage_category'] = llm_result['category']
                        result['company_type'] = llm_result.get('company_type', '')
                        result['confidence'] = llm_result['confidence']
                        result['analysis_reason'] = llm_result['reason']
                        
                        print(f"分类结果: {'是储能领域' if llm_result['is_energy_storage'] else '非储能领域'}")
                        if llm_result['is_energy_storage']:
                            print(f"具体类别: {llm_result['category']}")
                            if result['company_type']:
                                print(f"公司类型: {result['company_type']}")
                            print(f"置信度: {llm_result['confidence']:.2f}")
                    else:
                        print(f"LLM分析失败: {llm_result.get('error', 'Unknown error')}")
                        result['llm_error'] = llm_result.get('error')
                else:
                    print(f"页面分析失败: {page_result.get('error', 'Unknown error')}")
                    result['page_error'] = page_result.get('error')
                
                # 添加延迟，避免请求过快
                if i < len(all_results) - 1:
                    time.sleep(1)  # 1秒延迟
            
            # 将分析后的结果重新组织回原来的结构
            analyzed_results = {}
            for result in all_results:
                keyword = result.pop('keyword')
                if keyword not in analyzed_results:
                    analyzed_results[keyword] = []
                analyzed_results[keyword].append(result)
            parsed_results = analyzed_results
        
        # 输出搜索结果
        print("\n搜索结果:")
        # 对于已分析的结果，只打印基本信息，避免输出过长的页面内容
        simplified_results = {}
        for keyword, results in parsed_results.items():
            simplified_results[keyword] = []
            for result in results:
                simplified = result.copy()
                # 移除可能过长的字段
                if 'page_content' in simplified:
                    simplified['page_content'] = simplified['page_content'][:200] + "..." if len(simplified['page_content']) > 200 else simplified['page_content']
                if 'page_metadata' in simplified:
                    simplified['page_metadata'] = f"标题: {simplified['page_metadata'].get('title', 'N/A')}, 字数: {simplified['page_metadata'].get('word_count', 0)}"
                simplified_results[keyword].append(simplified)
        output_formatter.print_results(simplified_results)
        
        # 保存结果到文件
        save_option = input("是否将结果保存到文件？(y/n，默认y): ").lower()
        if save_option in ["y", ""]:
            # 直接保存为Excel文件
            current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            excel_filename = f"数据源{current_time}.xlsx"
            output_formatter.save_to_excel(parsed_results, excel_filename)
    
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
    
    finally:
        # 关闭浏览器
        print("\n正在关闭浏览器...")
        search_executor.close()
        print("==============================================")
        print("搜索工具已退出")
        print("==============================================")

if __name__ == "__main__":
    main()