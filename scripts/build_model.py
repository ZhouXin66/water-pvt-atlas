from pathlib import Path
import csv,json,sys,math
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.geometry import Boundaries, triangulate, coexistence, TC,PC,TT,PT

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'processed_data'

def read(name):
    with (OUT/name).open(encoding='utf-8-sig') as f:
        rows=list(csv.DictReader(f))
    for r in rows:
        for k in r:
            if k.endswith(('_K','_Pa','_kg','_m3')) or k in ['pdf_page']:
                try:r[k]=float(r[k])
                except ValueError:pass
    return rows

def main():
    sat=read('saturation_temperature.csv');satp=read('saturation_pressure.csv')
    fluid=read('fluid_table3.csv');ice=read('ice_density.csv');eq=read('ice_equilibria.csv')
    # Preserve printed rounding in CSV. A separate documented geometric join uses exact T,p.
    for r in eq:
        r['printed_p_Pa']=r['p_Pa']
        if r['T_K']==TT:r['p_Pa']=PT
        if r['kind']=='sl' and r['T_K']==273.152519:r['p_Pa']=101325.
    sat[0]['printed_p_Pa']=sat[0]['p_Pa'];sat[0]['p_Pa']=PT
    b=Boundaries(sat,eq)
    groups={k:[] for k in ['ice','liquid','vapor','supercritical']};rejected=[];refs={}
    allrows=sat+satp+fluid+ice+eq+read('special_states.csv')
    for r in allrows:refs[r['id']]=r
    for r in fluid+ice:
        T,p=r['T_K'],r['p_Pa']
        reason=''
        if r.get('italic_metastable')=='True':reason='NIST italic metastable liquid'
        elif p<=0:reason='zero pressure: outside positive equilibrium/log domain'
        elif T<130:reason='ice low-temperature polymorph uncertainty; display cap T>=130 K'
        elif T>1273.15:reason='NIST explicitly identifies T>1000 C as extrapolation'
        elif p>100e6:reason='project conservative fluid cap p<=100 MPa'
        elif r in ice and p>50e6:reason='project conservative ice Ih cap p<=50 MPa'
        phase=b.phase(T,p) if not reason else None
        if not reason and phase is None:reason='uncovered solid polymorph or unsupported stability domain'
        if r in ice and phase!='ice' and not reason:reason='outside conservative stable Ih domain'
        if reason:
            rejected.append(dict(id=r['id'],reason=reason));continue
        endpoint=r.get('saturation_endpoint')
        if endpoint:phase=endpoint
        groups[phase].append([T,p,r['v_m3_kg'],r['id'],'published table',None])
    # Exact boundary endpoints are vertices, never interpolate across the coexistence interval.
    for r in sat:
        for phase,key in [('liquid','v_liquid_m3_kg'),('vapor','v_vapor_m3_kg')]:
            groups[phase].append([r['T_K'],r['p_Pa'],r[key],r['id'],'published endpoint',None])
    for r in eq:
        if r['kind']=='sl' and r['p_Pa']>100e6:continue
        for phase,key in [('ice','v_ice_m3_kg'),('liquid' if r['kind']=='sl' else 'vapor','v_other_m3_kg')]:
            if phase=='ice' and r['p_Pa']>50e6:continue
            groups[phase].append([r['T_K'],r['p_Pa'],r[key],r['id'],'published endpoint',None])
    surfaces={}
    for phase,pts in groups.items():
        pts,tri=triangulate(pts,phase,b)
        surfaces[phase]=dict(points=pts,triangles=tri)
        print(phase,len(pts),len(tri),flush=True)
    equilibrium={}
    for kind in ['lv','sl','sv']:
        rows=[]
        for r in (sat if kind=='lv' else [e for e in eq if e['kind']==kind and (kind!='sl' or e['p_Pa']<=100e6)]):
            rows.append(dict(id=r['id'],T_K=r['T_K'],p_Pa=r['p_Pa'],
                             v1=r['v_liquid_m3_kg'] if kind=='lv' else r['v_ice_m3_kg'],
                             v2=r['v_vapor_m3_kg'] if kind=='lv' else r['v_other_m3_kg']))
        equilibrium[kind]=rows
        pts,tri=coexistence(rows,kind);surfaces[kind]=dict(points=pts,triangles=tri)
    # One common triple line: two printed sources differ by rounding (< 6 ppm).
    vi=next(r['v_ice_m3_kg'] for r in eq if r['kind']=='sl' and r['T_K']==TT)
    triple=dict(T_K=TT,p_Pa=PT,v_ice=vi,v_liquid=sat[0]['v_liquid_m3_kg'],v_vapor=sat[0]['v_vapor_m3_kg'],
                source='F19-273.16 | N1-p1-r1 | F18-Triple')
    model=dict(version=1,surfaces=surfaces,equilibrium=equilibrium,pressure_choices=satp,
               references=refs,triple=triple,critical=dict(T_K=TC,p_Pa=PC,v_m3_kg=sat[-1]['v_liquid_m3_kg'],source=sat[-1]['id']))
    (OUT/'model.json').write_text(json.dumps(model,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    (OUT/'excluded_rows.json').write_text(json.dumps(rejected,ensure_ascii=False,indent=2),encoding='utf-8')
    stats={k:dict(vertices=len(s['points']),triangles=len(s['triangles'])) for k,s in surfaces.items()}
    (OUT/'model_summary.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
    print('excluded',len(rejected))

if __name__=='__main__':main()
