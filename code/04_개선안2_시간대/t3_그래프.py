# 시간대 파트 그래프 (발표 덱 색: 파랑 계열 + 회색, 강조 노랑)
import pandas as pd, numpy as np, json, glob
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MP
for f in glob.glob('/usr/local/lib/python3.13/site-packages/koreanize_matplotlib/fonts/*.ttf'): fm.fontManager.addfont(f)
BLUE='#1F5FBF'; BLUE_L='#8FB3EA'; GRAY='#9AA3AF'; INK='#1F2937'; INK2='#4B5563'; YEL='#F2B705'; RED='#C2410C'
plt.rcParams.update({'font.family':'NanumGothic','axes.unicode_minus':False,'font.size':14,'axes.labelcolor':INK2,'xtick.color':INK2,'ytick.color':INK2,
 'axes.edgecolor':'#D5DCE6','axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.color':'#E5E8EE','axes.axisbelow':True,
 'savefig.dpi':220,'savefig.bbox':'tight','savefig.pad_inches':.08,'figure.facecolor':'white'})
P='/mnt/project-files/프로젝트2'; R=f'{P}/최종발표/시간대_1107/결과'; G=f'{P}/최종발표/시간대_1107/그래프'
SV=[5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,0]; XL=[f'{h}' for h in SV]
# G1 서울 전체: 승하차 몫 vs 운행 몫
sh=pd.read_csv(f'{R}/1_서울_시간별_몫.csv',index_col=0,encoding='utf-8-sig'); sh.index=sh.index.astype(int); sh=sh.loc[SV]
fig,ax=plt.subplots(figsize=(11,5)); x=np.arange(len(SV))
ax.plot(x,sh['수요몫']*100,color=BLUE,lw=3,marker='o',ms=6,label='타고 내린 사람')
ax.plot(x,sh['운행몫']*100,color=GRAY,lw=3,marker='o',ms=6,label='버스 운행')
ax.fill_between(x,sh['수요몫']*100,sh['운행몫']*100,where=sh['수요몫']>sh['운행몫'],color=BLUE_L,alpha=.35,interpolate=True)
for i in [3,13]: ax.annotate(f"버스 1회당\n평소의 {sh['회당_서울평균대비'].iloc[i]:.1f}배",(x[i],sh['수요몫'].iloc[i]*100),xytext=(0,14),textcoords='offset points',ha='center',fontsize=12,color=INK)
ax.annotate(f"평소의 {sh['회당_서울평균대비'].iloc[17]:.1f}배",(x[17],sh['운행몫'].iloc[17]*100),xytext=(0,12),textcoords='offset points',ha='center',fontsize=12,color=INK2)
ax.set_ylim(0,11); ax.set_xticks(x); ax.set_xticklabels(XL); ax.set_xlabel('시각'); ax.set_ylabel('하루 중 몫 (%)'); ax.legend(frameon=False,loc='upper right')
ax.set_title('사람은 출퇴근에 몰리는데 지나가는 버스는 그만큼 늘지 않는다 (서울 418개 동, 2022.4)',loc='left',fontsize=15,color=INK)
fig.savefig(f'{G}/T1_서울_시간별_사람vs버스.png'); plt.close()
# G2 유형 4개: 승차 모양 vs 운행 모양
prof=pd.read_csv(f'{R}/5_유형_모양.csv',index_col=0,encoding='utf-8-sig')
X=pd.read_csv(f'{R}/0_패널_버스_04.csv',dtype={'hj':str},encoding='utf-8-sig').set_index('hj')
U=pd.read_csv(f'{R}/5_유형_동별.csv',dtype={'hj':str},encoding='utf-8-sig').set_index('hj')
run=pd.DataFrame({h:X[f'평일운행_{h:02d}']*21+X[f'주말운행_{h:02d}']*9 for h in SV}); rs=run.div(run.sum(axis=1),axis=0)
on=pd.DataFrame({h:X[f'승차_{h:02d}'] for h in SV}); os_=on.div(on.sum(axis=1),axis=0); off=pd.DataFrame({h:X[f'하차_{h:02d}'] for h in SV}); of_=off.div(off.sum(axis=1),axis=0)
NAME={1:'주거형: 아침에 떠나고 저녁에 돌아옴',2:'일터·상권형: 아침에 도착, 저녁·밤에 떠남',0:'섞임형: 아침·저녁 모두 타고 내림',3:'보통형: 주거 쪽에 약간 기운 동네'}
fig,axs=plt.subplots(2,2,figsize=(14,8.5),sharey=True)
for ax,t in zip(axs.flat,[1,2,0,3]):
    idx=U.index[U['유형']==t]
    ax.plot(x,os_.loc[idx].median()*100,color=BLUE,lw=3,label='타는 사람')
    ax.plot(x,of_.loc[idx].median()*100,color=BLUE_L,lw=2.2,ls='--',label='내리는 사람')
    ax.plot(x,rs.loc[idx].median()*100,color=GRAY,lw=3,label='버스 운행')
    ax.set_title(f'{NAME[t]}  {len(idx)}곳',loc='left',fontsize=14,color=INK); ax.set_xticks(x[::2]); ax.set_xticklabels(XL[::2])
