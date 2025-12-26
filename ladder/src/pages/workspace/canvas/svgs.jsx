export const NormalOpenSvg = () => (
  <g>
    <line stroke-width="3" y2="80" x2="25" y1="20" x1="25" stroke="#000000" fill="none"/>
    <line stroke-width="3" y2="80" x2="75" y1="20" x1="75" stroke="#000000" fill="none"/>
    <line y2="49" y1="49" x1="25" stroke-width="3" stroke="#000000" fill="none"/>
    <line y2="48.66387" x2="75" y1="48.66387" x1="100" stroke-width="3" stroke="#000000" fill="none"/>
  </g>
);

export const NormalClosedSvg = () => (
  <g>
    <line stroke-width="3" y2="80" x2="25" y1="20" x1="25" stroke="#000000" fill="none"/>
    <line stroke-width="3" y2="80" x2="75" y1="20" x1="75" stroke="#000000" fill="none"/>
    <line y2="49" y1="49" x1="25" stroke-width="3" stroke="#000000" fill="none"/>
    <line y2="48.66387" x2="75" y1="48.66387" x1="100" stroke-width="3" stroke="#000000" fill="none"/>
    <line stroke-width="3" y2="30" x2="65.17394" y1="70.36014" x1="35" stroke="#000000" fill="none"/>
  </g>
);


export const CoilSvg = () => (
  <g>
    <line y2="49" y1="49" x1="25" stroke-width="3" stroke="#000000" fill="none"/>
    <text style={{cursor: 'move'}} xmlSpace="preserve" textAnchor="start" fontFamily="Noto Sans JP" fontSize="50" y="67.59988" x="-10.32629" strokeWidth="0" stroke="#000000" fill="#000000">（    ）</text>
  </g>
);


export const ModelSvg = () => (
  <g>
    <line stroke="#000000" x2="-0.47359" y2="49" y1="49" x1="19.67213" stroke-width="3" fill="none"/>
    <line stroke="#000000" x2="80.18214" y2="49" y1="49" x1="100.32786" stroke-width="3" fill="none"/>
    <rect height="80" width="60" y="10" x="20" stroke-width="3" stroke="#000000" fill="none"/>
  </g>
);


export const ConnectUpSvg = () => (
  <g>
    <line stroke="#000000" x2="0" y2="49" y1="49" x1="50.56338" stroke-width="3" fill="none"/>
    <path d="m42.20423,14.71432l6.5996,-11.5493l6.5996,11.5493l-13.1992,0z" stroke-width="3" stroke="#000000" fill="#000000"/>
    <line y2="4.0578" x2="49" y1="49" x1="49" stroke-width="3" stroke="#000000" fill="none"/>
  </g>
);

export const ConnectDownSvg = () => (
  <g>
    <line fill="none" stroke-width="3" x1="50.56338" y1="49" y2="49" stroke="#000000"/>
    <g transform="rotate(180 49.1372 73.1381)">
      <path fill="#000000" stroke="#000000" stroke-width="3" d="m42.53756,61.76987l6.5996,-11.5493l6.5996,11.5493l-13.1992,0z"/>
      <line fill="none" stroke="#000000" stroke-width="3" x1="49.33333" y1="96.05555" x2="49.33333" y2="51.11335"/>
    </g>
  </g>
);

export const ConnectRightSvg = () => (
  <g>
    <path d="m75.77705,25.68092l-51.33261,0" transform="rotate(90 50.1107 25.6809)" stroke-width="3" stroke="#000000" fill="none"/>
    <g transform="rotate(90 74.1682 49.5072)">
      <path fill="#000000" stroke="#000000" stroke-width="3" d="m67.56858,38.139l6.5996,-11.5493l6.5996,11.5493l-13.1992,0z"/>
      <line fill="none" stroke="#000000" stroke-width="3" x1="74.36435" y1="72.42468" x2="74.36435" y2="27.48248"/>
    </g>
  </g>
);