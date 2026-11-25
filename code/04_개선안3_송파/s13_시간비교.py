# 동 짝별 걸리는 시간(대략): 초안 버스 vs 지하철(갈아타기 포함) vs 지금 바로 가는 버스
# 가정: 버스 평균 17km/h, 초안 출근 배차 7분(기다림 3.5분), 지하철 역 사이 2분·갈아타기 5분·첫 기다림 3분, 걷기는 두 수단 모두 양끝 합 8분(같게 둠)
import pandas as pd, numpy as np, json, heapq
K=json.load(open('결과_경로후보_상세.json'))['D 기본+장지차고지 종점']; C=pd.DataFrame(K['pairs'])
lines={'5하남':['천호','강동','길동','굽은다리','명일','고덕','상일동','강일'],'5마천':['천호','강동','둔촌동','올림픽공원','방이','오금','개롱','거여','마천'],
 '8':['암사','천호','강동구청','몽촌토성','잠실','석촌','송파','가락시장','문정','장지','복정'],'3':['오금','경찰병원','가락시장','수서'],
 '9':['중앙보훈병원','둔촌오륜','올림픽공원','한성백제','송파나루','석촌','석촌고분','삼전'],'2':['잠실나루','잠실','잠실새내','종합운동장']}
G={}
for L,ss in lines.items():
    for a,b in zip(ss,ss[1:]):
        for x,y in ((a,b),(b,a)): G.setdefault((x,L),[]).append(((y,L),2))
names={}
for (s,L) in list(G):
    names.setdefault(s,[]).append(L)
for s,Ls in names.items():
    for a in Ls:
        for b in Ls:
            if a!=b: G[(s,a)].append(((s,b),5))
def sub(o,d):
    best=99
    for so in o:
        for sd in d:
            if so==sd: return 0
            src=[(so,L) for L in names.get(so,[])]; D={x:3 for x in src}; h=[(3,x) for x in src]
            while h:
                t,x=heapq.heappop(h)
                if x[0]==sd: best=min(best,t); break
                if t>D.get(x,99): continue
                for y,w in G.get(x,[]):
                    if t+w<D.get(y,99): D[y]=t+w; heapq.heappush(h,(t+w,y))
    return best
# 동 → 가까운 역(동 안 또는 경계, 걸어서 10분 안팎으로 본 대표역)
st={'강동구 강일동':['강일'],'강동구 상일제1동':['상일동'],'강동구 상일제2동':['강일','상일동'],'강동구 고덕제1동':['고덕'],'강동구 고덕제2동':['상일동','고덕'],
'강동구 명일제1동':['명일'],'강동구 명일제2동':['명일','고덕'],'강동구 암사제3동':['명일','고덕'],'강동구 천호제1동':['굽은다리'],'강동구 천호제3동':['천호','강동'],
'강동구 길동':['길동','굽은다리'],'강동구 성내제3동':['둔촌동','강동'],'강동구 둔촌제1동':['둔촌동','둔촌오륜'],'강동구 둔촌제2동':['중앙보훈병원','둔촌동'],
'송파구 오륜동':['올림픽공원','둔촌오륜'],'송파구 오금동':['오금','방이'],'송파구 방이1동':['방이','올림픽공원'],'송파구 가락본동':['가락시장','송파'],'송파구 가락2동':['오금','경찰병원','개롱'],
'송파구 문정1동':['문정'],'송파구 문정2동':['문정'],'송파구 장지동':['장지'],'송파구 거여1동':['거여','개롱'],'송파구 위례동':['복정','장지'],'송파구 마천1동':['마천']}
C['지하철분']=[sub(st.get(a,[]),st.get(b,[]))+8 if a in st and b in st else np.nan for a,b in zip(C.강동동,C.송파동)]
C['초안버스분']=C.초안km/17*60+3.5+8
C['지금버스분']=C.y22_최단버스경로km/17*60+4+8
C['가장빠름']=np.select([C.초안버스분<=C[['지하철분','지금버스분']].min(axis=1).fillna(999)],['초안버스'],default=np.where(C.지하철분<=C.지금버스분.fillna(999),'지하철','지금버스'))
C['초안-지하철']=C.초안버스분-C.지하철분
C.to_csv('결과_시간비교_동짝.csv',index=False)
print(C.sort_values('양방향',ascending=False).head(20).round(0).to_string())
tot=C.양방향.sum(); print('짝',len(C),'이동',round(tot))
print('초안 버스가 가장 빠른 이동 비율',round(C[C.가장빠름=='초안버스'].양방향.sum()/tot,3))
print('초안이 지하철보다 5분 넘게 느리지 않은 이동 비율',round(C[C['초안-지하철']<=5].양방향.sum()/tot,3))
print('지금 버스 대비 줄어드는 시간(수요가중, 바로 가는 버스 있던 짝)', round(np.average((C.지금버스분-C.초안버스분).dropna(),weights=C.loc[C.지금버스분.notna(),'양방향']),1),'분')
print('수요가중 평균: 초안',round(np.average(C.초안버스분,weights=C.양방향),1),'지하철',round(np.average(C.지하철분.fillna(C.지하철분.mean()),weights=C.양방향),1))

