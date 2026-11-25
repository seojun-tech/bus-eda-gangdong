# ① 교수님 데이터 4종 전처리 재점검: 점검 항목마다 결과를 기록하고, 정제본을 저장한다.
import pandas as pd, numpy as np, json, os, re
RAW = '/tmp/claude-0/raw'
EXT = '/mnt/project-files/프로젝트2/동단위_레이어/외부데이터'
OUT = '/mnt/project-files/프로젝트2/재정비/1_전처리'
WK = '/tmp/claude-0/work'
LOG = []
def chk(data, item, result, action, ok=True):
    LOG.append(dict(데이터=data, 점검=item, 결과=result, 처리=action, 상태='통과' if ok else '수정'))
    print(f'[{data}] {item}: {result} -> {action}')

# ---------------- 1.1 버스 승하차 ----------------
D = '1.1 버스 승하차'
bus = pd.read_csv(f'{RAW}/1.1 BUS_STATION_BOARDING_MONTH_202204.csv', encoding='cp949', dtype={'버스정류장ARS번호': str, '노선번호': str, '사용일자': str})
n0 = len(bus)
chk(D, '행·열', f'{n0:,}행 × {bus.shape[1]}열, 인코딩 cp949', '그대로')
chk(D, '원본 결측', f'{int(bus.isna().sum().sum())}개', '없음')
days = sorted(bus['사용일자'].unique())
chk(D, '날짜 범위', f'{days[0]}~{days[-1]}, {len(days)}일', '4월 30일 모두 있음' if len(days) == 30 else '빠진 날 있음', len(days) == 30)
dup = bus.duplicated(['사용일자', '노선번호', '버스정류장ARS번호']).sum()
dupfull = bus.duplicated().sum()
dn = bus[bus.duplicated(['사용일자', '노선번호', '버스정류장ARS번호'], keep=False)]['노선번호']
chk(D, '중복 키(날짜·노선·ARS)', f'{dup:,}행 (완전 중복 {dupfull:,}). 많은 노선: ' + ', '.join(dn.value_counts().head(5).index), '순환 노선(01A 등)이 같은 정류장을 두 번 지나거나, 심야(N)·일부 노선이 달 중간 노선명이 바뀌어 두 줄로 기록된 것 → 별개 통과 기록이라 지우지 않고 합산 (교수님 합계와도 같음)', True)
neg = int((bus[['승차총승객수', '하차총승객수']] < 0).sum().sum())
chk(D, '음수 승하차', f'{neg}개', '없음', neg == 0)
zero = ((bus['승차총승객수'] == 0) & (bus['하차총승객수'] == 0)).sum()
chk(D, '승하차 모두 0인 행', f'{zero:,}행 ({zero/n0:.1%})', '그대로 둠(정류장 존재 정보, 합계 영향 없음)')
tilde = (bus['버스정류장ARS번호'] == '~').sum()
chk(D, "ARS '~' (가상 기점·종점)", f'{tilde:,}행, 승차 {bus.loc[bus["버스정류장ARS번호"]=="~","승차총승객수"].sum():,}명', '제외', False)
bus = bus[bus['버스정류장ARS번호'] != '~'].copy()
badlen = (~bus['버스정류장ARS번호'].str.fullmatch(r'\d{5}')).sum()
chk(D, 'ARS 5자리 숫자 형식', f'형식 어긋남 {badlen}행', "dtype=str로 읽어 앞자리 0 보존 (int로 바꾸면 06243→6243이 되어 구 매핑이 깨짐; 교수님 코드는 astype(int))", badlen == 0)
# 등록일자
lag = (pd.to_datetime(bus['등록일자'].astype(str)) - pd.to_datetime(bus['사용일자'])).dt.days
chk(D, '등록일자', f'사용일자 +{lag.min()}~{lag.max()}일 뒤 등록', '분석에 안 씀(집계 시점 정보)')
# 서울 정류장 목록
st = pd.read_csv(f'{RAW}/1.1 bus_station.csv', encoding='utf-8-sig', dtype=str)
st.columns = ['ARS', '정류소명']
chk('1.1 정류장 목록', '머리글', "첫 열 이름이 BOM 두 번('癤풞RS-ID')으로 깨져 있음", "encoding='utf-8-sig' + 열 이름 직접 지정", False)
chk('1.1 정류장 목록', '행 수·중복', f'{len(st):,}개, ARS 중복 {st["ARS"].duplicated().sum()}', '그대로')
# 2022-04-01 공식 좌표 목록(외부)과 비교
s22 = pd.read_csv(f'{EXT}/버스정류소_유형_20220401.csv', dtype={'ARS번호': str, '행정동코드': str})
s22['ARS'] = s22['ARS번호'].str.zfill(5)
chk('1.1 정류장 목록', '2022-04-01 서울시 공식 정류소(좌표) 목록과 비교', f'교수님 목록 {len(st):,} / 공식 {s22["ARS"].nunique():,}, 교수님 목록 중 공식에 있는 비율 {st["ARS"].isin(s22["ARS"]).mean():.1%}', '좌표·행정동은 공식 목록 사용')
gu = {f'{i:02d}': g for i, g in enumerate('종로구 중구 용산구 성동구 광진구 동대문구 중랑구 성북구 강북구 도봉구 노원구 은평구 서대문구 마포구 양천구 강서구 구로구 금천구 영등포구 동작구 관악구 서초구 강남구 송파구 강동구'.split(), 1)}
bus['구_ARS'] = bus['버스정류장ARS번호'].str[:2].map(gu)
out_prefix = bus['구_ARS'].isna()
chk(D, 'ARS 앞자리 01~25 밖', f'{out_prefix.sum():,}행, 승차 {bus.loc[out_prefix,"승차총승객수"].sum():,}명 (경기·인천 정류장)', '제외', False)
inseoul = bus['버스정류장ARS번호'].isin(st['ARS'])
fake = (~out_prefix) & (~inseoul)
ex = bus.loc[fake, '역명'].drop_duplicates().head(6).tolist()
chk(D, '앞자리는 01~25인데 서울 목록에 없는 정류장', f'{bus.loc[fake,"버스정류장ARS번호"].nunique()}개 정류장, {fake.sum():,}행, 승차 {bus.loc[fake,"승차총승객수"].sum():,}명 (예: {", ".join(ex)})', '제외 (교수님 코드의 inner merge가 실제 서울 필터 역할)', False)
bus = bus[inseoul & ~out_prefix].copy()
# 공식 좌표 목록의 행정동 기준 구와 ARS 앞자리 구 비교
hj = s22.drop_duplicates('ARS').set_index('ARS')['행정동코드']
bus['행정동코드'] = bus['버스정류장ARS번호'].map(hj)
cov = bus.groupby(bus['행정동코드'].notna())['승차총승객수'].sum()
chk(D, '정류장 → 행정동(2022-04-01 공식 좌표 목록의 행정동코드)', f'승차 기준 {cov.get(True,0)/cov.sum():.2%} 매칭, 정류장 {bus.loc[bus["행정동코드"].notna(),"버스정류장ARS번호"].nunique():,}/{bus["버스정류장ARS번호"].nunique():,}', '안 맞는 정류장은 2026 좌표 + 행정동 경계로 보충')
# 보충: 기존 캐시(2026 좌표→경계) 사용
old = pd.read_csv('/mnt/project-files/프로젝트2/동단위_레이어/캐시/정류장_행정동.csv', dtype=str)
oldmap = old.set_index('ARS')['hj']
both = bus[['버스정류장ARS번호', '행정동코드']].drop_duplicates()
both['old'] = both['버스정류장ARS번호'].map(oldmap)
bb = both.dropna()
agree = (bb['행정동코드'] == bb['old']).mean()
chk(D, '예전 매핑(2026 좌표+경계)과 공식 행정동코드 일치율', f'{agree:.1%} ({(bb["행정동코드"]!=bb["old"]).sum()}개 정류장 다름)', '이번부터 2022 공식 코드를 우선 사용 (예전 분석은 2026 좌표 기준이었음)', agree > .99)
miss = bus['행정동코드'].isna()
bus.loc[miss, '행정동코드'] = bus.loc[miss, '버스정류장ARS번호'].map(oldmap)
cov2 = bus['행정동코드'].notna()
chk(D, '보충 후 행정동 매칭', f'승차 기준 {bus.loc[cov2,"승차총승객수"].sum()/bus["승차총승객수"].sum():.2%}, 남은 정류장 {bus.loc[~cov2,"버스정류장ARS번호"].nunique()}개', '남은 정류장은 구 집계에만 쓰고 동 분석에서 제외')
# 행정동 코드 앞 5자리 구 vs ARS 구 일치
gucode = pd.read_csv(f'{EXT}/행정동_주민등록인구_연령_202204.csv', dtype={'행정동코드': str})
code2gu = gucode.set_index('행정동코드')['구']
bus['구_행정동'] = bus['행정동코드'].map(code2gu)
m = bus['구_행정동'].notna()
diff = bus.loc[m & (bus['구_행정동'] != bus['구_ARS'])]
chk(D, 'ARS 앞자리 구 vs 실제 위치(행정동) 구', f'다른 정류장 {diff["버스정류장ARS번호"].nunique()}개, 승차 {diff["승차총승객수"].sum()/bus["승차총승객수"].sum():.2%} (구 경계 도로 위 정류장)', '구 집계는 실제 위치(행정동) 기준으로 바꿈, ARS 기준과 비교표 남김', False)
# 노선 유형
bus['노선유형'] = np.select([bus['노선번호'].str.startswith('N'), bus['노선번호'].str.contains('[가-힣]'), bus['노선번호'].str.fullmatch(r'\d{4}'), bus['노선번호'].str.fullmatch(r'\d{3}'), bus['노선번호'].str.fullmatch(r'\d{2}')],
                       ['심야', '마을', '지선', '간선', '순환'], '기타')
