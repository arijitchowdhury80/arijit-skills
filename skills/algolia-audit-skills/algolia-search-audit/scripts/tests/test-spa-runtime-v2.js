const fs = require('fs');
const path = process.argv[2];
if (!path) { console.error('Usage: node test-spa-runtime-v2.js <index.html>'); process.exit(1); }
const html = fs.readFileSync(path, 'utf8');
const failures = [];
function check(label, cond) { if (!cond) failures.push(`FAIL: ${label}`); else console.log(`  ✓ ${label}`); }
check('role-btn ae', html.includes('data-role="ae"'));
check('role-btn bdr', html.includes('data-role="bdr"'));
check('role-btn sl', html.includes('data-role="sl"'));
check('role-view elements', (html.match(/class="role-view"/g)||[]).length >= 3);
check('finding-cards container', html.includes('finding-cards') || html.includes('id="fc-'));
check('fc- elements (>=10)', (html.match(/id="fc-f/gi)||[]).length >= 10);
check('fc-expand-btn', html.includes('fc-expand-btn'));
check('research-drawer', html.includes('id="research-drawer"'));
check('drawer-overlay', html.includes('id="drawer-overlay"'));
check('openDrawer function', html.includes('openDrawer('));
check('research-library section', html.includes('research-lib') || html.includes('research-library'));
check('deliverables.html link', html.includes('deliverables.html'));
check('AUDIT_DATA injected', html.includes('window.AUDIT_DATA'));
if (failures.length) { failures.forEach(f => console.error(`  ${f}`)); process.exit(1); }
console.log('\n✓ All 13 checks passed.');
