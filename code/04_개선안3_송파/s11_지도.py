import json, pandas as pd, numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import matplotlib.patheffects as pe
fm.fontManager.addfont('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'); plt.rcParams.update({'font.family':'WenQuanYi Zen Hei','axes.unicode_minus':False})
X='../../동단위_레이어/'
g=json.load(open(X+'외부데이터/행정동_경계_20220401_서울.geojson'))
lp=pd.read_csv(X+'외부데이터/행정동_생활인구_202204_평일주말_시간대평균.csv',dtype=str).drop_duplicates('행정동코드'); nm10=dict(zip(lp.행정동코드,lp.구_행정동)); nm10.update({'1174052500':'강동구 상일제1동','1174052600':'강동구 상일제2동'})
K=json.load(open('결과_경로후보_상세.json'))['D 기본+장지차고지 종점']; c=pd.DataFrame(K['pairs']); o=c.groupby('강동동').양방향.sum(); d=c.groupby('송파동').양방향.sum()
st=pd.DataFrame(K['stops']); J={'km':st.누적km.iloc[-1]}
rs=pd.read_csv('서울시버스노선별정류소정보_20260902.csv',dtype={'노선명':str}); r3=rs[rs.노선명=='3413'].sort_values('순번')
fig,ax=plt.subplots(figsize=(11,12),dpi=150); ax.set_facecolor('white')
vmax=max(o.max(),d.max())
cm=plt.get_cmap('Oranges')
for f in g['features']:
    p=f['properties']; gu=p['sggnm']
    if gu not in ('강동구','송파구'): continue
    nm=nm10.get(p['adm_cd2'],''); v=(o.get(nm,0) if gu=='강동구' else d.get(nm,0))
    col=cm(0.08+0.8*v/vmax) if v>0 else '#f2f2f2'
    for poly in f['geometry']['coordinates']:
        ax.add_patch(Polygon(np.array(poly[0]),closed=True,fc=col,ec='white',lw=1.0))
    cs=np.array(f['geometry']['coordinates'][0][0]); cx,cy=cs.mean(0)
    ax.text(cx,cy,p['adm_nm'].split()[-1].replace('제',''),fontsize=7,ha='center',va='center',color='#555')
# 구 경계 굵게
for f in g['features']:
    pass
ax.plot(r3.X좌표,r3.Y좌표,color='#8a8a8a',lw=1.4,ls='--',alpha=0.8,label='지금 3413번 (문정까지 크게 돌아감)')
ax.plot(st.x,st.y,color='#1f5fbf',lw=4,solid_capstyle='round',label=f'초안 노선 ({J["km"]:.1f}km, 정류장 {len(st)}곳)',zorder=5)
ax.scatter(st.x,st.y,s=14,color='white',edgecolor='#1f5fbf',lw=1.2,zorder=6)
key={'강동공영차고지':'기점 강동공영차고지','상일동역1번출구':'상일동역','고덕역':'고덕역','명일역2번출구':'명일역','굽은다리역구민회관.강동홈플러스':'굽은다리역','길동역1번출구':'길동역','둔촌동역4번출구':'둔촌동역','올림픽공원역':'올림픽공원역','오금역3번출구':'오금역','문정역2번출구':'문정역','문정법조단지.건영아파트':'문정법조단지','장지공영차고지':'종점 장지공영차고지'}
halo=[pe.withStroke(linewidth=3,foreground='white')]
for _,s in st.iterrows():
    if s.이름 in key: ax.annotate(key.pop(s.이름),(s.x,s.y),xytext=(6,4),textcoords='offset points',fontsize=10,fontweight='bold',color='#173f7a',path_effects=halo,zorder=7)
ax.set_xlim(127.08,127.19); ax.set_ylim(37.462,37.585); ax.set_aspect(1/np.cos(np.radians(37.53))); ax.axis('off')
ax.legend(loc='lower right',fontsize=10,frameon=False)
ax.set_title('강동 동남부 → 문정 업무지구(문정2동, 일하는 사람 10만 명): 바로 가는 버스가 없는 길을 잇는 초안\n색 = 이 노선으로 짧아지는 강동–송파 이동량(하루 양방향, 2023.4 평일)',fontsize=13,loc='left')
sm=plt.cm.ScalarMappable(cmap=cm,norm=plt.Normalize(0,vmax)); cb=fig.colorbar(sm,ax=ax,shrink=0.35,pad=0.01); cb.set_label('하루 이동(건)')
fig.text(0.02,0.02,'자료: 수도권 생활이동(2023.4 평일 4일), 버스 운행·승하차(2022.4), 노선별 정류소(2026.9 경로 근사). 경로는 2022년에 버스가 다니던 정류장 연결만 이어 붙임.',fontsize=8,color='#666')
plt.savefig('그래프_S1_노선초안_지도.png',bbox_inches='tight'); print('ok')
