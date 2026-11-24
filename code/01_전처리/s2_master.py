# ①-2 외부데이터 점검 + 행정동 기본표(분석 단위) 만들기
import pandas as pd, numpy as np, json, re, geopandas as gpd
from shapely.geometry import Point
EXT = '/mnt/project-files/프로젝트2/동단위_레이어/외부데이터'
OLD = '/mnt/project-files/프로젝트2/동단위_레이어'
OUT = '/mnt/project-files/프로젝트2/재정비/1_전처리'
WK = '/tmp/claude-0/work'
LOG = []
def chk(data, item, result, action, ok=True):
    LOG.append(dict(데이터=data, 점검=item, 결과=result, 처리=action, 상태='통과' if ok else '수정'))
    print(f'[{data}] {item}: {result} -> {action}')
HRS = list(range(24))

bus = pd.read_pickle(f'{WK}/bus_clean.pkl')
pop = pd.read_csv(f'{EXT}/행정동_주민등록인구_연령_202204.csv', dtype={'행정동코드': str}).rename(columns={'행정동코드': 'hj'})
D = pop.set_index('hj')[['구', '행정동', '총인구', '65세이상', '20_34세', '65세이상비율', '20_34세비율']].copy()
chk('외부: 주민등록 행정동', '동 수·합계', f'{len(D)}개 동, 총인구 {D["총인구"].sum():,} (교수님 구 자료 한국인 1분기 {9506778:,})', '4월 말 기준, 1분기 말과 차이 작음 확인')
# ---- 버스(교수님) → 행정동
b = bus[bus['행정동코드'].notna()].copy()
b['전반'] = b['사용일자'] < '20220418'
wd = b[b['평일']].groupby('행정동코드')['승차총승객수'].sum() / 21
we = b[~b['평일']].groupby('행정동코드')['승차총승객수'].sum() / 9
D['평일승차'] = wd; D['주말승차'] = we
D['평일하차'] = b[b['평일']].groupby('행정동코드')['하차총승객수'].sum() / 21
D['정류장수'] = b.groupby('행정동코드')['버스정류장ARS번호'].nunique()
tt = b.groupby(['행정동코드', '노선유형'])['승차총승객수'].sum().unstack(fill_value=0)
D['마을비중'] = tt['마을'] / tt.sum(axis=1); D['지선마을비중'] = (tt['마을'] + tt['지선']) / tt.sum(axis=1)
# 4/18 전후 (평일 날 수: 전반 4/1~17 평일 11일, 후반 10일)
dd = pd.to_datetime(b['사용일자'])
D['평일승차_전반'] = b[b['평일'] & b['전반']].groupby('행정동코드')['승차총승객수'].sum() / ((dd[b['평일'] & b['전반']]).dt.date.nunique())
D['평일승차_후반'] = b[b['평일'] & ~b['전반']].groupby('행정동코드')['승차총승객수'].sum() / ((dd[b['평일'] & ~b['전반']]).dt.date.nunique())

# ---- 공급: 2022 실제 운행횟수
names = set(bus['노선번호'])
def norm(x):
    x = str(x)
    if x in names: return x
    m = re.match(r'^([가-힣]*\d+[A-Z]?)', x)
    return m.group(1) if m and m.group(1) in names else x
HC = [f'버스운행횟수_{h:02d}시' for h in HRS]
s22 = pd.read_csv(f'{EXT}/버스정류소_유형_20220401.csv', dtype={'ARS번호': str, '행정동코드': str}); s22['ARS'] = s22['ARS번호'].str.zfill(5)
stop_hj = bus.drop_duplicates('버스정류장ARS번호').set_index('버스정류장ARS번호')['행정동코드']
# 운행 기록만 있는 정류장(승차 기록 없음)도 행정동 붙이기
allmap = s22.drop_duplicates('ARS').set_index('ARS')['행정동코드']
oldmap = pd.read_csv(f'{OLD}/캐시/정류장_행정동.csv', dtype=str).set_index('ARS')['hj']
def stop2hj(a):
    if a in stop_hj.index and pd.notna(stop_hj[a]): return stop_hj[a]
    if a in allmap.index: return allmap[a]
    return oldmap.get(a, np.nan)
