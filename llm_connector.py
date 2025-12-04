import json
import logging
import time
import requests
from typing import Dict, List, Optional, Any, Union

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LLMConnector:
    """
    LLM连接器，负责与大语言模型进行交互
    注意：这里实现了一个基础框架，实际使用时需要根据具体的LLM API进行调整
    """
    
    def __init__(self, api_key: str = None, model_name: str = "qwen-long", timeout: int = 60, retry_count: int = 3, retry_delay: int = 5):
        """
        初始化LLM连接器
        
        Args:
            api_key: Qwen API密钥
            model_name: 使用的LLM模型名称（默认qwen-long）
            timeout: 请求超时时间（秒）
            retry_count: 请求失败重试次数
            retry_delay: 重试间隔时间（秒）
        """
        self.api_key = api_key or "sk-eb5fa97b35874410a8887818ef0cfc2c"
        self.model_name = model_name
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    
    def prepare_prompt(self, page_content: str, task: str = "储能领域分类") -> List[Dict[str, str]]:
        """
        准备发送给LLM的提示
        
        Args:
            page_content: 页面内容
            task: 任务描述
            
        Returns:
            格式化的提示列表
        """
        # 根据页面内容长度截取，避免超出API限制
        max_content_length = 4000  # 可以根据实际API限制调整
        if len(page_content) > max_content_length:
            page_content = page_content[:max_content_length] + "\n[内容过长，已截断]"
        
        system_prompt = f"""
        你是一个专业的储能领域信息分析专家。请严格按照以下标准和步骤分析提供的网页内容：
        
        步骤1：判断内容相关性
        - 检查是否包含储能相关关键词：如电池储能、抽水蓄能、压缩空气储能、飞轮储能、氢储能、电化学储能、储能系统、热能储存、Solar-plus-Storage、BESS、ESS、energy storage、PV ESS、Hybrid System、Integrated Renewable System、Microgrid等
        - 判断内容是否主要围绕储能技术、产品、服务、市场、政策或企业展开
        
        步骤2：类别精确定义与分类
        若属于储能领域，请分类为以下类别之一：
        - 储能技术：关于储能材料、设备、系统设计、工作原理、技术创新、性能指标等技术层面的内容
        - 储能项目：具体的储能项目信息，包括项目规划、建设、运营、案例分析、项目参数等
        - 储能公司-设备制造商：专门生产储能设备（如电池、PCS、BMS、EMS等）的制造企业
        - 储能公司-系统集成商：提供储能系统整体解决方案，集成各种设备和技术的服务商
        - 储能公司-项目开发商：负责储能电站项目的规划、开发、建设和运营的公司
        - 储能公司-技术提供商：提供储能相关技术、软件、算法或专利技术的公司
        - 储能公司-项目投资商：投资储能项目或储能公司的投资机构或企业
        - 储能公司-EPC：提供储能项目设计、采购、施工一体化服务的工程总承包商
        - 储能政策：政府出台的储能相关法规、补贴政策、规划目标、行业标准等政策文件
        - 储能市场分析：市场规模、增长预测、竞争格局、价格趋势、投资机会等市场研究内容
        - 其他储能相关：无法归类到上述类别的其他储能相关内容
        
        注意：一个公司可能同时具有多个身份，例如既是系统集成商又是EPC。在这种情况下，请在company_type字段中使用逗号分隔多个类型。
        
        步骤3：置信度评分标准
        根据内容匹配度给出0-1之间的置信度评分：
        - 0.9-1.0：内容明确且高度聚焦于储能主题，有大量专业术语和具体数据
        - 0.7-0.89：内容主要涉及储能主题，但有部分非储能相关信息
        - 0.5-0.69：内容部分涉及储能，但主题不明确或储能内容占比较小
        - 0.3-0.49：内容仅有少量储能相关词汇，难以确定是否为储能主题
        - 0-0.29：内容几乎不涉及储能主题
        
        步骤4：提供判断理由
        简明扼要说明判断依据（100字以内），重点提及：
        - 关键储能相关关键词或概念
        - 判断类别的主要依据
        - 排除其他类别的简要理由
        
        注意事项：
        - 严格按照JSON格式输出，不要包含任何额外文本
        - 类别必须从指定选项中选择，不要自创类别
        - 对于边缘或混合内容，优先根据主要内容方向和核心主题进行分类
        - 若内容明显不属于储能领域，category字段可设置为空字符串
        
        请以JSON格式输出结果，包含以下字段：
        - is_energy_storage: 布尔值，表示是否属于储能领域
        - category: 字符串，表示具体类别
        - company_type: 字符串，公司具体类型1,公司具体类型2（多个类型时用逗号分隔）
        - confidence: 0-1之间的浮点数，表示判断的置信度
        - reason: 字符串，说明判断理由
        
        注意：当一个公司具有多个身份时，请在company_type字段中使用逗号分隔多个类型。例如："储能公司-系统集成商,储能公司-EPC"
        """
        
        user_prompt = f"""
        请分析以下网页内容：
        
        {page_content}
        """
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def call_llm(self, messages: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """
        调用Qwen LLM API
        
        Args:
            messages: 提示消息列表
            
        Returns:
            LLM返回的响应，如果调用失败则返回None
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 转换消息格式为Qwen API格式
        prompt = ""
        system_content = ""
        for message in messages:
            if message["role"] == "system":
                system_content = message["content"]
            elif message["role"] == "user":
                prompt = message["content"]
        
        data = {
            "model": self.model_name,
            "input": {
                "messages": [
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": prompt}
                ]
            },
            "parameters": {
                "result_format": "message"
            }
        }
        
        logger.info(f"调用Qwen LLM API: {self.model_name}")
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            # 解析Qwen API响应
            if "output" in result and "choices" in result["output"] and len(result["output"]["choices"]) > 0:
                content = result["output"]["choices"][0]["message"]["content"]
                
                # 尝试解析返回的JSON内容
                try:
                    parsed_content = json.loads(content)
                    return parsed_content
                except json.JSONDecodeError:
                    # 如果返回的不是JSON格式，创建一个默认响应
                    logger.warning("API返回内容不是有效的JSON格式，使用默认解析")
                    return {
                        "is_energy_storage": True,
                        "category": "其他储能相关",
                        "confidence": 0.7,
                        "reason": content
                    }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Qwen API调用失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"解析API响应时发生错误: {str(e)}")
            return None
        
        return None
    
    def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析LLM响应
        
        Args:
            response: LLM返回的原始响应
            
        Returns:
            解析后的结构化数据
        """
        # 这里可以根据实际API返回的格式进行解析
        # 当前已经是结构化数据，直接返回
        return response
    
    def analyze_content(self, page_content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        分析页面内容并返回LLM的分析结果
        
        Args:
            page_content: 页面内容
            metadata: 页面元数据（可选）
            
        Returns:
            分析结果
        """
        result = {
            'success': False,
            'is_energy_storage': False,
            'category': 'unknown',
            'company_type': '',
            'confidence': 0.0,
            'reason': '',
            'error': None
        }
        
        try:
            # 准备提示
            messages = self.prepare_prompt(page_content)
            
            # 调用LLM并处理重试
            for attempt in range(self.retry_count):
                try:
                    logger.info(f"分析内容，第{attempt + 1}次尝试")
                    response = self.call_llm(messages)
                    if response:
                        # 解析响应
                        parsed_result = self.parse_response(response)
                        
                        # 更新结果
                        result['success'] = True
                        result.update(parsed_result)
                        
                        logger.info(f"内容分析成功，类别: {result['category']}, 置信度: {result['confidence']}")
                        return result
                except Exception as e:
                    logger.warning(f"LLM调用失败: {str(e)}")
                    if attempt < self.retry_count - 1:
                        logger.info(f"{self.retry_delay}秒后重试...")
                        time.sleep(self.retry_delay)
            
            # 多次尝试后仍然失败
            result['error'] = 'Failed to get response from LLM after multiple attempts'
            logger.error(result['error'])
            
        except Exception as e:
            logger.error(f"分析内容时发生错误: {str(e)}")
            result['error'] = str(e)
        
        return result
    
    def batch_analyze(self, contents: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        批量分析多个内容
        
        Args:
            contents: 内容列表
            metadatas: 元数据列表（可选）
            
        Returns:
            分析结果列表
        """
        results = []
        
        # 如果没有提供元数据，则创建空列表
        if metadatas is None:
            metadatas = [None] * len(contents)
        
        # 注意：这里可以根据需要实现并发处理，当前为串行处理
        for i, content in enumerate(contents):
            metadata = metadatas[i] if i < len(metadatas) else None
            result = self.analyze_content(content, metadata)
            results.append(result)
        
        return results


# 示例用法
if __name__ == "__main__":
    # 创建LLM连接器
    connector = LLMConnector()
    
    # 模拟页面内容
    sample_content = """
    某大型储能项目成功并网运行
    
    近日，由ABC公司投资建设的100MW/200MWh锂电池储能项目成功并网运行。该项目采用了最新的磷酸铁锂电池技术，
    配备了先进的BMS系统，可实现快速充放电，为当地电网提供调峰调频服务。项目总投资约5亿元，预计年收益可达8000万元。
    该项目的投运将有效提高当地电网的稳定性和可靠性，促进可再生能源的消纳。
    """
    
    # 分析内容
    result = connector.analyze_content(sample_content)
    print("\n分析结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))