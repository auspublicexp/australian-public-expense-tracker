"""Build reviewed June 2024-2026 NDIS snapshots. Standard library only.

Usage: python build_ndis.py --raw DIR --out DIR
Validated snapshots intentionally pinned: review new releases before extending.
"""
import argparse, csv, hashlib, html, json
from pathlib import Path
from read_xlsx import sheets

CLASSES = {'Capacity Building', 'Capital', 'Core', 'Missing'}
DIMS = ['SuppCatNm', 'SuppItemNmbr', 'SuppItemDesc', 'RsdsInStateCd',
        'RsdsInSrvcDstrctNm', 'NDISDsbltyGrpNm', 'NDIAAgeBnd']
STATES = {'ACT':'Australian Capital Territory', 'NSW':'New South Wales',
          'NT':'Northern Territory', 'QLD':'Queensland', 'SA':'South Australia',
          'TAS':'Tasmania', 'VIC':'Victoria', 'WA':'Western Australia'}
SOURCE = 'https://dataresearch.ndis.gov.au/media/4577/download?attachment'
REPORT = 'https://dataresearch.ndis.gov.au/media/4560/download?attachment'

def amount(value):
    if value in ('n/a', '', 'NULL'): return None
    return int(value)

def total(values):
    return None if any(v is None for v in values) else sum(values)

RELEASES = {2024:(4480,4029,['Table E.116','Table E.117']),2025:(4476,4359,['Table E.111','Table E.112']),2026:(4577,4560,['Table E.109','Table E.110'])}

