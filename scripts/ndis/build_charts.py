"""Build NDIS chart assets from validated annual website JSON. Requires matplotlib.
Run after build_ndis.py: python scripts/ndis/build_charts.py --out website/public_html/ndis
"""
import argparse,csv,json,math,textwrap,struct
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator
YEARS=['2023-24','2024-25','2025-26']
TEAL='#176378'; NEG='#9b4b28'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'path','svg.hashsalt':'apet-ndis','axes.spines.top':False,'axes.spines.right':False})

def build(out):
 data={fy:json.loads((out/('payments.json' if fy=='2025-26' else f'fy{fy}-payments.json')).read_text(encoding='utf-8')) for fy in YEARS}
 for fy,d in data.items():
  assert d['period_start']==fy[:4]+'-07-01' and d['period_end']=='20'+fy[-2:]+'-06-30'
  assert len(d['categories'])==len({r['label'] for r in d['categories']})==16
 assets=out/'charts';assets.mkdir(exist_ok=True)
 manifest={}
 def save(fig,key,title,rows,columns):
  fig.savefig(assets/(key+'.svg'),bbox_inches='tight',metadata={'Date':None,'Title':title,'Description':'Source: NDIA June payments snapshots. AUD, not adjusted for inflation. See APET source notes.'})
  fig.savefig(assets/(key+'.png'),bbox_inches='tight',dpi=150,metadata={'Title':title})
  plt.close(fig)
  with (assets/(key+'.csv')).open('w',newline='',encoding='utf-8') as f:
   w=csv.writer(f);w.writerow(columns);w.writerows(rows)
  width,height=struct.unpack('>II',(assets/(key+'.png')).read_bytes()[16:24])
  manifest[key]={'title':title,'columns':columns,'rows':rows,'width':width,'height':height}
 totals=[data[y]['national_aud'] for y in YEARS]
 growth=[None]+[(totals[i]/totals[i-1]-1)*100 for i in [1,2]]
 fig,ax=plt.subplots(figsize=(6,4.5));ax.bar(YEARS,[v/1e9 for v in totals],color=TEAL,width=.55)
 ax.set_ylim(0,max(totals)/1e9*1.25);ax.set_ylabel('Payments (AUD billions)')
 ax.set_title('Annual NDIS payments',loc='left',weight='bold',pad=20)
 for i,v in enumerate(totals): ax.text(i,v/1e9+.8,f'${v/1e9:.3f}bn'+('' if growth[i] is None else f'\n+{growth[i]:.1f}% from prior year'),ha='center',fontsize=10)
 ax.set_axisbelow(True);ax.grid(axis='y',alpha=.2);fig.text(.02,.01,'NDIA June snapshots · Not adjusted for inflation',fontsize=9)
 save(fig,'annual','Annual NDIS payments',[[y,v,g] for y,v,g in zip(YEARS,totals,growth)],['financial_year','payments_aud','change_from_prior_year_percent'])
 def bars(key,title,items,columns,rows,change=False):
  items=sorted(items,key=lambda x:x[1],reverse=True)
  fig,ax=plt.subplots(figsize=(10,8));labels=[textwrap.fill(k,34) for k,v in items];vals=[v/1e9 for k,v in items]
  ax.barh(range(len(vals)),vals,color=[TEAL if v>=0 else NEG for v in vals],height=.65)
  ax.set_yticks(range(len(vals)),labels,fontsize=10);ax.invert_yaxis();ax.axvline(0,color='#555',linewidth=.7)
  maxabs=max(abs(v) for v in vals);lo=min(0,min(vals));hi=max(0,max(vals));ax.set_xlim(lo-maxabs*.17,hi+maxabs*.27)
  for i,(name,value) in enumerate(items):
   label=('+' if value>0 and change else '−' if value<0 else '')+f'${abs(value)/1e6:,.3f}m'
   ax.text(vals[i]+maxabs*.012 if value>=0 else vals[i]-maxabs*.012,i,label,va='center',ha='left' if value>=0 else 'right',fontsize=9)
  ax.set_xlabel(('Change in payments' if change else 'Payments')+' (AUD billions)')
  ax.set_title(title,loc='left',weight='bold',pad=20);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
  fig.text(.02,.01,'NDIA June snapshots · Values labelled in millions · Not adjusted for inflation',fontsize=9)
  fig.tight_layout(rect=(0,.035,1,1));save(fig,key,title,rows,columns)
 for fy,d in data.items():
  items=[(r['label'],r['amount']) for r in d['categories']];assert all(v is not None for k,v in items)
  bars('categories-'+fy,'Where payments go · '+fy,items,['financial_year','support_category','payments_aud'],[[fy,k,v] for k,v in items])
 for i,start in enumerate(YEARS):
  for end in YEARS[i+1:]:
   a={r['label']:r['amount'] for r in data[start]['categories']};b={r['label']:r['amount'] for r in data[end]['categories']};assert a.keys()==b.keys()
   items=[(k,b[k]-a[k]) for k in a]
   bars('change-'+start+'-'+end,f'Category payment changes · {start} to {end}',items,
        ['from_financial_year','to_financial_year','support_category','from_payments_aud','to_payments_aud','change_aud'],[[start,end,k,a[k],b[k],v] for k,v in items],True)
   assert sum(v for k,v in items)==sum(b.values())-sum(a.values())
 states={r['code']:r['label'] for r in data[YEARS[0]]['states'] if r['amount'] is not None}
 assert len(states)==8
 for code,label in states.items():
  values=[next(r['amount'] for r in data[y]['states'] if r['code']==code) for y in YEARS]
  assert all(v is not None for v in values)
  fig,ax=plt.subplots(figsize=(4.6,3.4));v=[x/1e9 for x in values];ax.plot(YEARS,v,marker='o',color=TEAL,linewidth=2)
  ax.set_ylim(0,max(v)*1.28);ax.set_xlim(-.25,2.25);ax.yaxis.set_major_locator(MaxNLocator(4));ax.set_ylabel('AUD billions',fontsize=10)
  ax.set_title(label,weight='bold',fontsize=11);ax.grid(axis='y',alpha=.2)
  for i,x in enumerate(v):ax.annotate(f'${x:.3f}bn',(i,x),xytext=(0,9),textcoords='offset points',ha='center',fontsize=9)
  fig.text(.02,.01,'NDIA · Not inflation-adjusted · Individual vertical scale',fontsize=8)
  fig.tight_layout(rect=(0,.04,1,1));save(fig,'state-'+code,label+' payments',[[y,code,label,v] for y,v in zip(YEARS,values)],['financial_year','state_code','state','payments_aud'])
 (assets/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(f'Built {len(manifest)} charts, each with SVG, PNG and CSV: annual, 3 categories, 3 changes, 8 states.')
 return manifest
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();build(a.out)
