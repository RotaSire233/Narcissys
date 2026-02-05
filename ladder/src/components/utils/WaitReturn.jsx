import React from 'react';


const useAsyncStateUpdate = () => {
  const resolveRefs = React.useRef(new Map());
  
  React.useEffect(() => {
    const keysToRemove = [];
    
    resolveRefs.current.forEach((resolve, key) => {
      if (resolve) {
        resolve({ success: true, key });
        keysToRemove.push(key);
      }
    });
    
    keysToRemove.forEach(key => resolveRefs.current.delete(key));
  });
  
  const wrapWithPromise = (setter, value, key) => {
    return new Promise(resolve => {
      resolveRefs.current.set(key || Date.now(), resolve);
      setter(value);
    });
  };
  
  return { wrapWithPromise };
};

export default useAsyncStateUpdate;