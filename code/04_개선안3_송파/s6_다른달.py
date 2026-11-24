import sys, zipfile, pandas as pd
src=sys.argv[1]; res=[]
for d in ['231017','231018']:
    z=zipfile.ZipFile(f'{src}/d{d}.zip')
    for ch in pd.read_csv(z.open(z.namelist()[0]),usecols=['o_admdong_cd','d_admdong_cd','st_time_cd','cnt'],dtype={'o_admdong_cd':str,'d_admdong_cd':str},chunksize=3_000_000,encoding='cp949'):
        ch=ch[ch.o_admdong_cd.str[:2].eq('11')&ch.d_admdong_cd.str[:2].eq('11')]
        ch['og']=ch.o_admdong_cd.str[:5]; ch['dg']=ch.d_admdong_cd.str[:5]; ch['h']=ch.st_time_cd.where(ch.st_time_cd<100,ch.st_time_cd//100)
        res.append(ch.groupby(['og','dg','h']).cnt.sum())
g=pd.concat(res).groupby(level=[0,1,2]).sum()/2
gg=g.groupby(level=[0,1]).sum().reset_index(); x=gg[gg.og!=gg.dg]
r=x.sort_values('cnt',ascending=False).groupby('og').apply(lambda t:t.cnt.iloc[0]/t.cnt.sum()).sort_values(ascending=False)
print('1위이웃몫 상위',r.head(4).round(3).to_dict())
o=x[x.og=='11740']; print('강동 구밖',round(o.cnt.sum()),'송파몫',round(o[o.dg=='11710'].cnt.sum()/o.cnt.sum(),3),'강동->송파',round(o[o.dg=='11710'].cnt.sum()))
h=g.loc['11740','11710']; ho=g.loc['11740'].drop('11740',level=0).groupby(level=1).sum()
print('시간대 송파몫', (h/ho).round(3).to_dict())
