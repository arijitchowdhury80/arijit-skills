const fs = require('fs');
const path = process.argv[2];
if (!path) { console.error('Usage: node test-deliverables-runtime.js <deliverables.html>'); process.exit(1); }
const html = fs.readFileSync(path, 'utf8');
const failures = [];
function check(label, cond) {
  if (!cond) failures.push(`FAIL: ${label}`); else console.log(`  ✓ ${label}`);
}
check('del-ae-brief section', html.includes('id="del-ae-brief"'));
check('del-bdr-outreach section', html.includes('id="del-bdr-outreach"'));
check('del-battle-card section', html.includes('id="del-battle-card"'));
check('del-leave-behind section', html.includes('id="del-leave-behind"'));
check('del-business-case section', html.includes('id="del-business-case"'));
check('AUDIT_DATA injected', html.includes('window.AUDIT_DATA'));
check('back to Command Center link', html.includes('index.html'));
check('togglePreview function', html.includes('togglePreview'));
check('copySection function', html.includes('copySection'));
if (failures.length) { failures.forEach(f => console.error(`  ${f}`)); process.exit(1); }
console.log(`\n✓ All ${9} deliverables checks passed.`);
