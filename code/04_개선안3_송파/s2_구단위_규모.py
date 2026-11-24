import pandas as pd
A=pd.read_csv('생활이동_구x구_시간_목적_202304_6일.csv.gz',dtype={'og':str,'dg':str,'day':str})
A['h']=A.st_time_cd.where(A.st_time_cd<100,A.st_time_cd//100)
A['wk']=A.day.isin(['230415','230416']).map({False:'평일',True:'주말'})
A['목적']=A.move_purpose.map({1:'출근',2:'등교',3:'귀가(추정)'}).fillna('그외')
S=A[A.og.str[:2].eq('11')&A.dg.str[:2].eq('11')].copy()
S['cnt']=S.cnt/S.wk.map({'평일':4,'주말':2})
gu=pd.read_csv('../../동단위_레이어/외부데이터/행정동_생활인구_202204_평일주말_시간대평균.csv',dtype=str)
gu['g5']=gu.생활인구_행정동코드.str[:5]; nm=gu.drop_duplicates('g5').set_index('g5').구_행정동.str.split().str[0]
S['o']=S.og.map(nm); S['d']=S.dg.map(nm)
S.to_pickle('/tmp/claude-0/-home-user/f40f7d73-25d6-5236-b08c-dfbc074fdb17/scratchpad/S.pkl')
g=S.groupby(['wk','o','d']).cnt.sum().reset_index()
for w in ['평일','주말']:
    x=g[(g.wk==w)&(g.o=='강동구')]; tot=x.cnt.sum(); out=x[x.d!='강동구']
    print(w,'강동 출발(서울 안) 하루',round(tot),'구 밖',round(out.cnt.sum()),'구밖비율',round(out.cnt.sum()/tot,3))
    print((out.set_index('d').cnt/out.cnt.sum()).sort_values(ascending=False).head(5).round(3).to_string())
x=g[(g.wk=='평일')&(g.o!=g.d)]
r=x.sort_values('cnt',ascending=False).groupby('o').apply(lambda t: pd.Series({'1위':t.d.iloc[0],'몫':t.cnt.iloc[0]/t.cnt.sum()}))
r=r.sort_values('몫',ascending=False); r.to_csv('결과_구별_1위이웃구_몫_평일.csv'); print(r.head(8).round(3).to_string()); print('강동 순위',list(r.index).index('강동구')+1,'/',len(r))
a=g[(g.wk=='평일')&(g.o=='강동구')&(g.d=='송파구')].cnt.sum(); b=g[(g.wk=='평일')&(g.o=='송파구')&(g.d=='강동구')].cnt.sum(); print('평일 강동->송파',round(a),'송파->강동',round(b))
# 시간대·목적
t=S[(S.o=='강동구')&(S.d=='송파구')].groupby(['wk','h']).cnt.sum().unstack(0)
o=S[(S.o=='강동구')&(S.d!='강동구')].groupby(['wk','h']).cnt.sum().unstack(0)
rv=S[(S.o=='송파구')&(S.d=='강동구')].groupby(['wk','h']).cnt.sum().unstack(0)
T=pd.DataFrame({'강동→송파_평일':t.평일,'송파몫_평일':t.평일/o.평일,'송파→강동_평일':rv.평일,'강동→송파_주말':t.주말,'송파몫_주말':t.주말/o.주말})
T.to_csv('결과_강동송파_시간대.csv'); print(T.round(3).to_string())
print(S[(S.o=='강동구')&(S.d=='송파구')&(S.wk=='평일')].groupby('목적').cnt.sum().round(0))
