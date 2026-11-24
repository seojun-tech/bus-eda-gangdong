# 돌아가면 덜 타는가: 송파 동별 '강동에서 버스로 온 사람(추정) ÷ 강동에서 온 전체 이동' vs '바로 가는 버스의 우회율'
import pandas as pd, numpy as np
X='../../동단위_레이어/'
s=pd.read_csv(X+'캐시/정류장_행정동.csv'); s['hj']=s.hj.astype('Int64').astype(str)
lp=pd.read_csv(X+'외부데이터/행정동_생활인구_202204_평일주말_시간대평균.csv',dtype=str).drop_duplicates('행정동코드'); nm=dict(zip(lp.행정동코드,lp.구_행정동))
b=pd.read_csv(X+'외부데이터/버스_노선별_정류장별_시간대별_승하차_202204.csv.gz',dtype={'버스정류장ARS번호':str,'노선번호':str})
b['ARS']=pd.to_numeric(b['버스정류장ARS번호'],errors='coerce'); b=b.merge(s,on='ARS',how='left')
hs=[c for c in b.columns if '승차' in c]; ha=[c for c in b.columns if '하차' in c]; b['승']=b[hs].sum(axis=1)/30; b['하']=b[ha].sum(axis=1)/30
rows=[]
for r,t in b.groupby('노선번호'):
    if not (t.hj.str[:5].eq('11740').any() and t.hj.str[:5].eq('11710').any()): continue
    sh=t[t.hj.str[:5]=='11740'].승.sum()/t.승.sum()
    x=t[t.hj.str[:5]=='11710'].groupby('hj').하.sum()*sh
    for k,v in x.items(): rows.append((r,k,v))
Bd=pd.DataFrame(rows,columns=['노선','hj','버스추정']); Bd['송파동']=Bd.hj.map(nm)
bus=Bd.groupby('송파동').버스추정.sum()
P=pd.read_csv('결과_동짝_이동vs버스연결_우회율.csv')
od=P.groupby('송파동')['강동→송파'].sum()
w=P.dropna(subset=['y22_우회율']); det=w.groupby('송파동').apply(lambda t: np.average(t.y22_우회율,weights=t['강동→송파']))
sub=P.groupby('송파동').apply(lambda t: (t.지하철바로*t['강동→송파']).sum()/t['강동→송파'].sum())
dist=P.groupby('송파동').apply(lambda t: np.average(t.중심거리km,weights=t['강동→송파']))
D=pd.DataFrame({'강동에서온이동':od,'버스추정':bus,'우회율':det,'지하철바로몫':sub,'거리km':dist}).dropna()
D['버스몫']=D.버스추정/D.강동에서온이동
D=D[D.강동에서온이동>=1000].sort_values('우회율'); D.to_csv('결과_우회율과_버스이용.csv')
print(D.round(2).to_string())
for nmx,DD in [('전체',D),('걷기 어려운 곳(2.5km+)',D[D.거리km>=2.5])]:
    print(nmx,'n',len(DD),'순위상관 우회율-버스몫',round(DD.우회율.rank().corr(DD.버스몫.rank()),2),' 거리-버스몫',round(DD.거리km.rank().corr(DD.버스몫.rank()),2),' 지하철바로몫-버스몫',round(DD.지하철바로몫.rank().corr(DD.버스몫.rank()),2))
DD=D[D.거리km>=2.5]; Xm=np.c_[np.ones(len(DD)),DD.우회율,DD.거리km,DD.지하철바로몫]; y=np.log(DD.버스몫)
beta=np.linalg.lstsq(Xm,y,rcond=None)[0]; print('log(버스몫) ~ 우회율+거리+지하철 계수',dict(zip(['상수','우회율','거리','지하철'],beta.round(3))))
rng=np.random.default_rng(0); bs=[]
for _ in range(2000):
    k=rng.integers(0,len(DD),len(DD)); bs.append(np.linalg.lstsq(Xm[k],y.values[k],rcond=None)[0][1])
print('우회율 계수 95% 구간',np.percentile(bs,[2.5,97.5]).round(3), ' 우회율 1 오를 때 버스몫 배수',round(np.exp(beta[1]),2))
lo=DD[DD.우회율<1.5]; hi=DD[DD.우회율>=1.5]
print('우회 1.5배 미만 버스몫(이동가중)',round(lo.버스추정.sum()/lo.강동에서온이동.sum(),3),' 1.5배 이상',round(hi.버스추정.sum()/hi.강동에서온이동.sum(),3), len(lo),len(hi))
# 3413 안에서: 잠실(바로) vs 문정(크게 돌아감)
t=b[b.노선번호=='3413']; print('3413 하차: 잠실6동',round(t[t.hj.map(nm)=='송파구 잠실6동'].하.sum()),' 문정2동',round(t[t.hj.map(nm)=='송파구 문정2동'].하.sum()))
print('강동→잠실6동 이동',round(od.get('송파구 잠실6동')),' 강동→문정2동',round(od.get('송파구 문정2동')))
