// test-finance-axis.mjs — pins the data-driven financial-chart axis.
//
// Regression guard for the Home Depot bug: the left $B axis was hardcoded to a
// max of 56 ($0–$50B gridlines), so any company with revenue > ~$56B (Home
// Depot ~$165B) rendered bars ~3x off the chart. The axis is now derived from
// the data via niceStep/axisMax (mirrored below — keep in sync with
// templates/index-template.html). Run: node test-finance-axis.mjs
//
// NOTE: this is a logic mirror, not an import (the functions live inside the
// HTML template literal). If you change axisMax in the template, change it here.

function niceStep(range){ if(!(range>0))return 1; const e=Math.floor(Math.log10(range)), f=range/Math.pow(10,e); const nf=f<1.5?1:f<3?2:f<7?5:10; return nf*Math.pow(10,e); }
function axisMax(vals, floor){
  const d=vals.filter(v=>typeof v==='number'&&v>0);
  const m=Math.max(d.length?Math.max(...d):0, floor||0);
  const step=niceStep(m/4);
  let max=Math.max(Math.ceil(m/step)*step, step);
  if(max<=m+1e-9) max+=step;
  const ticks=[]; for(let v=0; v<=max+1e-9; v+=step) ticks.push(Math.round(v*100)/100);
  return {max, step, ticks};
}

let pass=0, fail=0;
function eq(name, got, want){
  const g=JSON.stringify(got), w=JSON.stringify(want);
  if(g===w){ pass++; } else { fail++; console.error(`✗ ${name}\n    got : ${g}\n    want: ${w}`); }
}
function ok(name, cond){ if(cond){ pass++; } else { fail++; console.error(`✗ ${name}`); } }

// Home Depot — the bug case. Revenue must NOT overflow.
const hdBars = axisMax([152.7,159.5,164.7, 50.9,53.2,54.9, 23.2,24.2,25.0], 0);
eq('HD left-axis ticks', hdBars.ticks, [0,50,100,150,200]);
ok('HD revenue 164.7 within axis (max>=data)', hdBars.max >= 164.7);
ok('HD revenue fill 70-95% (good headroom, not clipped)', (164.7/hdBars.max) > 0.7 && (164.7/hdBars.max) <= 0.95);

// Small/mid caps still get tight, readable axes (not stuck at the old $0-50B).
eq('PetSmart ~$9B ticks', axisMax([8.9,9.3,9.6, 3.1,3.2,3.3, 1.2,1.25,1.3],0).ticks, [0,2,4,6,8,10]);
eq('Small $2B ticks',     axisMax([1.8,1.9,2.0, 0.7,0.72,0.75],0).ticks,           [0,0.5,1,1.5,2,2.5]);

// Mega cap.
ok('Mega $400B axis covers data', axisMax([380,394,401, 120,125,130],0).max >= 401);

// Percent axis: at least a 0-20 frame; SaaS-style high margins must fit.
ok('margin axis keeps >=20 frame for stable ~15% margins', axisMax([15.2,15.2,15.2], 20).max >= 20);
ok('high 42% margin fits', axisMax([41,42,43], 20).max >= 43);

// Empty / absent data must not throw or produce a 0 axis.
ok('empty bars -> positive axis', axisMax([], 0).max > 0);

console.log(`\nfinance-axis: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