def load_run(path):
    r = pd.read_csv(path, dtype={'정류장_ARS': str, '노선명': str})
    r['노선번호'] = r['노선명'].map(norm)
    r = r.groupby(['노선번호', '정류장_ARS', '평일주말'], as_index=False)[['버스운행횟수_일'] + HC].sum().rename(columns={'정류장_ARS': 'ARS'})
    u = r['ARS'].drop_duplicates(); mp = pd.Series([stop2hj(a) for a in u], index=u)
    r['hj'] = r['ARS'].map(mp)
    return r
run4 = load_run(f'{EXT}/버스_노선별_정류장별_운행횟수_202204_평일주말평균.csv.gz')
# 매칭률: 평일 승차 중 같은 노선·정류장 운행 기록이 있는 비율
w = b[b['평일']].groupby(['노선번호', '버스정류장ARS번호'])['승차총승객수'].sum().reset_index()
k = set(zip(run4.loc[run4['평일주말'] == '평일', '노선번호'], run4.loc[run4['평일주말'] == '평일', 'ARS']))
w['m'] = [(a, c) in k for a, c in zip(w['노선번호'], w['버스정류장ARS번호'])]
chk('외부: 2022-04 실제 운행횟수', '승차 기록과 노선·정류장 매칭', f'평일 승차 기준 {w.loc[w.m,"승차총승객수"].sum()/w["승차총승객수"].sum():.1%}', "노선명 정규화(예: '110B국민대'→'110B')")
chk('외부: 2022-04 실제 운행횟수', '정류장 → 행정동', f'운행 기록 정류장 {run4["ARS"].nunique():,}개 중 {run4.drop_duplicates("ARS")["hj"].notna().mean():.1%}', '승차 매핑과 같은 규칙')
# 합계 시간대 = 일 합계 확인
diffh = (run4[HC].sum(axis=1) - run4['버스운행횟수_일']).abs().sum() / run4['버스운행횟수_일'].sum()
chk('외부: 2022-04 실제 운행횟수', '시간대 합 = 하루 합', f'전체 차이 {diffh:.3%} (하루 평균을 시간대별로 따로 낸 반올림 차이)', '확인', diffh < .001)
chk('외부: 2022-04 실제 운행횟수', '행정동 못 붙은 정류장(45%)', '서울 정류장 목록에 없는 정류장 = 서울 노선이 지나는 경기·인천 구간', '서울 밖이라 제외(정상)')
r4 = run4.dropna(subset=['hj'])
for lab, wk in [('평일', '평일'), ('주말', '주말')]:
    g = r4[r4['평일주말'] == wk].groupby('hj')
    D[f'{lab}정차'] = g['버스운행횟수_일'].sum()
    for h in HRS: D[f'{lab}정차_{h:02d}'] = g[HC[h]].sum()
D['노선수'] = r4[r4['평일주말'] == '평일'].groupby('hj')['노선번호'].nunique()
# ---- 시간대별 승차 (월 합계): 4·6·10월
def load_hour(m):
    h = pd.read_csv(f'{EXT}/버스_노선별_정류장별_시간대별_승하차_2022{m}.csv.gz', dtype={'버스정류장ARS번호': str})
    h = h[h['버스정류장ARS번호'].str.fullmatch(r'\d{5}', na=False)]
    u = h['버스정류장ARS번호'].drop_duplicates(); mp = pd.Series([stop2hj(a) for a in u], index=u)
    h['hj'] = h['버스정류장ARS번호'].map(mp)
    cols = [f'{"00" if x == 0 else x}시승차총승객수' for x in HRS]
    return h, cols
