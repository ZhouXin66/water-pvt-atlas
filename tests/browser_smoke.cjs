/* Offline browser acceptance test. Uses installed Playwright or Codex bundled package. */
const fs=require('node:fs'),path=require('node:path');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..');
(async()=>{
 const browser=await chromium.launch({downloadsPath:path.join(root,'tests/downloads'),executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-webgl','--ignore-gpu-blocklist','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1600,height:1050},acceptDownloads:true});
 await page.addInitScript(()=>{
  window.__saveRequests=[];window.__savedPNGs=[];window.__exportedModel=null;
  const originalClick=HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click=function(){
   if(this.download==='water-pvt-model.json'){
    fetch(this.href).then(response=>response.json()).then(model=>{window.__exportedModel=model;});
    return;
   }
   return originalClick.call(this);
  };
  Object.defineProperty(window,'showSaveFilePicker',{configurable:true,value:async options=>{
   window.__saveRequests.push({name:options.suggestedName,active:navigator.userActivation.isActive});
   return{name:options.suggestedName,createWritable:async()=>({
    write:async blob=>{const bytes=new Uint8Array(await blob.arrayBuffer());window.__savedPNGs.push({size:bytes.length,signature:Array.from(bytes.slice(0,8)),width:new DataView(bytes.buffer).getUint32(16),height:new DataView(bytes.buffer).getUint32(20)});},
    close:async()=>{},abort:async()=>{}
   })};
  }});
 });
 const errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 await page.route(/^https?:/,r=>{requests.push(r.request().url());r.abort();});
 await page.goto('file:///'+path.join(root,'dist/index.html').replaceAll('\\','/'));
 await page.waitForFunction(()=>window.waterAtlas&&!window.waterAtlas.state.busy&&document.querySelector('#plot').data?.length>0,{timeout:120000});
 const tests=[];async function check(name,fn){if(!await fn())throw new Error(name);tests.push(name);console.log('PASS',name);}
 await check('Offline file opens with actual meshes',()=>page.evaluate(()=>document.querySelector('#plot').data.filter(t=>t.type==='mesh3d'&&t.i.length>0).length===6));
 await check('Custom favicon renders offline',()=>page.evaluate(()=>new Promise(resolve=>{
  const link=document.querySelector('link[rel="icon"]'),image=new Image();
  image.onload=()=>resolve(document.title==='水的 p–v–T 状态相图'&&image.naturalWidth>0&&image.naturalHeight>0);
  image.onerror=()=>resolve(false);
  image.src=link?.href||'';
 })));
 await page.screenshot({path:path.join(root,'tests/overview.png')});
 for(const view of ['pt','pv','tv','3d']){await page.locator('[data-view="'+view+'"]').click();await page.waitForFunction(()=>!waterAtlas.state.busy);await check('Projection '+view,()=>page.evaluate(v=>waterAtlas.state.view===v&&!document.querySelector('#viewnote').textContent.includes('失败'),view));}
 await page.selectOption('#preset','condensed');await page.waitForFunction(()=>!waterAtlas.state.busy);await page.screenshot({path:path.join(root,'tests/condensed.png')});
 await page.selectOption('#pscale','linear');await page.selectOption('#vscale','linear');await page.waitForFunction(()=>!waterAtlas.state.busy);await check('Linear axes retain real values',()=>page.evaluate(()=>{const p=waterAtlas.mixture();return document.querySelector('#plot').data.some(t=>t.name==='当前混合物'&&t.x[0]===p[2]&&t.z[0]===p[1]);}));
 await page.selectOption('#pscale','log');await page.selectOption('#vscale','log');await page.selectOption('#preset','engineering');await page.waitForFunction(()=>!waterAtlas.state.busy);
 await page.locator('#quality').fill('0');await page.locator('#quality').dispatchEvent('input');await check('Quality x=0 is saturated liquid',()=>page.evaluate(()=>waterAtlas.mixture()[2]===waterAtlas.model.pressure_choices[Number(document.querySelector('#pressure').value)].v_liquid_m3_kg));
 await page.locator('#quality').fill('1000');await page.locator('#quality').dispatchEvent('input');await check('Quality x=1 is saturated vapor',()=>page.evaluate(()=>waterAtlas.mixture()[2]===waterAtlas.model.pressure_choices[Number(document.querySelector('#pressure').value)].v_vapor_m3_kg));
 await page.click('#inspectMix');await check('Click details include table source',()=>page.locator('#details').innerText().then(t=>t.includes('NISTIR 5078 Table 2')));await page.click('#closeDetails');
 await page.check('#raw');await page.waitForFunction(()=>!waterAtlas.state.busy);await check('Raw published points visible',()=>page.evaluate(()=>document.querySelector('#plot').data.some(t=>t.type==='scatter3d'&&t.customdata?.length>100&&t.customdata[0][4].includes('原表'))));
 await page.locator('#layers input').first().uncheck();await page.waitForFunction(()=>!waterAtlas.state.busy);await check('Phase toggle works',()=>page.evaluate(()=>!waterAtlas.state.visible.ice));await page.locator('#layers input').first().check();await page.waitForFunction(()=>!waterAtlas.state.busy);
 await page.click('#sources');await check('Source dialog opens',()=>page.locator('#sourceDialog').isVisible());await page.click('#closeSources');
 await page.selectOption('#pressure','100');await page.waitForFunction(()=>!waterAtlas.state.busy);await check('Pressure selector uses exact published row',()=>page.evaluate(()=>{const p=waterAtlas.mixture(),r=waterAtlas.model.pressure_choices[100];return p[0]===r.T_K&&p[1]===r.p_Pa;}));
 await page.click('#animate');await page.waitForFunction(()=>waterAtlas.mixture()[5]>.05);await page.click('#animate');await check('Quality animation advances and pauses',()=>page.evaluate(()=>waterAtlas.state.animation===null&&waterAtlas.mixture()[5]>.05));
 for(const preset of ['full','critical','engineering']){await page.selectOption('#preset',preset);await page.waitForFunction(()=>!waterAtlas.state.busy);await check('Range preset '+preset,()=>page.evaluate(()=>!document.querySelector('#viewnote').textContent.includes('失败')));}
 await page.uncheck('#triple');await page.uncheck('#critical');await page.waitForFunction(()=>!waterAtlas.state.busy);await check('Special state toggles',()=>page.evaluate(()=>!document.querySelector('#plot').data.some(t=>t.name==='三相线'||t.name==='临界点')));await page.check('#triple');await page.check('#critical');await page.waitForFunction(()=>!waterAtlas.state.busy);
 const box=await page.locator('#plot').boundingBox();await page.mouse.move(box.x+box.width*.55,box.y+box.height*.45);await page.mouse.down();await page.mouse.move(box.x+box.width*.68,box.y+box.height*.53,{steps:10});await page.mouse.up();
 await check('3D camera responds to drag',()=>page.evaluate(()=>{const e=document.querySelector('#plot')._fullLayout.scene.camera.eye;return Math.abs(e.x-1.55)>.001||Math.abs(e.y-1.55)>.001;}));
 await page.click('#reset');await check('Reset view',()=>page.evaluate(()=>Math.abs(document.querySelector('#plot')._fullLayout.scene.camera.eye.x-1.55)<.001));
 if(await page.locator('#details').isVisible())await page.click('#closeDetails');
 const zoomTarget=await page.evaluate(()=>{
  const scene=document.querySelector('#plot')._fullLayout.scene._scene;
  const rect=scene.glplot.canvas.getBoundingClientRect(),view=scene.glplot.cameraParams.view,projection=scene.glplot.cameraParams.projection;
  const camera=scene.getCamera(),distance=Math.hypot(...['x','y','z'].map(k=>camera.eye[k]-camera.center[k]));
  const x=.22,y=.32,anchor={};
  for(const [i,key] of ['x','y','z'].entries())anchor[key]=camera.center[key]+distance*((2*x-1)*view[i*4]/projection[0]+(1-2*y)*view[i*4+1]/projection[5]);
  window.__zoomAnchor=anchor;
  return{px:rect.left+rect.width*x,py:rect.top+rect.height*y,distance};
 });
 await page.mouse.move(zoomTarget.px,zoomTarget.py);await page.mouse.wheel(0,-160);
 await page.waitForFunction(oldDistance=>{
  const camera=document.querySelector('#plot')._fullLayout.scene._scene.getCamera();
  return Math.hypot(...['x','y','z'].map(k=>camera.eye[k]-camera.center[k]))<oldDistance*.99;
 },zoomTarget.distance);
 await check('3D wheel zoom keeps off-center cursor anchor',()=>page.evaluate(target=>{
  const scene=document.querySelector('#plot')._fullLayout.scene._scene;
  const rect=scene.glplot.canvas.getBoundingClientRect(),v=scene.glplot.cameraParams.view,p=scene.glplot.cameraParams.projection,a=window.__zoomAnchor;
  const pos=[v[0]*a.x+v[4]*a.y+v[8]*a.z+v[12],v[1]*a.x+v[5]*a.y+v[9]*a.z+v[13],v[2]*a.x+v[6]*a.y+v[10]*a.z+v[14]];
  const px=rect.left+rect.width*(1+p[0]*pos[0]/-pos[2])/2;
  const py=rect.top+rect.height*(1-p[5]*pos[1]/-pos[2])/2;
  const c=scene.getCamera().center;
  return Math.hypot(px-target.px,py-target.py)<2&&Math.hypot(c.x,c.y,c.z)>.01;
 },zoomTarget));
 await page.mouse.wheel(0,160);
 await page.waitForFunction(()=>{
  const c=document.querySelector('#plot')._fullLayout.scene._scene.getCamera();
  return Math.hypot(c.center.x,c.center.y,c.center.z)<1e-4&&Math.abs(c.eye.x-1.55)<1e-4;
 });
 await check('Reverse wheel restores camera',()=>page.evaluate(()=>{
  const c=document.querySelector('#plot')._fullLayout.scene._scene.getCamera();
  return Math.hypot(c.center.x,c.center.y,c.center.z)<1e-4;
 }));
 await page.click('#reset');await check('Reset clears wheel pan',()=>page.evaluate(()=>{
  const c=document.querySelector('#plot')._fullLayout.scene._scene.getCamera().center;
  return Math.hypot(c.x,c.y,c.z)<1e-6;
 }));
 await page.click('#export');await page.waitForFunction(()=>window.__savedPNGs.length===1,{timeout:120000});
 await check('PNG Save As has dated name and valid image',()=>page.evaluate(()=>{
  const request=window.__saveRequests[0],image=window.__savedPNGs[0];
  return request.active&&/^water-pvt-3d-\d{8}-\d{6}\.png$/.test(request.name)
   &&image.signature.join(',')==='137,80,78,71,13,10,26,10'&&image.width===1600&&image.height===1100&&image.size>10000;
 }));
 await page.click('#exportData');await page.waitForFunction(()=>window.__exportedModel!==null);
 await check('JSON model export',()=>page.evaluate(()=>window.__exportedModel.version===1));
 await check('No runtime HTTP requests',async()=>requests.length===0);await check('No browser errors',async()=>errors.length===0);
 fs.writeFileSync(path.join(root,'tests/browser_report.json'),JSON.stringify({status:'PASS',tests,errors,requests},null,2));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
