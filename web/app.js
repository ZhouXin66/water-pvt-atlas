'use strict';
const MODEL=JSON.parse(document.getElementById('model').textContent);
const $=id=>document.getElementById(id);
const PHASES={ice:['冰 Ih','#a8c9fc','单相'],liquid:['液态水','#35bcb9','单相'],vapor:['水蒸气','#f8b96c','单相'],sl:['固液共存','#bf9aec','两相'],lv:['汽液共存','#5fe0c0','两相'],sv:['固气共存','#df94b5','两相'],supercritical:['超临界流体','#8592a8','临界以上']};
const state={view:'3d',visible:Object.fromEntries(Object.keys(PHASES).map(k=>[k,k!=='supercritical'])),busy:false,rerun:false,animation:null};
const PRESETS={engineering:{T:[230,900],p:[1,1e8],v:[8.5e-4,2e4],note:'当前窗口：230–900 K；1 Pa–100 MPa。更低温升华数据请选“全部数据范围”。'},full:{T:[130,1273.15],p:[1e-8,1e8],v:[8e-4,6e12],note:'全部域跨越约16个压力数量级、16个体积数量级；凝聚相细节请切换专用视图。'},condensed:{T:[245,285],p:[1e4,1e8],v:[8.8e-4,1.12e-3],note:'放大观察 v液 < v冰，以及熔化温度随压力升高而降低。'},critical:{T:[620,680],p:[15e6,30e6],v:[1.4e-3,9e-3],note:'汽液面两端在临界点合并；此处干度失去定义。'}};
const defaultCamera=()=>({eye:$('plot').clientWidth<600?{x:2.15,y:2.15,z:1.48}:{x:1.55,y:1.55,z:1.05},center:{x:0,y:0,z:0},up:{x:0,y:0,z:1}});
const fmt=(n,d=6)=>Number(n).toPrecision(d).replace(/\.?0+e/,'e').replace(/(\.\d*?)0+$/,'$1').replace(/\.$/,'');
const units={T:'温度 T / K',p:'压力 p / Pa',v:'比体积 v / m³·kg⁻¹'};
const field={T:0,p:1,v:2};
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const tags={'published table':'原表值（含单位换算）','published endpoint':'原表平衡端点（含单位换算）','mass mixture':'质量守恒混合','geometric interpolation + mixture':'平衡行间几何插值 + 质量守恒混合','triple':'三相线质量组合','process':'定压路径：表 3 原表值'};
const scaled=(n,key)=>key==='T'?n:$(key==='p'?'pscale':'vscale').value==='log'?Math.log10(n):n;
const point=(T,p,v,ref,tag,x=null)=>[T,p,v,ref,tag,x];
function axis(key){const range=PRESETS[$('preset').value][key];const islog=key!=='T'&&$(key==='p'?'pscale':'vscale').value==='log';const a={title:{text:units[key]+(islog?'（对数）':'')},range:range.map(v=>scaled(v,key)),gridcolor:'#26384b',zerolinecolor:'#2b3e52',color:'#b0c3d2',showspikes:false};if(islog){let lo=Math.ceil(Math.log10(range[0])),hi=Math.floor(Math.log10(range[1]));let step=Math.max(1,Math.ceil((hi-lo)/8));a.tickvals=[];a.ticktext=[];for(let i=lo;i<=hi;i+=step){a.tickvals.push(i);a.ticktext.push('10<sup>'+i+'</sup>');}if(hi-lo<2){let vals=key==='v'?[.0009,.001,.0011,.0015,.002,.003,.005,.008]:[1e7,1.5e7,2e7,3e7,5e7,1e8];a.tickvals=vals.filter(v=>v>=range[0]&&v<=range[1]).map(Math.log10);a.ticktext=vals.filter(v=>v>=range[0]&&v<=range[1]).map(v=>fmt(v,3));}}return a;}
function custom(points,key){return points.map(r=>[r[0],r[1],r[2],PHASES[key]?.[0]||key,tags[r[4]]||r[4],r[3],r[5]==null?'—':fmt(r[5],4)]);}
const hover='<b>%{customdata[3]}</b><br>T = %{customdata[0]:.6g} K<br>p = %{customdata[1]:.6g} Pa<br>v = %{customdata[2]:.7g} m³/kg<br>x = %{customdata[6]}<br>%{customdata[4]}<br>来源：%{customdata[5]}<extra></extra>';
function coords(points){let keys=state.view==='3d'?['v','T','p']:state.view==='pt'?['T','p']:state.view==='pv'?['v','p']:['v','T'];let data={};keys.forEach((k,i)=>data[['x','y','z'][i]]=points.map(r=>scaled(r[field[k]],k)));return data;}
function line(points,key,name,color,width=3,mode='lines'){return{...coords(points),type:state.view==='3d'?'scatter3d':'scatter',mode,name,line:{color,width},marker:{color,size:mode.includes('markers')?7:3,symbol:'circle'},customdata:custom(points,key),hovertemplate:hover,showlegend:false,connectgaps:false};}
function selected(){return MODEL.pressure_choices[Number($('pressure').value)];}
function mixture(){const r=selected(),x=Number($('quality').value)/1000;return point(r.T_K,r.p_Pa,(1-x)*r.v_liquid_m3_kg+x*r.v_vapor_m3_kg,r.id,'mass mixture',x);}
function updateReadout(){const r=mixture();$('xValue').textContent=fmt(r[5],3);$('mixture').innerHTML='<span class="metric">'+fmt(r[2],6)+'</span> <small>m³/kg</small><br><span class="subtle">T = '+fmt(r[0],6)+' K · p = '+fmt(r[1],5)+' Pa</span>';}
function processTraces(){if(!$('process').checked)return[];const r=selected();const p=mixture();let path=[];for(let j=0;j<61;j++){let v=Math.exp(Math.log(r.v_liquid_m3_kg)+(Math.log(r.v_vapor_m3_kg)-Math.log(r.v_liquid_m3_kg))*j/60);path.push(point(r.T_K,r.p_Pa,v,r.id,'mass mixture',(v-r.v_liquid_m3_kg)/(r.v_vapor_m3_kg-r.v_liquid_m3_kg)));}const raw=Object.values(MODEL.references).filter(a=>a.source==='NISTIR 5078 Table 3'&&a.p_Pa===r.p_Pa&&a.T_K<=900&&!a.saturation_endpoint&&a.italic_metastable==='False'&&a.T_K>=273.16).sort((a,b)=>a.T_K-b.T_K);let before=raw.filter(a=>a.T_K<r.T_K).map(a=>point(a.T_K,a.p_Pa,a.v_m3_kg,a.id,'process'));let after=raw.filter(a=>a.T_K>r.T_K).map(a=>point(a.T_K,a.p_Pa,a.v_m3_kg,a.id,'process'));return[line([...before,...path,...after],'lv','定压过程','#f4edf5',5),line([p],'lv','当前混合物','#ffffff',5,'markers')];}
async function render(){if(state.busy){state.rerun=true;return;}state.busy=true;$('loading').classList.remove('hidden');updateReadout();try{const traces=[];for(const [key,s] of Object.entries(MODEL.surfaces)){if(!state.visible[key])continue;const color=PHASES[key][1],points=s.points;if(state.view==='3d'){traces.push({...coords(points),type:'mesh3d',i:s.triangles.map(t=>t[0]),j:s.triangles.map(t=>t[1]),k:s.triangles.map(t=>t[2]),name:PHASES[key][0],color,opacity:Number($('opacity').value)/100,flatshading:false,lighting:{ambient:.75,diffuse:.7,specular:.15,roughness:.8},customdata:custom(points,key),hovertemplate:hover,showlegend:false});}else{traces.push({...coords(points),type:'scattergl',mode:'markers',name:PHASES[key][0],marker:{size:['sl','sv','lv'].includes(key)?2:3,color,opacity:.35},customdata:custom(points,key),hovertemplate:hover,showlegend:false});}if($('raw').checked){let original=points.filter(r=>r[4].startsWith('published'));traces.push({...coords(original),type:state.view==='3d'?'scatter3d':'scattergl',mode:'markers',marker:{size:state.view==='3d'?2.5:4,color,opacity:1},customdata:custom(original,key),hovertemplate:hover,showlegend:false});}}
if($('boundaries').checked){for(const [kind,rows] of Object.entries(MODEL.equilibrium)){if(!state.visible[kind])continue;for(let endpoint of ['v1','v2']){let pts=rows.map(r=>point(r.T_K,r.p_Pa,r[endpoint],r.id,'published endpoint'));traces.push(line(pts,kind,PHASES[kind][0]+'边界',PHASES[kind][1],4));}}}
if($('triple').checked){const t=MODEL.triple;const pts=Array.from({length:70},(_,j)=>point(t.T_K,t.p_Pa,Math.exp(Math.log(t.v_liquid)+(Math.log(t.v_vapor)-Math.log(t.v_liquid))*j/69),t.source,'triple'));pts.push(point(t.T_K,t.p_Pa,t.v_ice,t.source,'triple'));traces.push(line(pts,'三相线','三相线','#ffe598',8));traces.push(line([point(t.T_K,t.p_Pa,t.v_ice,t.source,'published endpoint')],'三相线','冰端点','#ffe598',4,'markers'));}
if($('critical').checked){const c=MODEL.critical;let tr=line([point(c.T_K,c.p_Pa,c.v_m3_kg,c.source,'published endpoint')],'临界点','临界点','#ff657d',5,'markers');tr.marker.symbol='diamond';tr.marker.size=9;traces.push(tr);}
traces.push(...processTraces());const base={paper_bgcolor:'#0a1421',plot_bgcolor:'#0a1421',font:{family:'Microsoft YaHei UI, PingFang SC, Noto Sans CJK SC, sans-serif',color:'#c9dce8',size:12},margin:{l:12,r:15,t:10,b:12},showlegend:false,uirevision:state.view+'-'+$('preset').value+'-'+$('pscale').value+'-'+$('vscale').value,hoverlabel:{bgcolor:'#172b40',bordercolor:'#527189',font:{size:13,color:'#edf6ff'}},dragmode:state.view==='3d'?'orbit':'zoom'};if(state.view==='3d'){base.scene={xaxis:axis('v'),yaxis:axis('T'),zaxis:axis('p'),aspectmode:'manual',aspectratio:{x:1.3,y:1.25,z:1},camera:defaultCamera(),bgcolor:'#0a1421'};}else{const keys=state.view==='pt'?['T','p']:state.view==='pv'?['v','p']:['v','T'];base.xaxis=axis(keys[0]);base.yaxis=axis(keys[1]);base.margin={l:100,r:35,t:25,b:74};}
await Plotly.react('plot',traces,base,{responsive:true,displaylogo:false,scrollZoom:true,modeBarButtonsToRemove:['toImage'],toImageButtonOptions:{format:'png'}});$('rangeNote').textContent=PRESETS[$('preset').value].note;$('viewnote').textContent=state.view==='3d'?'拖动旋转 · 光标处滚轮缩放 · Shift 拖动平移 · 点击查看来源':'投影复用三维网格顶点 · 拖动框选放大 · 双击恢复 · 点击查看来源';}catch(error){$('viewnote').textContent='绘图失败：'+error.message;console.error(error);}finally{state.busy=false;$('loading').classList.add('hidden');if(state.rerun){state.rerun=false;render();}}}
function details(cd){if(!cd)return;const refs=cd[5].split(' | ').map(id=>MODEL.references[id]).filter(Boolean);$('details').innerHTML='<button id="closeDetails" aria-label="关闭详情">×</button><h3>'+esc(cd[3])+'</h3><div class="metric">'+fmt(cd[2],7)+' m³/kg</div><p>T = '+fmt(cd[0],7)+' K<br>p = '+fmt(cd[1],7)+' Pa<br>x = '+esc(cd[6])+'</p><p class="subtle">'+esc(cd[4])+'</p>'+refs.map(r=>'<strong>'+esc(r.source)+'</strong><div class="subtle">PDF 第 '+r.pdf_page+' 页 · '+esc(r.id)+'</div><pre>'+esc(JSON.stringify(r,null,2))+'</pre>').join('')+(refs.length?'':'<p class="subtle">'+esc(cd[5])+'</p>');$('details').classList.remove('hidden');$('closeDetails').onclick=()=>$('details').classList.add('hidden');}
function toast(message){$('toast').textContent=message;$('toast').classList.remove('hidden');setTimeout(()=>$('toast').classList.add('hidden'),3000);}
Object.entries(PHASES).forEach(([k,[name,color,en]])=>{const label=document.createElement('label');label.className='phase';label.innerHTML='<input type="checkbox" '+(state.visible[k]?'checked':'')+'><span class="dot" style="background:'+color+'"></span>'+name+'<small>'+en+'</small>';label.querySelector('input').onchange=e=>{state.visible[k]=e.target.checked;render();};$('layers').appendChild(label);});
MODEL.pressure_choices.forEach((r,i)=>{if(r.T_K>=647.096)return;const o=document.createElement('option');o.value=i;o.textContent=(r.p_Pa>=1e6?fmt(r.p_Pa/1e6,5)+' MPa':fmt(r.p_Pa/1000,5)+' kPa')+' · '+fmt(r.T_K,6)+' K';if(r.p_Pa===1e5)o.selected=true;$('pressure').appendChild(o);});
for(const id of ['pscale','vscale','preset','raw','boundaries','triple','critical','pressure','process'])$(id).onchange=()=>render();
let opacityFrame=null;
let opacityUpdating=false;
function updateOpacity(){
  if(opacityFrame!==null||opacityUpdating)return;
  opacityFrame=requestAnimationFrame(async()=>{
    opacityFrame=null;
    if(state.busy){updateOpacity();return;}
    const plot=$('plot');
    const ids=(plot.data||[]).flatMap((trace,i)=>trace.type==='mesh3d'?[i]:[]);
    if(!ids.length)return;
    const opacity=Number($('opacity').value)/100;
    opacityUpdating=true;
    try{await Plotly.restyle(plot,{opacity},ids);}
    finally{
      opacityUpdating=false;
      if(Number($('opacity').value)/100!==opacity)updateOpacity();
    }
  });
}
$('opacity').oninput=()=>{
  $('alphaValue').textContent=$('opacity').value+'%';
  updateOpacity();
};
$('quality').oninput=()=>{updateReadout();if(!$('process').checked)return;const plot=$('plot');if(!plot.data)return;const ids=plot.data.map((t,i)=>t.name==='当前混合物'?i:-1).filter(i=>i>=0);if(ids.length){let p=mixture(),c=coords([p]);const update={x:[c.x],y:[c.y],customdata:[custom([p],'lv')]};if(c.z)update.z=[c.z];Plotly.restyle(plot,update,ids);}};
document.querySelectorAll('[data-view]').forEach(btn=>btn.onclick=()=>{state.view=btn.dataset.view;document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b===btn));render();});
$('reset').onclick=()=>{if(state.view==='3d')Plotly.relayout('plot',{'scene.camera':defaultCamera()});else{const keys=state.view==='pt'?['T','p']:state.view==='pv'?['v','p']:['v','T'];Plotly.relayout('plot',{'xaxis.range':axis(keys[0]).range,'yaxis.range':axis(keys[1]).range});}};
// Plotly's built-in 3D wheel zoom moves only the eye, so it always zooms around
// the middle of the scene. Move both eye and center toward the cursor ray instead.
let wheelDelta=0,wheelPosition=null,wheelFrame=null,wheelUpdating=false;
function queueWheelZoom(){
  if(wheelFrame!==null||wheelUpdating)return;
  wheelFrame=requestAnimationFrame(async()=>{
    wheelFrame=null;
    if(state.busy||state.view!=='3d'){wheelDelta=0;return;}
    const plot=$('plot'),scene=plot._fullLayout?.scene?._scene;
    if(!scene?.glplot?.canvas){wheelDelta=0;return;}
    const rect=scene.glplot.canvas.getBoundingClientRect();
    const projection=scene.glplot.cameraParams.projection;
    if(!rect.width||!rect.height||!projection?.[0]||!projection?.[5]){wheelDelta=0;return;}
    const camera=scene.getCamera(),view=scene.glplot.cameraParams.view;
    const eye=camera.eye,center=camera.center;
    const distance=Math.hypot(eye.x-center.x,eye.y-center.y,eye.z-center.z);
    if(!distance){wheelDelta=0;return;}
    const x=2*(wheelPosition.x-rect.left)/rect.width-1;
    const y=1-2*(wheelPosition.y-rect.top)/rect.height;
    const anchor={};
    for(const [i,key] of ['x','y','z'].entries()){
      anchor[key]=center[key]+distance*(x*view[i*4]/projection[0]+y*view[i*4+1]/projection[5]);
    }
    const factor=Math.max(.05/distance,Math.min(100/distance,Math.exp(Math.max(-500,Math.min(500,wheelDelta))*.001)));
    wheelDelta=0;
    const move=v=>Object.fromEntries(['x','y','z'].map(key=>[key,anchor[key]+(v[key]-anchor[key])*factor]));
    wheelUpdating=true;
    try{await Plotly.relayout(plot,{'scene.camera':{eye:move(eye),center:move(center),up:camera.up,projection:camera.projection}});}
    finally{wheelUpdating=false;if(wheelDelta)queueWheelZoom();}
  });
}
$('plot').addEventListener('wheel',event=>{
  if(state.view!=='3d'||state.busy)return;
  event.preventDefault();
  event.stopImmediatePropagation();
  wheelDelta+=event.deltaY*(event.deltaMode===1?16:event.deltaMode===2?$('plot').clientHeight:1);
  wheelPosition={x:event.clientX,y:event.clientY};
  queueWheelZoom();
},{capture:true,passive:false});
$('sources').onclick=()=>$('sourceDialog').showModal();$('closeSources').onclick=()=>$('sourceDialog').close();$('inspectMix').onclick=()=>details(custom([mixture()],'lv')[0]);
$('animate').onclick=()=>{if(state.animation){clearInterval(state.animation);state.animation=null;$('animate').textContent='▶ 演示汽化';return;}$('process').checked=true;render();$('quality').value=0;$('animate').textContent='Ⅱ 暂停';state.animation=setInterval(()=>{const x=Number($('quality').value);$('quality').value=Math.min(1000,x+10);$('quality').oninput();if(x>=1000){clearInterval(state.animation);state.animation=null;$('animate').textContent='▶ 演示汽化';}},70);};
function exportTimestamp(){
  const d=new Date(),pad=n=>String(n).padStart(2,'0');
  return d.getFullYear()+pad(d.getMonth()+1)+pad(d.getDate())+'-'+pad(d.getHours())+pad(d.getMinutes())+pad(d.getSeconds());
}
$('export').onclick=async()=>{
  if(typeof window.showSaveFilePicker!=='function'){
    toast('请选择使用桌面版 Chrome 或 Edge 打开本页面，以选择 PNG 的保存位置');
    return;
  }
  const button=$('export');button.disabled=true;
  let writable=null;
  try{
    // Ask for a destination while the click still has user activation, before rendering.
    const handle=await window.showSaveFilePicker({
      id:'water-pvt-png',
      suggestedName:'water-pvt-'+state.view+'-'+exportTimestamp()+'.png',
      types:[{description:'PNG 图像',accept:{'image/png':['.png']}}],
      excludeAcceptAllOption:true
    });
    button.textContent='正在保存…';
    const data=await Plotly.toImage('plot',{format:'png',width:1600,height:1100});
    const bytes=Uint8Array.from(atob(data.split(',')[1]),c=>c.charCodeAt(0));
    writable=await handle.createWritable();
    await writable.write(new Blob([bytes],{type:'image/png'}));
    await writable.close();writable=null;
    toast('已保存：'+handle.name);
  }catch(e){
    if(writable)await writable.abort().catch(()=>{});
    if(e.name!=='AbortError')toast('导出失败：'+e.message);
  }
  finally{button.disabled=false;button.textContent='导出 PNG';}
};
$('exportData').onclick=()=>{const blob=new Blob([JSON.stringify(MODEL)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='water-pvt-model.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};
$('counts').textContent=Object.keys(MODEL.references).length.toLocaleString()+' 条可追溯表格记录 · 点击曲面查看详情';
render().then(()=>$('plot').on('plotly_click',event=>details(event.points?.[0]?.customdata)));
window.waterAtlas={state,model:MODEL,render,mixture};