vt = bus.groupby('노선유형')['승차총승객수'].sum()
chk(D, '노선 유형(번호 규칙으로 분류)', ', '.join(f'{k} {v/vt.sum():.1%}' for k, v in vt.sort_values(ascending=False).items()), '한글 번호 = 마을버스, N = 심야, 4자리 = 지선, 3자리 = 간선, 2자리 = 순환, 그 밖(01A·광역 9xxx 등) = 기타', True)
# 마을버스 포함 여부: 노선번호에 한글(예: 관악01)
ma = bus['노선번호'].str.contains('[가-힣]')
chk(D, '마을버스(관악01 등) 포함 여부', f'한글 노선번호 {bus.loc[ma,"노선번호"].nunique()}개 노선, 승차 {bus.loc[ma,"승차총승객수"].sum():,}', '마을버스 포함됨 → 동네 안 짧은 이동까지 잡힘 (단 마을버스는 차가 작아 같은 승차도 더 붐빔)', True)
# 이상치: 한 정류장×노선×날짜 최대
top = bus.nlargest(3, '승차총승객수')[['사용일자', '노선번호', '역명', '승차총승객수']]
chk(D, '이상치(행 단위 최대 승차)', '; '.join(f'{r.사용일자} {r.노선번호} {r.역명} {r.승차총승객수:,}' for r in top.itertuples()), '실제 대형 환승 거점(값 자체는 정상 범위) → 그대로')
# 일별 합계 흐름 + 요일
daily = bus.groupby('사용일자')['승차총승객수'].sum()
dts = pd.to_datetime(daily.index)
hol = []  # 2022년 4월 공휴일 없음
wk = daily[dts.weekday < 5]; we = daily[dts.weekday >= 5]
chk(D, '평일·주말 일수와 하루 평균', f'평일 {len(wk)}일 {wk.mean()/1e4:.0f}만 / 주말 {len(we)}일 {we.mean()/1e4:.0f}만 (4월 공휴일 없음)', '평일·주말 나눠 하루 평균으로 비교')
z = (wk - wk.median()) / wk.median()
chk(D, '튀는 날(평일 중앙값 대비 ±10%)', f'{(z.abs()>.1).sum()}일 ' + ', '.join(f'{d}({v:+.0%})' for d, v in z[z.abs() > .1].items()), '없으면 그대로')
bus['평일'] = pd.to_datetime(bus['사용일자']).dt.weekday < 5
chk(D, '최종 정제본', f'{len(bus):,}행, 정류장 {bus["버스정류장ARS번호"].nunique():,}, 노선 {bus["노선번호"].nunique()}, 승차 합계 {bus["승차총승객수"].sum():,}', '저장')
bus.to_pickle(f'{WK}/bus_clean.pkl')
# 교수님 코드 재현값 대조 (구 정류장 수 등, ARS 기준)
prof = bus.groupby('구_ARS').agg(정류장수=('버스정류장ARS번호', 'nunique'), 노선수=('노선번호', 'nunique'), 승차=('승차총승객수', 'sum'))
prev = pd.read_csv('/mnt/project-files/프로젝트2/전처리/df_seoul_bus_station.csv')
pv = prev.set_index('자치구')
same = (prof.loc[pv.index, '정류장수'].values == pv['정류장수'].values).all() and (prof.loc[pv.index, '승차'].values == pv['승차총승객수'].values).all()
chk(D, '10/16 전처리본(df_seoul_bus_station.csv)과 구별 정류장수·승차 대조', '25개 구 모두 일치' if same else '불일치 있음', '재현 확인', same)
# 구 집계 ARS 기준 vs 위치 기준 비교표
g1 = bus.groupby('구_ARS')['승차총승객수'].sum(); g2 = bus.groupby('구_행정동')['승차총승객수'].sum()
cmp = pd.DataFrame({'승차_ARS앞자리기준': g1, '승차_실제위치기준': g2}); cmp['차이%'] = (cmp.iloc[:, 1] / cmp.iloc[:, 0] - 1) * 100
cmp.round(2).to_csv(f'{OUT}/비교_구집계_ARS기준vs위치기준.csv', encoding='utf-8-sig')

