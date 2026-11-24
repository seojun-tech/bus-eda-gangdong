import pandas as pd
X='../../동단위_레이어/'
s=pd.read_csv(X+'캐시/정류장_행정동.csv'); s['gu']=(s.hj//100000).astype('Int64')
b=pd.read_csv(X+'외부데이터/버스_노선별_정류장별_시간대별_승하차_202204.csv.gz',dtype={'버스정류장ARS번호':str})
b['ARS']=pd.to_numeric(b['버스정류장ARS번호'],errors='coerce'); b=b.merge(s,on='ARS',how='left')
hs=[f'{h}시승차총승객수' if h else '00시승차총승객수' for h in range(24)]; ha=[c.replace('승차','하차') for c in hs]
g=b.groupby('노선번호').gu.agg(lambda x:set(x.dropna())); both=[r for r,v in g.items() if 11740 in v and 11710 in v]
r=b[b.노선번호.isin(both)]
rows=[]
for k,t in r.groupby('노선번호'):
    G=t[t.gu==11740][hs].sum().values; T=t[hs].sum().values; P=t[t.gu==11710][ha].sum().values
    Gd=t[t.gu==11710][hs].sum().values; Pa=t[t.gu==11740][ha].sum().values
    rows.append(dict(노선=k,노선명=t.노선명.iloc[0],강동승차=G.sum()/30,송파하차=P.sum()/30,추정_강동to송파=(P*G.sum()/T.sum()).sum()/30,
                     추정_송파to강동=(Pa*Gd.sum()/T.sum()).sum()/30))
R=pd.DataFrame(rows).sort_values('추정_강동to송파',ascending=False); R.to_csv('결과_버스14노선_강동송파_추정.csv',index=False)
print(R.round(0).to_string()); print('합',R[['강동승차','송파하차','추정_강동to송파','추정_송파to강동']].sum().round(0).to_dict())
# 시간대별 추정
H=[]
for k,t in r.groupby('노선번호'):
    G=t[t.gu==11740][hs].sum().values; T=t[hs].sum().values; P=t[t.gu==11710][ha].sum().values
    H.append(P*G.sum()/T.sum()/30)
H=pd.Series(sum(H),index=range(24)); H.to_csv('결과_버스_강동송파_시간대추정.csv'); print(H.round(0).to_dict())
m=pd.read_csv(X+'외부데이터/지하철_역별_시간대별_승하차_202204.csv')
cols=[c for c in m.columns if '승차' in c]
gd={('5호선','강동'),('5호선','강일'),('5호선','고덕'),('5호선','굽은다리(강동구민회관앞)'),('5호선','길동'),('5호선','둔촌동'),('5호선','명일'),('5호선','상일동'),('5호선','천호(풍납토성)'),('8호선','강동구청'),('8호선','암사'),('8호선','천호(풍납토성)')}
m['k']=list(zip(m.호선명,m.지하철역)); mg=m[m.k.isin(gd)]
d=mg.set_index('k')[cols].sum(1)/30; print('지하철 강동 역 하루 승차', d.round(0).to_dict(), '합',round(d.sum()))
print('8호선 강동3역+둔촌동(마천 쪽) 승차', round(d[[('8호선','강동구청'),('8호선','암사'),('8호선','천호(풍납토성)'),('5호선','둔촌동')]].sum()))