h4, hc = load_hour('04')
tot_h = h4[hc].sum().sum()
chk('외부: 시간대별 승하차 2022-04', '교수님 일별 자료와 월 합계 대조', f'시간대 자료 승차 {tot_h:,.0f} vs 교수님 자료(서울 외 포함 전체) {bus["승차총승객수"].sum():,} → 비율 {tot_h/bus["승차총승객수"].sum():.3f}', '시간대 자료에는 경기 정류장 포함, 서울 정류장만 행정동에 붙여 사용')
g = h4.dropna(subset=['hj']).groupby('hj')[hc].sum()
for i, c in enumerate(hc): D[f'승차월_{i:02d}'] = g[c]
# 일별 자료와 동별 월 승차 비교
mon = b.groupby('행정동코드')['승차총승객수'].sum()
rr = pd.concat([mon, g.sum(axis=1)], axis=1).dropna()
chk('외부: 시간대별 승하차 2022-04', '동별 월 승차: 시간대 자료 vs 교수님 일별 자료', f'상관 {np.corrcoef(rr.iloc[:,0], rr.iloc[:,1])[0,1]:.4f}, 합계 비 {rr.iloc[:,1].sum()/rr.iloc[:,0].sum():.4f}', '같은 원천이라 거의 같아야 함')
# 6·10월: 시간대 승차 + 운행
for m, (nwd, nwe) in {'06': (20, 10), '10': (19, 12)}.items():
    hm, hcm = load_hour(m)
    gm = hm.dropna(subset=['hj']).groupby('hj')[hcm].sum()
    for i, c in enumerate(hcm): D[f'승차월{m}_{i:02d}'] = gm[c]
    rm = load_run(f'{EXT}/버스_노선별_정류장별_운행횟수_2022{m}_평일주말중앙값.csv.gz').dropna(subset=['hj'])
    for lab in ['평일', '주말']:
        gg = rm[rm['평일주말'] == lab].groupby('hj')
        for h in HRS: D[f'{lab}정차{m}_{h:02d}'] = gg[HC[h]].sum()
        D[f'{lab}정차{m}'] = gg['버스운행횟수_일'].sum()
    D[f'일수{m}'] = f'{nwd}/{nwe}'
# 6·10월 일별(교수님과 같은 형식) → 평일 하루 승차
for m in ['06', '10']:
    x = pd.read_csv(f'{EXT}/BUS_STATION_BOARDING_MONTH_2022{m}_원본.csv.gz', encoding='cp949', dtype=str)
    x.columns = ['사용일자', '노선번호', '노선명', '표준ID', 'ARS', '역명', '승차', '하차', '등록일자']
    x = x[x['ARS'].str.fullmatch(r'\d{5}', na=False)]; x['승차'] = pd.to_numeric(x['승차'])
    dt = pd.to_datetime(x['사용일자'])
    hol = {'06': ['20220601', '20220606'], '10': ['20221003', '20221010']}[m]
    x['평일'] = (dt.dt.weekday < 5) & ~x['사용일자'].isin(hol)
    u = x['ARS'].drop_duplicates(); mp = pd.Series([stop2hj(a) for a in u], index=u); x['hj'] = x['ARS'].map(mp)
    x = x[x['ARS'].isin(bus['버스정류장ARS번호'].unique()) | x['hj'].notna()]
    nd = x.loc[x['평일'], '사용일자'].nunique()
    D[f'평일승차_{m}'] = x[x['평일']].groupby('hj')['승차'].sum() / nd
    chk(f'외부: 버스 승하차 2022-{m}', '평일 수·공휴일', f'평일 {nd}일 (공휴일 {", ".join(hol)} 제외)', '평일 하루 평균')

# ---- 생활인구
lp = pd.read_csv(f'{EXT}/행정동_생활인구_202204_평일주말_시간대평균.csv', dtype={'행정동코드': str, '시간대구분': str})
chk('외부: 생활인구 2022-04', '동 수', f'{lp["행정동코드"].nunique()}개 (상일1·2동 합본, 구로 항동 없음)', '상일1·2는 주민 비율로 나눠 붙임, 항동은 결측')
pv = lp.pivot_table(index=['행정동코드', '평일주말'], columns='시간대구분', values='총생활인구수')
wdp = pv.xs('평일', level=1)
day = wdp[[f'{h:02d}' for h in range(10, 17)]].mean(axis=1); night = wdp[['03', '04', '05']].mean(axis=1)
D['낮생활인구'] = day; D['새벽생활인구'] = night
# 상일 합본 처리
sang = [h for h in D.index if D.loc[h, '행정동'] in ('상일제1동', '상일제2동')]
src = [c for c in lp['행정동코드'].unique() if c not in D.index]
chk('외부: 생활인구 2022-04', '주민등록에 없는 코드', f'{src}', '상일동 합본 코드 → 두 동에 주민 비율로 배분')
for c in src:
    for col, ser in [('낮생활인구', day), ('새벽생활인구', night)]:
        tot = D.loc[sang, '총인구'].sum()
        for h in sang: D.loc[h, col] = ser[c] * D.loc[h, '총인구'] / tot