# ---------------- 1.2 생활이동 ----------------
D = '1.2 생활이동'
cols = ['요일', '도착시간', '출발 시군구 코드', '도착 시군구 코드', '성별', '나이', '이동유형', '평균 이동 시간(분)', '이동인구(합)']
chunks = []; nrow = 0; star = 0; allmin = []
for c in pd.read_csv(f'{RAW}/1.2 seoul_moving_month_4.csv', usecols=cols + ['대상연월'], dtype={'이동인구(합)': str, '평균 이동 시간(분)': str, '대상연월': str}, chunksize=3_000_000):
    nrow += len(c)
    assert (c['대상연월'] == '202204').all()
    s = c['이동인구(합)'] == '*'; star += s.sum()
    v = pd.to_numeric(c.loc[~s, '이동인구(합)']); allmin.append(v.min())
    c['별표'] = s
    c['이동인구'] = pd.to_numeric(c['이동인구(합)'].where(~s, np.nan))
    c['이동시간'] = pd.to_numeric(c['평균 이동 시간(분)'], errors='coerce')
    c = c.drop(columns=['이동인구(합)', '평균 이동 시간(분)', '대상연월'])
    for k in ['요일', '성별', '이동유형']: c[k] = c[k].astype('category')
    c['출발 시군구 코드'] = c['출발 시군구 코드'].astype('int32'); c['도착 시군구 코드'] = c['도착 시군구 코드'].astype('int32')
    c['나이'] = c['나이'].astype('int16'); c['도착시간'] = c['도착시간'].astype('int8')
    chunks.append(c)
