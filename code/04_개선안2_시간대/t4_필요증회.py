# 시간대 계획안: 강동 부족 동의 시간대별 '서울 같은 시각 보통 수준'까지 필요한 증회 (평일 하루, 4월)
# 1회당 승차 = 시각별 한 달 승차 / 한 달 운행(평일21+주말9). 서울 같은 시각 동 중앙값까지 낮추려면 운행이 몇 회 더 필요한가.
import pandas as pd, numpy as np
P='/mnt/project-files/프로젝트2'; R=f'{P}/최종발표/시간대_1107/결과'
D=pd.read_csv(f'{P}/최종발표/결과/3_정정_행정동_두잣대.csv',dtype={'hj':str},encoding='utf-8-sig').set_index('hj')
X=pd.read_csv(f'{R}/0_패널_버스_04.csv',dtype={'hj':str},encoding='utf-8-sig').set_index('hj')
S=pd.read_csv(f'{P}/최종발표/결과/2_행정동_운행_정정.csv',dtype={'hj':str},encoding='utf-8-sig').set_index('hj')
H=[6,7,8,17,18,19,22,23]
rows=[]
for h in H:
    run=X[f'평일운행_{h:02d}']*21+X[f'주말운행_{h:02d}']*9; per=X[f'승차_{h:02d}']/run.replace(0,np.nan); med=per.median()
    need=(X[f'승차_{h:02d}']/med-run)/30   # 하루 평균 증회
    for hj in D.index[(D.구=='강동구')&(D.판정=='부족 확정')]:
        rows.append(dict(동=D.loc[hj,'행정동'],시=h,평일운행=round(X.loc[hj,f'평일운행_{h:02d}'],1),회당승차=round(per[hj],1),서울중앙=round(med,1),배=round(per[hj]/med,2),하루필요증회=round(max(need[hj],0),1)))
T=pd.DataFrame(rows); P_=T.pivot(index='동',columns='시',values='하루필요증회'); B=T.pivot(index='동',columns='시',values='배')
print(B.to_string()); print(P_.to_string())
T.to_csv(f'{R}/9_강동_시간대_필요증회.csv',index=False,encoding='utf-8-sig')
# 이름 정정 영향: 암사2 정정 전 운행이면 1회당 배수
print('정정 전/후 운행 비 암사2',S.loc['1174058000','정차_원래']/S.loc['1174058000','정차_정정'])
