"""발표에 쓴 주요 숫자가 out/ 의 결과 파일과 같은지 확인한다.

원본 데이터 없이 out/ 만으로 돌아간다:  python verify.py
"""
import os
import pandas as pd

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
rd = lambda p, **k: pd.read_csv(os.path.join(R, p), **k)
fails = []


def check(name, got, want, tol=0.0):
    ok = abs(got - want) <= tol if isinstance(want, (int, float)) else got == want
    print(f"{'OK  ' if ok else 'FAIL'} {name}: {got} (발표 {want})")
    if not ok:
        fails.append(name)


# 서울 전체 (발표 4·7·9·10장)
D = rd('02_서울전체/3_정정_행정동_두잣대.csv', dtype={'hj': str})
check('분석 행정동 수', len(D), 418)
v = D['판정'].value_counts()
check('버스 부족 동', int(v['부족 확정']), 63)
check('한쪽 기준만 상위 25%', int(v['한쪽 신호']), 84)
check('해당 없음', int(v['해당 없음']), 271)
num = rd('02_서울전체/3_정정_숫자.csv').set_index('항목')['값']
check('기준 A 회귀 R²', round(float(num['잣대 A R²']), 2), 0.51)
G = D[D['구'] == '강동구']
check('강동 부족 동 / 전체', f"{(G['판정'] == '부족 확정').sum()}/{len(G)}", '11/19')
ratio = D.assign(부족=D['판정'] == '부족 확정').groupby('구')['부족'].mean().sort_values(ascending=False)
check('부족 동 비율 1위 구', ratio.index[0], '강동구')
check('강동 부족 동 비율(%)', round(ratio['강동구'] * 100), 58)
sens = pd.concat([rd(f'02_서울전체/{f}') for f in
                  ['1_민감도.csv', '3_서울노선_민감도.csv', '3_정정_민감도.csv', '3_정정_착시보정_민감도.csv']])
check('다시 계산 횟수', len(sens), 28)
check('그중 강동 1위 횟수', int((sens['강동_확정비율순위'] == 1).sum()), 24)

# 강동 (발표 16장)
K = rd('03_강동/강동_노선수_비교.csv')
check('노선 수 비율(중앙값)', round(K['비율'].median(), 2), 0.42)
check('부족 동 노선 수 중앙값', K['노선수'].median(), 9)
check('비슷한 동 노선 수 중앙값', K['비슷한동_중앙값'].median(), 18)

# 개선안 ② 시간대 (발표 24·25·27장)
t = rd('04_개선안2_시간대/10_서울노선_출근대낮_운행비.csv')['출근대낮_운행비']
check('서울 노선 수', len(t), 634)
check('출근÷대낮 운행 중앙값', round(t.median(), 2), 1.00)
check('출근 운행 1.2배 넘게 늘린 노선', int((t > 1.2).sum()), 80)
s = rd('04_개선안2_시간대/숫자.csv').set_index('항목')['값']
check('시간 불일치: 부족 동 vs 나머지', s['① 부족 확정 동 시간어긋남 중앙값 vs 나머지'], '0.145 vs 0.140, MWU p=0.764')
check('주말 운행 ÷ 평일', s['③ 주말 운행비 서울 중앙값 / 10~90%'].split(' / ')[0], '0.82')
check('주말 승차 ÷ 평일', s['③ 주말 승차비 중앙값 / 10~90%'].split(' / ')[0], '0.66')

# 개선안 ③ 송파 (발표 15장)
N = rd('04_개선안3_송파/결과_구별_1위이웃구_몫_평일.csv').set_index('o')
check('강동 구 밖 이동 중 송파 몫(%)', round(N.loc['강동구', '몫'] * 100), 33)
check('이웃 한 구로 가는 몫 1위', N['몫'].idxmax(), '강동구')

print('\n모두 일치' if not fails else f'\n불일치 {len(fails)}건: {fails}')
raise SystemExit(1 if fails else 0)