mv = pd.concat(chunks, ignore_index=True); del chunks
for k in ['요일', '성별', '이동유형']: mv[k] = mv[k].astype('category')
chk(D, '행·열', f'{nrow:,}행, 대상연월 202204 한 값', 'usecols·dtype·chunksize로 메모리 절약')
chk(D, "'*' 값(소수 인원 비공개)", f'{star:,}행 ({star/nrow:.1%}), * 아닌 값의 최솟값 {min(allmin):.2f}', '* = 3명 미만이라 1.5명으로 대체, 0·3명으로 민감도 확인', False)
age_star = mv.groupby('나이')['별표'].mean()
chk(D, "'*'가 나오는 나이", ', '.join(f'{a}세 {v:.0%}' for a, v in age_star[age_star > .01].items()), '고령층(65+)에는 * 없음 → 고령 분석은 대체값 영향 없음')
mt = mv['이동시간'].isna().sum()
chk(D, '평균 이동 시간 결측·범위', f'결측 {mt:,}, 범위 {mv["이동시간"].min():.0f}~{mv["이동시간"].max():.0f}분', '그대로')
chk(D, '요일·도착시간·성별·이동유형 값', f'요일 {sorted(mv["요일"].unique().tolist())}, 시간 {mv["도착시간"].min()}~{mv["도착시간"].max()}, 유형 {sorted(mv["이동유형"].unique().tolist())}', 'H=야간상주지(집), W=주간상주지(직장·학교), E=기타')
dupm = mv.duplicated(['요일', '도착시간', '출발 시군구 코드', '도착 시군구 코드', '성별', '나이', '이동유형']).sum()
chk(D, '중복 키', f'{dupm:,}행', '없음' if dupm == 0 else '확인 필요', dupm == 0)
seoul = (mv['출발 시군구 코드'].between(11000, 11999)) & (mv['도착 시군구 코드'].between(11000, 11999))
chk(D, '서울→서울 이동 비중', f'행 {seoul.mean():.1%}', '서울 안 이동만 사용(버스 자료도 서울 안)')
mv['이동인구1.5'] = mv['이동인구'].fillna(1.5)
mv = mv[seoul].copy()
codes = sorted(mv['도착 시군구 코드'].unique())
chk(D, '서울 시군구 코드 수', f'{len(codes)}개 ({codes[0]}~{codes[-1]})', '구 이름 대응표로 변환')
# 요일 수 보정
nd = {'월': 4, '화': 4, '수': 4, '목': 4, '금': 5, '토': 5, '일': 4}
chk(D, '요일별 날 수', '4월: 금·토 5번, 나머지 4번', '요일 합계를 날 수로 나눠 하루 평균으로 비교', False)
chk(D, '이동인구 단위', '월 합계인지 하루 평균인지 데이터 설명에 없음', '요일·시간대별 합으로 보고, 구 사이 비교(상대값)에만 사용', True)
mv.to_pickle(f'{WK}/moving_seoul.pkl')
# 10/16 전처리본 대조
prevm = pd.read_csv('/mnt/project-files/프로젝트2/전처리/df_seoul_moving.csv')
mm = mv[mv['도착시간'].between(5, 23)].groupby('도착 시군구 코드')['이동인구1.5'].sum()
diffm = (mm.loc[prevm['도착 시군구 코드']].values / prevm['유입 이동인구'].values - 1)
chk(D, '10/16 전처리본(유입 이동인구)과 대조', f'최대 차이 {np.abs(diffm).max():.4%}', '재현 확인', np.abs(diffm).max() < 1e-6)

