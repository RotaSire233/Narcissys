import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

import uvicorn

if __name__ == "__main__":
    # 通过模块字符串方式运行，这样相对导入可以正常工作
    uvicorn.run("core.core:app", host="127.0.0.1", port=5000, reload=True)