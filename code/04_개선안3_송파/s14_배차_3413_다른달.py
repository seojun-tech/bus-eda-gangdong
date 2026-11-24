import pandas as pd, numpy as np, json, zipfile, sys
X='../../동단위_레이어/'
K=json.load(open('결과_경로후보_상세.json'))['D 기본+장지차고지 종점']; C=pd.DataFrame(K['pairs']); pairs=set(zip(C.강동동,C.송파동))
lp=pd.read_csv(X+'외부데이터/행정동_생활인구_202204_평일주말_시간대평균.csv',dtype=str).drop_duplicates('생활인구_행정동코드')
c8=dict(zip(lp.생활인구_행정동코드,lp.구_행정동)); c8.update({'11740525':'강동구 상일제1동','11740526':'강동구 상일제2동'})
B=pd.read_csv('생활이동_강동관련_동x동_시간_목적_202304_6일.csv.gz',dtype={'o_admdong_cd':str,'d_admdong_cd':str,'day':str})
B['주말']=B.day.isin(['230415','230416']); B['cnt']=B.cnt/B.주말.map({False:4,True:2})
B['h']=B.st_time_cd.where(B.st_time_cd<100,B.st_time_cd//100); B['o']=B.o_admdong_cd.map(c8); B['d']=B.d_admdong_cd.map(c8)
B['방향']=np.select([[ (a,b) in pairs for a,b in zip(B.o,B.d)],[ (b,a) in pairs for a,b in zip(B.o,B.d)]],['강동→송파','송파→강동'],'')
F=B[B.방향!='']
# 1) 시간대 배차표
T=F.pivot_table(index='h',columns=['주말','방향'],values='cnt',aggfunc='sum').fillna(0)
rows=[]
for h in range(5,24):
    for wk in [False,True]:
        mx=max(T.get((wk,'강동→송파'),pd.Series(dtype=float)).get(h,0),T.get((wk,'송파→강동'),pd.Series(dtype=float)).get(h,0))
        pax=mx*0.18; need=int(np.ceil(pax/45)); cap=4 if wk else (4 if 10<=h<=16 or h>=20 else 3)  # 최소 간격 정책: 15~20분
        runs=max(need, 3 if h<22 else 2)
        rows.append(dict(시=h,구분='주말' if wk else '평일',많은방향_이동=round(mx),예상승객_18pct=round(pax),운행횟수=runs,간격_분=round(60/runs)))
S=pd.DataFrame(rows); S.to_csv('결과_배차표_평일주말.csv',index=False)
print(S.pivot(index='시',columns='구분',values=['많은방향_이동','운행횟수','간격_분']).to_string())
L=15.7; cyc=2*(L/17*60)+20
for g in ['평일','주말']:
    s=S[S.구분==g]; print(g,'하루 운행(한 방향)',s.운행횟수.sum(),' 최대 시간당',s.운행횟수.max(),' 필요 차량',int(np.ceil(s.운행횟수.max()*cyc/60)),'(한 바퀴',round(cyc),'분)')
# 2) 동별 타고 내리는 이동(평일, 양방향 합, 18%)
o=F[~F.주말].groupby(['방향','o']).cnt.sum(); d=F[~F.주말].groupby(['방향','d']).cnt.sum()
Q=pd.DataFrame({'강동동_출발(강동→송파)':o['강동→송파'],'강동동_도착(송파→강동)':d['송파→강동']}).fillna(0)
Q2=pd.DataFrame({'송파동_도착(강동→송파)':d['강동→송파'],'송파동_출발(송파→강동)':o['송파→강동']}).fillna(0)
(Q*0.18).round(0).sort_values('강동동_출발(강동→송파)',ascending=False).to_csv('결과_동별_예상승하차_평일.csv'); (Q2*0.18).round(0).sort_values('송파동_도착(강동→송파)',ascending=False).to_csv('결과_송파동별_예상승하차_평일.csv')
print((Q*0.18).round(0).sort_values('강동동_출발(강동→송파)',ascending=False).to_string()); print((Q2*0.18).round(0).sort_values('송파동_도착(강동→송파)',ascending=False).to_string())
print('평일 하루 예상 승객(18%)',round(F[~F.주말].cnt.sum()*0.18),' 10%~25%:',round(F[~F.주말].cnt.sum()*0.10),'~',round(F[~F.주말].cnt.sum()*0.25))
# 3) 3413 운행 여유: 1회당 승차 (2022.4) vs 서울 노선 중앙값
b=pd.read_csv(X+'외부데이터/버스_노선별_정류장별_시간대별_승하차_202204.csv.gz',dtype={'노선번호':str}); hs=[c for c in b.columns if '승차' in c]
u=pd.read_csv(X+'외부데이터/버스_노선별_정류장별_운행횟수_202204_평일주말중앙값.csv.gz',dtype={'노선명':str}); u=u[u.평일주말=='평일']
runs=u.groupby('노선명').버스운행횟수_일.max(); board=b.groupby('노선번호')[hs].sum().sum(axis=1)/30
r=(board/runs).dropna(); r=r[(runs>20)]
print('3413 1회당 승차',round(r.get('3413'),1),' 서울 노선 중앙값',round(r.median(),1),' 3413 백분위',round((r<r['3413']).mean(),2))
hr=[f'{h}시승차총승객수' if h else '00시승차총승객수' for h in range(24)]
t=b[b.노선번호=='3413'][hr].sum()/30; ru=u[u.노선명=='3413'][[f'버스운행횟수_{h:02d}시' for h in range(24)]].max()
print('3413 시간대별 1회당 승차', dict(zip(range(5,24),(t.values[5:]/np.maximum(ru.values[5:],1)).round(0))))
