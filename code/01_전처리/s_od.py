# 2023-04 평일 6일 행정동 출발-도착(서울 생활이동 OA-22300) → 출발 동별 출근 이동 시간·거리
import pandas as pd, numpy as np, glob
rows = []
for f in sorted(glob.glob('/tmp/claude-0/dl/od/*.csv')):
    x = pd.read_csv(f, encoding='cp949', usecols=['o_admdong_cd', 'd_admdong_cd', 'move_purpose', 'move_dist', 'move_time', 'cnt', 'in_forn_div_nm'])
    x = x[(x.in_forn_div_nm == '내국인') & (x.move_purpose == 1) & x.o_admdong_cd.astype(str).str.startswith('11') & x.d_admdong_cd.astype(str).str.startswith('11')]
    x = x[x.move_dist > 0]
    x['day'] = f[-12:-4]; rows.append(x.drop(columns=['in_forn_div_nm', 'move_purpose']))
X = pd.concat(rows)
X['lt'] = np.log(X.move_time.clip(lower=1)); X['ld'] = np.log(X.move_dist)
b = np.polyfit(X['ld'], X['lt'], 1, w=np.sqrt(X.cnt)); X['res'] = X['lt'] - np.polyval(b, X['ld'])
print('log time ~ log dist slope', b)
g = X.groupby('o_admdong_cd')
A = pd.DataFrame({'출근이동시간': (X.move_time * X.cnt).groupby(X.o_admdong_cd).sum() / g.cnt.sum(),
                  '출근이동거리km': (X.move_dist * X.cnt).groupby(X.o_admdong_cd).sum() / g.cnt.sum() / 1000,
                  '출근시간_거리보정': (X.res * X.cnt).groupby(X.o_admdong_cd).sum() / g.cnt.sum(),
                  '출근인원_일': g.cnt.sum() / X.day.nunique()})
A['출근속도kmh'] = A['출근이동거리km'] / (A['출근이동시간'] / 60)
A.to_csv('/tmp/claude-0/work/od_agg_202304.csv'); print(A.describe()); print('days', X.day.unique())