def build(raw, out, year=2026):
    media, report_media, tables = RELEASES[year]
    fy=f'{year-1}-{str(year)[-2:]}'
    source = raw / f'payments_{year}-06.csv'
    source_url=f'https://dataresearch.ndis.gov.au/media/{media}/download?attachment'
    with source.open(encoding='utf-8-sig', newline='') as f:
        rows = [r for r in csv.DictReader(f) if any(r.values())]
    assert {r['RprtDt'] for r in rows} == {f'30-Jun-{str(year)[-2:]}'}, 'Unexpected reporting date'
    assert {r['SuppClass'] for r in rows} == CLASSES | ({'0'} if year==2024 else set()), 'Review support classes'
    def select(except_dim=None):
        return [r for r in rows if all(r[d] == 'ALL' for d in DIMS if d != except_dim)]
    classes = select()
    assert len(classes) == 4 and {r['SuppClass'] for r in classes} == CLASSES
    national = total([amount(r['PmtAmt']) for r in classes])
    assert national is not None
    categories = [r for r in select('SuppCatNm') if r['SuppCatNm'] != 'ALL']
    assert len(categories) == len({r['SuppCatNm'] for r in categories}) == 16
    for cls in CLASSES:
        parts = [amount(r['PmtAmt']) for r in categories if r['SuppClass'] == cls]
        subtotal = next(amount(r['PmtAmt']) for r in classes if r['SuppClass'] == cls)
        assert total(parts) is not None and abs(sum(parts)-subtotal) <= 1000 * len(parts)
    locations = [r for r in select('RsdsInStateCd') if r['RsdsInStateCd'] != 'ALL']
    assert {r['RsdsInStateCd'] for r in locations} == set(STATES) | {'OT','Missing'}
    states = []
    for code, name in STATES.items():
        group = [r for r in locations if r['RsdsInStateCd'] == code]
        assert len(group) == 4 and {r['SuppClass'] for r in group} == CLASSES
        states.append({'label':name, 'code':code, 'amount':total([amount(r['PmtAmt']) for r in group])})
    # Do not combine duplicated Missing labels or infer suppressed amounts.
    states += [{'label':'Other territories (OT)', 'code':'OT', 'amount':None},
               {'label':'Missing location', 'code':'Missing', 'amount':None}]
    cat = [{'label':r['SuppCatNm'], 'support_class':r['SuppClass'], 'amount':amount(r['PmtAmt'])} for r in categories]
    cls = [{'label':r['SuppClass'], 'amount':amount(r['PmtAmt'])} for r in classes]
    workbook=raw/f'national_{fy}_Q4.xlsx'
    report_values={}
    for name, sheet_rows in sheets(workbook):
        if name not in tables: continue
        cells={k:v for row in sheet_rows for k,v in row.items()}
        assert cells['A18']=='All' and f'year ending 30 June {year}' in cells['B2']
        report_values[name]=cells['B18']
    assert set(report_values)==set(tables)
    reconciliation={'source_url':f'https://dataresearch.ndis.gov.au/media/{report_media}/download?attachment',
                    'sha256':hashlib.sha256(workbook.read_bytes()).hexdigest(),
                    'tables_aud':report_values,'total_aud':round(sum(report_values.values()),2),
                    'status':'Comparison only; difference not explained'}
    report_total = reconciliation['total_aud']
    data = {'report_date':f'{year}-06-30','period_start':f'{year-1}-07-01','period_end':f'{year}-06-30',
            'period':f'1 July {year-1} – 30 June {year}','national_aud':national,
            'support_classes':cls, 'states':states, 'categories':cat,
            'source_url':source_url, 'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'report_comparison':reconciliation, 'difference_aud':round(national-report_total,2),
            'retrieved':'2026-10-16'}
    out.mkdir(parents=True,exist_ok=True)
    prefix='' if year==2026 else f'fy{fy}-'
    (out/(prefix+'payments.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (out/(prefix+'payments-summary.csv')).open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f); w.writerow(['period_start','period_end','view','group','payments_aud','status'])
        for view, values in [('National',[{'label':'Australia','amount':national}]),('Support class',cls),('State',states),('Support category',cat)]:
            for r in values: w.writerow([data['period_start'],data['period_end'],view,r['label'],r['amount'] if r['amount'] is not None else '', 'Unavailable' if r['amount'] is None else 'Published amount'])
    def table(items, heading):
        maxvalue=max(r['amount'] or 0 for r in items)
        result='<div class="table-responsive"><table class="table align-middle"><caption>Payments, '+data['period']+'. Australian dollars.</caption><thead><tr><th scope="col">'+heading+'</th><th scope="col" class="text-end">Payments (AUD)</th></tr></thead><tbody>'
        for r in sorted(items,key=lambda r:r['amount'] if r['amount'] is not None else -float('inf'),reverse=True):
            value=r['amount']; label=html.escape(r['label'])
            bar='' if value is None or value <= 0 else f'<div class="ndis-bar" style="width:{value/maxvalue*100:.3f}%" aria-hidden="true"></div>'
            display='Unavailable' if value is None else ('−' if value<0 else '')+'$'+f'{abs(value):,}'
            result+=f'<tr><th scope="row" class="fw-normal">{label}{bar}</th><td class="text-end text-nowrap">{display}</td></tr>'
        return result+'</tbody></table></div>'
    template=(Path(__file__).parent/'page-template.php').read_text(encoding='utf-8')
    template=template.replace('NDIS Payments |',f'NDIS Payments {fy} |')
    template=template.replace('FY2025–26','FY'+fy.replace('-','–')).replace('1 July 2025','1 July '+str(year-1)).replace('June 2026','June '+str(year)).replace('2025–26 Q4',fy.replace('-','–')+' Q4')
    template=template.replace(SOURCE,source_url).replace(REPORT,reconciliation['source_url']).replace('Tables E.109 and E.110','Tables '+tables[0].removeprefix('Table ')+' and '+tables[1].removeprefix('Table '))
    template=template.replace('Table E.111 uses the year support was provided and is a different measure.','Tables organised by the year support was provided use a different measure.')
    template=template.replace('Its negative $3,000 entry is retained as published; the data rules do not explain it.', 'Its negative $3,000 entry is retained as published; the data rules do not explain it.' if year==2026 else 'Its published amount is included in the national total.')
    if year==2024:
        template=template.replace('Small differences between category and class sums are retained rather than adjusted.','Small differences between category and class sums are retained rather than adjusted. Four suppressed detail rows use support class “0”; they have no national aggregate row and are not added to the published support-class totals.')
    for filename in ['payments-summary.csv','payments.json','validation.json']:
        template=template.replace('href="'+filename+'"','href="'+prefix+filename+'"')
    navigation='<nav aria-label="Financial year" class="d-flex flex-wrap align-items-center gap-2 my-4"><span class="fw-semibold me-2">Financial year:</span>'
    for y in sorted(RELEASES,reverse=True):
        label=f'{y-1}–{str(y)[-2:]}'
        url='/ndis/' if y==2026 else f'/ndis/fy{y-1}-{str(y)[-2:]}.php'
        navigation+=f'<a class="btn btn-'+('dark' if y==year else 'outline-dark')+'" href="'+url+'"'+(' aria-current="page"' if y==year else '')+'>'+label+'</a>'
    navigation+='</nav><p class="small text-secondary">Available annual snapshots: July 2023 to June 2026. Each June snapshot covers the preceding financial year; amounts are not adjusted for inflation.</p>'
    template=template.replace('<h1>NDIS payments</h1>','<h1>NDIS payments</h1>'+navigation)
    replacements={'@@TOTAL@@':f'{national/1e9:.3f}','@@EXACT@@':f'{national:,}',
                  '@@STATES@@':table(states,'Participant residence'), '@@CLASSES@@':table(cls,'Support class'),
                  '@@CATEGORIES@@':table(cat,'Support category'),
                  '@@REPORT@@':f'{report_total/1e9:.3f}', '@@DIFF@@':f'{(national-report_total)/1e6:.3f}',
                  '@@PERCENT@@':f'{(national-report_total)/report_total*100:.3f}'}
    for k,v in replacements.items(): template=template.replace(k,v)
    assert '@@' not in template
    (out/('index.php' if year==2026 else f'fy{fy}.php')).write_text(template,encoding='utf-8')
    checks={'raw_rows':len(rows),'national_aud':national,'category_sum_aud':sum(r['amount'] for r in cat),
            'category_difference_aud':sum(r['amount'] for r in cat)-national,
            'report_difference_aud':data['difference_aud'],
            'state_rows_available':sum(r['amount'] is not None for r in states),
            'missing_location_rows':sum(r['RsdsInStateCd']=='Missing' for r in locations),
            'source_sha256':data['source_sha256'], 'status':'PASS with disclosed source differences'}
    (out/(prefix+'validation.json')).write_text(json.dumps(checks,indent=2)+'\n')
    return checks

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--raw',type=Path,required=True); p.add_argument('--out',type=Path,required=True)
    a=p.parse_args(); print(json.dumps({year:build(a.raw,a.out,year) for year in RELEASES},indent=2))
