# 시간대 파트(11/07) 1단계: 질문 ①~⑤ 계산 (4월 기본) + 6·10월 다시 계산
import pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore')
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, adjusted_rand_score
P='/mnt/project-files/프로젝트2'; R=f'{P}/최종발표/시간대_1107/결과'; EXT=f'{P}/동단위_레이어/외부데이터'
D=pd.read_csv(f'{P}/최종발표/결과/3_정정_행정동_두잣대.csv',dtype={'hj':str},encoding='utf-8-sig').set_index('hj')
NM=(D['구'].str[:-1]+' '+D['행정동'].str.replace('제','',regex=False))
H=list(range(24)); SV=[5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,0]  # 버스가 다니는 시간(05~01시)
LOG=[]
def lg(k,v): LOG.append(dict(항목=k,값=v)); print(k,'|',v)
def load(m,runfile=None):
    X=pd.read_csv(f'{R}/0_패널_버스_{m}.csv',dtype={'hj':str},encoding='utf-8-sig').set_index('hj')
    if runfile is not None:
        Y=pd.read_csv(runfile,dtype={'hj':str},encoding='utf-8-sig').set_index('hj'); X[Y.columns]=Y
    wd,we={'04':(21,9),'06':(20,10),'10':(19,12)}[m]
    run=pd.DataFrame({h:X[f'평일운행_{h:02d}']*wd+X[f'주말운행_{h:02d}']*we for h in H})
    on=pd.DataFrame({h:X[f'승차_{h:02d}'] for h in H}); off=pd.DataFrame({h:X[f'하차_{h:02d}'] for h in H})
    return X,run,on,off
def tvd(a,b):
    a=a.div(a.sum(axis=1),axis=0); b=b.div(b.sum(axis=1),axis=0); return 0.5*(a-b).abs().sum(axis=1)
def shape48(on,off):
    S=pd.concat([on[SV],off[SV]],axis=1); S.columns=[f'승차_{h:02d}' for h in SV]+[f'하차_{h:02d}' for h in SV]; return S.div(S.sum(axis=1),axis=0)
