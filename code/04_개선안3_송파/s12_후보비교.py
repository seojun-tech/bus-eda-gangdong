# 경로 후보 여러 개를 같은 기준으로 평가: 닿는 동(400m), 짧아지는 이동, 1km당 이동, 지금 버스 대비 길이
import pandas as pd, numpy as np, heapq, json
X='../../동단위_레이어/'
rs=pd.read_csv('서울시버스노선별정류소정보_20260902.csv',dtype={'노선명':str,'ARS_ID':str}); rs['ARS']=rs.ARS_ID.str.zfill(5)
u22=set(pd.read_csv(X+'외부데이터/버스_노선별_정류장별_운행횟수_202204_평일주말중앙값.csv.gz',usecols=['노선명'],dtype=str).노선명)
pos=rs.drop_duplicates('ARS').set_index('ARS')[['정류소명','X좌표','Y좌표']]
km=lambda a,b: float(np.hypot((pos.X좌표[a]-pos.X좌표[b])*88.2,(pos.Y좌표[a]-pos.Y좌표[b])*111.0))
E={}
for rid,t in rs[rs.노선명.isin(u22)].sort_values(['ROUTE_ID','순번']).groupby('ROUTE_ID'):
    a=t.ARS.values
    for i in range(len(a)-1):
        if a[i]==a[i+1]: continue
        w=km(a[i],a[i+1])
        if w>2.0: continue
        for x,y in ((a[i],a[i+1]),(a[i+1],a[i])): E.setdefault(x,{}); E[x][y]=min(w,E[x].get(y,9e9))
def path(src,dst):
    D={s:0 for s in src}; prev={}; h=[(0,s) for s in src]; dst=set(dst)
    while h:
        d,x=heapq.heappop(h)
        if x in dst:
            p=[x]
            while p[-1] in prev: p.append(prev[p[-1]])
            return d,p[::-1]
        if d>D.get(x,9e9): continue
        for y,w in E.get(x,{}).items():
            if d+w<D.get(y,9e9): D[y]=d+w; prev[y]=x; heapq.heappush(h,(d+w,y))
W={'강동공영차고지':['25101','25341','25102'],'상일동역':['25133','25131','25523','25166','25134','25132','25165','25740'],'고덕역':['25139','25140','25518','25528'],
   '명일역':['25234','25233','25232','25235','25546'],'굽은다리역':['25782','25236','25348','25349','25237','25781'],'길동역':['25240','25241'],
   '둔촌동역':['25728','25247','25246','25727'],'중앙보훈병원역':['25330','25302','25303','25331','25539','25682'],'올림픽공원역':['24244','24245'],
   '오금역':['24515','24338','24249','24767','24369','24523','24766','24339'],'가락시장역':['24009','24380','24363','24010','24385','24444'],
   '문정역':['24331','24547','24330'],'문정법조단지':['24013'],'장지공영차고지':['24446','24447']}
V={'A 기본(둔촌동역)':['강동공영차고지','상일동역','고덕역','명일역','굽은다리역','길동역','둔촌동역','올림픽공원역','오금역','문정역','문정법조단지'],
   'B 보훈병원 경유':['강동공영차고지','상일동역','고덕역','명일역','굽은다리역','길동역','중앙보훈병원역','둔촌동역','올림픽공원역','오금역','문정역','문정법조단지'],
   'C 가락시장역 경유':['강동공영차고지','상일동역','고덕역','명일역','굽은다리역','길동역','둔촌동역','올림픽공원역','오금역','가락시장역','문정역','문정법조단지'],
   'D 기본+장지차고지 종점':['강동공영차고지','상일동역','고덕역','명일역','굽은다리역','길동역','둔촌동역','올림픽공원역','오금역','문정역','문정법조단지','장지공영차고지']}
lp=pd.read_csv(X+'외부데이터/행정동_생활인구_202204_평일주말_시간대평균.csv',dtype=str).drop_duplicates('행정동코드'); nm=dict(zip(lp.행정동코드,lp.구_행정동)); nm.update({'1174052500':'강동구 상일제1동','1174052600':'강동구 상일제2동'})
s=pd.read_csv(X+'캐시/정류장_행정동.csv'); s['ARS']=s.ARS.astype(str).str.zfill(5); s['hj']=s.hj.astype('Int64').astype(str)
allst=rs.drop_duplicates('ARS')[['ARS','X좌표','Y좌표']].merge(s,on='ARS'); allst['동']=allst.hj.map(nm)
P=pd.read_csv('결과_동짝_이동vs버스연결_우회율.csv',dtype={'o':str,'d':str})
res=[]; keep={}
for k,wp in V.items():
    seq=[]; cur=W[wp[0]]
    for nxt in wp[1:]:
        d,p=path(cur,W[nxt]); seq+= p if not seq else p[1:]; cur=[p[-1]]
    st=pd.DataFrame({'ARS':seq}); st['이름']=st.ARS.map(pos.정류소명); st['x']=st.ARS.map(pos.X좌표); st['y']=st.ARS.map(pos.Y좌표)
    st['누적km']=np.r_[0,np.hypot(np.diff(st.x)*88.2,np.diff(st.y)*111.0)].cumsum()
    reach={}
    for _,r in st.iterrows():
        dd=np.hypot((allst.X좌표-r.x)*88.2,(allst.Y좌표-r.y)*111.0)
        for dn in allst[dd<=0.4].동.dropna().unique():
            if dn[:3] in ('강동구','송파구'): reach[dn]=min(reach.get(dn,99),r.누적km)
    cov=P[P.강동동.isin(reach)&P.송파동.isin(reach)].copy()
    cov['초안km']=[abs(reach[b]-reach[a]) for a,b in zip(cov.강동동,cov.송파동)]
    cov['혜택']=(~cov.지하철바로)&(cov.중심거리km>=2.0)&((cov.y22_최단버스경로km.isna())|(cov.y22_최단버스경로km-cov.초안km>=1.5))
    c=cov[cov.혜택]; w=c.dropna(subset=['y22_최단버스경로km'])
    L=st.누적km.iloc[-1]
    res.append(dict(후보=k,길이km=round(L,1),정류장=len(st),혜택짝=len(c),하루이동=round(c.양방향.sum()),아침7_9=round(c['강동→송파_7_9시'].sum()),
       km당이동=round(c.양방향.sum()/L),지금버스km=round(np.average(w.y22_최단버스경로km,weights=w.양방향),1),초안km=round(np.average(w.초안km,weights=w.양방향),1),
       버스없던짝이동=round(c[c.y22_최단버스경로km.isna()].양방향.sum()),굴곡=round(L/np.hypot((st.x.iloc[-1]-st.x.iloc[0])*88.2,(st.y.iloc[-1]-st.y.iloc[0])*111.0),2)))
    keep[k]=dict(stops=st.to_dict('records'),pairs=c[['강동동','송파동','양방향','초안km','y22_최단버스경로km']].to_dict('records'))
R=pd.DataFrame(res); print(R.to_string()); R.to_csv('결과_경로후보_비교.csv',index=False)
json.dump(keep,open('결과_경로후보_상세.json','w'),ensure_ascii=False)
