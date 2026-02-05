export const getFileNameWithExt = (filePath) => {
  if (!filePath) return '';
  
  const separator = filePath.includes('\\') ? '\\' : '/';
  const parts = filePath.split(separator);
  return parts[parts.length - 1];
};

export const getFileNameWithoutExt = (filePath) => {
  if (!filePath) return '';
  
  const fileNameWithExt = getFileNameWithExt(filePath);
  const dotIndex = fileNameWithExt.lastIndexOf('.');
  
  if (dotIndex === -1) return fileNameWithExt;
  
  return fileNameWithExt.substring(0, dotIndex);
};

export const getFileExtension = (filePath) => {
  if (!filePath) return '';
  
  const fileNameWithExt = getFileNameWithExt(filePath);
  const dotIndex = fileNameWithExt.lastIndexOf('.');
  
  if (dotIndex === -1) return '';
  
  return fileNameWithExt.substring(dotIndex);
};

export const joinPath = (...parts) => {
  if (!parts || parts.length === 0) return '';
  
  const validParts = parts.filter(part => part && part.trim() !== '');
  if (validParts.length === 0) return '';
  
  let separator = '/';
  if (validParts[0].includes('\\')) {
    separator = '\\';
  }
  
  return validParts.reduce((result, part, index) => {
    if (index === 0) return part;
    
    const trimmedPart = part.startsWith(separator) ? part.substring(1) : part;
    const trimmedResult = result.endsWith(separator) ? result.substring(0, result.length - 1) : result;
    
    return `${trimmedResult}${separator}${trimmedPart}`;
  });
};

export const getDirectoryPath = (filePath) => {
  if (!filePath) return '';
  
  const separator = filePath.includes('\\') ? '\\' : '/';
  const parts = filePath.split(separator);
  if (parts.length <= 1) return '';
  
  parts.pop();
  return parts.join(separator);
};


export const normalizePath = (filePath, separator = 'auto') => {
  if (!filePath) return '';
  
  if (separator === 'auto') {
    separator = filePath.includes('\\') ? '\\' : '/';
  }

  return filePath.replace(/[\\/]/g, separator);
};

export default {
  getFileNameWithExt,
  getFileNameWithoutExt,
  getFileExtension,
  joinPath,
  getDirectoryPath,
  normalizePath
};
