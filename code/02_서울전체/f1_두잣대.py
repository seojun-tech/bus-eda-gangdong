# 최종 ① 두 잣대 교차 확인 (사전등록: 결과/0_사전등록_두잣대_1029.md)
# 잣대 A = 우리 '있어야 할 운행' 모델에서 승차를 빼고 이동 수요(생활인구)로 바꾼 판
# 잣대 B = 팀원 기준(오가는 사람 ÷ 버스 시설)의 동 단위판
import pandas as pd, numpy as np, statsmodels.api as sm, sys
from scipy.stats import spearmanr
# 실행: python f1_두잣대.py [원래|정정|서울노선|정정_착시보정]  (원래 = 사전등록 그대로 첫 실행, 정정 = f2 운행 정정 후 본 판정)
VAR = sys.argv[1] if len(sys.argv) > 1 else '원래'; PRE = '1' if VAR == '원래' else f'3_{VAR}'
P = '/mnt/project-files/프로젝트2'
EXT = f'{P}/동단위_레이어/외부데이터'; OUT = f'{P}/최종발표/결과'
D = pd.read_csv(f'{P}/재정비/1_전처리/행정동_기본표.csv', dtype={'hj': str}).set_index('hj')
od = pd.read_csv(f'{P}/재정비/1_전처리/외부_행정동_출근이동시간_202304.csv', dtype={'행정동코드': str}).set_index('행정동코드')
D['출근이동시간'] = od['출근이동시간']
D = D[D['분석대상'] & D['출근이동시간'].notna() & D['낮생활인구'].notna()].copy()
if VAR != '원래':
    S = pd.read_csv(f'{P}/최종발표/결과/2_행정동_운행_정정.csv', dtype={'hj': str}).set_index('hj')
    D['평일정차'] = S[f'정차_{VAR}']; D['노선수'] = S['노선수_정정' if VAR != '서울노선' else '노선수_서울노선']
    D = D[D['평일정차'].gt(0)].copy()
NUM = []
def note(k, v): NUM.append(dict(항목=k, 값=v)); print(k, '|', v)
note('대상 동', len(D))

# ---- 이동 수요 M: 평일 시간대 평균 생활인구 (상일1·2 합본은 주민 비율로 나눔 = 기본표와 같은 처리)
lp = pd.read_csv(f'{EXT}/행정동_생활인구_202204_평일주말_시간대평균.csv', dtype={'행정동코드': str, '시간대구분': str})
pv = lp[lp['평일주말'] == '평일'].pivot_table(index='행정동코드', columns='시간대구분', values='총생활인구수')
def lpser(hours):
    s = pv[[f'{h:02d}' for h in hours]].mean(axis=1)
    if '1174052500|1174052600' in s.index:
        tot = s.pop('1174052500|1174052600')
        pop = pd.read_csv(f'{EXT}/행정동_주민등록인구_연령_202204.csv', dtype={'행정동코드': str}).set_index('행정동코드')
        c = pop.columns[[('총' in x) or ('계' in x) for x in pop.columns]][0]
        w = pop.loc[['1174052500', '1174052600'], c].astype(float); w = w / w.sum()
        for h, ww in w.items(): s[h] = tot * ww
    return s
D['M'] = lpser(range(7, 23)); D['M24'] = lpser(range(24)); D['M08'] = lpser([8])
note('M 결측', int(D['M'].isna().sum()))
chk = spearmanr(D['M'], D['낮생활인구'])[0]; note('M vs 기본표 낮생활인구 순위상관(같은 자료인지 점검)', round(chk, 3))

# ---- 잣대 A
D['log주민'] = np.log(D['총인구']); D['log종사자'] = np.log(D['종사자수'].clip(lower=1)); D['log지하철'] = np.log1p(D['지하철평일승차'])
DRV = ['log주민', 'log종사자', '1인세대비율', '65세이상비율', '역500비율', 'log지하철', '고도범위', '출근이동시간']
def fitA(mcol, supply='평일정차', extra=None):
    Z = D[DRV].copy(); Z['logM'] = np.log(D[mcol])
    if extra: Z[extra] = np.log(D[extra])
    Zs = (Z - Z.mean()) / Z.std(); y = np.log(D[supply])
    f = sm.OLS(y, sm.add_constant(Zs)).fit(cov_type='HC3')
    return f, f.fittedvalues - y
fA, D['A'] = fitA('M')
note('잣대 A R²', round(fA.rsquared, 3))
co = pd.DataFrame({'표준화계수': fA.params, 'p': fA.pvalues}).drop('const').round(4); co.to_csv(f'{OUT}/{PRE}_잣대A_계수.csv', encoding='utf-8-sig'); print(co)
D['A_부족비율'] = 1 - np.exp(-D['A'])
# 기존 모델(승차 포함) 재현 → 이전 결과와 같은지 점검
old = pd.read_csv(f'{P}/재정비/4_계산/결과_행정동_공급차이_유형.csv', dtype={'hj': str}).set_index('hj')
fO, D['old'] = fitA('낮생활인구', extra='평일승차')
note('기존 모델 재현: 이전 공급차이와 상관', round(np.corrcoef(D['old'], old.loc[D.index, '공급차이'])[0, 1], 4))
if VAR == '원래': D['old'] = old.loc[D.index, '공급차이']