D['낮유입배율'] = D['낮생활인구'] / D['새벽생활인구']
chk('외부: 생활인구 2022-04', '새벽(3~5시) 생활인구 vs 주민등록 인구', f'상관 {D[["새벽생활인구","총인구"]].corr().iloc[0,1]:.3f}, 비 중위 {(D["새벽생활인구"]/D["총인구"]).median():.2f}', '낮 유입 배율 = 평일 낮(10~16시) ÷ 평일 새벽(3~5시) 생활인구, 같은 자료끼리 나눠 주민등록과의 차이 영향 제거')
# ---- 세대·사업체·자동차
hh = pd.read_csv(f'{EXT}/행정동_세대원수별_세대수_202204.csv', dtype={'행정동코드': str}).set_index('행정동코드')
D['1인세대비율'] = hh['1인세대비율']; D['전체세대'] = hh['전체세대']
bz = pd.read_csv(f'{EXT}/행정동_사업체_종사자_2021_2022.csv', dtype={'행정동코드': str})
z21 = bz[bz['기준연도'] == 2021].set_index('행정동코드'); z22 = bz[bz['기준연도'] == 2022].set_index('행정동코드')
D['종사자수'] = z21['종사자수']; D['종사자수_2022'] = z22['종사자수']
chk('외부: 사업체현황', '기준 연도 선택', f'2021년 말 기준을 사용(2022-04에 더 가까움). 2021 vs 2022 동별 종사자 순위상관 {D[["종사자수","종사자수_2022"]].corr("spearman").iloc[0,1]:.3f}', '2022 기준으로도 같은지 확인용 열 보관')
car = pd.read_csv(f'{EXT}/행정동_자동차등록_202204.csv', dtype={'행정동코드': str}).set_index('행정동코드')
D['자가용승용'] = car['자가용승용대수']
# ---- 면적
gj = gpd.read_file(f'{EXT}/행정동_경계_20220401_서울.geojson')
gj = gj.set_index('adm_cd2'); D['면적km2'] = gj.to_crs(5179).area / 1e6
chk('외부: 행정동 경계 2022-04-01', '코드 일치', f'경계 {len(gj)}개, 주민등록 코드와 일치 {gj.index.isin(D.index).sum()}', '면적 계산(EPSG:5179)')