X,run,on,off=load('04'); dem=on+off
ok=(run[SV].sum(axis=1)>0)&(dem[SV].sum(axis=1)>0)
lg('분석 동 수',int(ok.sum()))
# ---------- ① 총량 vs 시간 배분 ----------
T=tvd(dem[SV],run[SV])[ok]
lg('① 시간 어긋남(옮겨야 할 운행 비율) 서울 중앙값',round(T.median(),3))
lg('① 상위 10% 기준',round(T.quantile(.9),3))
# 동마다: 어느 시간이 버스에 비해 사람이 몰리나 (수요 몫 - 운행 몫)
ds=dem[SV].div(dem[SV].sum(axis=1),axis=0); rs=run[SV].div(run[SV].sum(axis=1),axis=0); gap=(ds-rs)
BAND={'새벽(05~06시)':[5,6],'출근(07~09시)':[7,8],'낮(10~16시)':[10,11,12,13,14,15],'퇴근(17~19시)':[17,18],'저녁(19~21시)':[19,20],'밤(22~01시)':[22,23,0]}
BAND={'새벽 05~06':[5],'출근 06~09':[6,7,8],'낮 09~17':[9,10,11,12,13,14,15,16],'퇴근 17~20':[17,18,19],'저녁 20~22':[20,21],'밤 22~01':[22,23,0]}
G=pd.DataFrame({k:gap[v].sum(axis=1) for k,v in BAND.items()})
out1=pd.DataFrame({'동':NM,'구':D['구'],'판정':D['판정'],'A_부족비율':D['A_부족비율'],'시간어긋남':T}).join(G.round(3))
out1['모자란시간']=G.idxmax(axis=1); out1['남는시간']=G.idxmin(axis=1)
# 지하철로 확인(버스와 무관한 수요 모양): 역 있는 동만
SW=pd.read_csv(f'{R}/0_패널_지하철.csv',dtype={'hj':str},encoding='utf-8-sig').set_index('hj')
sub=pd.DataFrame({h:SW[f'지하철승차_{h:02d}']+SW[f'지하철하차_{h:02d}'] for h in H})
hs=(sub[SV].sum(axis=1)>20000)&ok
T2=tvd(sub[SV],run[SV])[hs]
rho=stats.spearmanr(T[hs],T2)
lg('① 확인: 버스 수요 기준 vs 지하철 수요 기준 어긋남 순위상관(역 있는 동)',f'{rho.correlation:.2f} (n={hs.sum()}, p={rho.pvalue:.1e})')
out1['시간어긋남_지하철기준']=T2
# 2x2: 총량 부족 x 시간 어긋남
hiT=out1['시간어긋남']>=out1['시간어긋남'].quantile(.75)
short=out1['판정'].eq('부족 확정')
out1['칸']=np.select([short&hiT,short&~hiT,~short&hiT],['총량도 부족+시간도 틀림','총량 부족','시간만 틀림'],'괜찮음')
lg('① 칸별 동 수',out1['칸'].value_counts().to_dict())
lg('① 부족 확정 동 시간어긋남 중앙값 vs 나머지',f"{out1.loc[short,'시간어긋남'].median():.3f} vs {out1.loc[~short,'시간어긋남'].median():.3f}, MWU p={stats.mannwhitneyu(out1.loc[short,'시간어긋남'].dropna(),out1.loc[~short,'시간어긋남'].dropna()).pvalue:.3f}")
# 시간 재배분만 했을 때 효과: 그 동 운행 총량 그대로, 수요 모양에 맞춰 나누면 가장 붐비는 시간 부하가 얼마나 줄어드나
L=(dem[SV]/run[SV].replace(0,np.nan)); Lday=dem[SV].sum(axis=1)/run[SV].sum(axis=1)
out1['가장붐빈시간_배']=(L.max(axis=1)/Lday).round(2)
out1['가장붐빈시']=L.idxmax(axis=1)
out1.to_csv(f'{R}/1_시간어긋남_동별.csv',encoding='utf-8-sig')
# 서울 전체: 시간별 수요 몫 - 운행 몫
sh=pd.DataFrame({'수요몫':dem[SV][ok].sum()/dem[SV][ok].sum().sum(),'운행몫':run[SV][ok].sum()/run[SV][ok].sum().sum()})
sh['회당_서울평균대비']=sh['수요몫']/sh['운행몫']; sh.to_csv(f'{R}/1_서울_시간별_몫.csv',encoding='utf-8-sig'); print(sh.round(3).T.to_string())
# ---------- ② 사람 수(생활인구) 기준 기대 운행 ----------
LP=pd.read_csv(f'{R}/0_패널_생활인구.csv',dtype={'hj':str},encoding='utf-8-sig').set_index('hj')
rows=[];RES={}
for h in SV:
    y=np.log1p(X[f'평일운행_{h:02d}']); x=np.log(LP[f'생활인구_평일_{h:02d}'])
    m_=ok&x.notna()&np.isfinite(x)
    b,a,r_,p_,se=stats.linregress(x[m_],y[m_])
    RES[h]=(np.expm1(y)-np.expm1(a+b*x))/np.expm1(a+b*x)
    rows.append(dict(시=h,기울기=round(b,3),설명력R2=round(r_**2,3),기울기_se=round(se,3)))
E=pd.DataFrame(rows); E.to_csv(f'{R}/2_시간별_사람수_따라가기.csv',index=False,encoding='utf-8-sig'); print(E.to_string())
RR=pd.DataFrame(RES)[SV]; RR.columns=[f'{h:02d}시' for h in SV]
out2=pd.DataFrame({'동':NM,'구':D['구'],'판정':D['판정']}).join(RR.round(3))
for k,v in BAND.items(): out2[k]=pd.DataFrame(RES)[v].mean(axis=1).round(3)
out2.to_csv(f'{R}/2_사람수기준_부족_동x시간.csv',encoding='utf-8-sig')
for k in BAND:
    t=out2.dropna(subset=[k]).nsmallest(5,k); lg(f'② {k} 사람 수 대비 운행 가장 적은 동',' / '.join(f"{a} {v:+.0%}" for a,v in zip(t['동'],t[k])))
