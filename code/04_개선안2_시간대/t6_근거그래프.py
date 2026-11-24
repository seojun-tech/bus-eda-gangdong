# 정정 근거(11/08): T7 서울 평일 시간당 지나간 버스(실측) vs 승차 / 서울 노선 634개 출근÷대낮 비율 분포 (운행 vs 승차)
import pandas as pd, numpy as np, glob
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
for f in glob.glob('/usr/local/lib/python3.13/site-packages/koreanize_matplotlib/fonts/*.ttf'): fm.fontManager.addfont(f)
BLUE='#1F5FBF'; GRAY='#9AA3AF'; INK='#1F2937'; INK2='#4B5563'
plt.rcParams.update({'font.family':'NanumGothic','axes.unicode_minus':False,'font.size':13,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.color':'#E5E8EE','axes.axisbelow':True,'savefig.dpi':220,'savefig.bbox':'tight','figure.facecolor':'white'})
P='/mnt/project-files/프로젝트2'; R=f'{P}/최종발표/시간대_1107/결과'; G=f'{P}/최종발표/시간대_1107/그래프'
X=pd.read_csv(f'{R}/0_패널_버스_04.csv',encoding='utf-8-sig')
HS=list(range(5,24))
run=np.array([X[f'평일운행_{h:02d}'].sum() for h in HS])/1e4
# 승차는 한 달(평일+주말) 합 → 하루 평균
ride=np.array([X[f'승차_{h:02d}'].sum() for h in HS])/30/1e4
fig,axs=plt.subplots(1,2,figsize=(14,5.2))
ax=axs[0]; x=np.arange(len(HS))
ax.bar(x-0.2,run,0.4,color=GRAY,label='버스가 정류장을 지나간 횟수 (평일, 만 회)')
ax.bar(x+0.2,ride,0.4,color=BLUE,label='승차 (하루 평균, 만 명)')
ax.set_xticks(x); ax.set_xticklabels(HS); ax.set_xlabel('시각'); ax.legend(frameon=False,fontsize=11,loc='upper right')
ax.set_title('정류장 통과 횟수는 6~22시 내내 시간당 19만~22만 회',loc='left',fontsize=14,color=INK)
# 노선 분포
r=pd.read_pickle('/tmp/claude-0/work/run04_ok.pkl'); w=r[r.평일주말=='평일']
g=w.groupby('노선_ID')[[f'버스운행횟수_{h:02d}시' for h in [7,8,11,12,13,14]]].sum()
rr=(g.iloc[:,:2].mean(axis=1)/g.iloc[:,2:].mean(axis=1)).replace(np.inf,np.nan)
rr=rr[(rr.index.str[:1]=='1')&(rr>0)&(rr<20)]
h=pd.read_csv(f'{P}/동단위_레이어/외부데이터/버스_노선별_정류장별_시간대별_승하차_202204.csv.gz',dtype={'노선번호':str,'버스정류장ARS번호':str})
b=h.groupby('노선번호')[[f'{x}시승차총승객수' for x in [7,8,11,12,13,14]]].sum()
br=(b.iloc[:,:2].mean(axis=1)/b.iloc[:,2:].mean(axis=1)).replace(np.inf,np.nan).dropna(); br=br[(b.iloc[:,2:].sum(axis=1)>1000)]
ax=axs[1]; bins=np.arange(0.4,3.6,0.1)
ax.hist(rr.clip(upper=3.5),bins=bins,color=GRAY,alpha=.9,label=f'운행 (노선 {len(rr)}개, 중앙 {rr.median():.2f}배)')
ax.hist(br.clip(upper=3.5),bins=bins,color=BLUE,alpha=.55,label=f'승차 (노선 {len(br)}개, 중앙 {br.median():.2f}배)')
ax.axvline(1,color=INK2,ls='--',lw=1); ax.set_xlabel('출근(7~8시) ÷ 대낮(11~14시)'); ax.set_ylabel('노선 수'); ax.legend(frameon=False,fontsize=11)
ax.set_title('노선마다 출근 때 승차는 1.6배, 운행은 1.0배',loc='left',fontsize=14,color=INK)
fig.suptitle('서울시는 출퇴근 집중배차를 하지만, 실제로 지나간 버스는 승객만큼 늘지 않았다 (2022년 4월 실측)',x=0.01,ha='left',fontsize=15,color=INK)
fig.tight_layout(); fig.savefig(f'{G}/T7_지나간버스_실측_근거.png'); plt.close()
pd.DataFrame({'시':HS,'평일_지나간버스_만회':run.round(2),'승차_하루평균_만명':ride.round(2)}).to_csv(f'{R}/10_서울_시간당_운행_승차_실수.csv',index=False,encoding='utf-8-sig')
pd.DataFrame({'출근대낮_운행비':rr}).to_csv(f'{R}/10_서울노선_출근대낮_운행비.csv',encoding='utf-8-sig')
print(len(rr),rr.median(),len(br),br.median(), run.round(1), ride.round(1))