# ---- 지하철역 (2022년 4월에 운행 중이던 역만)
st = json.load(open('/mnt/project-files/프로젝트2/스토리라인/외부데이터/지하철역_주소좌표.geojson'))
S = pd.DataFrame([{**f['properties'], 'x': f['geometry']['coordinates'][0], 'y': f['geometry']['coordinates'][1]} for f in st['features']])
sub = pd.read_csv(f'{EXT}/지하철_역별_일별_승하차_202204.csv')
nrm = lambda s: re.sub(r'\(.*?\)', '', str(s)).replace('역', '').strip() if str(s) != '서울역' else '서울'
sub['k'] = sub['역명'].map(nrm); S['k'] = S['name'].map(nrm).replace({'불암산': '당고개', '자양': '뚝섬유원지'})
only_sl = S['lines'].str.contains('신림') & ~S['lines'].str.contains(';')
sinbun = S['lines'].str.contains('신분당') & S['in_seoul']
S4 = S[(S['k'].isin(sub['k']) | sinbun) & ~only_sl & S['in_seoul']].copy()
chk('외부: 지하철역 좌표', '역 이름 바뀐 곳·빠진 노선', '불암산(2024 개명)=당고개, 자양(2024 개명)=뚝섬유원지로 되돌림. 신분당선(양재시민의숲·청계산입구)은 서울교통공사 승하차 자료에 없지만 2022년 운행 중 → 좌표에 포함(승차 0으로 처리)', '보정', False)
miss = sorted(set(sub['k']) - set(S['k']))
chk('외부: 지하철역 좌표', '2022-04 운행 역만 고르기', f'좌표 목록 {len(S)}개 중 2022-04 승하차 기록 있는 서울 역 {len(S4)}개 (신림선 단독 역 제외). 승하차 역명 중 좌표 못 찾은 것 {len(miss)}개: {", ".join(miss[:12])}', '좌표 목록에 2024~2025년 개통 역이 섞여 있어 승하차 기록으로 걸러냄', False)
sgeo = gpd.GeoDataFrame(S4, geometry=gpd.points_from_xy(S4.x, S4.y), crs=4326).to_crs(5179)
# 정류장 좌표(2022-04-01 공식)
s22g = gpd.GeoDataFrame(s22.drop_duplicates('ARS'), geometry=gpd.points_from_xy(s22.drop_duplicates('ARS').X, s22.drop_duplicates('ARS').Y), crs=4326).to_crs(5179)
from scipy.spatial import cKDTree
tree = cKDTree(np.c_[sgeo.geometry.x, sgeo.geometry.y])
dist, _ = tree.query(np.c_[s22g.geometry.x, s22g.geometry.y])
s22g['역거리'] = dist
used = s22g[s22g['ARS'].isin(bus['버스정류장ARS번호'])]
used = used.assign(hj=used['ARS'].map(stop_hj))
D['역500비율'] = used.groupby('hj')['역거리'].apply(lambda v: (v <= 500).mean())
D['역거리중위'] = used.groupby('hj')['역거리'].median()
old = pd.read_csv(f'{OLD}/결과_2022운행_재계산_행정동.csv', dtype={'hj': str}).set_index('hj')
cc = pd.concat([D['역500비율'], old['역500비율']], axis=1).dropna()
chk('외부: 지하철역 좌표', '역500비율: 새 계산(2022 공식 정류장 좌표) vs 예전(2026 좌표)', f'순위상관 {cc.corr("spearman").iloc[0,1]:.3f}, 평균 차이 {(cc.iloc[:,0]-cc.iloc[:,1]).abs().mean():.3f}', '새 계산 사용')
# 지하철 승차: 역 → 행정동 (평일 하루)
sub['dt'] = pd.to_datetime(sub['사용일자'].astype(str)); sw = sub[sub['dt'].dt.weekday < 5].groupby('k')['승차총승객수'].sum() / 21
sj = gpd.sjoin(sgeo[['k', 'geometry']], gj.to_crs(5179)[['geometry']], predicate='within')
sj = sj.rename(columns={'adm_cd2': 'hj'}) if 'adm_cd2' in sj.columns else sj.rename(columns={'index_right': 'hj'})
sj = sj.drop_duplicates('k')
D['지하철평일승차'] = sj.assign(v=sj['k'].map(sw)).groupby('hj')['v'].sum()
D['지하철평일승차'] = D['지하철평일승차'].fillna(0)
D['지하철역수'] = sj.groupby('hj').size(); D['지하철역수'] = D['지하철역수'].fillna(0)
# 신림선 역이 있는 동
sl = S[S['lines'].str.contains('신림')]
slg = gpd.GeoDataFrame(sl, geometry=gpd.points_from_xy(sl.x, sl.y), crs=4326).to_crs(5179)
slj = gpd.sjoin(slg, gj.to_crs(5179)[['geometry']], predicate='within')
key = 'adm_cd2' if 'adm_cd2' in slj.columns else 'index_right'
D['신림선역동'] = D.index.isin(slj[key])
chk('외부: 신림선', '역이 있는 행정동', ', '.join(D.loc[D['신림선역동'], '구'] + ' ' + D.loc[D['신림선역동'], '행정동']), '2022-05-28 개통, 4월 분석에선 제외하고 4→6·10월 변화에만 사용')
# ---- 경사 (정류장 100m 평균 경사, AWS terrarium z13)
sl_ = pd.read_csv(f'{OLD}/처방레이어/정류장_고도경사.csv', dtype={'ARS': str})
sl_['hj'] = sl_['ARS'].map(stop_hj)
D['경사'] = sl_.groupby('hj')['경사100_도'].median()
D['고도'] = sl_.groupby('hj')['고도_m'].median()
D['고도범위'] = sl_.groupby('hj')['고도_m'].agg(lambda v: v.quantile(.9) - v.quantile(.1))
flat = D.loc[D['행정동'].isin(['여의동', '목1동', '잠실2동']), '경사'].round(1).tolist(); hill = D.loc[D['행정동'].isin(['후암동', '삼양동', '난곡동', '옥수동']), '경사'].round(1).tolist()
chk('외부: 경사', '평지 동 vs 언덕 동 값이 상식과 맞나', f'평지(여의·목1·잠실2) {flat} / 언덕(후암·삼양·난곡·옥수) {hill}', '정류장 100m 평균 경사(약 15m 해상도). 건물 높이가 섞인 지표면 자료라 평지도 2~3도로 나옴 → 순위로만 사용, 동 안 고도 차(상위10%−하위10%)로 교차 확인')

