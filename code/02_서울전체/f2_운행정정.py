# 최종 ② 서울 안 운행 정확히 세기
# 발견(10/29): 운행횟수 자료(OA-21220)의 경기 노선 정류장 ARS 번호가 서울 정류장 번호와 겹쳐, 경기도 정류장 정차가 서울 동에 잘못 붙은 행이 있음
#   예) 1광명 '월곶역' → ARS가 같은 '강일리버5단지' (강일동)로 붙음
# 정정: 운행 자료의 정류장명과 2022-04-01 서울 정류소 목록 이름이 맞는 행만 서울 정차로 셈 (모든 노선에 똑같이)
# 민감도: 서울 면허 노선(노선_ID 1로 시작)만 셈
# 착시 보정(사전등록): 한 노선이 한 동 안에서 많은 정류장을 도는 경우 정류장 수를 서울 중앙값까지만 셈
import pandas as pd, numpy as np
P = '/mnt/project-files/프로젝트2'; EXT = f'{P}/동단위_레이어/외부데이터'; WK = '/tmp/claude-0/work'; OUT = f'{P}/최종발표/결과'
HC = [f'버스운행횟수_{h:02d}시' for h in range(24)]
r = pd.read_pickle(f'{WK}/run4.pkl')
raw = pd.read_csv(f'{EXT}/버스_노선별_정류장별_운행횟수_202204_평일주말평균.csv.gz', dtype=str, usecols=['노선_ID', '정류장_ARS', '정류장명']).drop_duplicates()
raw['ARS'] = raw['정류장_ARS'].str.zfill(5)
nm = raw.groupby(['노선_ID', 'ARS'])['정류장명'].agg(lambda s: '|'.join(sorted(set(s))))
r['운행정류장명'] = [nm.get((a, b), '') for a, b in zip(r['노선_ID'], r['ARS'])]
def bigr(s): s = ''.join(ch for ch in str(s) if ch.isalnum()); return {s[i:i + 2] for i in range(len(s) - 1)}
def same(a, b):
    if not isinstance(b, str): return False
    for x in a.split('|'):
        A, B = bigr(x), bigr(b)
        if A and B and len(A & B) / min(len(A), len(B)) >= 0.34: return True
    return False
r = r[r['hj'].notna()].copy()
pairs = r[['운행정류장명', '정류소명']].drop_duplicates()
pairs['일치'] = [same(a, b) for a, b in zip(pairs['운행정류장명'], pairs['정류소명'])]
r = r.merge(pairs, on=['운행정류장명', '정류소명'], how='left')
r['서울노선'] = r['노선_ID'].str[:1] == '1'
w = r[r['평일주말'] == '평일']
LOG = []
def lg(k, v): LOG.append(dict(항목=k, 값=v)); print(k, '|', v)
tot = w['버스운행횟수_일'].sum()
lg('서울 동에 붙은 평일 정차 합', round(tot))
lg('이름이 안 맞는 정차(다른 지역 정류장이 번호만 같아 붙은 것) 비중', f"{w.loc[~w['일치'], '버스운행횟수_일'].sum() / tot:.2%}")
lg('  그중 경기 노선 / 서울 노선', f"{w.loc[~w['일치'] & ~w['서울노선'], '버스운행횟수_일'].sum():.0f} / {w.loc[~w['일치'] & w['서울노선'], '버스운행횟수_일'].sum():.0f}")
lg('이름이 맞는 경기 노선 정차 비중(경기 버스가 실제 서울 정류장에 선 것)', f"{w.loc[w['일치'] & ~w['서울노선'], '버스운행횟수_일'].sum() / tot:.2%}")
# 서울 노선인데 이름 안 맞는 예시 점검용
w.loc[~w['일치']].groupby(['노선명', '운행정류장명', '정류소명'])['버스운행횟수_일'].sum().sort_values(ascending=False).head(60).to_csv(f'{OUT}/2_이름불일치_상위60.csv', encoding='utf-8-sig')
r.to_pickle(f'{WK}/run4_flag.pkl')

def supply(df, cap=None):
    x = df.copy()
    if cap is not None:
        k = x.groupby(['hj', '노선_ID'])['ARS'].transform('nunique')
        x['버스운행횟수_일'] = x['버스운행횟수_일'] * np.minimum(k, cap) / k
    return x.groupby('hj')['버스운행횟수_일'].sum()
ok = w[w['일치']]
k_all = ok.groupby(['hj', '노선_ID'])['ARS'].nunique(); cap = float(k_all.median())
lg('노선×동 정류장 수 중앙값(착시 보정 상한)', cap)
S = pd.DataFrame({'정차_원래': supply(w), '정차_정정': supply(ok), '정차_서울노선': supply(ok[ok['서울노선']]), '정차_정정_착시보정': supply(ok, cap)})
S['노선수_원래'] = w.groupby('hj')['노선_ID'].nunique(); S['노선수_정정'] = ok.groupby('hj')['노선_ID'].nunique()
S['노선수_서울노선'] = ok[ok['서울노선']].groupby('hj')['노선_ID'].nunique()
S['정류장수_정정'] = ok.groupby('hj')['ARS'].nunique()
for h in range(24): S[f'평일정차_{h:02d}'] = ok.groupby('hj')[HC[h]].sum()
wk = r[(r['평일주말'] == '주말') & r['일치']]
S['주말정차_정정'] = wk.groupby('hj')['버스운행횟수_일'].sum()
S['잘못붙은_비중'] = 1 - S['정차_정정'] / S['정차_원래']
B = pd.read_csv(f'{P}/재정비/1_전처리/행정동_기본표.csv', dtype={'hj': str}).set_index('hj')
S = S.join(B[['구', '행정동']], how='left')
S.to_csv(f'{OUT}/2_행정동_운행_정정.csv', encoding='utf-8-sig')
print(S.sort_values('잘못붙은_비중', ascending=False)[['구', '행정동', '정차_원래', '정차_정정', '잘못붙은_비중', '노선수_원래', '노선수_정정']].head(25).round(3).to_string())
g = S.groupby('구')[['정차_원래', '정차_정정']].sum(); g['비중'] = 1 - g['정차_정정'] / g['정차_원래']
print(g.sort_values('비중', ascending=False).round(3).to_string())
pd.DataFrame(LOG).to_csv(f'{OUT}/2_숫자.csv', index=False, encoding='utf-8-sig')
