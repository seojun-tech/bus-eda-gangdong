# 기존(2022에 있던) 버스가 실제로 다니는 정류장 사이 연결만 이어 붙여 새 노선 초안 경로 만들기
import pandas as pd, numpy as np, heapq, json, sys
X='../../동단위_레이어/'
rs=pd.read_csv('서울시버스노선별정류소정보_20260902.csv',dtype={'노선명':str,'ARS_ID':str}); rs['ARS']=rs.ARS_ID.str.zfill(5)
u22=set(pd.read_csv(X+'외부데이터/버스_노선별_정류장별_운행횟수_202204_평일주말중앙값.csv.gz',usecols=['노선명'],dtype=str).노선명)
r=rs[rs.노선명.isin(u22)].sort_values(['ROUTE_ID','순번'])
pos=rs.drop_duplicates('ARS').set_index('ARS')[['정류소명','X좌표','Y좌표']]
def dd(a,b): return float(np.hypot((pos.X좌표[a]-pos.X좌표[b])*88.2,(pos.Y좌표[a]-pos.Y좌표[b])*111.0))
E={}
for rid,t in r.groupby('ROUTE_ID'):
    a=t.ARS.values
    for i in range(len(a)-1):
        if a[i]==a[i+1] or a[i] not in pos.index or a[i+1] not in pos.index: continue
        w=dd(a[i],a[i+1])
        if w>2.0: continue
        E.setdefault(a[i],{}); E[a[i]][a[i+1]]=min(w,E[a[i]].get(a[i+1],9e9))
def path(src,dst):
    D={s:0 for s in src}; prev={}; h=[(0,s) for s in src]; dst=set(dst)
    while h:
        d,x=heapq.heappop(h)
        if x in dst:
            p=[x]
            while p[-1] in prev: p.append(prev[p[-1]])
            return d,p[::-1]
        if d>D.get(x,9e9): continue
        for y,w in E.get(x,{}).items():
            if d+w<D.get(y,9e9): D[y]=d+w; prev[y]=x; heapq.heappush(h,(d+w,y))
    return None
W={'강동공영차고지':['25101','25341','25102'],'상일동역':['25133','25131','25523','25166','25134','25132','25165','25740'],'고덕역':['25139','25140','25518','25528'],
   '명일역':['25234','25233','25232','25235','25546'],'굽은다리역':['25782','25236','25348','25349','25237','25781'],'길동역':['25240','25241'],
   '둔촌동역':['25728','25247','25246','25727'],'중앙보훈병원역':['25330','25302','25303','25331','25539','25682'],'오금역':['24515','24338','24249','24767','24369','24523','24766','24339'],
   '가락시장역':['24009','24380','24363','24010','24385','24444'],'문정역':['24331','24547','24330'],'동부지법':['24530','24535'],'문정법조단지':['24013'],'문정2동주민센터':['24333'],'장지역.가든파이브':['24015','24475','24573','24442','24476','24801','24016']}
V={'A_문정직행':['강동공영차고지','상일동역','고덕역','명일역','굽은다리역','길동역','둔촌동역','오금역','문정역','문정법조단지'],
   'A2_가락시장경유':['강동공영차고지','상일동역','고덕역','명일역','굽은다리역','길동역','둔촌동역','오금역','가락시장역','문정역','문정법조단지']}
if len(sys.argv)>1 and sys.argv[1]=='both':  # 도로는 양방향이므로 반대 방향 연결도 허용
    for a in list(E):
        for b,w in list(E[a].items()): E.setdefault(b,{}); E[b][a]=min(w,E[b].get(a,9e9))
s=pd.read_csv(X+'캐시/정류장_행정동.csv'); s['ARS']=s.ARS.astype(str).str.zfill(5); hj=dict(zip(s.ARS,s.hj.astype('Int64').astype(str)))
out={}
for k,wp in V.items():
    seq=[]; tot=0; legs=[]
    cur=W[wp[0]]
    for nxt in wp[1:]:
        res=path(cur,W[nxt])
        if res is None: print(k,'끊김',nxt); break
        d,p=res; tot+=d; legs.append((nxt,round(d,2),len(p)-1)); seq+= p if not seq else p[1:]; cur=[p[-1]]
    out[k]=dict(km=round(tot,2),stops=seq,legs=legs)
    print(k,'총',round(tot,1),'km 정류장',len(seq)); print(legs)
    print(' → '.join(f"{pos.정류소명[a]}" for a in seq))
json.dump({k:dict(km=v['km'],legs=v['legs'],stops=[dict(ARS=a,이름=pos.정류소명[a],x=float(pos.X좌표[a]),y=float(pos.Y좌표[a]),행정동=hj.get(a)) for a in v['stops']]) for k,v in out.items()},open('결과_노선초안_경로.json','w'),ensure_ascii=False,indent=1)
