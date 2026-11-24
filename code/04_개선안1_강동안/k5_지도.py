import json, pandas as pd, numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon
import matplotlib.patheffects as pe
fm.fontManager.addfont('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'); plt.rcParams.update({'font.family':'WenQuanYi Zen Hei','axes.unicode_minus':False})
X='../../동단위_레이어/'; S='../송파이동_1107/'
g=json.load(open(X+'외부데이터/행정동_경계_20220401_서울.geojson'))
D=pd.read_csv('../결과/3_정정_행정동_두잣대.csv',dtype={'hj':str}).set_index('hj')
st=pd.DataFrame(json.load(open('결과_k3_경로후보_상세.json'))['D1 명일역 경유, 고덕역→비즈밸리→상일동역']['stops'])
sp=pd.DataFrame(json.load(open(S+'결과_경로후보_상세.json'))['D 기본+장지차고지 종점']['stops'])
rs=pd.read_csv(S+'서울시버스노선별정류소정보_20260902.csv',dtype={'노선명':str}); r3=rs[rs.노선명=='3324'].sort_values(['ROUTE_ID','순번'])
fig,ax=plt.subplots(figsize=(12,9),dpi=150)
cm=plt.get_cmap('Reds')
for f in g['features']:
    p=f['properties']
    if p['sggnm']!='강동구': continue
    hj=p['adm_cd2'][:10]; v=D.A_부족비율.get(hj,np.nan) if hj in D.index else np.nan
    col=cm(0.1+0.8*max(v,0)/0.8) if pd.notna(v) and v>0 else '#eef3f8'
    for poly in f['geometry']['coordinates']:
        ax.add_patch(Polygon(np.array(poly[0]),closed=True,fc=col,ec='white',lw=1.2))
    cs=np.array(f['geometry']['coordinates'][0][0]); cx,cy=cs.mean(0)
    lab=p['adm_nm'].split()[-1].replace('제','')+('\n부족 확정' if D.판정.get(hj,'')=='부족 확정' else '')
    ax.text(cx,cy,lab,fontsize=7.5,ha='center',va='center',color='#444')
ax.plot(r3.X좌표,r3.Y좌표,color='#7a7a7a',lw=1.3,ls=':',label='(비교) 2024년 생긴 3324번 · 2022 데이터로 판단할 때는 보지 않음',zorder=3)
ax.plot(sp.x,sp.y,color='#2a9d8f',lw=3,alpha=0.55,label='강동→송파 계획안 노선(따로 설계)',zorder=4)
ax.plot(st.x,st.y,color='#1f5fbf',lw=4.5,solid_capstyle='round',label=f'강동 안 출근 맞춤 노선 ({st.누적km.iloc[-1]:.1f}km, 정류장 {len(st)}곳)',zorder=5)
ax.scatter(st.x,st.y,s=16,color='white',edgecolor='#1f5fbf',lw=1.3,zorder=6)
key={'천호역3번출구.현대백화점':'천호역','암사역2번출구.암사종합시장':'암사역','암사3동주민센터.프라이어팰리스':'암사3동주민센터','명일역2번출구':'명일역','고덕역':'고덕역','고덕비즈밸리입구교차로':'고덕비즈밸리','상일동역2번출구':'상일동역'}
halo=[pe.withStroke(linewidth=3,foreground='white')]
for _,s in st.iterrows():
    if s.이름 in key: ax.annotate(key.pop(s.이름),(s.x,s.y),xytext=(6,5),textcoords='offset points',fontsize=11,fontweight='bold',color='#173f7a',path_effects=halo,zorder=7)
ax.set_xlim(127.105,127.185); ax.set_ylim(37.522,37.582); ax.set_aspect(1/np.cos(np.radians(37.55))); ax.axis('off')
ax.legend(loc='lower right',fontsize=9.5,frameon=True,framealpha=0.9)
ax.set_title('강동 안 출근 맞춤 노선: 버스가 모자란 서쪽(암사·천호) → 지하철역 4곳 → 고덕비즈밸리\n색 = 있어야 할 운행보다 모자란 정도(2022.4, 진할수록 부족) · 흰색 = 기대 이상',fontsize=12.5,loc='left')
fig.text(0.02,0.02,'자료: 버스 운행·승하차(2022.4), 행정동 경계(2022.4), 노선별 정류소(2026.9 경로 근사). 경로는 2022년에 버스가 다니던 정류장 연결만 이어 붙임(경기 노선 번호 겹침 제외).',fontsize=8,color='#666')
plt.savefig('그래프_K1_강동안_노선_지도.png',bbox_inches='tight'); print('ok')