# ---- 파생 지표
D['평일승차_주민천명당'] = D['평일승차'] / D['총인구'] * 1000
D['운행당승차'] = D['평일승차'] / D['평일정차']
D['주말운행당승차'] = D['주말승차'] / D['주말정차']
D['천명당정차'] = D['평일정차'] / D['총인구'] * 1000
D['종사자배율'] = D['종사자수'] / D['총인구']
D['지하철_주민당'] = D['지하철평일승차'] / D['총인구']
# 시간대 운행당 (월 승차 ÷ 월 정차 = 평일×21 + 주말×9)
def per_trip(hs, month=''):
    if month == '':
        num = sum(D[f'승차월_{h:02d}'] for h in hs); den = sum(D[f'평일정차_{h:02d}'] * 21 + D[f'주말정차_{h:02d}'] * 9 for h in hs)
    else:
        nwd, nwe = map(int, D[f'일수{month}'].iloc[0].split('/'))
        num = sum(D[f'승차월{month}_{h:02d}'] for h in hs); den = sum(D[f'평일정차{month}_{h:02d}'] * nwd + D[f'주말정차{month}_{h:02d}'] * nwe for h in hs)
    return num / den.replace(0, np.nan)
for m in ['', '06', '10']:
    D[f'출근운행당{m}'] = per_trip([7, 8], m)
    D[f'퇴근운행당{m}'] = per_trip([18, 19], m)
    D[f'낮운행당{m}'] = per_trip(range(10, 17), m)
    D[f'심야운행당{m}'] = per_trip([22, 23, 0, 1, 2, 3], m)
    D[f'하루운행당{m}'] = per_trip(HRS, m)
D['분석대상'] = (D['정류장수'] >= 5) & D['평일정차'].gt(0) & D['총인구'].gt(0)
chk('분석 단위', '행정동 선택 기준', f'정류장 5곳 이상·운행 기록 있음: {int(D["분석대상"].sum())}/{len(D)}개 동, 평일 승차의 {D.loc[D["분석대상"],"평일승차"].sum()/D["평일승차"].sum():.1%}', '정류장 4곳 이하 동은 값이 튀어서 제외 (제외 동 목록 남김)')
ex = D[~D['분석대상']]
chk('분석 단위', '제외된 동', ', '.join(ex['구'] + ' ' + ex['행정동']), '부록에 기록')
D.to_pickle(f'{WK}/dong.pkl')
keep = [c for c in D.columns if not re.search(r'_\d\d$', c)]
D[keep].to_csv(f'{OUT}/행정동_기본표.csv', encoding='utf-8-sig')
old_log = pd.read_csv(f'{WK}/점검표_교수님.csv')
pd.concat([old_log, pd.DataFrame(LOG)]).to_csv(f'{OUT}/점검표_전처리.csv', index=False, encoding='utf-8-sig')
print('dong rows', len(D), 'analysis', int(D['분석대상'].sum()))
