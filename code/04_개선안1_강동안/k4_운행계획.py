# D 노선(출근 맞춤 역 잇기)의 시간대 수요·배차·효과 (2023.4 평일 생활이동 + 2022.4 버스)
import pandas as pd, numpy as np, json
X='../../동단위_레이어/'; S='../송파이동_1107/'; T='../시간대_1107/결과/'
exec(open('k1_강동안_이동.py').read().split('# 강동 안 동 짝')[0].split("T=B.groupby")[0])
B['동o']=B.o.map(nm10).str.replace('강동구 ',''); B['동d']=B.d.map(nm10).str.replace('강동구 ','')
서=['암사제1동','암사제2동','암사제3동','천호제1동','천호제2동','천호제3동','명일제1동']; 동=['상일제1동','상일제2동','고덕제2동','고덕제1동']
I=B[B.종류=='강동 다른 동']
f=I[I.동o.isin(서)&I.동d.isin(동)]; r=I[I.동o.isin(동)&I.동d.isin(서)]
H=pd.DataFrame({'서→동(암사·천호→고덕·상일)':f.groupby('h').cnt.sum(),'동→서':r.groupby('h').cnt.sum()}).fillna(0).round(0)
H['서→동 출근']=f[f.move_purpose==1].groupby('h').cnt.sum().round(0)
print(H.to_string()); H.to_csv('결과_k4_축_시간대이동.csv')
day=H.iloc[:,0].sum(); m=H.loc[[7,8],H.columns[0]].sum(); mid=H.loc[10:15,H.columns[0]].mean()
print('서→동 하루',round(day),'7~8시',round(m),'몫',round(m/day*100,1),'%  7~8시 시간당/낮 시간당',round(m/2/mid,2))
print('서→동 출근목적 몫', round(f[f.move_purpose==1].cnt.sum()/day*100,1),'%  7~8시 중 출근', round(f[(f.move_purpose==1)&f.h.isin([7,8])].cnt.sum()/m*100,1))
# 2022 운행: D 노선이 지나는 정류장의 7~8시 시간당 통과(평일 중앙값)
st=json.load(open('결과_k3_경로후보_상세.json'))['D1 명일역 경유, 고덕역→비즈밸리→상일동역']['stops']
u=pd.read_csv(X+'외부데이터/버스_노선별_정류장별_운행횟수_202204_평일주말중앙값.csv.gz',dtype={'노선명':str,'정류장_ARS':str}); u=u[u.평일주말=='평일']
import re
u=u[[not re.search('[가-힣]',str(r)) or str(r).startswith('강동') for r in u.노선명]]  # 경기 노선 번호 겹침 제외
u['ARS']=u.정류장_ARS.astype(str).str.zfill(5); s=pd.read_csv(X+'캐시/정류장_행정동.csv'); s['ARS']=s.ARS.astype(str).str.zfill(5); s['hj']=s.hj.astype('Int64').astype(str)
rows=[]
for x in st:
    t=u[u.ARS==x['ARS']]
    rows.append(dict(ARS=x['ARS'],이름=x['이름'],누적km=round(x['누적km'],2),동=nm10.get(s.set_index('ARS').hj.get(x['ARS'],''),'').replace('강동구 ',''),
        노선수=t.노선명.nunique(),통과_7시=t.버스운행횟수_07시.sum(),통과_8시=t.버스운행횟수_08시.sum(),통과_12시=t.버스운행횟수_12시.sum(),노선=' '.join(sorted(t.노선명.unique()))))
R=pd.DataFrame(rows); pd.set_option('display.width',250); print(R.to_string()); R.to_csv('결과_k4_D정류장_2022운행.csv',index=False)
# 처음부터 끝까지(천호역 근처~비즈밸리 입구) 한 번에 가는 2022 노선이 있는가: 정류장 집합 겹침 비율
cov=u[u.ARS.isin(R.ARS)].groupby('노선명').ARS.nunique().sort_values(ascending=False)
print('D 정류장 23곳 중 노선별 겹침', cov.head(10).to_dict())
