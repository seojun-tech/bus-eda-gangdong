# 최종 ③ 강동 동별 '어디로 가나' (노선 초안의 연결 목적지)
# 서울 생활이동 행정동 OD(OA-22300) 2023-04 평일 6일(4·5·6·11·12·13일). 2022년 동 단위판은 공개 안 됨 → 출근 이동 시간과 같은 자료.
# 서울 안 이동만(출발·도착 모두 11로 시작), 내국인+외국인 모두, '*'는 원자료에 없음(cnt 소수 = 추정값)
import pandas as pd, glob
OUT = '/mnt/project-files/프로젝트2/최종발표/결과'
rows = []
for f in sorted(glob.glob('/tmp/claude-0/dl/od/x_*/*.csv')):
    for x in pd.read_csv(f, encoding='cp949', usecols=['o_admdong_cd', 'd_admdong_cd', 'st_time_cd', 'move_purpose', 'move_time', 'move_dist', 'cnt'], dtype={'o_admdong_cd': str, 'd_admdong_cd': str, 'st_time_cd': str}, chunksize=4_000_000):
        x = x[x.o_admdong_cd.str.startswith('11') & x.d_admdong_cd.str.startswith('11')]
        x = x[x.o_admdong_cd.str.startswith('11740') | x.d_admdong_cd.str.startswith('11740')]
        x['tt'] = x['move_time'] * x['cnt']; x['dd'] = x['move_dist'] * x['cnt']
        rows.append(x.groupby(['o_admdong_cd', 'd_admdong_cd', 'st_time_cd', 'move_purpose'], as_index=False)[['cnt', 'tt', 'dd']].sum())
    print(f)
X = pd.concat(rows).groupby(['o_admdong_cd', 'd_admdong_cd', 'st_time_cd', 'move_purpose'], as_index=False)[['cnt', 'tt', 'dd']].sum()
X[['cnt', 'tt', 'dd']] /= 6
X.to_csv(f'{OUT}/4_강동관련_OD_2023평일평균.csv.gz', index=False, encoding='utf-8-sig')
print(len(X), X['cnt'].sum())
