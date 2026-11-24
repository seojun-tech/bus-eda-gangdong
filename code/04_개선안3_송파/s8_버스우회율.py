# 동 짝마다 '갈아타지 않고 가는 가장 짧은 버스 경로'의 길이 / 직선거리 (2022에 있던 노선만, 경로는 2026 정류소 순서로 근사)
import pandas as pd, numpy as np
X='../../동단위_레이어/'
rs=pd.read_csv('서울시버스노선별정류소정보_20260902.csv',dtype={'노선명':str,'ARS_ID':str})
u22=pd.read_csv(X+'외부데이터/버스_노선별_정류장별_운행횟수_202204_평일주말중앙값.csv.gz',usecols=['노선명'],dtype=str).노선명.unique()
print('2026 노선', rs.노선명.nunique(), '그중 2022에도 있던 노선', len(set(rs.노선명)&set(u22)))
new26=sorted(set(rs[rs.ARS_ID.isin([])].노선명))
s=pd.read_csv(X+'캐시/정류장_행정동.csv'); s['hj']=s.hj.astype('Int64').astype(str); s['ARS']=s.ARS.astype(str).str.zfill(5)
rs['ARS']=rs.ARS_ID.str.zfill(5); rs=rs.merge(s,on='ARS',how='left')
rs=rs.sort_values(['ROUTE_ID','순번'])
def run(rs,tag):
    out={}
    for rid,t in rs.groupby('ROUTE_ID'):
        if not (t.hj.str[:5].eq('11740').any() and t.hj.str[:5].eq('11710').any()): continue
        x=t.X좌표.values; y=t.Y좌표.values; seg=np.r_[0,np.hypot(np.diff(x)*88.2,np.diff(y)*111.0)]; cum=seg.cumsum(); hj=t.hj.values; n=len(t); nm=t.노선명.iloc[0]
        idxA=[i for i in range(n) if str(hj[i]).startswith('11740')]; idxB=[i for i in range(n) if str(hj[i]).startswith('11710')]
        for i in idxA:
            for j in idxB:
                if j<=i: continue
                L=cum[j]-cum[i]; k=(hj[i],hj[j])
                if k not in out or L<out[k][0]: out[k]=(L,nm,j-i)
    R=pd.DataFrame([(a,b,*v) for (a,b),v in out.items()],columns=['o','d',tag+'_최단버스경로km',tag+'_노선',tag+'_정류장수'])
    return R
R22=run(rs[rs.노선명.isin(u22)],'y22'); R26=run(rs,'y26')
P=pd.read_csv('결과_동짝_이동vs버스연결.csv',dtype={'o':str,'d':str})
P=P.merge(R22,on=['o','d'],how='left').merge(R26,on=['o','d'],how='left')
P['y22_우회율']=P.y22_최단버스경로km/P.중심거리km; P['y26_우회율']=P.y26_최단버스경로km/P.중심거리km
P.to_csv('결과_동짝_이동vs버스연결_우회율.csv',index=False)
G=P[(P.중심거리km>=2.5)&(~P.지하철바로)].sort_values('양방향',ascending=False)
print(G[['강동동','송파동','양방향','강동→송파_7_9시','중심거리km','바로가는운행_일','y22_최단버스경로km','y22_우회율','y22_노선','y22_정류장수','y26_노선','y26_우회율']].head(30).round(2).to_string())
w=G.dropna(subset=['y22_우회율']); print('수요가중 우회율 2022', round(np.average(w.y22_우회율,weights=w.양방향),2))
