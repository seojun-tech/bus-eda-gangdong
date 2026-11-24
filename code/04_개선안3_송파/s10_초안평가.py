# 초안 노선이 닿는 동(정류장 400m 안) · 혜택 짝 · 시간대 수요 · 배차 · 3413 겹침
import pandas as pd, numpy as np, json
X='../../동단위_레이어/'
J=json.load(open('결과_노선초안_경로.json'))['A_문정직행']; st=pd.DataFrame(J['stops'])
st['누적km']=np.r_[0,np.hypot(np.diff(st.x)*88.2,np.diff(st.y)*111.0)].cumsum()
lp=pd.read_csv(X+'외부데이터/행정동_생활인구_202204_평일주말_시간대평균.csv',dtype=str).drop_duplicates('행정동코드'); nm=dict(zip(lp.행정동코드,lp.구_행정동)); nm.update({'1174052500':'강동구 상일제1동','1174052600':'강동구 상일제2동'})
rs=pd.read_csv('서울시버스노선별정류소정보_20260902.csv',dtype={'노선명':str,'ARS_ID':str}); rs['ARS']=rs.ARS_ID.str.zfill(5)
s=pd.read_csv(X+'캐시/정류장_행정동.csv'); s['ARS']=s.ARS.astype(str).str.zfill(5); s['hj']=s.hj.astype('Int64').astype(str)
allst=rs.drop_duplicates('ARS')[['ARS','X좌표','Y좌표']].merge(s,on='ARS'); allst['동']=allst.hj.map(nm)
reach={}
for _,r in st.iterrows():
    d=np.hypot((allst.X좌표-r.x)*88.2,(allst.Y좌표-r.y)*111.0)
    for dn in allst[d<=0.4].동.dropna().unique():
        if dn[:3] in ('강동구','송파구'): reach[dn]=min(reach.get(dn,99),r.누적km)
reach=pd.Series(reach).sort_values(); print('닿는 동(400m)',reach.round(1).to_dict())
st['동']=st.행정동.map(nm); st.to_csv('결과_노선초안_정류장.csv',index=False)
P=pd.read_csv('결과_동짝_이동vs버스연결_우회율.csv',dtype={'o':str,'d':str})
cov=P[P.강동동.isin(reach.index)&P.송파동.isin(reach.index)].copy()
cov['초안km']=[abs(reach[b]-reach[a]) for a,b in zip(cov.강동동,cov.송파동)]
cov['지금버스km']=cov.y22_최단버스경로km
cov['혜택']=(~cov.지하철바로)&(cov.중심거리km>=2.0)&((cov.지금버스km.isna())|(cov.지금버스km-cov.초안km>=1.5))
c=cov[cov.혜택].sort_values('양방향',ascending=False); c.to_csv('결과_노선초안_혜택짝.csv',index=False)
print(c[['강동동','송파동','양방향','강동→송파_7_9시','중심거리km','지금버스km','y22_노선','초안km']].head(25).round(1).to_string())
print('혜택 짝',len(c),'하루 양방향',round(c.양방향.sum()),'강동→송파',round(c['강동→송파'].sum()),'아침7~9',round(c['강동→송파_7_9시'].sum()),'저녁17~19 송파→강동',round(c['송파→강동_17_19시'].sum()))
w=c.dropna(subset=['지금버스km']); print('지금 버스 길이(수요가중)',round(np.average(w.지금버스km,weights=w.양방향),1),'km → 초안',round(np.average(w.초안km,weights=w.양방향),1),'km / 바로 가는 버스 없는 짝 이동',round(c[c.지금버스km.isna()].양방향.sum()))
# 시간대별: 혜택 짝 강동→송파 이동 (생활이동 원자료에서)
B=pd.read_csv('생활이동_강동관련_동x동_시간_목적_202304_6일.csv.gz',dtype={'o_admdong_cd':str,'d_admdong_cd':str,'day':str})
B=B[~B.day.isin(['230415','230416'])].copy(); B['cnt']/=4; B['h']=B.st_time_cd.where(B.st_time_cd<100,B.st_time_cd//100)
c8=dict(zip(lp.생활인구_행정동코드,lp.구_행정동)); c8.update({'11740525':'강동구 상일제1동','11740526':'강동구 상일제2동'})
B['o']=B.o_admdong_cd.map(c8); B['d']=B.d_admdong_cd.map(c8)
pairs=set(zip(c.강동동,c.송파동)); fw=B[[ (a,b) in pairs for a,b in zip(B.o,B.d)]]; bw=B[[ (b,a) in pairs for a,b in zip(B.o,B.d)]]
H=pd.DataFrame({'강동→송파':fw.groupby('h').cnt.sum(),'송파→강동':bw.groupby('h').cnt.sum()}).fillna(0)
# 버스 몫 가정: 지금 강동→송파 이동 중 버스 추정 몫(약 18%)을 기본으로 10~25% 범위
for sh in [0.10,0.18,0.25]: H[f'승객_{int(sh*100)}%']=H.max(axis=1)*sh
H['필요배차_18%(대당45명)']=np.ceil(H['승객_18%']/45)
H.to_csv('결과_노선초안_시간대수요_배차.csv'); print(H.round(0).to_string())
# 3413 겹침
o3=set(rs[rs.노선명=='3413'].ARS); print('초안 정류장 중 3413도 서는 곳',sum(a in o3 for a in st.ARS),'/',len(st))
