// 事件总线
class EventBus {
  constructor() {
    this.events = {};
  }
  // 订阅事件
  on(eventName, callback) {
    if (!this.events[eventName]) {
      this.events[eventName] = [];
    }
    this.events[eventName].push(callback);
  }

  // 发布事件
 emit(eventName, ...args) {
  if (this.events[eventName]) {
    this.events[eventName].forEach(callback => {
      callback(...args);
    });
  }
}

  // 取消订阅
  off(eventName, callback) {
    if (this.events[eventName]) {
      this.events[eventName] = this.events[eventName].filter(cb => cb !== callback);
    }
  }
}

class SemaphoreManager {
  constructor() {
    this.resources = {};
  }

  initSemaphore(resourceKey, initialValue = 1) {
    if (!this.resources[resourceKey]) {
      this.resources[resourceKey] = {
        value: initialValue,
        waitQueue: [],
        isProcessing: false,
      };
      console.log('[SemaphoreManager] Semaphore initialized:', resourceKey, initialValue);
    }
  }

  async acquire(resourceKey) {
    if (!this.resources[resourceKey]) {
      this.initSemaphore(resourceKey);
    }
    const resource = this.resources[resourceKey];
    return new Promise((resolve) => {
      if (resource.value > 0) {
        resource.value--;
        console.log(`[SemaphoreManager] Get semaphore: ${resourceKey}, Remaining: ${resource.value}`);
        resolve();
      } else {
        resource.waitQueue.push(resolve);
        console.log(`[SemaphoreManager] Not available, added to queue: ${resourceKey}, Queue length: ${resource.waitQueue.length}`);
      }
    });
  }

  release(resourceKey) {
    const resource = this.resources[resourceKey];
    if (!resource) {
      console.log(`[SemaphoreManager] Release semaphore: ${resourceKey}, Not found`);
      return;
    }

    resource.value++;
    console.log(`[SemaphoreManager] Release semaphore: ${resourceKey}, Remaining: ${resource.value}`);

    if (resource.waitQueue.length > 0) {
      const next = resource.waitQueue.shift();
      resource.value--;
      console.log(`[SemaphoreManager] Resolve semaphore: ${resourceKey}, Remaining: ${resource.value}`);
      next();
    }

  }

  async executeSemaphore(resourceKey, operationFn, ...args) {
    try {
      await this.acquire(resourceKey);
      return await operationFn(...args);
    } finally {
      this.release(resourceKey);
    }
  }

  getSemaphoreStatus(resourceKey) {
    const resource = this.resources[resourceKey];
    if (!resource) {
      return null;
    }
    return {
      value: resource.value,
      waitQueueLength: resource.waitQueue.length
    };
  }

}

export default new EventBus();

export const semaphoreManager = new SemaphoreManager();




