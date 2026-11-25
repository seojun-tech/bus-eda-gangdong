# 강동 안 이동 거리 구간 + 동 짝별 바로 가는 버스(2022 노선, 경로는 2026 정류소 순서로 근사)
import pandas as pd, numpy as np
X='../../동단위_레이어/'; S='../송파이동_1107/'
exec(open('k1_강동안_이동.py').read().split('# 강동 안 동 짝')[0].split("T=B.groupby")[0])
# 거리 구간: 행(시간x목적x동짝) 평균거리 기준 근사
B['km']=B.cd/B.cnt/1000
B['구간']=pd.cut(B.km,[0,1,2,3,5,100],labels=['~1km','1~2km','2~3km','3~5km','5km~'])
K=B[B.d.str[:5]=='11740'].pivot_table(index='구간',columns='종류',values='cnt',aggfunc='sum',observed=False)
print((K/K.sum()*100).round(1)); print((K.sum(1)/K.sum().sum()*100).round(1))
K.to_csv('결과_k2_거리구간.csv')
P=pd.read_csv('결과_k1_강동안_동짝.csv',dtype={'a':str,'b':str})
rs=pd.read_csv(S+'서울시버스노선별정류소정보_20260902.csv',dtype={'노선명':str,'ARS_ID':str})
u=pd.read_csv(X+'외부데이터/버스_노선별_정류장별_운행횟수_202204_평일주말중앙값.csv.gz',dtype={'노선명':str,'정류장_ARS':str}); u=u[u.평일주말=='평일']
u22=set(u.노선명)
s=pd.read_csv(X+'캐시/정류장_행정동.csv'); s['hj']=s.hj.astype('Int64').astype(str); s['ARS']=s.ARS.astype(str).str.zfill(5)
# 상일동(2022 1174052000?) 분리 문제: 정류장 행정동 코드 확인
print(s[s.hj.str[:5]=='11740'].hj.value_counts().sort_index())
rs['ARS']=rs.ARS_ID.str.zfill(5); rs=rs.merge(s[['ARS','hj']],on='ARS',how='left').sort_values(['ROUTE_ID','순번'])
rs=rs[rs.노선명.isin(u22)]
out={}
for rid,t in rs.groupby('ROUTE_ID'):
    hj=t.hj.fillna('').astype(str).values
    if (pd.Series(hj).str[:5]=='11740').sum()<2: continue
    x=t.X좌표.values; y=t.Y좌표.values; cum=np.r_[0,np.hypot(np.diff(x)*88.2,np.diff(y)*111.0)].cumsum(); nm=t.노선명.iloc[0]; n=len(t)
    idx=[i for i in range(n) if hj[i].startswith('11740')]
    for i in idx:
        for j in idx:
            if j<=i or hj[i]==hj[j]: continue
            k=tuple(sorted((hj[i],hj[j]))); L=cum[j]-cum[i]
            if k not in out or L<out[k][0]: out[k]=(L,nm,j-i)
R=pd.DataFrame([(a,b,*v) for (a,b),v in out.items()],columns=['a','b','버스최단km','노선','정류장수'])
# 바로 가는 운행(하루): 두 동을 모두 지나는 노선의 운행 min 합
uu=u.copy(); uu['ARS']=uu.정류장_ARS.astype(str).str.zfill(5); uu=uu.merge(s[['ARS','hj']],on='ARS'); uu=uu[uu.hj.str[:5]=='11740']
ru=uu.groupby(['노선명','hj']).버스운행횟수_일.max().reset_index(); rows=[]
for r,t in ru.groupby('노선명'):
    h=t.set_index('hj').버스운행횟수_일
    for i in h.index:
        for j in h.index:
            if i<j: rows.append((i,j,r,min(h[i],h[j])))
C=pd.DataFrame(rows,columns=['a','b','노선명','운행']).groupby(['a','b']).agg(바로노선수=('노선명','nunique'),바로운행_일=('운행','sum'),마을만=('노선명',lambda x: all(str(v).startswith('강동0') for v in x)),노선목록=('노선명',lambda x:' '.join(sorted(set(x))))).reset_index()
P=P.merge(R,on=['a','b'],how='left').merge(C,on=['a','b'],how='left')
P['바로노선수']=P.바로노선수.fillna(0); P['바로운행_일']=P.바로운행_일.fillna(0); P['우회율']=P.버스최단km/P.중심거리km
# 지하철 바로(갈아타기 없음): 동 안 역, 5호선 하남갈래(5H)·마천갈래(5M) 구분
stn={'천호':'8 5H 5M','강동구청':'8','암사':'8','강동':'5H 5M','길동':'5H','굽은다리':'5H','명일':'5H','고덕':'5H','상일동':'5H','둔촌동':'5M'}
bs=pd.read_csv(X+'외부데이터/버스정류소_유형_20220401.csv'); bs['hj']=bs.행정동코드.astype('Int64').astype(str)
Lm={}
for n,ls in stn.items():
    t=bs[bs.정류소명.str.contains(n+'역',na=False)&(bs.hj.str[:5]=='11740')]
    if n=='강동': t=t[~t.정류소명.str.contains('강동구청')]
    for h in t.hj.unique(): Lm.setdefault(h,set()).update(ls.split())
P['지하철바로']=[bool(Lm.get(a,set())&Lm.get(b,set())) for a,b in zip(P.a,P.b)]
P.to_csv('결과_k2_강동안_동짝_버스연결.csv',index=False)
tot=P.양방향.sum()
far=P[P.중심거리km>=2]
print('강동 안 동짝 이동 합',round(tot),' 중심 2km+ 짝',len(far),round(far.양방향.sum()),round(far.양방향.sum()/tot*100,1),'%')
far=far.assign(빈=(~far.지하철바로)&((far.바로노선수==0)|(far.우회율>=1.8)))
print('2km+ 중 지하철 없고 버스 없음/1.8배 우회', far.빈.sum(), round(far[far.빈].양방향.sum()), round(far[far.빈].양방향.sum()/tot*100,1),'%')
print('2km+ 중 버스 없음', (far.바로노선수==0).sum(), round(far[far.바로노선수==0].양방향.sum()))
cols=['동A','동B','양방향','7_8시','출근','중심거리km','바로노선수','바로운행_일','버스최단km','우회율','노선','지하철바로']
print(far[far.빈].sort_values('양방향',ascending=False)[cols].head(30).round(2).to_string())
print('--- 2km+ 상위 전체'); print(far.sort_values('양방향',ascending=False)[cols].head(25).round(2).to_string())
