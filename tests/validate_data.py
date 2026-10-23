"""Scientific consistency / provenance checks, not equation-of-state validation."""
from pathlib import Path
import csv,json,hashlib,math

ROOT=Path(__file__).resolve().parents[1]
def read(name):return list(csv.DictReader((ROOT/'processed_data'/name).open(encoding='utf-8-sig')))
def main():
    checks=[]
    def check(condition,message):
        assert condition,message
        checks.append(message)
    manifest=json.loads((ROOT/'raw_data/manifest.json').read_text(encoding='utf-8'))
    for s in manifest['sources']:
        check(hashlib.sha256((ROOT/'raw_data'/s['file']).read_bytes()).hexdigest()==s['sha256'],'SHA256 '+s['file'])
    sat=read('saturation_temperature.csv');satp=read('saturation_pressure.csv');fluid=read('fluid_table3.csv');ice=read('ice_density.csv');eq=read('ice_equilibria.csv')
    check([len(sat),len(satp),len(fluid),len(ice),len(eq)]==[375,272,9524,164,56],'All extracted table row counts')
    errors=[abs(float(r['v_m3_kg'])*float(r['rho_kg_m3'])-1) for r in fluid]
    check(max(errors)<6e-5,'Table 3 v*rho agrees within printed rounding (<6e-5)')
    for data in [sat,satp]:
        check(all(abs(float(r['v_liquid_m3_kg'])*float(r['rho_liquid_kg_m3'])-1)<8e-5 and abs(float(r['v_vapor_m3_kg'])*float(r['rho_vapor_kg_m3'])-1)<2e-4 for r in data),'Saturation density/volume unit consistency')
        check(abs(float(data[-1]['T_K'])-647.096)<1e-8 and float(data[-1]['p_Pa'])==22.064e6,'Published critical T,p')
        check(float(data[-1]['v_liquid_m3_kg'])==float(data[-1]['v_vapor_m3_kg'])==.0031056,'Critical endpoints merge (printed v precision)')
    sl=[r for r in eq if r['kind']=='sl'];sv=[r for r in eq if r['kind']=='sv']
    check(all(float(r['delta_v_m3_kg'])<0 for r in sl),'Table 19: melting volume is negative')
    check(all(float(a['T_K'])>float(b['T_K']) and float(a['p_Pa'])<float(b['p_Pa']) for a,b in zip(sl,sl[1:])),'Melting dp/dT < 0')
    check(float(sv[-1]['p_Pa'])==1.2004e-8,'Table 20 scientific notation: 130 K pressure = 1.2004e-8 Pa')
    check(abs(float(sv[-1]['v_other_m3_kg'])-4.9982e12)<1,'Table 20: cm3/kg -> m3/kg, positive exponent')
    check(abs(float(sl[0]['v_other_m3_kg'])-.00100021)<1e-12,'Table 19: v_liquid = v_ice + delta_v')
    special=read('special_states.csv')
    check(float(special[0]['p_Pa'])==611.657 and float(special[0]['T_K'])==273.16,'Table 18 independently extracted triple state')
    check(float(special[0]['v_m3_kg'])==.0010908581273664,'Table 18 precise ice triple specific volume')
    m=json.loads((ROOT/'processed_data/model.json').read_text(encoding='utf-8'))
    check(m['triple']['T_K']==273.16 and m['triple']['p_Pa']==611.657,'Triple line exact T,p join')
    check(len([r for r in m['surfaces']['lv']['points'] if r[0]==647.096])==1,'Exactly one critical apex vertex')
    for name,s in m['surfaces'].items():
        pts=s['points'];check(bool(s['triangles']),name+' has actual triangular faces')
        check(all(math.isfinite(r[i]) and r[i]>0 for r in pts for i in [0,1,2]),name+' finite positive physical coordinates')
        check(all(0<=i<len(pts) for t in s['triangles'] for i in t),name+' valid mesh indices')
        check(all(len(set(t))==3 for t in s['triangles']),name+' no collapsed triangle indices')
        if name in ['sl','sv','lv']:
            check(all(r[5] is None or -1e-8<=r[5]<=1+1e-8 for r in pts),name+' mass fraction bounds')
            check(len(set(tuple(r[:3]) for r in pts))==len(pts),name+' unique geometric vertices (critical apex welded)')
            for r in pts:
                if r[5] is None:continue
                ids=r[3].split(' | ')
                parents=[m['references'][i] for i in ids]
                lo,hi=parents[0],parents[-1]
                f=0 if len(parents)==1 else (r[0]-lo['T_K'])/(hi['T_K']-lo['T_K'])
                v1=(1-f)*lo['v_liquid_m3_kg']+f*hi['v_liquid_m3_kg'] if name=='lv' else (1-f)*lo['v_ice_m3_kg']+f*hi['v_ice_m3_kg']
                v2=(1-f)*lo['v_vapor_m3_kg']+f*hi['v_vapor_m3_kg'] if name=='lv' else (1-f)*lo['v_other_m3_kg']+f*hi['v_other_m3_kg']
                assert math.isclose(r[2],(1-r[5])*v1+r[5]*v2,rel_tol=1e-10,abs_tol=1e-14),(name,r)
        if name=='ice':check(max(r[1] for r in pts)<=50e6 and min(r[0] for r in pts)>=130,'Conservative ice Ih display domain')
        if name in ['ice','liquid','vapor','supercritical']:
            check(all(any(pts[i][4]=='published table' for i in tri) for tri in s['triangles']),name+' cannot form a single-phase face from equilibrium-line vertices alone')
    for r in m['references'].values():check(bool(r['source']) and r['pdf_page']>0,'provenance:'+r['id'])
    for r in m['pressure_choices'][:-1]:
        for x in [0,.001,.5,1]:
            v=(1-x)*r['v_liquid_m3_kg']+x*r['v_vapor_m3_kg']
            check(r['v_liquid_m3_kg']-1e-12<=v<=r['v_vapor_m3_kg']+1e-12,'mixture:'+r['id'])
    report=dict(status='PASS',checks=len(checks),max_table3_density_volume_relative_error=max(errors),rows=dict(table1=len(sat),table2=len(satp),table3=len(fluid),table11=len(ice),table19=len(sl),table20=len(sv)),notes=['Printed table precision, not EOS precision','No accuracy claim for geometric interpolation','Conservative gaps intentionally retained'])
    (ROOT/'processed_data/validation_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
