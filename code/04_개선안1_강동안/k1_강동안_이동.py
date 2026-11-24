# 강동 안 이동: 같은 동 / 강동 다른 동 / 서울 다른 구 (2023.4 평일 4일 평균, 생활이동 OA-22300). 경기 목적지는 제외(교수님 지시)
import pandas as pd, numpy as np, json
X='../../동단위_레이어/'; S='../송파이동_1107/'
lp=pd.read_csv(X+'외부데이터/행정동_생활인구_202204_평일주말_시간대평균.csv',dtype=str).drop_duplicates('생활인구_행정동코드')
c8to10=dict(zip(lp.생활인구_행정동코드,lp.행정동코드)); nm10=dict(zip(lp.행정동코드,lp.구_행정동))
c8to10.update({'11740525':'1174052500','11740526':'1174052600'}); nm10.update({'1174052500':'강동구 상일제1동','1174052600':'강동구 상일제2동'})
B=pd.read_csv(S+'생활이동_강동관련_동x동_시간_목적_202304_6일.csv.gz',dtype={'o_admdong_cd':str,'d_admdong_cd':str,'day':str})
B=B[~B.day.isin(['230415','230416'])].copy(); B['cnt']=B.cnt/4; B['cd']=B.cd/4
B['h']=B.st_time_cd.where(B.st_time_cd<100,B.st_time_cd//100)
B['o']=B.o_admdong_cd.map(c8to10); B['d']=B.d_admdong_cd.map(c8to10)
B=B[B.o.str[:5].eq('11740',) & B.d.str[:2].eq('11')]   # 강동 출발, 서울 도착
B['종류']=np.where(B.o==B.d,'같은 동',np.where(B.d.str[:5]=='11740','강동 다른 동','서울 다른 구'))
T=B.groupby('종류').agg(이동=('cnt','sum'),cd=('cd','sum')); T['몫%']=T.이동/T.이동.sum()*100; T['평균거리km']=T.cd/T.이동/1000
T['출근몫%']=B[B.move_purpose==1].groupby('종류').cnt.sum()/T.이동*100
print(T.round(2)); T.to_csv('결과_k1_이동종류.csv')
# 목적: 1출근 2등교 3귀가 4쇼핑 5관광 6병원 7기타 (OA-22300 정의)
pm=B.pivot_table(index='종류',columns='move_purpose',values='cnt',aggfunc='sum'); print((pm.div(pm.sum(1),axis=0)*100).round(1))
# 동별
D=B.pivot_table(index='o',columns='종류',values='cnt',aggfunc='sum'); D=D.div(D.sum(1),axis=0)*100
D['같은동_평균거리km']=B[B.종류=='같은 동'].groupby('o').apply(lambda t:t.cd.sum()/t.cnt.sum()/1000)
D.index=D.index.map(nm10); print(D.round(1).sort_values('같은 동',ascending=False)); D.to_csv('결과_k1_동별_이동종류.csv')
# 강동 안 동 짝 (양방향 합)
I=B[B.종류=='강동 다른 동'].copy()
I['a']=np.minimum(I.o,I.d); I['b']=np.maximum(I.o,I.d)
P=I.groupby(['a','b']).agg(양방향=('cnt','sum'),cd=('cd','sum')); P['평균거리km']=P.cd/P.양방향/1000
P['7_8시']=I[I.h.isin([7,8])].groupby(['a','b']).cnt.sum(); P['출근']=I[I.move_purpose==1].groupby(['a','b']).cnt.sum()
P=P.fillna(0).drop(columns='cd').reset_index()
g=json.load(open(X+'외부데이터/행정동_경계_20220401_서울.geojson')); cen={}
for f in g['features']:
    cs=np.array([p for poly in f['geometry']['coordinates'] for ring in poly for p in ring]); cen[f['properties']['adm_cd2']]=cs.mean(0)
# 상일1·2는 2022 경계에 없음(상일동 하나) → 상일동 중심 사용
for k in ['1174052500','1174052600']:
    if k not in cen:
        base=[c for c in cen if c.startswith('117405')]; 
P['중심거리km']=[np.hypot((cen[a][0]-cen[b][0])*88.2,(cen[a][1]-cen[b][1])*111.0) if a in cen and b in cen else np.nan for a,b in zip(P.a,P.b)]
P['동A']=P.a.map(nm10).str.replace('강동구 ',''); P['동B']=P.b.map(nm10).str.replace('강동구 ','')
P=P.sort_values('양방향',ascending=False); P.to_csv('결과_k1_강동안_동짝.csv',index=False)
print('짝 수',len(P),'중심거리 없는 짝', P.중심거리km.isna().sum())
print(P.head(25).round(2).to_string())
print([c for c in cen if c.startswith('11740')])
