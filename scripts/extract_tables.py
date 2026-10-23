"""Position-aware extraction of published PDF columns. No property equations."""
from pathlib import Path
import csv, json, re
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'processed_data'

def cell(chars, x0, x1, y, tol=2.4):
    selected = [c for c in chars if x0 <= (c['x0']+c['x1'])/2 < x1 and abs(c['top']-y)<tol]
    return ''.join(c['text'] for c in sorted(selected, key=lambda c:c['x0'])).replace(' ', '').replace('*','')

def rows_at(chars, x0, x1, ymin, ymax):
    ys=[]
    for c in sorted(chars,key=lambda c:c['top']):
        if x0<=c['x0']<x1 and ymin<c['top']<ymax and (not ys or c['top']-ys[-1]>2):
            ys.append(c['top'])
    return ys

def save(name, rows):
    with (OUT/name).open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(name,len(rows),flush=True)

def saturation(table):
    result=[]
    with pdfplumber.open(ROOT/f'raw_data/nist_table{table}.pdf') as pdf:
        for page_no,page in enumerate(pdf.pages,1):
            chars=page.chars
            # Table 2 exchanges p and t, with the rest shifted 6.5 pt to the right.
            bounds=([70,101,150,185,230,266,303,339,380,413,446,488,531] if table==1 else
                    [70,120,157,191,237,273,310,346,387,420,453,495,537])
            if table==2 and page_no>1:
                bounds=[70,103,144,179,222,260,296,333,370,405,442,478,532]
            for y in rows_at(chars,bounds[0],bounds[1],122,741):
                values=[cell(chars,a,b,y) for a,b in zip(bounds,bounds[1:])]
                if values[0] in ['tc','t']:
                    values[0]='373.946' if table==1 else '22.064'
                if table==2 and values[0] in ['pc','p']:
                    values[0]='22.064'
                if table==2 and values[1] in ['tc','t']:
                    values[1]='373.946'
                try:
                    v=[float(x.replace('Pa','')) for x in values]
                except ValueError:
                    continue
                T,p=(v[0]+273.15,v[1]*1e6) if table==1 else (v[1]+273.15,v[0] if 'Pa' in values[0] else v[0]*1e6)
                result.append(dict(id=f'N{table}-p{page_no}-r{len(result)+1}',T_K=T,p_Pa=p,
                                   rho_liquid_kg_m3=v[2],rho_vapor_kg_m3=v[3],
                                   v_liquid_m3_kg=v[10]*1e-3,v_vapor_m3_kg=v[11]*1e-3,
                                   source=f'NISTIR 5078 Table {table}',pdf_page=page_no,
                                   original_first=values[0],original_second=values[1]))
    return result

def fluid():
    result=[]
    with pdfplumber.open(ROOT/'raw_data/nist_table3.pdf') as pdf:
        for page_no,page in enumerate(pdf.pages,1):
            chars=page.chars
            header=page.crop((60,95,540,114)).extract_text()
            pressures=[float(x)*1e6 for x in re.findall(r'([\d.]+)\s+MPa',header)]
            temps=[float(x)+273.15 for x in re.findall(r'=\s*([\d.]+)',header)]
            assert len(pressures)==3,(page_no,header)
            for y in rows_at(chars,208,230,130,735):
                ts=cell(chars,207,231,y)
                sat='(L)' in ts or '(V)' in ts
                try:
                    T=None if sat else float(ts)+273.15
                except ValueError:
                    continue
                for col,p in enumerate(pressures):
                    # The first pressure block shares the temperature column in block 2.
                    offset=[0,161.28,323.28][col]
                    vs=cell(chars,69+offset,105+offset,y)
                    rs=cell(chars,105+offset,140+offset,y)
                    try: v,rho=float(vs)*1e-3,float(rs)
                    except ValueError: continue
                    italic=any('Italic' in c['fontname'] for c in chars if 69+offset<c['x0']<140+offset and abs(c['top']-y)<1.6)
                    result.append(dict(id=f'N3-p{page_no}-c{col+1}-r{len(result)+1}',
                                       T_K=temps[col] if sat else T,p_Pa=p,v_m3_kg=v,rho_kg_m3=rho,
                                       saturation_endpoint=('liquid' if '(L)' in ts else 'vapor') if sat else '',
                                       original_v_cm3_g=vs,italic_metastable=italic,
                                       source='NISTIR 5078 Table 3',pdf_page=page_no))
            print('Table 3 page',page_no,flush=True)
    return result

