/* Check readable layout and horizontal overflow at common window sizes. */
const fs=require('node:fs'),path=require('node:path');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const report=[];
 try{
  for(const [width,height] of [[1600,1050],[1024,768],[768,900],[390,844]]){
   const page=await browser.newPage({viewport:{width,height}});
   await page.goto('file:///'+path.join(root,'dist/index.html').replaceAll('\\','/'));
   await page.waitForFunction(()=>window.waterAtlas&&!waterAtlas.state.busy);
   const result=await page.evaluate(()=>{
    const doc=document.documentElement,plot=document.querySelector('#plot'),toolbar=document.querySelector('.toolbar');
    const controls=[...document.querySelectorAll('.toolbar button')].map(b=>({text:b.textContent,rect:b.getBoundingClientRect().toJSON()}));
    const p=plot.getBoundingClientRect(),t=toolbar.getBoundingClientRect();
    return {viewport:innerWidth,scrollWidth:doc.scrollWidth,plotWidth:p.width,plotHeight:p.height,toolbarHeight:t.height,
     clippedControls:controls.filter(c=>c.rect.left<0||c.rect.right>innerWidth+1).map(c=>c.text),
     headingSize:getComputedStyle(document.querySelector('h1')).fontSize,
     labelSize:getComputedStyle(document.querySelector('.phase')).fontSize};
   });
   if(result.scrollWidth>width+1||result.clippedControls.length||result.plotWidth<250||result.plotHeight<300)throw new Error(JSON.stringify({width,result}));
   await page.screenshot({path:path.join(root,'tests',`layout-${width}.png`),fullPage:width<=800});
   if(width===390){
    await page.click('#sources');
    const dialog=await page.locator('#sourceDialog').evaluate(d=>({width:d.clientWidth,scrollWidth:d.scrollWidth}));
    if(dialog.scrollWidth>dialog.width+1)throw new Error('Source dialog overflows: '+JSON.stringify(dialog));
    await page.screenshot({path:path.join(root,'tests/layout-sources-390.png')});
   }
   console.log('PASS layout',width+'x'+height,JSON.stringify(result));report.push({width,height,...result});
   await page.close();
  }
  fs.writeFileSync(path.join(root,'tests/layout_report.json'),JSON.stringify({status:'PASS',report},null,2));
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exit(1)});
