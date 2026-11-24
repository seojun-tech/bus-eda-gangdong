# 최종 ④ 강동 개선안(솔루션) 근거 — 2022-04 자료(출발→도착만 2023-04)
# (1) 시간대별 붐빔(출근·퇴근·심야·주말) 정정 운행 기준, 서울 동 중앙값과 비교
# (2) 노선별 강동 구간 승차·운행당 승차 (있는 노선이 이미 꽉 찼나)
# (3) 심야버스(N) 강동 통과 현황
# (4) 동별 지하철역 거리·언덕·노선 수 (마을순환·소형 노선 조건)
# (5) 구 안 재배치로 메울 수 있는 양
# (6) 출발→도착: 아침에 어디로 가나
import pandas as pd, numpy as np, json
P = '/mnt/project-files/프로젝트2'; EXT = f'{P}/동단위_레이어/외부데이터'; WK = '/tmp/claude-0/work'; OUT = f'{P}/최종발표/결과'
B = pd.read_csv(f'{P}/재정비/1_전처리/행정동_기본표.csv', dtype={'hj': str}).set_index('hj')
S = pd.read_csv(f'{OUT}/2_행정동_운행_정정.csv', dtype={'hj': str}).set_index('hj')
F = pd.read_pickle(f'{WK}/f1_정정.pkl')
GD = B[B['구'] == '강동구'].index
NAME = B['행정동'].str.replace('제', '', regex=False)
LOG = []
def lg(k, v): LOG.append(dict(항목=k, 값=v)); print(k, '|', v)

# ---------- (1) 시간대별 승차: 이름 맞는 정류장만 ----------
h = pd.read_csv(f'{EXT}/버스_노선별_정류장별_시간대별_승하차_202204.csv.gz', dtype={'버스정류장ARS번호': str, '노선번호': str})
h = h[h['버스정류장ARS번호'].str.fullmatch(r'\d{5}', na=False)].copy()
s22 = pd.read_csv(f'{EXT}/버스정류소_유형_20220401.csv', dtype={'ARS번호': str, '행정동코드': str}); s22['ARS'] = s22['ARS번호'].str.zfill(5)
s22 = s22.drop_duplicates('ARS').set_index('ARS')
h['hj'] = h['버스정류장ARS번호'].map(s22['행정동코드']); h['정류소명'] = h['버스정류장ARS번호'].map(s22['정류소명'])
def bigr(s): s = ''.join(ch for ch in str(s) if ch.isalnum()); return {s[i:i + 2] for i in range(len(s) - 1)}
def same(a, b):
    A, Bb = bigr(a), bigr(b); return bool(A and Bb and len(A & Bb) / min(len(A), len(Bb)) >= 0.34)
