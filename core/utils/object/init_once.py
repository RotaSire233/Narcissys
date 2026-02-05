import threading

class OnceCache:
    _instance_lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        attr_name = f"_{cls.__name__}_instance"
        if not hasattr(cls, attr_name):
            with cls._instance_lock:
                if not hasattr(cls, attr_name):
                    setattr(cls, attr_name, super(OnceCache, cls).__new__(cls))
        return getattr(cls, attr_name)

    def __init__(self):
        if not self._initialized:
            self._init_data()
            self._initialized = True

    def _init_data(self):
        """子类实现自己的初始化逻辑"""
        raise NotImplementedError()

    def reset(self):
        """子类可重写此方法以支持测试重置"""
        self._init_data()