# ---------------- 1.3 주민등록 ----------------
D = '1.3 주민등록'
p = pd.read_csv(f'{RAW}/1.3 seoul_people.csv', sep='\t', encoding='cp949', header=None)
chk(D, '머리글', '머리글이 3줄(인구/합계·한국인·외국인/계·남·여)', '3줄을 이어 열 이름 직접 지정 (교수님 코드 header=2는 계·남자·여자 열 이름이 한국인·외국인과 겹침 → 계.1, 계.2로 바뀜)', False)
p = p.iloc[3:].copy()
p.columns = ['기간', '자치구', '세대', '인구', '남', '여', '한국인', '한국인남', '한국인여', '외국인', '외국인남', '외국인여', '세대당인구', '65세이상']
for c in p.columns[2:]: p[c] = pd.to_numeric(p[c].astype(str).str.replace(',', ''))
chk(D, '기간', f'{p["기간"].unique().tolist()}', '2022년 1분기 말 기준 (버스 4월과 한 달 차이, 영향 작음)')
tot = p[p['자치구'] == '합계'].iloc[0]; p = p[p['자치구'] != '합계'].copy()
chk(D, "'합계' 행", '서울 전체 합계 1행 포함', '제외 (교수님 코드 drop(0)과 같은 결과)', False)
s_ok = all(abs(p[c].sum() - tot[c]) < 1 for c in ['세대', '인구', '65세이상'])
chk(D, '구 합 = 합계 행', '일치' if s_ok else '불일치', '확인', s_ok)
chk(D, '인구 = 한국인 + 외국인', f'최대 오차 {int((p["인구"]-p["한국인"]-p["외국인"]).abs().max())}', '확인')
r1 = (p['한국인'] / p['세대']).round(2); r2 = (p['인구'] / p['세대']).round(2)
chk(D, '세대당인구 정의', f'한국인÷세대와 일치 {int((r1==p["세대당인구"]).sum())}/25, 전체인구÷세대와 일치 {int((r2==p["세대당인구"]).sum())}/25', '한국인 기준임을 명시', True)
p['65세이상비율'] = p['65세이상'] / p['한국인']
chk(D, '65세 이상의 분모', '65세이상고령자는 한국인 기준(통계 원자료 정의)', '65세이상비율 = 65세이상 ÷ 한국인')
chk(D, '구별 65세 이상 비율 범위', f'{p["65세이상비율"].min():.1%}~{p["65세이상비율"].max():.1%}', '구 사이 차이가 작음 → 구 단위 고령 분석 변별력 약함, 동 단위(외부 주민등록)로 보강', False)
p.to_csv(f'{OUT}/정제_주민등록_구.csv', index=False, encoding='utf-8-sig')