# ---- 잣대 B
D['B1'] = D['M'] / D['노선수']; D['B2'] = D['M'] / D['정류장수']; D['B3'] = D['M'] / D['평일정차']
D['B'] = (D['B1'].rank(pct=True) + D['B2'].rank(pct=True)) / 2
zz = lambda s: (s - s.mean()) / s.std()
D['B_z'] = (zz(D['B1']) + zz(D['B2'])) / 2
D['이용률'] = D['평일승차'] / D['M']
D['B_원식'] = (zz(D['B1']) + zz(D['B2']) - zz(D['이용률'])) / 3

# ---- 판정
q = lambda s: s >= s.quantile(.75)
D['A상위'] = q(D['A']); D['B상위'] = q(D['B'])
D['판정'] = np.select([D['A상위'] & D['B상위'], D['A상위'] | D['B상위']], ['부족 확정', '한쪽 신호'], '해당 없음')
n = len(D); both = int((D['A상위'] & D['B상위']).sum())
note('A-B 순위상관', round(spearmanr(D['A'], D['B'])[0], 3))
note('부족 확정 동 수 (우연 기대 = 6.25%)', f'{both}/{n} = {both/n:.1%} (기대 {n*.0625:.0f})')
note('A vs 기존 모델 순위상관', round(spearmanr(D['A'], D['old'])[0], 3))
note('B vs 기존 모델 순위상관', round(spearmanr(D['B'], D['old'])[0], 3))

G = D.groupby('구').agg(동수=('A', 'size'), 확정=('판정', lambda s: (s == '부족 확정').sum()), A상위=('A상위', 'sum'), B상위=('B상위', 'sum'),
                       A평균=('A', 'mean'), 실제=('평일정차', 'sum'))
D['기대A'] = D['평일정차'] * np.exp(D['A'])
G['기대A'] = D.groupby('구')['기대A'].sum(); G['A_구부족'] = 1 - G['실제'] / G['기대A']
G['M합'] = D.groupby('구')['M'].sum(); G['노선수_구'] = np.nan
G['확정비율'] = G['확정'] / G['동수']
G = G.sort_values(['확정비율', 'A평균'], ascending=False); G['확정비율_순위'] = range(1, len(G) + 1)
G['A평균_순위'] = G['A평균'].rank(ascending=False).astype(int); G['A_구부족_순위'] = G['A_구부족'].rank(ascending=False).astype(int)
G.round(4).to_csv(f'{OUT}/{PRE}_구별_두잣대.csv', encoding='utf-8-sig'); print(G.round(3).head(10))
gd = G.loc['강동구']; note('강동: 확정 비율 순위 / 확정 동', f"{gd['확정비율_순위']}위 / {int(gd['확정'])}/{int(gd['동수'])}")
note('강동: 잣대A 동 평균 순위 / 구 전체 부족', f"{gd['A평균_순위']}위 / {gd['A_구부족']:.1%} ({gd['A_구부족_순위']}위)")

D['A순위'] = D['A'].rank(ascending=False).astype(int); D['B순위'] = D['B'].rank(ascending=False).astype(int); D['old순위'] = D['old'].rank(ascending=False).astype(int)
cols = ['구', '행정동', '총인구', 'M', '평일정차', '노선수', '정류장수', 'A', 'A_부족비율', 'A순위', 'B1', 'B2', 'B', 'B순위', 'old', 'old순위', '판정']
D.sort_values('A', ascending=False)[cols].round(4).to_csv(f'{OUT}/{PRE}_행정동_두잣대.csv', encoding='utf-8-sig')
print(D[D['구'] == '강동구'].sort_values('A', ascending=False)[['행정동', 'A_부족비율', 'A순위', 'B순위', 'old순위', '판정']].round(3).to_string())

# ---- 민감도 (판정 바꾸지 않음)
SEN = []
def sens(lab, a, b):
    t = q(a) & q(b); g = pd.Series(t).groupby(D['구']).mean().rank(ascending=False, method='min')
    gk = D[D['구'] == '강동구']
    SEN.append(dict(설정=lab, 확정동수=int(t.sum()), 강동_확정비율순위=int(g['강동구']),
                     암사3=bool(t[gk.index[gk['행정동'] == '암사제3동'][0]]), 천호2=bool(t[gk.index[gk['행정동'] == '천호제2동'][0]]),
                     강동_확정동=', '.join(gk.loc[t[gk.index], '행정동'])))
sens('본 판정 (M 07~22시, B 순위평균)', D['A'], D['B'])
for mc, lab in [('M24', 'M 24시간 평균'), ('M08', 'M 08시(출근)')]:
    _, a = fitA(mc); b = (( D[mc] / D['노선수']).rank(pct=True) + (D[mc] / D['정류장수']).rank(pct=True)) / 2; sens(lab, a, b)
sens('B = z 평균', D['A'], D['B_z'])
sens('B = 팀원 원래 식(③ 이용률 포함)', D['A'], D['B_원식'])
sens('B3 운행당 이동', D['A'], D['B3'])
sens('A 대신 기존 모델(승차 포함)', D['old'], D['B'])
SEN = pd.DataFrame(SEN); SEN.to_csv(f'{OUT}/{PRE}_민감도.csv', index=False, encoding='utf-8-sig'); print(SEN.to_string())
D.to_pickle(f'/tmp/claude-0/work/f1_{VAR}.pkl')
pd.DataFrame(NUM).to_csv(f'{OUT}/{PRE}_숫자.csv', index=False, encoding='utf-8-sig')