axs[0,0].legend(frameon=False,fontsize=12); axs[0,0].set_ylabel('하루 중 몫 (%)'); axs[1,0].set_ylabel('하루 중 몫 (%)')
fig.suptitle('동네마다 하루 모양은 다른데, 회색(버스) 선은 네 칸 모두 거의 같다',x=0.01,ha='left',fontsize=16,color=INK)
fig.tight_layout(); fig.savefig(f'{G}/T2_동네유형4_사람vs버스.png'); plt.close()
# G3 유형 지도
gj=json.load(open(f'{P}/동단위_레이어/외부데이터/행정동_경계_20220401_서울.geojson'))
COL={1:'#1F5FBF',0:'#F2B705',2:'#C2410C',3:'#D5DCE6'}
fig,ax=plt.subplots(figsize=(11,9))
def polys(geom):
    if geom['type']=='Polygon': return [geom['coordinates'][0]]
    return [p[0] for p in geom['coordinates']]
for f in gj['features']:
    hj=f['properties']['adm_cd2']; t=U['유형'].get(hj,np.nan); gu=f['properties']['sggnm']
    for ring in polys(f['geometry']):
        ax.add_patch(MP(ring,closed=True,fc=COL.get(t,'#FFFFFF'),ec='white',lw=.4))
        if gu=='강동구': ax.add_patch(MP(ring,closed=True,fc='none',ec=INK,lw=1.2))
ax.autoscale(); ax.set_aspect(1.25); ax.axis('off')
from matplotlib.patches import Patch
ax.legend(handles=[Patch(fc=COL[t],label=NAME[t]) for t in [1,2,0,3]],frameon=False,loc='lower left',fontsize=12)
ax.set_title('하루 모양으로 나눈 서울 동네 4가지 (검은 테두리: 강동구)',loc='left',fontsize=15,color=INK)
fig.savefig(f'{G}/T3_동네유형_지도.png'); plt.close()
# G4 사람 수 대비 운행: 가장 부족한 15곳 x 시간대
O2=pd.read_csv(f'{R}/2_사람수기준_부족_동x시간.csv',dtype={'hj':str},encoding='utf-8-sig').set_index('hj')
hc=[f'{h:02d}시' for h in SV]; O2['평균']=O2[hc].mean(axis=1); top=O2.nsmallest(15,'평균')
fig,ax=plt.subplots(figsize=(13,7))
im=ax.imshow(top[hc].values*100,cmap='Blues_r',vmin=-100,vmax=0,aspect='auto')
ax.set_yticks(range(len(top))); ax.set_yticklabels([f"{d}{'  ●' if g=='강동구' else ''}" for d,g in zip(top['동'],top['구'])]); ax.set_xticks(range(len(hc))); ax.set_xticklabels(XL); ax.grid(False)
for i in range(len(top)):
    for j in [2,3,13,17]: ax.text(j,i,f"{top[hc].iloc[i,j]*100:.0f}",ha='center',va='center',fontsize=9,color='white' if top[hc].iloc[i,j]<-.5 else INK)
