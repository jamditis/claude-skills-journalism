import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
const root = path.resolve('docs/dot-skills');
test('dot workflow pages have real internal links and accessible structure', () => {
 for (const slug of ['', 'status-cards', 'incident-updates', 'visual-audits', 'source-evidence', 'rough-edges']) {
  const filename = path.join(root,slug,'index.html'); const html=fs.readFileSync(filename,'utf8');
  assert.equal((html.match(/<h1>/g)||[]).length,1); assert.match(html, /id="main"/); assert.match(html,/class="skip"/);
  for(const [,href] of html.matchAll(/(?:href|src)="([^"]+)"/g)){
   if (/^(https?:|#|\/)/.test(href))continue;
   const target=path.resolve(path.dirname(filename),href.split('#')[0]);assert.ok(fs.existsSync(target),`${filename}: ${href}`);
  }
 }
});
test('motion control and repeated demo checks preserve the estimate',()=>{
 const handlers={};const classes=new Set();const motion={setAttribute:(k,v)=>handlers[k]=v,addEventListener:(k,v)=>handlers.motion=v};const checked={textContent:''};const check={addEventListener:(k,v)=>handlers.check=v};
 const context={document:{body:{classList:{toggle:(k,v)=>v?classes.add(k):classes.delete(k)}},querySelector:s=>({'#motion':motion,'#checked':checked,'#check':check}[s])},window:{matchMedia:()=>({matches:true,addEventListener:(k,v)=>handlers.preference=v})},Intl,Date};
 vm.runInNewContext(fs.readFileSync(path.join(root,'workshop.js'),'utf8'),context);
 assert.ok(classes.has('paused'));assert.equal(handlers['aria-pressed'],'true');handlers.motion();assert.equal(handlers['aria-pressed'],'false');handlers.preference({matches:true});assert.ok(classes.has('paused'));
 handlers.check();assert.match(checked.textContent,/^Demo checked:/);handlers.check();assert.match(checked.textContent,/^Demo checked:/);
 assert.match(fs.readFileSync(path.join(root,'index.html'),'utf8'),/<span>60%<\/span>/);
});
test('homepage feature precedes Codex and motion honors reduced-motion',()=>{
 const home=fs.readFileSync('docs/index.html','utf8');assert.ok(home.indexOf('href="dot-skills/"')<home.indexOf('The Codex review setup I run.'));
 assert.match(fs.readFileSync(path.join(root,'style.css'),'utf8'),/@media\(prefers-reduced-motion:reduce\)/);
});
