# 시간대 파트(11/07) 0단계: 행정동 x 시간 패널 만들기 (새 데이터 없이 기존 외부데이터 재사용)
#  - 버스 운행(평일/주말, 시간별): 운행횟수 자료 + 정류장 이름 일치 정정(f2와 같은 규칙: 경기 정류장이 번호만 같아 붙은 행 제외)
#  - 버스 승차·하차(시간별, 한 달 합): 노선별 정류장별 시간대별 승하차
#  - 생활인구(평일/주말, 시간별 평균), 지하철 역별 시간대 승하차(역 좌표 → 행정동)
#  - 4월이 기본, 6·10월은 다시 계산용
import pandas as pd, numpy as np, json, sys, re
from shapely.geometry import shape, Point
P='/mnt/project-files/프로젝트2'; EXT=f'{P}/동단위_레이어/외부데이터'; WK='/tmp/claude-0/work'; O=f'{P}/최종발표/시간대_1107/결과'
HC=[f'버스운행횟수_{h:02d}시' for h in range(24)]
s22=pd.read_csv(f'{EXT}/버스정류소_유형_20220401.csv',dtype={'ARS번호':str,'행정동코드':str}); s22['ARS']=s22['ARS번호'].str.zfill(5)
allmap=s22.drop_duplicates('ARS').set_index('ARS')
oldmap=pd.read_csv(f'{P}/동단위_레이어/캐시/정류장_행정동.csv',dtype=str).set_index('ARS')['hj']
D=pd.read_csv(f'{P}/최종발표/결과/3_정정_행정동_두잣대.csv',dtype={'hj':str},encoding='utf-8-sig').set_index('hj')
IDX=D.index
def bigr(s): s=''.join(ch for ch in str(s) if ch.isalnum()); return {s[i:i+2] for i in range(len(s)-1)}
def same(a,b):
    if not isinstance(b,str) or not isinstance(a,str): return False
    for x in a.split('|'):
        A,B=bigr(x),bigr(b)
        if A and B and len(A&B)/min(len(A),len(B))>=0.34: return True
    return False
def runs(fn):
    r=pd.read_csv(f'{EXT}/{fn}',dtype={'정류장_ARS':str,'노선_ID':str})
    r['ARS']=r['정류장_ARS'].str.zfill(5)
    r=r.groupby(['노선_ID','ARS','평일주말'],as_index=False).agg({**{c:'sum' for c in ['버스운행횟수_일']+HC},'정류장명':'first'})
    r['hj']=r['ARS'].map(allmap['행정동코드']).fillna(r['ARS'].map(oldmap)); r['정류소명']=r['ARS'].map(allmap['정류소명'])
    r=r[r['hj'].notna()]
    pr=r[['정류장명','정류소명']].drop_duplicates(); pr['일치']=[same(a,b) for a,b in zip(pr['정류장명'],pr['정류소명'])]
    r=r.merge(pr,on=['정류장명','정류소명'],how='left'); return r[r['일치']]
def boards(m):
    h=pd.read_csv(f'{EXT}/버스_노선별_정류장별_시간대별_승하차_2022{m}.csv.gz',dtype={'버스정류장ARS번호':str,'노선번호':str})
    h=h[h['버스정류장ARS번호'].str.fullmatch(r'\d{5}',na=False)].copy(); h['hj']=h['버스정류장ARS번호'].map(allmap['행정동코드']).fillna(h['버스정류장ARS번호'].map(oldmap))
    on={x:f'{"00" if x==0 else x}시승차총승객수' for x in range(24)}; off={x:f'{"00" if x==0 else x}시하차총승객수' for x in range(24)}
    B=pd.DataFrame({f'승차_{x:02d}':pd.to_numeric(h[on[x]],errors='coerce').fillna(0).groupby(h['hj']).sum() for x in range(24)})
    A=pd.DataFrame({f'하차_{x:02d}':pd.to_numeric(h[off[x]],errors='coerce').fillna(0).groupby(h['hj']).sum() for x in range(24)})
    return B.join(A).reindex(IDX).fillna(0)
def runpanel(r,tag):
    wk=r[r['평일주말']=='평일'].groupby('hj')[HC].sum(); we=r[r['평일주말']=='주말'].groupby('hj')[HC].sum()
    wk.columns=[f'{tag}평일운행_{h:02d}' for h in range(24)]; we.columns=[f'{tag}주말운행_{h:02d}' for h in range(24)]
    return wk.join(we,how='outer').reindex(IDX).fillna(0)
