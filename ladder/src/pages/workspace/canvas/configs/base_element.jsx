export const ELEMENT_TYPES = {
  NORMAL_OPEN: { 
    id: 'normal_open', 
    icon: '| |', 
    name: '常开触点',
    tooltip: '',
    canConnectLeft: true,
    canConnectRight: true
  },
  NORMAL_CLOSED: { 
    id: 'normal_closed', 
    icon: '|/|', 
    name: '常闭触点',
    tooltip: '',
    canConnectLeft: true,
    canConnectRight: true
  },
  COIL: { 
    id: 'coil', 
    icon: '( )', 
    name: '输出线圈',
    tooltip: '',
    canConnectLeft: true,
    canConnectRight: false
  },
  MODEL: {
    id: 'model',
    icon: '-□-',
    name: '模型',
    tooltip: '',
    canConnectLeft: true,
    canConnectRight: true
  },
  CONNECT_UP: { 
    id: 'connect_up', 
    icon: '↑', 
    name: '向上连接',
    tooltip: '',
    canConnectLeft: true,
    canConnectRight: false
  },
  CONNECT_DOWN: { 
    id: 'connect_down', 
    icon: '↓', 
    name: '向下连接',
    tooltip: '',
    canConnectLeft: true,
    canConnectRight: true
  },
  CONNECT_RIGHT: {
    id: 'connect_right',
    icon: '→',
    name: '向右连接',
    tooltip: '',
    canConnectLeft: true,
    canConnectRight: true
  },
};