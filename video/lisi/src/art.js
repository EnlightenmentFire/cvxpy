/* 手绘矢量素材（剪影 / 版画质感）。全部原创路径，无外部素材。 */
(function () {
  const A = {};

  /* 通用滤镜与纹理 */
  A.defs = `
  <svg width="0" height="0" style="position:absolute">
    <defs>
      <filter id="rough" x="-10%" y="-10%" width="120%" height="120%">
        <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="7" result="n"/>
        <feDisplacementMap in="SourceGraphic" in2="n" scale="7" xChannelSelector="R" yChannelSelector="G"/>
      </filter>
      <filter id="rough2" x="-10%" y="-10%" width="120%" height="120%">
        <feTurbulence type="fractalNoise" baseFrequency="0.09" numOctaves="2" seed="11" result="n"/>
        <feDisplacementMap in="SourceGraphic" in2="n" scale="4" xChannelSelector="R" yChannelSelector="G"/>
      </filter>
      <filter id="inkbleed" x="-10%" y="-10%" width="120%" height="120%">
        <feTurbulence type="fractalNoise" baseFrequency="0.6" numOctaves="2" seed="5" result="n"/>
        <feDisplacementMap in="SourceGraphic" in2="n" scale="3"/>
      </filter>
      <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
      <filter id="glowBig" x="-100%" y="-100%" width="300%" height="300%">
        <feGaussianBlur stdDeviation="18"/>
      </filter>
      <pattern id="hatchH" width="12" height="7" patternUnits="userSpaceOnUse">
        <path d="M0 3.5 H12" stroke="#000" stroke-width="2.4" opacity=".55"/>
      </pattern>
      <pattern id="hatchD" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(-32)">
        <path d="M0 4.5 H9" stroke="#000" stroke-width="2" opacity=".5"/>
      </pattern>
      <pattern id="hatchLight" width="10" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(-18)">
        <path d="M0 3 H10" stroke="#f3e2bb" stroke-width="1.1" opacity=".5"/>
      </pattern>
    </defs>
  </svg>`;

  /* 瘦鼠（厕鼠）：弓背、收腹、警觉。朝右。viewBox 0 0 460 240 */
  A.ratThin = (fill = '#050505') => `
  <g filter="url(#rough2)">
    <path d="M70 150 C 20 168, -10 140, -52 176 C -74 196, -96 190, -110 172" fill="none" stroke="${fill}" stroke-width="9" stroke-linecap="round"/>
    <path d="M110 168 C 96 176, 84 190, 88 204 L 132 206 L 130 196 L 116 192 C 124 184, 136 176, 150 172 Z" fill="${fill}"/>
    <path d="M286 164 C 284 178, 284 192, 290 204 L 320 204 L 318 195 L 306 192 C 304 182, 306 172, 312 164 Z" fill="${fill}"/>
    <path d="M404 132 C 392 116, 372 104, 350 100 C 330 92, 300 74, 262 66 C 208 54, 140 62, 96 102 C 70 126, 62 150, 78 170 C 96 186, 130 176, 168 166 C 204 158, 246 160, 282 168 C 304 172, 326 164, 344 152 C 362 148, 392 146, 404 132 Z" fill="${fill}"/>
    <ellipse cx="338" cy="86" rx="17" ry="23" transform="rotate(-18 338 86)" fill="${fill}"/>
    <ellipse cx="318" cy="90" rx="13" ry="18" transform="rotate(-30 318 90)" fill="${fill}"/>
  </g>
  <circle cx="372" cy="118" r="4.2" fill="#d8c9a3" opacity=".85"/>
  <g stroke="#d8c9a3" stroke-width="2" opacity=".35" fill="none" stroke-linecap="round">
    <path d="M150 96 C 170 112, 180 132, 182 156"/><path d="M186 82 C 204 100, 214 124, 216 152"/>
    <path d="M224 76 C 240 96, 250 122, 252 154"/><path d="M262 78 C 274 98, 282 124, 284 152"/>
  </g>
  <g stroke="${fill}" stroke-width="1.6" fill="none" stroke-linecap="round" opacity=".9">
    <path d="M398 130 L 440 116"/><path d="M398 134 L 444 136"/><path d="M396 138 L 436 154"/>
  </g>`;

  /* 肥鼠（仓鼠＝粮仓里的老鼠）：圆腹、坐姿、安稳。朝左。viewBox 0 0 460 260 */
  A.ratFat = (fill = '#050505') => `
  <g filter="url(#rough2)">
    <path d="M392 214 C 440 216, 476 196, 500 206 C 520 214, 538 208, 548 196" fill="none" stroke="${fill}" stroke-width="12" stroke-linecap="round"/>
    <path d="M52 150 C 62 128, 84 112, 110 104 C 132 78, 176 46, 240 40 C 320 32, 392 76, 408 140 C 420 186, 400 220, 356 228 L 150 230 C 132 230, 122 222, 124 210 C 108 204, 92 190, 84 172 C 68 170, 54 162, 52 150 Z" fill="${fill}"/>
    <ellipse cx="128" cy="92" rx="19" ry="25" transform="rotate(16 128 92)" fill="${fill}"/>
    <ellipse cx="152" cy="88" rx="15" ry="20" transform="rotate(28 152 88)" fill="${fill}"/>
    <path d="M150 196 C 138 204, 134 218, 140 230 L 196 232 L 192 220 L 174 216 Z" fill="${fill}"/>
  </g>
  <circle cx="88" cy="136" r="4.6" fill="#f0d79a" opacity=".9"/>
  <g stroke="#f0d79a" stroke-width="2.2" opacity=".28" fill="none" stroke-linecap="round">
    <path d="M214 60 C 250 92, 262 150, 240 214"/><path d="M270 54 C 312 90, 322 152, 300 216"/><path d="M326 66 C 364 104, 368 160, 348 214"/>
  </g>
  <g stroke="${fill}" stroke-width="1.6" fill="none" stroke-linecap="round" opacity=".9">
    <path d="M58 148 L 14 134"/><path d="M58 152 L 10 156"/><path d="M60 156 L 20 174"/>
  </g>`;

  /* 奔跑的猎犬（细腰、垂耳、卷尾），朝右。viewBox 0 0 360 170 */
  A.dog = (fill = '#050505') => `
  <g filter="url(#rough2)" fill="${fill}">
    <path d="M70 62 C 110 44, 170 44, 214 52 C 240 56, 258 66, 262 82 C 264 98, 250 108, 232 108 C 200 106, 176 96, 150 92 C 122 88, 96 92, 78 86 C 64 80, 60 70, 70 62 Z"/>
    <path d="M232 60 C 246 46, 262 36, 278 32 L 300 40 L 290 62 C 280 78, 262 90, 246 92 Z"/>
    <path d="M272 30 C 282 20, 298 18, 310 24 C 326 28, 342 36, 352 46 C 354 52, 350 56, 344 56 C 330 58, 314 58, 300 54 C 288 52, 276 44, 272 30 Z"/>
    <path d="M280 26 C 276 38, 270 52, 262 62 C 256 56, 258 40, 266 28 C 270 22, 278 20, 280 26 Z"/>
    <path d="M74 66 C 54 60, 36 46, 30 26 C 28 18, 34 14, 38 20 C 46 38, 60 50, 80 56 Z"/>
    <path d="M236 96 C 258 104, 286 110, 318 108 L 336 104 L 338 114 L 318 120 C 284 124, 252 118, 226 108 Z"/>
    <path d="M222 100 C 240 114, 262 128, 290 134 L 304 132 L 304 142 L 288 146 C 256 142, 228 126, 210 108 Z"/>
    <path d="M92 84 C 76 100, 54 116, 26 124 L 10 122 L 10 132 L 28 136 C 62 132, 90 114, 108 94 Z"/>
    <path d="M108 86 C 100 106, 82 128, 56 144 L 40 146 L 42 156 L 60 156 C 92 142, 114 118, 126 94 Z"/>
  </g>`;

  /* 野兔，跃起，朝右。viewBox 0 0 200 120 */
  A.hare = (fill = '#050505') => `
  <g filter="url(#rough2)"><path fill="${fill}" d="
    M 14 70 C 24 48, 60 36, 100 42 C 118 44, 132 40, 142 30 L 150 2 L 158 26 L 172 4 L 170 34
    C 184 38, 194 48, 196 58 C 186 64, 172 64, 160 62 C 152 70, 140 76, 128 78
    C 142 88, 160 94, 178 94 L 178 102 C 156 106, 130 100, 110 88
    C 90 92, 68 92, 50 86 C 40 98, 22 108, 4 110 L 2 102 C 18 96, 30 84, 34 72 C 26 74, 18 74, 14 70 Z"/></g>`;

  /* 城门楼（上蔡东门）。viewBox 0 0 520 420，底边 y=420 */
  A.gate = (fill = '#050505') => `
  <g filter="url(#rough2)" fill="${fill}">
    <path d="M0 420 L 0 250 L 30 250 L 30 232 L 60 232 L 60 250 L 100 250 L 100 232 L 130 232 L 130 250 L 390 250 L 390 232 L 420 232 L 420 250 L 460 250 L 460 232 L 490 232 L 490 250 L 520 250 L 520 420 L 310 420 L 310 330 C 310 296, 210 296, 210 330 L 210 420 Z"/>
    <path d="M150 250 L 150 190 L 370 190 L 370 250 Z"/>
    <path d="M110 192 C 150 186, 170 170, 186 150 L 334 150 C 350 170, 370 186, 410 192 L 404 200 L 116 200 Z"/>
    <path d="M178 150 L 178 110 L 342 110 L 342 150 Z"/>
    <path d="M140 112 C 180 106, 204 88, 222 64 L 298 64 C 316 88, 340 106, 380 112 L 374 120 L 146 120 Z"/>
    <rect x="254" y="48" width="12" height="20"/>
  </g>`;

  /* 人物剪影（长袍），高约 200。viewBox 0 0 90 210 */
  A.man = (fill = '#050505', bent = false) => `
  <g filter="url(#rough2)" fill="${fill}">
    <ellipse cx="${bent ? 50 : 45}" cy="22" rx="15" ry="17"/>
    <rect x="${bent ? 44 : 39}" y="0" width="12" height="12" rx="3"/>
    <path d="M ${bent ? 34 : 28} 44 C 40 36, 56 36, ${bent ? 68 : 62} 44 C 74 70, 80 150, 84 206 L 6 206 C 10 150, 16 70, ${bent ? 34 : 28} 44 Z"/>
  </g>`;

  /* 辒辌车：有窗的卧车，四马只示意辕。viewBox 0 0 640 380 */
  A.carriage = (fill = '#050505', glow = '#e9b45a') => `
  <g filter="url(#rough2)" fill="${fill}">
    <path d="M96 120 C 110 70, 180 40, 320 40 C 460 40, 530 70, 544 120 L 560 128 L 560 140 L 80 140 L 80 128 Z"/>
    <rect x="104" y="138" width="432" height="128"/>
    <rect x="70" y="262" width="500" height="18" rx="4"/>
    <path d="M70 268 L -40 296 L -40 306 L 70 286 Z"/>
    <circle cx="210" cy="300" r="74"/><circle cx="430" cy="300" r="74"/>
  </g>
  <g fill="none" stroke="#1d1a16" stroke-width="5">
    <circle cx="210" cy="300" r="56"/><circle cx="430" cy="300" r="56"/>
  </g>
  <g stroke="#1d1a16" stroke-width="4">
    ${[0, 30, 60, 90, 120, 150].map(a => `<path d="M210 300 l ${56 * Math.cos(a * Math.PI / 180)} ${56 * Math.sin(a * Math.PI / 180)} M210 300 l ${-56 * Math.cos(a * Math.PI / 180)} ${-56 * Math.sin(a * Math.PI / 180)}"/>`).join('')}
    ${[0, 30, 60, 90, 120, 150].map(a => `<path d="M430 300 l ${56 * Math.cos(a * Math.PI / 180)} ${56 * Math.sin(a * Math.PI / 180)} M430 300 l ${-56 * Math.cos(a * Math.PI / 180)} ${-56 * Math.sin(a * Math.PI / 180)}"/>`).join('')}
  </g>
  <g class="carWin">
    <rect x="150" y="166" width="96" height="62" fill="${glow}" opacity=".9"/>
    <rect x="394" y="166" width="96" height="62" fill="${glow}" opacity=".55"/>
    <g stroke="${fill}" stroke-width="6">
      <path d="M150 187 H246 M150 208 H246 M182 166 V228 M214 166 V228"/>
      <path d="M394 187 H490 M394 208 H490 M426 166 V228 M458 166 V228"/>
    </g>
  </g>`;

  /* 封好的诏书（简牍 + 封泥）。viewBox 0 0 300 200 */
  A.letter = () => `
  <g filter="url(#rough2)">
    ${Array.from({ length: 9 }, (_, i) => `<rect x="${14 + i * 30}" y="20" width="26" height="160" fill="${i % 2 ? '#b89a62' : '#c4a66c'}"/>`).join('')}
    <path d="M6 62 H294 M6 138 H294" stroke="#5b3d1c" stroke-width="7"/>
    <rect x="118" y="78" width="64" height="44" rx="6" fill="#7a2f22"/>
    <rect x="128" y="86" width="44" height="28" rx="2" fill="none" stroke="#c98a6d" stroke-width="3"/>
  </g>`;

  /* 玺：方印 + 钮。viewBox 0 0 160 170 */
  A.seal = () => `
  <g filter="url(#rough2)">
    <path d="M52 58 C 46 26, 64 8, 80 8 C 96 8, 114 26, 108 58 Z" fill="#cdbb8e"/>
    <rect x="18" y="56" width="124" height="96" rx="6" fill="#d9c79a"/>
    <rect x="18" y="132" width="124" height="20" rx="4" fill="#a3221a"/>
    <path d="M30 70 H130 M30 86 H130" stroke="#a8946a" stroke-width="3" opacity=".7"/>
  </g>`;

  /* 面具（官冠 + 空眼）。viewBox 0 0 220 300 */
  A.mask = (tone = '#cdbf9c') => `
  <g filter="url(#rough2)">
    <path d="M60 44 L 60 10 L 160 10 L 160 44 L 176 50 L 176 70 L 44 70 L 44 50 Z" fill="#0a0908" stroke="${tone}" stroke-width="3"/>
    <path d="M40 78 C 40 70, 180 70, 180 78 C 192 150, 176 236, 110 284 C 44 236, 28 150, 40 78 Z" fill="${tone}"/>
    <path d="M62 132 C 76 120, 94 122, 100 134 C 90 142, 72 142, 62 132 Z" fill="#0a0908"/>
    <path d="M120 134 C 126 122, 144 120, 158 132 C 148 142, 130 142, 120 134 Z" fill="#0a0908"/>
    <path d="M110 150 L 102 196 L 118 196 Z" fill="#a89a78"/>
    <path d="M84 226 C 100 232, 120 232, 136 226" fill="none" stroke="#0a0908" stroke-width="5" stroke-linecap="round"/>
  </g>`;

  /* 小车马图标（车骑以千数），朝左。viewBox 0 0 100 50 */
  A.cart = (fill = '#c9a45c') => `
  <g fill="${fill}">
    <path d="M52 15 Q 72 1 92 15 Z"/><rect x="56" y="17" width="32" height="13"/>
    <circle cx="72" cy="36" r="10" fill="none" stroke="${fill}" stroke-width="3.2"/>
    <path d="M56 26 L 34 26 L 34 29 L 56 29 Z"/>
    <path d="M12 20 C 18 16, 30 16, 36 20 L 36 30 L 33 30 L 33 45 L 30 45 L 29 32 L 19 32 L 18 45 L 15 45 L 14 30 C 11 28, 11 23, 12 20 Z"/>
    <path d="M13 22 L 5 9 L 9 8 L 10 3 L 14 8 L 20 18 Z"/><path d="M36 21 C 40 24, 41 30, 39 36 L 37 35 C 38 30, 37 26, 35 24 Z"/>
  </g>`;

  /* 小人（刑者相半于道）。viewBox 0 0 40 90 */
  A.figure = (fill = '#8f8369') => `
  <g fill="${fill}"><circle cx="20" cy="12" r="9"/><path d="M10 26 C 14 22, 26 22, 30 26 L 35 86 L 5 86 Z"/></g>`;

  window.ART = A;
})();