MON={'04':'버스_노선별_정류장별_운행횟수_202204_평일주말평균.csv.gz','04중':'버스_노선별_정류장별_운행횟수_202204_평일주말중앙값.csv.gz','06':'버스_노선별_정류장별_운행횟수_202206_평일주말중앙값.csv.gz','10':'버스_노선별_정류장별_운행횟수_202210_평일주말중앙값.csv.gz'}
DAYS={'04':(21,9),'06':(21,9),'10':(19,12)}  # 평일/주말·공휴일 일수 (4월: 21/9, 6월: 지방선거6/1·현충일6/6 → 20/10이 맞음, 아래서 보정)
DAYS['06']=(20,10)  # 2022-06: 평일 22일 중 6/1(선거), 6/6(현충일) 휴일 → 20/10
DAYS['10']=(19,12)  # 2022-10: 평일 21일 중 10/3, 10/10 휴일 → 19/12
import os
for m in ([] if os.path.exists(f'{O}/0_패널_버스_10.csv') else ['04','06','10']):
    r=runs(MON[m]); rp=runpanel(r,'')
    if m=='04':
        r.to_pickle(f'{WK}/run04_ok.pkl')
        rm=runs(MON['04중']); runpanel(rm,'').to_csv(f'{O}/0_패널_운행_04중앙값.csv',encoding='utf-8-sig')
    bp=boards(m); X=rp.join(bp); X.attrs={}
    X.to_csv(f'{O}/0_패널_버스_{m}.csv',encoding='utf-8-sig'); print(m,'운행합',rp.filter(like='평일').sum().sum().round(),'승차합',bp.filter(like='승차').sum().sum())
# 생활인구
L=pd.read_csv(f'{EXT}/행정동_생활인구_202204_평일주말_시간대평균.csv',dtype={'행정동코드':str})
L['시']=L['시간대구분'].astype(int)
LP=L.pivot_table(index='행정동코드',columns=['평일주말','시'],values='총생활인구수')
LP.columns=[f'생활인구_{a}_{b:02d}' for a,b in LP.columns]; LP=LP.reindex(IDX); LP.to_csv(f'{O}/0_패널_생활인구.csv',encoding='utf-8-sig')
print('생활인구 결측 동',LP.isna().any(axis=1).sum())
# 지하철: 역 좌표 → 행정동
G=json.load(open(f'{EXT}/행정동_경계_20220401_서울.geojson')); polys=[(f['properties']['adm_cd2'],shape(f['geometry'])) for f in G['features']]
S=json.load(open(f'{P}/스토리라인/외부데이터/지하철역_주소좌표.geojson'))
st={}
for f in S['features']:
    p=Point(f['geometry']['coordinates']); hj=next((c for c,g in polys if g.contains(p)),None)
    st[f['properties']['name']]=(hj,*f['geometry']['coordinates'])
sw=pd.read_csv(f'{EXT}/지하철_역별_시간대별_승하차_202204.csv')
def norm(n): return re.sub(r'\(.*?\)','',str(n)).strip().rstrip('역')
key={}
for f in S['features']:
    nm=f['properties']['name']; full=str(f['properties'].get('name_full',nm))
    for part in re.split(r'[()]',full)+[nm]:
        if part.strip(): key.setdefault(norm(part),nm)
key.update({'당고개':key.get('불암산','당고개'),'이수':key.get('총신대입구','이수'),'뚝섬유원지':key.get('자양','뚝섬유원지')})
sw['역']=sw['지하철역'].map(lambda n: key.get(norm(n)))
miss=sw[sw['역'].isna()]['지하철역'].unique(); print('지하철 이름 못 맞춤',len(miss),list(miss)[:30])
sw['hj']=sw['역'].map(lambda k: st[k][0] if isinstance(k,str) and k in st else None)
cols={}
for c in sw.columns:
    m_=re.match(r'(\d\d)시-\d\d시 (승차|하차)인원',c)
    if m_: cols[c]=f'지하철{m_.group(2)}_{int(m_.group(1)):02d}'
SW=sw.dropna(subset=['hj']).groupby('hj')[list(cols)].sum().rename(columns=cols).reindex(IDX).fillna(0)
SW.to_csv(f'{O}/0_패널_지하철.csv',encoding='utf-8-sig')
pd.DataFrame([(k,*v) for k,v in st.items()],columns=['역','hj','X','Y']).to_csv(f'{O}/0_지하철역_행정동.csv',index=False,encoding='utf-8-sig')
print('지하철 있는 동',(SW.sum(axis=1)>0).sum(),'지하철 하차합 서울안', SW.filter(like='하차').sum().sum(), '원자료', sw[[c for c in cols if '하차' in c]].sum().sum())
