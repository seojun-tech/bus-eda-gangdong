"""강동 부족 동 11곳의 '들어오는 노선 수'를 생활인구가 비슷한 동과 비교 (발표 16장, 0.42배).

- 노선: 2022년 4월 평일 운행이 있는 서울 면허 노선(노선_ID가 1로 시작)
- 비슷한 동: 생활인구(M)가 0.8~1.25배인 다른 동, 그 노선 수의 중앙값
- 결과: 동별 비율의 중앙값
"""
import os
import numpy as np
import pandas as pd

ROOT = os.environ.get('P2_DIR', '/mnt/project-files/프로젝트2')  # 원래 작업 폴더
OUT = os.path.join(os.path.dirname(__file__), '..', 'out', '03_강동', '강동_노선수_비교.csv')

r = pd.read_csv(f'{ROOT}/동단위_레이어/외부데이터/버스_노선별_정류장별_운행횟수_202204_평일주말평균.csv.gz',
                dtype={'노선_ID': str, '정류장_ARS': str},
                usecols=['노선_ID', '정류장_ARS', '평일주말', '버스운행횟수_일'])
r = r[(r['평일주말'] == '평일') & r['노선_ID'].str.startswith('1') & (r['버스운행횟수_일'] > 0)]
m = pd.read_csv(f'{ROOT}/동단위_레이어/캐시/정류장_행정동.csv', dtype=str)
r = r.merge(m, left_on='정류장_ARS', right_on='ARS')
n_routes = r.groupby('hj')['노선_ID'].nunique()

d = pd.read_csv(f'{ROOT}/최종발표/결과/3_정정_행정동_두잣대.csv', dtype={'hj': str}).set_index('hj')
d['노선수_서울면허'] = n_routes
k = d[(d['구'] == '강동구') & (d['판정'] == '부족 확정')]

rows = []
for h, x in k.iterrows():
    sim = d[(d['M'] >= 0.8 * x['M']) & (d['M'] <= 1.25 * x['M']) & (d.index != h)]
    med = sim['노선수_서울면허'].median()
    rows.append({'행정동': x['행정동'], '노선수': x['노선수_서울면허'], '비슷한동_중앙값': med,
                 '비율': x['노선수_서울면허'] / med, '비슷한동_수': len(sim)})
T = pd.DataFrame(rows)
T.round(4).to_csv(OUT, index=False, encoding='utf-8-sig')
print(T.round(2).to_string(index=False))
print('노선 수 중앙값', T['노선수'].median(), 'vs', T['비슷한동_중앙값'].median(), '| 비율 중앙값', round(T['비율'].median(), 2))
