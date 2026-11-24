# 추가 확인: 유형별 운행 모양이 다른가 / 강동 위치 / 암사2 밤 확인 / ②③ 중앙값 운행으로 다시
import pandas as pd, numpy as np
from scipy import stats
P='/mnt/project-files/프로젝트2'; R=f'{P}/최종발표/시간대_1107/결과'
SV=[5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,0]
X=pd.read_csv(f'{R}/0_패널_버스_04.csv',dtype={'hj':str},encoding='utf-8-sig').set_index('hj')
run=pd.DataFrame({h:X[f'평일운행_{h:02d}']*21+X[f'주말운행_{h:02d}']*9 for h in SV}); on=pd.DataFrame({h:X[f'승차_{h:02d}'] for h in SV}); off=pd.DataFrame({h:X[f'하차_{h:02d}'] for h in SV})
U=pd.read_csv(f'{R}/5_유형_동별.csv',dtype={'hj':str},encoding='utf-8-sig').set_index('hj')
BAND={'출근 06~09':[6,7,8],'낮 09~17':[9,10,11,12,13,14,15,16],'퇴근 17~20':[17,18,19],'밤 22~01':[22,23,0]}
rs=run.div(run.sum(axis=1),axis=0); ds=(on+off).div((on+off).sum(axis=1),axis=0); os_=on.div(on.sum(axis=1),axis=0)
rows=[]
for t,g in U.groupby('유형'):
    for k,v in BAND.items():
        rows.append(dict(유형=t,시간=k,운행몫=rs.loc[g.index,v].sum(axis=1).median(),승차몫=os_.loc[g.index,v].sum(axis=1).median(),승하차몫=ds.loc[g.index,v].sum(axis=1).median()))
Q=pd.DataFrame(rows); print(Q.pivot(index='유형',columns='시간',values='운행몫').round(3)); print(Q.pivot(index='유형',columns='시간',values='승차몫').round(3))
Q.to_csv(f'{R}/5_유형_운행몫_vs_승차몫.csv',index=False,encoding='utf-8-sig')
# 운행 모양이 유형 따라 얼마나 다른가 vs 승차 모양이 얼마나 다른가 (크루스칼)
for k,v in BAND.items():
    a=stats.kruskal(*[rs.loc[g.index,v].sum(axis=1) for _,g in U.groupby('유형')]); b=stats.kruskal(*[os_.loc[g.index,v].sum(axis=1) for _,g in U.groupby('유형')])
    print(k,'운행몫 유형간 H',round(a.statistic,1),'| 승차몫 유형간 H',round(b.statistic,1))
# 동 운행 모양의 동 간 퍼짐 vs 승차 모양 퍼짐 (출근몫 표준편차)
for k,v in BAND.items(): print(k,'동간 표준편차 운행몫',round(rs[v].sum(axis=1).std(),4),'승차몫',round(os_[v].sum(axis=1).std(),4))
# 강동
O1=pd.read_csv(f'{R}/1_시간어긋남_동별.csv',dtype={'hj':str},encoding='utf-8-sig').set_index('hj')
O2=pd.read_csv(f'{R}/2_사람수기준_부족_동x시간.csv',dtype={'hj':str},encoding='utf-8-sig').set_index('hj')
W=pd.read_csv(f'{R}/3_주말_동별.csv',dtype={'hj':str},encoding='utf-8-sig').set_index('hj')
N=pd.read_csv(f'{R}/4_막차_동별.csv',dtype={'hj':str},encoding='utf-8-sig').set_index('hj')
g=O1[O1.구=='강동구'][['동','판정','시간어긋남','칸','모자란시간','가장붐빈시','가장붐빈시간_배']].join(U[['유형']]).join(O2[list(BAND)]).join(W[['주말운행비','주말승차비','주말틈']]).join(N[['밤_내린사람_버스1회당','막차시']])
O1['어긋남순위']=O1['시간어긋남'].rank(ascending=False); g=g.join(O1[['어긋남순위']])
print(g.round(2).to_string()); g.to_csv(f'{R}/7_강동_한눈에.csv',encoding='utf-8-sig')
# 유형별 판정 비율
ct=pd.crosstab(U['유형'],U['판정'],normalize='index'); print(ct.round(2))
# 암사2 밤
st=pd.read_csv(f'{R}/0_지하철역_행정동.csv',dtype={'hj':str}); print(st[st.hj.isin(O1[O1.구=='강동구'].index)])
print(N.loc[O1[O1.동=='강동 암사2동'].index].T)
