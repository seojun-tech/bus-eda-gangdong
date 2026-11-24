# 2023.10 평일 2일로 같은 계산: 빈 짝 중 문정2동 순위, 초안 혜택 짝 이동량
import sys, zipfile, pandas as pd, json, numpy as np
src=sys.argv[1]; X='../../동단위_레이어/'
lp=pd.read_csv(X+'외부데이터/행정동_생활인구_202204_평일주말_시간대평균.csv',dtype=str).drop_duplicates('생활인구_행정동코드')
c8=dict(zip(lp.생활인구_행정동코드,lp.구_행정동)); c8.update({'11740525':'강동구 상일제1동','11740526':'강동구 상일제2동'})
R=[]
for d in ['231017','231018']:
    z=zipfile.ZipFile(f'{src}/d{d}.zip')
    for ch in pd.read_csv(z.open(z.namelist()[0]),usecols=['o_admdong_cd','d_admdong_cd','st_time_cd','cnt'],dtype={'o_admdong_cd':str,'d_admdong_cd':str},chunksize=3_000_000,encoding='cp949'):
        m=(ch.o_admdong_cd.str[:5].eq('11740')&ch.d_admdong_cd.str[:5].eq('11710'))|(ch.o_admdong_cd.str[:5].eq('11710')&ch.d_admdong_cd.str[:5].eq('11740'))
        ch=ch[m]; ch['h']=ch.st_time_cd.where(ch.st_time_cd<100,ch.st_time_cd//100); R.append(ch.groupby(['o_admdong_cd','d_admdong_cd','h']).cnt.sum())
g=(pd.concat(R).groupby(level=[0,1,2]).sum()/2).reset_index(); g['o']=g.o_admdong_cd.map(c8); g['d']=g.d_admdong_cd.map(c8)
f=g[g.o.str.startswith('강동')].groupby(['o','d']).cnt.sum(); b=g[g.o.str.startswith('송파')].groupby(['d','o']).cnt.sum()
f.index.names=['강동동','송파동']; b.index.names=['강동동','송파동']; tw=f.add(b,fill_value=0).rename('10월_양방향').reset_index()
P=pd.read_csv('결과_동짝_이동vs버스연결_우회율.csv'); P=P.merge(tw,on=['강동동','송파동'],how='left')
gap=(P.중심거리km>=2.5)&(~P.지하철바로)&((P.y22_우회율.isna())|(P.y22_우회율>=1.8))
for col in ['양방향','10월_양방향']:
    r=P[gap].groupby('송파동')[col].sum().sort_values(ascending=False); print(col,'빈 짝 목적지 상위',r.head(4).round(0).to_dict(),' 빈 짝 몫',round(P[gap][col].sum()/P[col].sum(),3))
K=json.load(open('결과_경로후보_상세.json'))['D 기본+장지차고지 종점']; C=pd.DataFrame(K['pairs'])
m=C.merge(P[['강동동','송파동','10월_양방향']],on=['강동동','송파동'],how='left')
print('초안 혜택 짝 하루 이동 4월',round(m.양방향.sum()),' 10월',round(m['10월_양방향'].sum()),' 순위상관',round(m[['양방향','10월_양방향']].corr('spearman').iloc[0,1],2))
