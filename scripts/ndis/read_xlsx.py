from zipfile import ZipFile
import xml.etree.ElementTree as E
from pathlib import PurePosixPath
N={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def sheets(path):
 with ZipFile(path) as z:
  def xml(name):
   return E.fromstring(z.read(name).replace(b'http://purl.oclc.org/ooxml/spreadsheetml/main',b'http://schemas.openxmlformats.org/spreadsheetml/2006/main').replace(b'http://purl.oclc.org/ooxml/officeDocument/relationships',b'http://schemas.openxmlformats.org/officeDocument/2006/relationships'))
  strings=[''.join(e.itertext()) for e in xml('xl/sharedStrings.xml').findall('s:si',N)] if 'xl/sharedStrings.xml' in z.namelist() else []
  rels={e.attrib['Id']:e.attrib['Target'] for e in E.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
  for sheet in xml('xl/workbook.xml').findall('s:sheets/s:sheet',N):
   target=rels[sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
   target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
   rows=[]
   for row in xml(target).findall('s:sheetData/s:row',N):
    cells={}
    for c in row.findall('s:c',N):
     v=c.find('s:v',N); val=v.text if v is not None else None
     if c.attrib.get('t')=='s' and val is not None: val=strings[int(val)]
     elif c.attrib.get('t')=='inlineStr': val=''.join(c.find('s:is',N).itertext())
     elif val is not None:
      try: val=float(val)
      except ValueError: pass
     cells[c.attrib['r']]=val
    rows.append(cells)
   yield sheet.attrib['name'],rows
if __name__=='__main__':
 from pathlib import Path
 for p in Path(__file__).parent.joinpath('raw').glob('*.xlsx'):
  for name,rows in sheets(p):
   if any('Total annualised committed supports and total payments' in str(v) for r in rows[:1] for v in r.values()): print(p.name,name,rows)
