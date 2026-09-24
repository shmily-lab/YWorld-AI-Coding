/* 构建只读版：从本地可编辑版生成"纯浏览"站点，供 HTTPS 发布使用
   用法：node build-readonly.js
   产出：D:\y'world\yworld-site-public\（index.html + ppt-campus-network.html）
   若存在 D:\y'world\yworld-site\yworld-projects.json，会把其中项目烘焙进只读版 */
const fs = require('fs');
const path = require('path');

const SRC = 'D:/y\'world/yworld-site/index.html';
const OUT_DIR = 'D:/y\'world/yworld-site-public';
const PPT = 'D:/y\'world/yworld-site/ppt-campus-network.html';
const PROJ = 'D:/y\'world/yworld-site/yworld-projects.json';

function once(html, find, replace, label) {
  const n = html.split(find).length - 1;
  if (n !== 1) {
    console.error('ANCHOR ERROR [' + label + ']: matched ' + n + ' times (expected 1)');
    process.exit(1);
  }
  return html.replace(find, replace);
}

let html = fs.readFileSync(SRC, 'utf8');
const srcLen = html.length;

/* 1) 隐藏所有站长 / 编辑相关 UI（元素仍在 DOM 中，JS 引用不会崩，只是不可见不可点） */
html = once(html,
  '  #lockBtn.owner:hover { border-color: rgba(255, 209, 102, 0.9); color: #ffe49a; }\n',
  '  #lockBtn.owner:hover { border-color: rgba(255, 209, 102, 0.9); color: #ffe49a; }\n' +
  '  #lockBtn, #ownerBar, #passModal, #delModal, #createModal { display: none !important; }\n',
  'hide owner UI');

/* 2) 去掉站长模式的 sessionStorage 记忆 —— 只读版永远是访客 */
html = once(html,
  "try { state.ownerMode = sessionStorage.getItem('yworld.owner') === '1'; } catch (e) {}",
  '/* 只读版本：无站长模式，永远访客身份 */',
  'no owner session');

/* 3) 关掉"创建项目"悬停气泡 */
html = once(html,
  '  if (state.hoverNode < 0 || state.hoverRegion >= 0 || flight.active || state._modalOpen) return;',
  '  return;                                   // 只读版本：不显示任何创建/编辑提示\n' +
  '  if (state.hoverNode < 0 || state.hoverRegion >= 0 || flight.active || state._modalOpen) return;',
  'no create bubble');

/* 4) 底部提示文案改为浏览导向 */
html = once(html, '站长解锁后可增删项目', '点击花朵可查看项目详情', 'footer hint');

/* 5) 烘焙已导出的自定义项目（若存在） */
let baked = 0;
if (fs.existsSync(PROJ)) {
  const parsed = JSON.parse(fs.readFileSync(PROJ, 'utf8'));
  const list = Array.isArray(parsed) ? parsed : (parsed.projects || []);
  if (list.length) {
    html = once(html,
      'const firstLon = regions[0].lon;',
      'const EMBEDDED_PROJECTS = ' + JSON.stringify(list) + ';\nconst firstLon = regions[0].lon;',
      'embed projects');
    html = once(html,
      '/* ---------------- 球面散点（拓扑网） ---------------- */',
      '/* 只读版：烘焙已上线的项目数据（来自 yworld-projects.json） */\n' +
      'EMBEDDED_PROJECTS.forEach(o => {\n' +
      '  const r = Object.assign({ live: false, custom: false }, o);\n' +
      '  r.center = latLon(r.lat, r.lon);\n' +
      '  regions.push(r);\n' +
      '});\n\n' +
      '/* ---------------- 球面散点（拓扑网） ---------------- */',
      'load embedded projects');
    baked = list.length;
  }
}

/* 6) 关键门禁自检：只读版不应残留任何"可 traits"的可见入口 */
const mustHide = ['#lockBtn', '#ownerBar', '#passModal'].map(s => html.includes('display: none !important') && html.includes(s));
if (!mustHide.every(Boolean)) { console.error('SAFETY CHECK FAILED: owner UI not hidden'); process.exit(1); }
if (html.includes("sessionStorage.getItem('yworld.owner')")) {
  console.error('SAFETY CHECK FAILED: owner session restore still present'); process.exit(1);
}

if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });
fs.writeFileSync(path.join(OUT_DIR, 'index.html'), html);
fs.copyFileSync(PPT, path.join(OUT_DIR, path.basename(PPT)));

console.log('READONLY BUILD OK');
console.log('  source      : ' + SRC + ' (' + srcLen + ' chars)');
console.log('  output      : ' + OUT_DIR);
console.log('  baked items : ' + baked);
console.log('  files       : index.html, ' + path.basename(PPT));