def ice():
    with pdfplumber.open(ROOT/'raw_data/feistel_wagner_2006.pdf') as pdf:
        densities=[]
        pg=pdf.pages[19]; chars=pg.chars
        for y in rows_at(chars,50,85,105,398):
            T=float(cell(chars,50,85,y))
            for p,a,b in zip([0,101325,50e6,100e6,150e6,200e6],
                             [110,190,275,355,437,519],[163,245,326,408,490,571]):
                value=cell(chars,a,b,y)
                try: rho=float(value)
                except ValueError: continue
                densities.append(dict(id=f'F11-{T:g}-{p:g}',T_K=T,p_Pa=p,rho_kg_m3=rho,v_m3_kg=1/rho,
                                      source='Feistel & Wagner (2006) Table 11',pdf_page=20))
        eq=[]
        for index,table,ymin,ymax in [(24,19,470,741),(25,20,108,421)]:
            pg=pdf.pages[index]
            # PDF embeds MathematicalPi-One glyph 1 as plus and 2 as minus.
            for c in pg.chars:
                if 'MathematicalPi-One' in c['fontname']:
                    c['text']={'1':'+','2':'-','—':'-'}.get(c['text'],c['text'])
            bounds=([55,125,180,250,310,380,445,500,560] if table==19 else
                    [55,102,162,226,302,364,433,498,560])
            for y in rows_at(pg.chars,55,100,ymin,ymax):
                values=[cell(pg.chars,a,b,y) for a,b in zip(bounds,bounds[1:])]
                try: vals=list(map(float,values))
                except ValueError: continue
                T,p,vi,dv=vals[:4]
                if not 130<=T<=274: continue
                p=p*1e6 if table==19 else p
                eq.append(dict(id=f'F{table}-{T:g}',kind='sl' if table==19 else 'sv',T_K=T,p_Pa=p,
                               v_ice_m3_kg=vi*1e-6,delta_v_m3_kg=dv*1e-6,v_other_m3_kg=(vi+dv)*1e-6,
                               original_v_cm3_kg=values[2],original_delta_v_cm3_kg=values[3],
                               source=f'Feistel & Wagner (2006) Table {table}',pdf_page=index+1))
        return densities,eq

def special_states():
    with pdfplumber.open(ROOT/'raw_data/feistel_wagner_2006.pdf') as pdf:
        pg=pdf.pages[24]
        for c in pg.chars:
            if 'MathematicalPi-One' in c['fontname']:
                c['text']={'1':'+','2':'-'}.get(c['text'],c['text'])
        result=[]
        for name,a,b in [('Triple',175,300),('NormalMelting',330,465)]:
            result.append(dict(id='F18-'+name,p_Pa=float(cell(pg.chars,a,b,101.3)),T_K=float(cell(pg.chars,a,b,111.2)),
                               v_m3_kg=float(cell(pg.chars,a,b,130)),source='Feistel & Wagner (2006) Table 18',pdf_page=25))
        return result

def main():
    OUT.mkdir(exist_ok=True)
    a,b=saturation(1),saturation(2)
    assert len(a)==375 and len(b)>200,(len(a),len(b))
    save('saturation_temperature.csv',a);save('saturation_pressure.csv',b)
    f=fluid();save('fluid_table3.csv',f)
    d,e=ice();save('ice_density.csv',d);save('ice_equilibria.csv',e)
    save('special_states.csv',special_states())
    assert len(d)==164,(len(d))
    assert len([x for x in e if x['kind']=='sl'])==26
    assert len([x for x in e if x['kind']=='sv'])==30
    (OUT/'extraction_summary.json').write_text(json.dumps(dict(table1=len(a),table2=len(b),table3=len(f),table11=len(d),table18=2,table19=26,table20=30),indent=2),encoding='utf-8')

if __name__=='__main__':main()
