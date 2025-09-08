import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from core.model_api.llm_api import ApiKeys, ApiConfig, ClientBase, KeyView



# 您的API密钥和URL
API_KEY = "sk-gmzrrhtzsjnerwygsmhvmfiqjyblktokxwndnmuxmlpzmuii"
BASE_URL = "https://api.siliconflow.cn/v1"

# 创建ApiConfig实例
api_config = ApiConfig(api_key=API_KEY, base_url=BASE_URL)

# 创建ClientBase实例
client = ClientBase(api_config)

# 调用classify_models方法并打印结果
classified_models = client.list_models_detailed().keys()
print("分类后的模型信息:")
print(classified_models)