pr = h[['역명', '정류소명']].drop_duplicates(); pr['ok'] = [same(a, b) for a, b in zip(pr['역명'], pr['정류소명'])]
h = h.merge(pr, on=['역명', '정류소명'], how='left'); h = h[h['ok'] & h['hj'].notna()]
RC = {x: f'{"00" if x == 0 else x}시승차총승객수' for x in range(24)}; AC = {x: f'{"00" if x == 0 else x}시하차총승객수' for x in range(24)}
for c in list(RC.values()) + list(AC.values()): h[c] = pd.to_numeric(h[c], errors='coerce').fillna(0)
ride = h.groupby('hj')[list(RC.values())].sum(); ride.columns = range(24)
r = pd.read_pickle(f'{WK}/run4_flag.pkl'); r = r[r['일치']]
HC = [f'버스운행횟수_{x:02d}시' for x in range(24)]
wd = r[r['평일주말'] == '평일'].groupby('hj')[HC].sum(); we = r[r['평일주말'] == '주말'].groupby('hj')[HC].sum()
wd.columns = we.columns = range(24)
mon_run = wd * 21 + we * 9
idx = F.index
def per(hs): return ride.loc[idx, hs].sum(axis=1) / mon_run.loc[idx, hs].sum(axis=1).replace(0, np.nan)
T = pd.DataFrame(index=idx)
T['구'] = F['구']; T['동'] = NAME.loc[idx]
T['하루'] = per(list(range(24))); T['출근7_9'] = per([7, 8]); T['퇴근18_20'] = per([18, 19]); T['낮10_17'] = per(list(range(10, 17)))
T['저녁20_23'] = per([20, 21, 22]); T['심야23_04'] = per([23, 0, 1, 2, 3])
# 주말: 시간대 자료는 월 합계라 평일·주말 구분 없음 → 교수님 일별 자료 기반 기본표의 주말 승차 ÷ 정정 주말 정차
T['주말운행당'] = B.loc[idx, '주말승차'] / S.loc[idx, '주말정차_정정']; T['평일운행당'] = B.loc[idx, '평일승차'] / S.loc[idx, '정차_정정']
T['주말붐빔비'] = T['주말운행당'] / T['평일운행당']
T['주말운행유지'] = S.loc[idx, '주말정차_정정'] / S.loc[idx, '정차_정정']; T['주말승차유지'] = B.loc[idx, '주말승차'] / B.loc[idx, '평일승차']
for c in ['출근7_9', '퇴근18_20', '저녁20_23', '심야23_04', '하루', '주말붐빔비']:
    T[f'{c}_서울백분위'] = T[c].rank(pct=True)
T['심야운행_평일'] = wd.loc[idx, [23, 0, 1, 2, 3]].sum(axis=1)
T['역거리중위'] = B.loc[idx, '역거리중위']; T['역500비율'] = B.loc[idx, '역500비율']; T['고도범위'] = B.loc[idx, '고도범위']; T['경사'] = B.loc[idx, '경사']
T['노선수'] = S.loc[idx, '노선수_정정']; T['정류장수'] = B.loc[idx, '정류장수']; T['1인세대비율'] = B.loc[idx, '1인세대비율']; T['65세이상비율'] = B.loc[idx, '65세이상비율']
T['종사자배율'] = B.loc[idx, '종사자배율']
for c in ['역거리중위', '고도범위', '경사', '노선수', '1인세대비율', '65세이상비율', '종사자배율']: T[f'{c}_서울백분위'] = T[c].rank(pct=True)
T['A_부족비율'] = F['A_부족비율']; T['판정'] = F['판정']; T['실제정차'] = F['평일정차']; T['기대정차A'] = F['기대A']
med = T.drop(columns=['구', '동', '판정']).median()
T.loc[T['구'] == '강동구'].round(3).to_csv(f'{OUT}/5_강동_동별_개선안지표.csv', encoding='utf-8-sig')
med.round(4).to_csv(f'{OUT}/5_서울_동중앙값.csv', encoding='utf-8-sig')
show = ['동', '판정', 'A_부족비율', '출근7_9', '퇴근18_20', '저녁20_23', '심야23_04', '주말붐빔비', '역거리중위', '고도범위', '노선수', '1인세대비율', '종사자배율']
print(T.loc[T['구'] == '강동구', show].sort_values('A_부족비율', ascending=False).round(2).to_string())
print('서울 중앙값\n', med[['출근7_9', '퇴근18_20', '저녁20_23', '심야23_04', '주말붐빔비', '역거리중위', '고도범위', '노선수', '1인세대비율', '종사자배율']].round(3).to_string())
T.to_pickle(f'{WK}/f4_T.pkl')