# ②-확인: 승차 기준 부족(판정)과 사람 수 기준 부족이 겹치나
oo=out2.join(out1[['시간어긋남']])
oo['사람수_하루']=pd.DataFrame(RES)[SV].mean(axis=1)
lg('② 사람수 기준 하루 평균 부족(−) vs 판정 부족 확정',f"부족확정 중앙 {oo.loc[short,'사람수_하루'].median():+.2f} vs 나머지 {oo.loc[~short,'사람수_하루'].median():+.2f}")
# ---------- ③ 주말 ----------
LPd=LP; wkp=LPd[[f'생활인구_평일_{h:02d}' for h in range(7,23)]].mean(axis=1); wep=LPd[[f'생활인구_주말_{h:02d}' for h in range(7,23)]].mean(axis=1)
C=pd.read_csv(f'{P}/동단위_레이어/캐시/정류장x노선_평일주말_승하차_202204.csv.gz',dtype={'ARS':str})
s22=pd.read_csv(f'{EXT}/버스정류소_유형_20220401.csv',dtype={'ARS번호':str,'행정동코드':str}); s22['ARS']=s22['ARS번호'].str.zfill(5); mp=s22.drop_duplicates('ARS').set_index('ARS')['행정동코드']
C['hj']=C['ARS'].str.zfill(5).map(mp); cb=C.pivot_table(index='hj',columns='구분',values='승차',aggfunc='sum')
we_run=X[[f'주말운행_{h:02d}' for h in H]].sum(axis=1); wk_run=X[[f'평일운행_{h:02d}' for h in H]].sum(axis=1)
W=pd.DataFrame({'동':NM,'구':D['구'],'판정':D['판정'],'주말운행비':we_run/wk_run,'주말사람비':wep/wkp,'주말승차비':((cb['주말']/9)/(cb['평일']/21)).reindex(D.index)}).loc[ok[ok].index]
r1=stats.spearmanr(W['주말사람비'],W['주말운행비'],nan_policy='omit'); r2=stats.spearmanr(W['주말승차비'],W['주말운행비'],nan_policy='omit')
lg('③ 주말 운행비 서울 중앙값 / 10~90%',f"{W['주말운행비'].median():.2f} / {W['주말운행비'].quantile(.1):.2f}~{W['주말운행비'].quantile(.9):.2f}")
lg('③ 주말 사람비 중앙값 / 10~90%',f"{W['주말사람비'].median():.2f} / {W['주말사람비'].quantile(.1):.2f}~{W['주말사람비'].quantile(.9):.2f}")
lg('③ 주말 승차비 중앙값 / 10~90%',f"{W['주말승차비'].median():.2f} / {W['주말승차비'].quantile(.1):.2f}~{W['주말승차비'].quantile(.9):.2f}")
lg('③ 주말 사람비 ↔ 주말 운행비 순위상관',f'{r1.correlation:.2f} (p={r1.pvalue:.2g})')
lg('③ 주말 승차비 ↔ 주말 운행비 순위상관',f'{r2.correlation:.2f} (p={r2.pvalue:.2g})')
W['주말틈']=W['주말승차비']/W['주말운행비']; W['주말틈_사람']=W['주말사람비']/W['주말운행비']
W.to_csv(f'{R}/3_주말_동별.csv',encoding='utf-8-sig')
t=W.nlargest(8,'주말틈'); lg('③ 주말 승차는 덜 줄었는데 운행은 줄어든 동(승차비/운행비)',' / '.join(f"{a} {b:.2f}" for a,b in zip(t['동'],t['주말틈'])))
# ---------- ④ 막차 ----------
late_sub=SW['지하철하차_23']+SW['지하철하차_00']
late_run=run[23]+run[0]+run[1]; late_on=on[23]+on[0]+on[1]
N=pd.DataFrame({'동':NM,'구':D['구'],'판정':D['판정'],'지하철_밤하차_하루':late_sub/30,'버스_밤운행_하루':late_run/30,'버스_밤승차_하루':late_on/30,
                '지하철_하루하차':SW[[f'지하철하차_{h:02d}' for h in H]].sum(axis=1)/30})
N['밤하차비중']=N['지하철_밤하차_하루']/N['지하철_하루하차']
N['밤_내린사람_버스1회당']=N['지하철_밤하차_하루']/N['버스_밤운행_하루'].replace(0,np.nan)
# 막차 시간: 평일 운행이 1회 이상인 마지막 시각 (24시 넘어가면 24+)
def lastbus(rw):
    for h in [3,2,1,0,23,22,21]:
        if rw[f'평일운행_{h:02d}']>=1: return h+24 if h<5 else h
    return np.nan