cb=fig.colorbar(im,ax=ax,shrink=.8); cb.set_label('같은 시각 비슷한 인구의 동보다 운행이 몇 % 적은가')
ax.set_title('승차 말고 "그 시각 그 동네에 있는 사람 수"로 봐도 부족한 곳 15곳 (● 강동)',loc='left',fontsize=15,color=INK)
fig.savefig(f'{G}/T4_사람수기준_부족15.png'); plt.close()
# G5 주말
W=pd.read_csv(f'{R}/3_주말_동별.csv',dtype={'hj':str},encoding='utf-8-sig').set_index('hj')
fig,ax=plt.subplots(figsize=(9,7))
ax.scatter(W['주말승차비'],W['주말운행비'],s=28,color=BLUE_L,ec='white',lw=.5)
gd=W[W['구']=='강동구']; ax.scatter(gd['주말승차비'],gd['주말운행비'],s=40,color=BLUE,ec='white',lw=.5,label='강동구')
ax.plot([.3,1.3],[.3,1.3],color=GRAY,ls='--',lw=1.5); ax.text(1.0,1.03,'승차 줄어든 만큼 운행도 줄인 선',color=INK2,fontsize=11,rotation=0)
for hj in W.nlargest(4,'주말틈').index: ax.annotate(W.loc[hj,'동'],(W.loc[hj,'주말승차비'],W.loc[hj,'주말운행비']),xytext=(5,-12),textcoords='offset points',fontsize=11,color=INK)
ax.set_xlim(.3,1.3); ax.set_ylim(.6,1.1); ax.set_xlabel('주말 하루 승차 ÷ 평일 하루 승차'); ax.set_ylabel('주말 하루 운행 ÷ 평일 하루 운행'); ax.legend(frameon=False,loc='lower right')
ax.set_title('주말 운행은 어느 동네나 평일의 약 0.8배로 같다',loc='left',fontsize=15,color=INK)
fig.savefig(f'{G}/T5_주말_승차vs운행.png'); plt.close()
# G6 2x2: 총량 부족 x 시간 어긋남
O1=pd.read_csv(f'{R}/1_시간어긋남_동별.csv',dtype={'hj':str},encoding='utf-8-sig').set_index('hj')
fig,ax=plt.subplots(figsize=(10,7))
c=np.where(O1['판정']=='부족 확정',BLUE,BLUE_L)
ax.scatter(O1['A_부족비율']*100,O1['시간어긋남']*100,s=26,c=c,ec='white',lw=.5)
q=O1['시간어긋남'].quantile(.75)*100; ax.axhline(q,color=GRAY,ls='--',lw=1.2)
ax.set_xlim(-150,90); ax.text(-145,q+.2,'시간 어긋남 상위 25%',fontsize=11,color=INK2)
for hj,rw in O1[O1['동'].isin(['강동 암사2동','강동 암사3동','강동 고덕1동','강동 천호3동','강동 암사1동'])].iterrows():
    ax.annotate(rw['동'].replace('강동 ',''),(rw['A_부족비율']*100,rw['시간어긋남']*100),xytext=(4,3),textcoords='offset points',fontsize=10,color=INK)
ax.set_xlabel('하루 총량: 있어야 할 운행보다 몇 % 적은가 (오른쪽일수록 부족)'); ax.set_ylabel('시간 어긋남: 사람 모양에 맞추려면 옮겨야 할 운행 (%)')
ax.set_title('총량 부족과 시간 어긋남은 서로 다른 문제다 (진한 점: 부족 확정 63곳)',loc='left',fontsize=15,color=INK)
fig.savefig(f'{G}/T6_총량부족_vs_시간어긋남.png'); plt.close()
print('ok')
