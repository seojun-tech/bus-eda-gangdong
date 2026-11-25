import pandas as pd
X='../../동단위_레이어/'
s=pd.read_csv(X+'캐시/정류장_행정동.csv'); s['gu']=(s.hj//100000).astype('Int64')
R=pd.read_csv('결과_버스14노선_강동송파_추정.csv',dtype={'노선':str}); routes=set(R.노선)
u=pd.read_csv(X+'외부데이터/버스_노선별_정류장별_운행횟수_202204_평일주말중앙값.csv.gz',dtype={'노선명':str,'정류장_ARS':str})
u['ARS']=pd.to_numeric(u.정류장_ARS,errors='coerce'); u=u.merge(s,on='ARS',how='left')
u=u[u.노선명.isin(routes)&(u.gu==11740)&(u.평일주말=='평일')]
print('찾은 노선',u.노선명.nunique())
hc=[f'버스운행횟수_{h:02d}시' for h in range(24)]
runs=u.groupby('노선명')[hc].max().sum(); runs.index=range(24)
T=pd.read_csv('결과_강동송파_시간대.csv',index_col='h')
bus=pd.read_csv('결과_버스_강동송파_시간대추정.csv',index_col=0).iloc[:,0]
D=pd.DataFrame({'생활이동_강동to송파_평일':T['강동→송파_평일'],'송파몫_평일':T['송파몫_평일'],'송파노선_운행_평일':runs,'버스추정_하루평균':bus})
D['1회당_송파행이동']=D.생활이동_강동to송파_평일/D.송파노선_운행_평일
D['이동몫']=D.생활이동_강동to송파_평일/D.생활이동_강동to송파_평일.sum(); D['운행몫']=D.송파노선_운행_평일/D.송파노선_운행_평일.sum()
D['배수_이동몫/운행몫']=D.이동몫/D.운행몫
D.to_csv('결과_송파행_수요vs운행_시간대.csv'); print(D.round(3).to_string())