N['막차시']=X.apply(lastbus,axis=1)
N=N[N['지하철_밤하차_하루']>200]
lg('④ 역 있는 동(밤 하차 200명/일 이상)',len(N))
t=N.nlargest(10,'밤_내린사람_버스1회당'); lg('④ 밤(23~01시) 지하철에서 내린 사람 / 버스 1회',' / '.join(f"{a} {b:.0f}" for a,b in zip(t['동'],t['밤_내린사람_버스1회당'])))
lg('④ 중앙값',round(N['밤_내린사람_버스1회당'].median(),1))
N.to_csv(f'{R}/4_막차_동별.csv',encoding='utf-8-sig')
# ---------- ⑤ 하루 모양 유형 ----------
S48=shape48(on,off)[ok].fillna(0)
sc={}
for k in range(3,8):
    km=KMeans(k,n_init=20,random_state=0).fit(S48); sc[k]=silhouette_score(S48,km.labels_)
lg('⑤ 묶음 수별 실루엣',{k:round(v,3) for k,v in sc.items()})
K=int(pd.Series(sc).idxmax()); K=max(K,4) if sc.get(4,0)>=0.9*max(sc.values()) else K
km=KMeans(K,n_init=50,random_state=0).fit(S48); lab=pd.Series(km.labels_,index=S48.index)
lg('⑤ 쓴 묶음 수',K)
prof=S48.groupby(lab).mean()
# 묶음 특징: 아침 승차 몫, 아침 하차 몫, 저녁 승차 몫, 밤 몫
on_c=[f'승차_{h:02d}' for h in SV]; off_c=[f'하차_{h:02d}' for h in SV]
feat=pd.DataFrame({'아침승차':prof[[f'승차_{h:02d}' for h in [6,7,8]]].sum(axis=1)/prof[on_c].sum(axis=1),
                   '아침하차':prof[[f'하차_{h:02d}' for h in [6,7,8]]].sum(axis=1)/prof[off_c].sum(axis=1),
                   '저녁승차':prof[[f'승차_{h:02d}' for h in [17,18,19]]].sum(axis=1)/prof[on_c].sum(axis=1),
                   '밤승차':prof[[f'승차_{h:02d}' for h in [21,22,23,0]]].sum(axis=1)/prof[on_c].sum(axis=1),
                   '낮승차':prof[[f'승차_{h:02d}' for h in range(10,16)]].sum(axis=1)/prof[on_c].sum(axis=1),
                   '동수':lab.value_counts()})
print(feat.round(3).to_string())
feat.to_csv(f'{R}/5_유형_특징.csv',encoding='utf-8-sig')
prof.to_csv(f'{R}/5_유형_모양.csv',encoding='utf-8-sig')
# 유형별 시간 부하: 승차/운행 (서울 같은 시간 대비)
Lh=(on[SV][ok]/run[SV][ok].replace(0,np.nan)); Lh=Lh/Lh.median()
LT=Lh.groupby(lab).median(); LT.to_csv(f'{R}/5_유형_시간별_붐빔.csv',encoding='utf-8-sig'); print(LT.round(2).to_string())
out5=pd.DataFrame({'동':NM,'구':D['구'],'판정':D['판정'],'유형':lab}).join(out1[['시간어긋남','칸']]).join(W[['주말틈']])
out5.to_csv(f'{R}/5_유형_동별.csv',encoding='utf-8-sig')
lg('⑤ 유형 x 판정(부족 확정 수)',pd.crosstab(out5['유형'],out5['판정']).to_dict())
# ---------- 다시 계산: 6·10월, 4월 중앙값 ----------
stab=[]
for tag,(m,rf) in {'4월 중앙값 운행':('04',f'{R}/0_패널_운행_04중앙값.csv'),'6월':('06',None),'10월':('10',None)}.items():
    X2,run2,on2,off2=load(m,rf); T_=tvd((on2+off2)[SV],run2[SV]).reindex(T.index)
    S2=shape48(on2,off2).reindex(S48.index).fillna(0); S2.columns=S48.columns; lab2=pd.Series(km.predict(S2),index=S2.index)
    km2=KMeans(K,n_init=50,random_state=0).fit(S2)
    hi1=set(T[T>=T.quantile(.75)].index); hi2=set(T_[T_>=T_.quantile(.75)].index)
    stab.append(dict(판=tag,어긋남_순위상관=round(stats.spearmanr(T,T_,nan_policy='omit').correlation,3),상위25_겹침=round(len(hi1&hi2)/len(hi1),2),
                     유형_그대로_비율=round((lab2==lab).mean(),3),새로묶어도_ARI=round(adjusted_rand_score(lab,km2.labels_),3)))
ST=pd.DataFrame(stab); print(ST.to_string()); ST.to_csv(f'{R}/6_다시계산.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(LOG).to_csv(f'{R}/숫자.csv',index=False,encoding='utf-8-sig')
