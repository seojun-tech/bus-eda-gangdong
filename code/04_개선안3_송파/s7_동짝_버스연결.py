# 강동·송파 동 짝: 생활이동(2023.4 평일, 양방향) vs 바로 가는 버스(2022.4 평일 운행)
import pandas as pd, json, numpy as np
X='../../동단위_레이어/'
lp=pd.read_csv(X+'외부데이터/행정동_생활인구_202204_평일주말_시간대평균.csv',dtype=str).drop_duplicates('생활인구_행정동코드')
c8to10=dict(zip(lp.생활인구_행정동코드,lp.행정동코드)); nm10=dict(zip(lp.행정동코드,lp.구_행정동))
B=pd.read_csv('생활이동_강동관련_동x동_시간_목적_202304_6일.csv.gz',dtype={'o_admdong_cd':str,'d_admdong_cd':str,'day':str})
B=B[~B.day.isin(['230415','230416'])].copy(); B['cnt']=B.cnt/4
c8to10.update({'11740525':'1174052500','11740526':'1174052600'}); nm10.update({'1174052500':'강동구 상일제1동','1174052600':'강동구 상일제2동'})  # 2023 OD는 상일 분리
B['h']=B.st_time_cd.where(B.st_time_cd<100,B.st_time_cd//100)
B['o']=B.o_admdong_cd.map(c8to10); B['d']=B.d_admdong_cd.map(c8to10)
gd=B.o.str[:5].eq('11740')&B.d.str[:5].eq('11710'); sg=B.o.str[:5].eq('11710')&B.d.str[:5].eq('11740')
F=B[gd]; R=B[sg].rename(columns={'o':'d','d':'o'})
def agg(t,p):
    a=t.groupby(['o','d']).agg(cnt=('cnt','sum'),cd=('cd','sum')); a[p+'_평균거리m']=a.cd/a.cnt/4  # cd도 /4 안 했으므로 보정
    a[p+'_7_9시']=t[t.h.isin([7,8])].groupby(['o','d']).cnt.sum(); a[p+'_17_19시']=t[t.h.isin([17,18])].groupby(['o','d']).cnt.sum()
    a[p+'_출근']=t[t.move_purpose==1].groupby(['o','d']).cnt.sum()
    return a.drop(columns='cd').rename(columns={'cnt':p})
P=agg(F,'강동→송파').join(agg(R,'송파→강동'),how='outer').fillna(0)
P['양방향']=P['강동→송파']+P['송파→강동']
# 버스 연결
s=pd.read_csv(X+'캐시/정류장_행정동.csv'); s['hj']=s.hj.astype('Int64').astype(str)
u=pd.read_csv(X+'외부데이터/버스_노선별_정류장별_운행횟수_202204_평일주말중앙값.csv.gz',dtype={'노선명':str,'정류장_ARS':str})
u=u[u.평일주말=='평일']; u['ARS']=pd.to_numeric(u.정류장_ARS,errors='coerce'); u=u.merge(s,on='ARS',how='left')
u=u[u.hj.str[:5].isin(['11740','11710'])]
ru=u.groupby(['노선명','hj']).버스운행횟수_일.max().reset_index()
rows=[]
for r,t in ru.groupby('노선명'):
    A=t[t.hj.str[:5]=='11740']; S=t[t.hj.str[:5]=='11710']
    for _,a in A.iterrows():
        for _,b in S.iterrows(): rows.append((a.hj,b.hj,r,min(a.버스운행횟수_일,b.버스운행횟수_일)))
C=pd.DataFrame(rows,columns=['o','d','노선','운행'])
CC=C.groupby(['o','d']).agg(바로가는노선수=('노선','nunique'),바로가는운행_일=('운행','sum'),노선목록=('노선',lambda x:' '.join(sorted(set(x)))))
P=P.join(CC,how='left'); P['바로가는노선수']=P.바로가는노선수.fillna(0); P['바로가는운행_일']=P.바로가는운행_일.fillna(0)
# 동 중심점 거리
g=json.load(open(X+'외부데이터/행정동_경계_20220401_서울.geojson'))
cen={}
for f in g['features']:
    cs=np.array([p for poly in f['geometry']['coordinates'] for ring in poly for p in ring]); cen[f['properties']['adm_cd2']]=cs.mean(0)
def dist(a,b):
    if a not in cen or b not in cen: return np.nan
    (x1,y1),(x2,y2)=cen[a],cen[b]; return np.hypot((x1-x2)*88.2,(y1-y2)*111.0)
P=P.reset_index(); P['중심거리km']=[dist(a,b) for a,b in zip(P.o,P.d)]
P['강동동']=P.o.map(nm10); P['송파동']=P.d.map(nm10)
P['운행1회당_양방향이동']=P.양방향/P.바로가는운행_일.replace(0,np.nan)
# 지하철 바로 연결(갈아타기 없음): 역 이름이 붙은 버스정류장이 있는 동 = 역 이용권
st={'암사':'8','천호':'8 5B','강동구청':'8','강동':'5B','둔촌동':'5B','중앙보훈병원':'9',
    '올림픽공원':'5B 9','방이':'5B','오금':'5B 3','개롱':'5B','거여':'5B','마천':'5B','몽촌토성':'8','잠실':'2 8','석촌':'8 9','송파':'8','가락시장':'8 3',
    '문정':'8','장지':'8','복정':'8','둔촌오륜':'9','한성백제':'9','송파나루':'9','석촌고분':'9','삼전':'9','잠실나루':'2','잠실새내':'2'}
bs=pd.read_csv(X+'외부데이터/버스정류소_유형_20220401.csv'); bs['hj']=bs.행정동코드.astype('Int64').astype(str)
L={}
for n,ls in st.items():
    pat=n+'역' if n not in ('중앙보훈병원',) else n
    t=bs[bs.정류소명.str.contains(pat,na=False)&bs.hj.str[:5].isin(['11740','11710'])]
    if n=='강동': t=t[~t.정류소명.str.contains('강동구청')]
    if n=='잠실': t=t[~t.정류소명.str.contains('잠실나루|잠실새내')]
    if n=='석촌': t=t[~t.정류소명.str.contains('석촌고분')]
    for h in t.hj.unique(): L.setdefault(h,set()).update(ls.split())
P['지하철바로']=[bool(L.get(a,set())&L.get(b,set())) for a,b in zip(P.o,P.d)]
pd.Series({nm10.get(k,k):' '.join(sorted(v)) for k,v in L.items()}).to_csv('결과_동별_지하철노선_이용권.csv')
P=P.sort_values('양방향',ascending=False); P.to_csv('결과_동짝_이동vs버스연결.csv',index=False)
print(P[['강동동','송파동','강동→송파','송파→강동','양방향','강동→송파_7_9시','중심거리km','바로가는노선수','바로가는운행_일','운행1회당_양방향이동','지하철바로']].head(30).round(1).to_string())
print('짝 수',len(P),'버스 없는 짝 이동 비중', round(P[P.바로가는노선수==0].양방향.sum()/P.양방향.sum(),3))
G=P[(P.중심거리km>=2.5)&(~P.지하철바로)].sort_values('양방향',ascending=False)
print('\n=== 걷기 어려운(2.5km+) 지하철 바로 없음 짝'); print(G[['강동동','송파동','양방향','강동→송파_7_9시','송파→강동_17_19시','중심거리km','바로가는노선수','바로가는운행_일','운행1회당_양방향이동','노선목록']].head(30).round(1).to_string())
G.to_csv('결과_빈짝_후보.csv',index=False)
