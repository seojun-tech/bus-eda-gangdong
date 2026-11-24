# 수도권 생활이동(OA-22300, 행정동 출발-도착, 목적별) 2023-04 6일 → 구×구 요약 + 강동 관련 동×동 요약
import sys, zipfile, pandas as pd
src = sys.argv[1]; out = sys.argv[2]
days = ['230411','230412','230413','230418','230415','230416']
A=[]; B=[]
for d in days:
    z = zipfile.ZipFile(f'{src}/d{d}.zip'); n = z.namelist()[0]
    for ch in pd.read_csv(z.open(n), usecols=['o_admdong_cd','d_admdong_cd','st_time_cd','move_purpose','move_dist','move_time','cnt'],
                          dtype={'o_admdong_cd':str,'d_admdong_cd':str,'st_time_cd':str}, chunksize=3_000_000, encoding='cp949'):
        ch['day']=d; ch['og']=ch.o_admdong_cd.str[:5]; ch['dg']=ch.d_admdong_cd.str[:5]
        ch['cd']=ch.cnt*ch.move_dist; ch['ct']=ch.cnt*ch.move_time
        A.append(ch.groupby(['day','og','dg','st_time_cd','move_purpose'])[['cnt','cd','ct']].sum().reset_index())
        m = (ch.og=='11740')|(ch.dg=='11740')
        B.append(ch[m].groupby(['day','o_admdong_cd','d_admdong_cd','st_time_cd','move_purpose'])[['cnt','cd','ct']].sum().reset_index())
    print(d, flush=True)
A=pd.concat(A).groupby(['day','og','dg','st_time_cd','move_purpose']).sum().reset_index()
B=pd.concat(B).groupby(['day','o_admdong_cd','d_admdong_cd','st_time_cd','move_purpose']).sum().reset_index()
A.to_csv(f'{out}/생활이동_구x구_시간_목적_202304_6일.csv.gz',index=False)
B.to_csv(f'{out}/생활이동_강동관련_동x동_시간_목적_202304_6일.csv.gz',index=False)
print(len(A),len(B))