# ---------- (2) 노선별: 강동 구간 하루 승차, 운행당 승차 ----------
hg = h[h['hj'].isin(GD)]
rg = r[r['hj'].isin(GD)]
RT = pd.DataFrame({'강동_월승차': hg.groupby('노선번호')[list(RC.values())].sum().sum(axis=1)})
rr = rg.copy(); rr['노선번호'] = rr['노선명'].str.replace(r'(시흥|광명|부천|안산|하남|남양주|구리|고양|성남|화성|안양)$', '', regex=True)
RT['강동_평일정차'] = rr[rr['평일주말'] == '평일'].groupby('노선번호')['버스운행횟수_일'].sum()
RT['강동_주말정차'] = rr[rr['평일주말'] == '주말'].groupby('노선번호')['버스운행횟수_일'].sum()
RT['강동_정류장수'] = rr.groupby('노선번호')['ARS'].nunique()
RT['하루운행'] = rr[rr['평일주말'] == '평일'].groupby('노선번호')['버스운행횟수_일'].max()
RT['강동_운행당승차'] = RT['강동_월승차'] / (RT['강동_평일정차'] * 21 + RT['강동_주말정차'].fillna(0) * 9)
RT['강동_하루승차'] = RT['강동_월승차'] / 30
# 서울 전체 노선별 하루 승차 (서울 정류장) → 노선 종류 비교
allr = h.groupby('노선번호')[list(RC.values())].sum().sum(axis=1) / 30
RT['서울전체_하루승차'] = allr
RT = RT.dropna(subset=['강동_월승차']).sort_values('강동_하루승차', ascending=False)
RT.round(2).to_csv(f'{OUT}/5_강동_노선별.csv', encoding='utf-8-sig'); print(RT.head(30).round(2).to_string())
# 마을버스 노선별 하루 승차: 서울 전체 순위
vil = allr[allr.index.str.match(r'^[가-힣]+\d')]
lg('서울 마을버스 노선 수', len(vil)); lg('마을버스 노선당 하루 승차 중앙값', round(vil.median()))
for k in ['강동01', '강동02', '강동05']:
    if k in vil.index: lg(f'{k} 하루 승차 / 서울 마을버스 중 순위', f"{vil[k]:.0f} / {int(vil.rank(ascending=False)[k])}위 (전체 {len(vil)})")
gv = vil.groupby(vil.index.str.extract(r'^([가-힣]+)', expand=False)).agg(['mean', 'size'])
gv.columns = ['평균', '노선수']; gv['평균순위'] = gv['평균'].rank(ascending=False)
gv.sort_values('평균', ascending=False).round(1).to_csv(f'{OUT}/5_구별_마을버스.csv', encoding='utf-8-sig'); print(gv.sort_values('평균', ascending=False).head(8).round(0))
# 구별 마을버스 노선당 운행·운행당 승차 (정정 운행)
rv = r[r['노선명'].str.match(r'^[가-힣]+\d') & (r['평일주말'] == '평일')]
vrun = rv.groupby('노선명')['버스운행횟수_일'].max()
lg('강동 마을버스 하루 운행(회)', ', '.join(f'{k} {vrun.get(k, np.nan):.0f}' for k in ['강동01', '강동02', '강동05']))
lg('서울 마을버스 하루 운행 중앙값', round(vrun.median()))

