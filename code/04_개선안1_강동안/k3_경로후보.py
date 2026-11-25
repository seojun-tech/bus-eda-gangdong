# 강동 안 경로 후보 비교(송파 s12와 같은 방식): 2022에 버스가 다니던 정류장 연결만 이어 붙인 최단경로, 400m 안 동, 짧아지는 강동 안 이동
import pandas as pd, numpy as np, heapq, json
X='../../동단위_레이어/'; S='../송파이동_1107/'
rs=pd.read_csv(S+'서울시버스노선별정류소정보_20260902.csv',dtype={'노선명':str,'ARS_ID':str}); rs['ARS']=rs.ARS_ID.str.zfill(5)
u22=set(pd.read_csv(X+'외부데이터/버스_노선별_정류장별_운행횟수_202204_평일주말중앙값.csv.gz',usecols=['노선명'],dtype=str).노선명)
import re
u22={r for r in u22 if not re.search('[가-힣]',r) or r.startswith('강동')}  # 경기 노선(번호 겹침) 제외
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
W={'천호역':['25161','25162'],'암사역':['25155','25156','25571','25602'],'서원마을':['25586'],'암사3동주민센터':['25147','25148'],
   '고덕역':['25139','25140','25518','25528'],'상일동역':['25133','25134','25131','25132','25165','25166','25523','25740'],
   '비즈밸리':['25291','25292'],'리엔파크1단지':['25103','25104','25526'],'강동공영차고지':['25101','25341','25102'],'명일역':['25234','25233','25232','25235','25546']}
V={'A 기존 초안(암사3 가로질러 역 잇기)':['천호역','암사역','암사3동주민센터','고덕역','상일동역','비즈밸리'],
   'B A + 서원마을 들르기':['천호역','암사역','서원마을','암사3동주민센터','고덕역','상일동역','비즈밸리'],
   'C 북쪽 강변(서원마을→비즈밸리 바로)':['천호역','암사역','서원마을','비즈밸리','상일동역'],
   'D 남쪽(명일역 경유)':['천호역','암사역','암사3동주민센터','명일역','고덕역','상일동역','비즈밸리'],
   'D1 명일역 경유, 고덕역→비즈밸리→상일동역':['천호역','암사역','암사3동주민센터','명일역','고덕역','비즈밸리','상일동역'],
   'D2 명일역 경유, 상일동역→리엔파크→비즈밸리':['천호역','암사역','암사3동주민센터','명일역','고덕역','상일동역','리엔파크1단지','비즈밸리']}
lp=pd.read_csv(X+'외부데이터/행정동_생활인구_202204_평일주말_시간대평균.csv',dtype=str).drop_duplicates('행정동코드'); nm=dict(zip(lp.행정동코드,lp.구_행정동)); nm.update({'1174052500':'강동구 상일제1동','1174052600':'강동구 상일제2동'})
s=pd.read_csv(X+'캐시/정류장_행정동.csv'); s['ARS']=s.ARS.astype(str).str.zfill(5); s['hj']=s.hj.astype('Int64').astype(str)
allst=rs.drop_duplicates('ARS')[['ARS','X좌표','Y좌표']].merge(s,on='ARS'); allst['동']=allst.hj.map(nm).str.replace('강동구 ','')
P=pd.read_csv('결과_k2_강동안_동짝_버스연결.csv',dtype={'a':str,'b':str})
부족=['암사제1동','암사제2동','암사제3동','천호제2동','천호제3동','고덕제1동','성내제3동','명일제1동']  # 최종 부족 확정 강동 동 일부(참고용)
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
        for dn in allst[(dd<=0.4)&allst.hj.str[:5].eq('11740')].동.dropna().unique(): reach.setdefault(dn,[]).append(r.누적km)
    cov=P[P.동A.isin(reach)&P.동B.isin(reach)].copy()
    cov['초안km']=[min(abs(x-y) for x in reach[a] for y in reach[b]) for a,b in zip(cov.동A,cov.동B)]
    cov['혜택']=(~cov.지하철바로)&(cov.중심거리km>=2.0)&((cov.버스최단km.isna())|(cov.버스최단km-cov.초안km>=1.0))
    c=cov[cov.혜택]; L=st.누적km.iloc[-1]
    res.append(dict(후보=k,길이km=round(L,1),정류장=len(st),닿는동=len(reach),혜택짝=len(c),하루이동=round(c.양방향.sum()),아침7_8=round(c['7_8시'].sum()),
        km당이동=round(c.양방향.sum()/max(L,0.1)),지금버스km=round(np.average(c.버스최단km,weights=c.양방향),1) if len(c) else None,초안km=round(np.average(c.초안km,weights=c.양방향),1) if len(c) else None,
        혜택짝목록=' / '.join(f'{a}-{b}' for a,b in zip(c.sort_values('양방향',ascending=False).동A,c.sort_values('양방향',ascending=False).동B))))
    keep[k]=dict(stops=st[['ARS','이름','x','y','누적km']].to_dict('records'),닿는동=sorted(reach))
R=pd.DataFrame(res); pd.set_option('display.width',250); pd.set_option('display.max_colwidth',200); print(R.to_string()); R.to_csv('결과_k3_경로후보_비교.csv',index=False)
json.dump(keep,open('결과_k3_경로후보_상세.json','w'),ensure_ascii=False,indent=0)
for k,v in keep.items(): print(k,'|',' → '.join(dict.fromkeys(x['이름'] for x in v['stops'])),'|',v['닿는동'])