# ---------------- 1.4 업종 ----------------
D = '1.4 업종'
b = pd.read_csv(f'{RAW}/1.4 business_type.csv', encoding='utf-8-sig', header=None)
inds = b.iloc[1, 2::2].tolist()
chk(D, '머리글', '3줄(상위10 / 업종명 / 사업체수·종사자수)', '업종명 × (사업체수, 종사자수)로 열 이름 직접 지정', False)
bb = b.iloc[3:].copy()
bb.columns = ['자치구', '동'] + [f'{i}|{k}' for i in inds for k in ['사업체수', '종사자수']]
for c in bb.columns[2:]: bb[c] = pd.to_numeric(bb[c].astype(str).str.replace(',', '').replace({'-': '0', 'nan': np.nan}))
chk(D, "'합계'·'소계' 행", f"합계 1행, 소계 {int((bb['동']=='소계').sum())}행", '동 분석에서 제외, 구 합계 검산에 사용', False)
dong = bb[(bb['동'] != '소계') & (bb['자치구'] != '합계')].copy()
chk(D, '동 단위', f'{len(dong)}개 동 (행정동 이름)', '행정동 코드로 맞춤')
# 행정동 이름 매칭
ref = gucode[['행정동코드', '구', '행정동']].copy()
norm = lambda s: re.sub(r'제(?=\d)', '', re.sub(r'[·.\s]', '', str(s)))
base = lambda s: re.sub(r'[·.\s]', '', str(s))
ref['k'] = ref['구'] + ref['행정동'].map(norm); dong['k'] = dong['자치구'] + dong['동'].map(base).replace({'여의도동': '여의동'})
mm_ = dong['k'].isin(ref['k'])
chk(D, '행정동 이름 → 2022-04 행정동 코드', f'{mm_.sum()}/{len(dong)} 매칭, 안 맞는 동: {", ".join((dong.loc[~mm_,"자치구"]+" "+dong.loc[~mm_,"동"]).tolist()[:8])}', '여의도동→여의동은 이름만 다름(수동 대응). 강동 상일동은 상일1·2동으로 나뉘기 전 이름 → 이 업종 자료는 2022-04보다 이전 기준(연도 표기 없음)', False)
chk(D, '업종 범위', f'서울 전체 사업체 수 상위 10개 업종만 ({", ".join(inds)})', '전체 일자리 규모가 아님 → 일자리 가설은 외부 「사업체현황」 전 업종 종사자 수로 판정, 이 자료는 업종 성격 EDA에만', False)
chk(D, '기준 연도', '파일에 연도 표기 없음', '한계로 명시')
sub = bb[bb['동'] == '소계'].set_index('자치구')
dsum = dong.groupby('자치구')[bb.columns[2:]].sum()
okb = np.allclose(dsum.loc[sub.index].values.astype(float), sub[bb.columns[2:]].values.astype(float), equal_nan=True)
chk(D, '동 합 = 소계', '일치' if okb else '일부 불일치', '확인', okb)
dong = dong.merge(ref[['k', '행정동코드']], on='k', how='left').drop(columns='k')
dong.to_csv(f'{OUT}/정제_업종_행정동.csv', index=False, encoding='utf-8-sig')

pd.DataFrame(LOG).to_csv(f'{WK}/점검표_교수님.csv', index=False, encoding='utf-8-sig')
print('done', len(LOG))
