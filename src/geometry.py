"""Geometric reconstruction from tables. Does not contain thermodynamic equations."""
import math
import numpy as np
from scipy.spatial import Delaunay

TC, PC, TT, PT = 647.096, 22.064e6, 273.16, 611.657

class Boundaries:
    def __init__(self, sat, ice):
        self.sat=sorted(sat,key=lambda r:r['T_K'])
        self.sl=sorted([r for r in ice if r['kind']=='sl' and r['p_Pa']<=210e6],key=lambda r:r['p_Pa'])
        self.sv=sorted([r for r in ice if r['kind']=='sv'],key=lambda r:r['T_K'])

    def melt_T(self,p):
        return float(np.interp(math.log10(p),[math.log10(r['p_Pa']) for r in self.sl],[r['T_K'] for r in self.sl]))

    def saturation_T(self,p):
        return float(np.interp(math.log10(p),[math.log10(r['p_Pa']) for r in self.sat],[r['T_K'] for r in self.sat]))

    def sublimation_p(self,T):
        return 10**float(np.interp(T,[r['T_K'] for r in self.sv],[math.log10(r['p_Pa']) for r in self.sv]))

    def phase(self,T,p):
        # Conservative ice cap avoids uncertain boundaries to other ice polymorphs.
        if T<TT-1e-7:
            if T<130 or p>100e6:return None
            if p<self.sublimation_p(T)*(1-2e-5):return 'vapor'
            if T<=self.melt_T(p)+1e-7:
                return 'ice' if p<=50e6*(1+1e-8) else None
            return 'liquid' if p>=PT else None
        if T>=TC and p>=PC:return 'supercritical'
        if p>=PC:return 'liquid'
        return 'liquid' if T<self.saturation_T(p) else 'vapor'

def triangulate(points,phase,boundaries):
    """Delaunay in (T/100, log10 p), with explicit boundary and gap rejection."""
    uv=np.array([[r[0]/100,math.log10(r[1])] for r in points])
    # Same T,p can only have one v inside a single phase; endpoint rows take precedence.
    _,indices=np.unique(np.round(uv,8),axis=0,return_index=True)
    points=[points[i] for i in sorted(indices)]
    uv=np.array([[r[0]/100,math.log10(r[1])] for r in points])
    tri=Delaunay(uv).simplices
    kept=[]
    weights=[(a/8,b/8,1-(a+b)/8) for a in range(9) for b in range(9-a)]
    for ids in tri:
        # A curved equilibrium line alone must never invent a single-phase sheet.
        if not any(points[i][4]=='published table' for i in ids):continue
        vertices=uv[ids]
        if np.ptp(vertices[:,0])>1.01:continue # no temperature edge >101 K
        if np.ptp(vertices[:,1])>(3 if phase=='ice' else .65):continue
        okay=True
        for w in weights:
            q=np.array(w)@vertices
            predicted=boundaries.phase(q[0]*100,10**q[1])
            # Vertices on an equilibrium boundary are valid for either adjacent phase.
            if max(w)>1-1e-8:continue
            if predicted!=phase:
                okay=False;break
        if okay:kept.append([int(i) for i in ids])
    return points,kept

def coexistence(rows,kind):
    """Ruled strip; interpolated anchors and mass fractions explicitly tagged."""
    rows=sorted(rows,key=lambda r:r['T_K'])
    anchors=[]
    for a,b in zip(rows,rows[1:]):
        for f in [0,.25,.5,.75]:
            anchors.append(dict(T=(1-f)*a['T_K']+f*b['T_K'],
                                p=10**((1-f)*math.log10(a['p_Pa'])+f*math.log10(b['p_Pa'])),
                                v1=(1-f)*a['v1']+f*b['v1'],v2=(1-f)*a['v2']+f*b['v2'],
                                ref=a['id'] if f==0 else a['id']+' | '+b['id'],original=f==0))
    last=rows[-1]
    anchors.append(dict(T=last['T_K'],p=last['p_Pa'],v1=last['v1'],v2=last['v2'],ref=last['id'],original=True))
    pts=[];tri=[];n=25
    for a in anchors:
        for j in range(n):
            # Geometric *sampling* in v only; every point still obeys mass conservation.
            v=a['v1']+(a['v2']-a['v1'])*j/(n-1) if kind=='sl' else math.exp((1-j/(n-1))*math.log(a['v1'])+j/(n-1)*math.log(a['v2']))
            if a['v1']==a['v2']:v=a['v1']
            x=(v-a['v1'])/(a['v2']-a['v1']) if a['v1']!=a['v2'] else None
            tag='published endpoint' if a['original'] and j in [0,n-1] else 'mass mixture' if a['original'] else 'geometric interpolation + mixture'
            pts.append([a['T'],a['p'],v,a['ref'],tag,x])
    for i in range(len(anchors)-1):
        for j in range(n-1):
            k=i*n+j;tri.extend([[k,k+1,k+n],[k+1,k+n+1,k+n]])
    # The critical row is one vertex, not 25 coincident vertices / zero-area faces.
    unique=[];lookup={};remap={}
    for i,r in enumerate(pts):
        key=tuple(r[:3])
        if key not in lookup:
            lookup[key]=len(unique);unique.append(r)
        remap[i]=lookup[key]
    faces=[[remap[i] for i in face] for face in tri]
    faces=[face for face in faces if len(set(face))==3]
    return unique,faces