# ── 걷는 시간을 실제 거리로: 동 중심 → 가장 가까운 역 / 초안 정류장 (걷기 4.5km/h, 길 굽음 1.3배) ──
X='../../동단위_레이어/'
rs=pd.read_csv('서울시버스노선별정류소정보_20260902.csv',dtype={'ARS_ID':str}).drop_duplicates('ARS_ID')
pat={s:s+'역' for s in names}; pat['중앙보훈병원']='중앙보훈병원역'
sx={}
for s,p in pat.items():
    t=rs[rs.정류소명.str.contains(p,na=False)&(rs.X좌표>127.0)&(rs.Y좌표>37.45)&(rs.Y좌표<37.6)]
    if s=='강동': t=t[~t.정류소명.str.contains('강동구청')]
    if s=='잠실': t=t[~t.정류소명.str.contains('잠실나루|잠실새내')]
    if s=='석촌': t=t[~t.정류소명.str.contains('석촌고분')]
    if s=='천호': t=t[t.X좌표<127.13]
    if len(t): sx[s]=(t.X좌표.median(),t.Y좌표.median())
lp=pd.read_csv(X+'외부데이터/행정동_생활인구_202204_평일주말_시간대평균.csv',dtype=str).drop_duplicates('행정동코드'); nm=dict(zip(lp.행정동코드,lp.구_행정동)); nm.update({'1174052500':'강동구 상일제1동','1174052600':'강동구 상일제2동'})
g=json.load(open(X+'외부데이터/행정동_경계_20220401_서울.geojson')); cen={}
for f in g['features']:
    cs=np.array(f['geometry']['coordinates'][0][0]); cen[nm.get(f['properties']['adm_cd2'],'')]=cs.mean(0)
D=lambda a,b: np.hypot((a[0]-b[0])*88.2,(a[1]-b[1])*111.0)
wm=lambda km: km*1.3/4.5*60
rst=[(s['x'],s['y']) for s in K['stops']]
def walk_st(dn,s): return wm(D(cen[dn],sx[s])) if dn in cen and s in sx else np.nan
def walk_rt(dn): return wm(min(D(cen[dn],p) for p in rst)) if dn in cen else np.nan
def sub2(o,d,tr):
    best=99
    for so in st.get(o,[]):
        for sd in st.get(d,[]):
            t=sub([so],[sd])
            if tr!=5: pass
            best=min(best,t+walk_st(o,so)+walk_st(d,sd))
    return best
C['지하철분_걷기포함']=[sub2(a,b,5) if a in st and b in st else np.nan for a,b in zip(C.강동동,C.송파동)]
C['초안버스분_걷기포함']=C.초안km/17*60+3.5+[walk_rt(a)+walk_rt(b) for a,b in zip(C.강동동,C.송파동)]
C['차이(버스-지하철)']=C.초안버스분_걷기포함-C.지하철분_걷기포함
C.to_csv('결과_시간비교_동짝.csv',index=False)
v=C.dropna(subset=['차이(버스-지하철)'])
print('\n[걷기 포함] 수요가중 평균 초안',round(np.average(v.초안버스분_걷기포함,weights=v.양방향),1),'지하철',round(np.average(v.지하철분_걷기포함,weights=v.양방향),1))
print('초안이 더 빠르거나 같은 이동',round(v[v['차이(버스-지하철)']<=0].양방향.sum()/v.양방향.sum(),3),' 5분 안쪽까지',round(v[v['차이(버스-지하철)']<=5].양방향.sum()/v.양방향.sum(),3))
print(v.sort_values('양방향',ascending=False)[['강동동','송파동','양방향','지하철분_걷기포함','초안버스분_걷기포함','차이(버스-지하철)']].head(15).round(0).to_string())
# 갈아타기 횟수