# ---------- (3) 심야버스 ----------
nr = r[r['노선명'].str.startswith('N') & (r['평일주말'] == '평일')]
ngd = nr[nr['hj'].isin(GD)].groupby(['노선명', 'hj'])['버스운행횟수_일'].sum().unstack(fill_value=0)
ngd.columns = [NAME[c] for c in ngd.columns]
ngd.to_csv(f'{OUT}/5_강동_심야버스.csv', encoding='utf-8-sig'); print(ngd.round(1).to_string())
nseoul = nr.groupby('hj')['버스운행횟수_일'].sum()
T2 = pd.DataFrame({'N정차': nseoul}).reindex(idx).fillna(0); T2['구'] = F['구']
gN = T2.groupby('구')['N정차'].sum(); gN_routes = nr.assign(구=nr['hj'].map(B['구'])).groupby('구')['노선명'].nunique()
lg('강동 N버스 노선 수 / 서울 구 중앙값', f"{gN_routes.get('강동구', 0)} / {gN_routes.median():.0f}")
lg('강동 평일 N버스 정차 / 순위(적은 순)', f"{gN.get('강동구', 0):.0f} / {int(gN.rank().get('강동구', 0))}위")
# 심야 생활이동(23~04시 출발) 동별 vs N 정차
od = pd.read_csv(f'{OUT}/4_강동관련_OD_2023평일평균.csv.gz', dtype={'o_admdong_cd': str, 'd_admdong_cd': str, 'st_time_cd': str})
od['hr'] = od['st_time_cd'].str[:2]; od['o'] = od['o_admdong_cd'] + '00'; od['d'] = od['d_admdong_cd'] + '00'
night = od[od['hr'].isin(['23', '00', '01', '02', '03'])]
nd = night[night['d'].isin(GD)].groupby('d')['cnt'].sum(); no = night[night['o'].isin(GD)].groupby('o')['cnt'].sum()
NT = pd.DataFrame({'심야도착': nd, '심야출발': no, '심야정차_N포함': T.loc[T['구'] == '강동구', '심야운행_평일'], 'N정차': T2['N정차']}).reindex(GD)
NT.index = NAME.loc[NT.index]; NT['심야이동_정차당'] = (NT['심야도착'] + NT['심야출발']) / NT['심야정차_N포함']
NT.round(1).to_csv(f'{OUT}/5_강동_심야이동.csv', encoding='utf-8-sig'); print(NT.round(1).sort_values('심야도착', ascending=False).to_string())

# ---------- (5) 구 안 재배치 ----------
k = F[F['구'] == '강동구'].copy(); k['차이'] = k['기대A'] - k['평일정차']
surplus = -k.loc[k['차이'] < 0, '차이'].sum(); deficit = k.loc[k['차이'] > 0, '차이'].sum()
lg('강동 안: 기대보다 많은 동의 여유 합 / 부족한 동의 부족 합 (정차, 잣대 A)', f'{surplus:.0f} / {deficit:.0f} → 재배치로 메울 수 있는 비율 {surplus / deficit:.0%}')
k['기대old'] = k['평일정차'] * np.exp(k['old']); k['차이old'] = k['기대old'] - k['평일정차']
s2 = -k.loc[k['차이old'] < 0, '차이old'].sum(); d2 = k.loc[k['차이old'] > 0, '차이old'].sum()
lg('같은 계산, 기존 모델(승차 포함)', f'{s2:.0f} / {d2:.0f} → {s2 / d2:.0%}')
lg('강동 전체: 실제 / 있어야 할 운행(A)', f"{k['평일정차'].sum():.0f} / {k['기대A'].sum():.0f}")

# ---------- (6) 아침 출발 → 도착 ----------
gname = B['구'].to_dict(); dname = NAME.to_dict()
am = od[od['hr'].isin(['07', '08']) & od['o'].isin(GD) & (od['move_purpose'] != 3)]
OD = []
for o, g in am.groupby('o'):
    tot = g['cnt'].sum(); dd = g.groupby('d')['cnt'].sum().sort_values(ascending=False)
    ingu = dd[dd.index.isin(GD)].sum() / tot
    gu = g.assign(구=g['d'].map(gname)).groupby('구')['cnt'].sum().sort_values(ascending=False)
    OD.append(dict(동=dname[o], 아침출발=round(tot), 구안비중=round(ingu, 3), 평균거리km=round(g['dd'].sum() / tot / 1000, 2), 평균시간분=round(g['tt'].sum() / tot, 1),
                   상위도착동=' / '.join(f"{gname.get(d, '?')[:-1]} {dname.get(d, d)} {v / tot:.0%}" for d, v in dd.head(6).items()),
                   상위도착구=' / '.join(f'{k2} {v / tot:.0%}' for k2, v in gu.head(4).items())))
OD = pd.DataFrame(OD).set_index('동'); OD.to_csv(f'{OUT}/5_강동_아침도착.csv', encoding='utf-8-sig'); print(OD.to_string())
pd.DataFrame(LOG).to_csv(f'{OUT}/5_숫자.csv', index=False, encoding='utf-8-sig')
