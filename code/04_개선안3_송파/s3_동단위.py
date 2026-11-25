import pandas as pd
B=pd.read_csv('생활이동_강동관련_동x동_시간_목적_202304_6일.csv.gz',dtype={'o_admdong_cd':str,'d_admdong_cd':str,'day':str})
B['h']=B.st_time_cd.where(B.st_time_cd<100,B.st_time_cd//100)
B['wk']=B.day.isin(['230415','230416']).map({False:'평일',True:'주말'})
B['cnt']=B.cnt/B.wk.map({'평일':4,'주말':2})
B=B[B.o_admdong_cd.str[:2].eq('11')&B.d_admdong_cd.str[:2].eq('11')]
gu=pd.read_csv('../../동단위_레이어/외부데이터/행정동_생활인구_202204_평일주말_시간대평균.csv',dtype=str).drop_duplicates('생활인구_행정동코드').set_index('생활인구_행정동코드').구_행정동
gu=pd.concat([gu,pd.Series({'11740525':'강동구 상일제1동','11740526':'강동구 상일제2동'})])  # 2023 코드: 상일동 분리(2022 생활인구 파일은 합쳐 있음)
B['o']=B.o_admdong_cd.map(gu); B['d']=B.d_admdong_cd.map(gu)
print('이름 못 붙은 코드', B.o.isna().sum(), B.d.isna().sum(), B[B.d.isna()].d_admdong_cd.unique()[:10])
B['og']=B.o_admdong_cd.str[:5]; B['dg']=B.d_admdong_cd.str[:5]
w=B[(B.wk=='평일')&(B.og=='11740')]
out=w[w.dg!='11740']
t=pd.DataFrame({'구밖이동':out.groupby('o').cnt.sum(),'송파행':out[out.dg=='11710'].groupby('o').cnt.sum(),'강남행':out[out.dg=='11680'].groupby('o').cnt.sum(),
  '송파행_7_8시':out[(out.dg=='11710')&out.h.isin([7,8])].groupby('o').cnt.sum(),'구밖_7_8시':out[out.h.isin([7,8])].groupby('o').cnt.sum(),
  '송파행_출근':out[(out.dg=='11710')&(out.move_purpose==1)].groupby('o').cnt.sum(),'전체출발':w.groupby('o').cnt.sum()})
t['송파몫']=t.송파행/t.구밖이동; t['송파몫_7_8시']=t.송파행_7_8시/t.구밖_7_8시; t['구밖비율']=t.구밖이동/t.전체출발
t=t.sort_values('송파몫',ascending=False); t.to_csv('결과_강동동별_송파의존_평일.csv'); print(t.round(3).to_string())
d=out[out.dg=='11710'].groupby('d').cnt.sum().sort_values(ascending=False); print((d/d.sum()).head(10).round(3).to_string())
d.to_csv('결과_송파도착동_평일.csv')
# 상위 동 짝
p=out[out.dg=='11710'].groupby(['o','d']).cnt.sum().sort_values(ascending=False).head(15); print(p.round(0).to_string())
p.to_csv('결과_강동송파_동짝_상위15_평일.csv')
