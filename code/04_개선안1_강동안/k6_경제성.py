# 경제성: 서울 노선(2022.4)과 같은 잣대로 비교 — 1회당 승차, 1km당 승차, 차 1대당 하루 승차(같은 공식으로 차량 추정)
import pandas as pd, numpy as np, re
X='../../동단위_레이어/'; S='../송파이동_1107/'
h=pd.read_csv(X+'외부데이터/버스_노선별_정류장별_시간대별_승하차_202204.csv.gz',dtype={'노선번호':str})
on=[c for c in h.columns if '승차' in c]; hr={c:int(re.match(r'(\d+)시',c).group(1)) for c in on}
H=h.groupby('노선번호')[on].sum(); H.columns=[hr[c] for c in on]
u=pd.read_csv(X+'외부데이터/버스_노선별_정류장별_운행횟수_202204_평일주말중앙값.csv.gz',dtype={'노선명':str})
u=u[[not re.search('[가-힣]',str(r)) or str(r).startswith(tuple('강서관광노도동마성송양영용은종중구금')) for r in u.노선명]]
hc=[f'버스운행횟수_{i:02d}시' for i in range(24)]
R=u.groupby(['노선명','평일주말'])[hc].max().reset_index()   # 노선이 지나는 정류장 중 최대 = 그 시간 운행 수
wd=R[R.평일주말=='평일'].set_index('노선명')[hc]; we=R[R.평일주말=='주말'].set_index('노선명')[hc].reindex(wd.index).fillna(0)
wd.columns=we.columns=range(24)
run_m=wd*21+we*9   # 한 달 운행(2022.4 평일 21·주말 9)
rs=pd.read_csv(S+'서울시버스노선별정류소정보_20260902.csv',dtype={'노선명':str}).sort_values(['ROUTE_ID','순번'])
L=rs.groupby('노선명').apply(lambda t: np.hypot(np.diff(t.X좌표)*88.2,np.diff(t.Y좌표)*111.0).sum())*1.25  # 직선→도로 보정 1.25
peak=[7,8,17,18]
idx=H.index.intersection(wd.index).intersection(L.index)
T=pd.DataFrame(index=idx)
T['하루승차']=H.loc[idx].sum(1)/30; T['하루운행_평일']=wd.loc[idx].sum(1); T['왕복km']=L.loc[idx]
T['1회당승차']=H.loc[idx].sum(1)/run_m.loc[idx].sum(1)
T['출퇴근1회당']=H.loc[idx,peak].sum(1)/run_m.loc[idx,peak].sum(1)
T['출퇴근1회당_km']=T.출퇴근1회당/T.왕복km
T['최대시간운행']=wd.loc[idx].max(1); T['차량추정']=np.ceil(T.최대시간운행*(T.왕복km/17*60+20)/60)
T['차1대당하루승차']=T.하루승차/T.차량추정
T=T[(T.하루운행_평일>=20)&(T.왕복km>3)&T.차량추정.gt(0)].replace([np.inf],np.nan).dropna()
T.to_csv('결과_k6_서울노선_효율.csv')
print('노선 수',len(T)); print(T[['1회당승차','출퇴근1회당','출퇴근1회당_km','왕복km','차량추정','차1대당하루승차']].describe(percentiles=[.25,.5,.75]).round(2).to_string())
for r in ['340','3411','3318','8333','강동02','강동05','8331','8221']:
    if r in T.index: print(r, T.loc[r,['1회당승차','출퇴근1회당','출퇴근1회당_km','왕복km','차량추정','차1대당하루승차']].round(2).to_dict())
# 이 노선안(D1): 출근 6:30~9:30, 퇴근 17~19:30 양방향 축 이동 × 버스 몫
A=pd.read_csv('결과_k4_축_시간대이동.csv',index_col=0)
w={6:0.5,7:1,8:1,9:0.5,17:1,18:1,19:0.5}
tot=sum((A.iloc[:,0].get(k,0)+A.iloc[:,1].get(k,0))*v for k,v in w.items())
runs=37*2; km=7.1*2; veh=9
for sh in [0.10,0.18,0.25]:
    rid=tot*sh; print(f'버스몫 {sh:.0%}: 하루 승객 {rid:.0f}, 1회(편도)당 {rid/runs:.1f}, 왕복당 {rid/runs*2:.1f}, 왕복km당 {rid/runs*2/km:.2f}, 차1대당 {rid/veh:.0f}')
print('창 시간 축 이동 합',round(tot))
