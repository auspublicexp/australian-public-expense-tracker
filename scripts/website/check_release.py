"""Render and check linked APET pages before a local website release.

This checks PHP output, internal targets and period metadata. It is not a
browser, screen-reader or complete accessibility conformance audit.
"""
from __future__ import annotations
import argparse
from collections import deque
from datetime import datetime,timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess
from urllib.parse import urljoin,urlsplit,parse_qs,unquote

class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links=[];self.assets=[];self.ids=[];self.title='';self.title_open=False
        self.meta={};self.canonical='';self.h1=0;self.tables=0;self.images=[];self.text=[]
        self.missing_alt=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='a' and a.get('href'):self.links.append(a['href'])
        if a.get('id'):self.ids.append(a['id'])
        if tag=='title':self.title_open=True
        if tag=='h1':self.h1+=1
        if tag=='table':self.tables+=1
        if tag=='meta':self.meta[a.get('name',a.get('property',''))]=a.get('content','')
        if tag=='link' and a.get('rel')=='canonical':self.canonical=a.get('href','')
        if tag in ['img','script'] and a.get('src'):self.assets.append(a['src'])
        if tag=='img':
            self.images.append(a.get('src',''))
            if 'alt' not in a:self.missing_alt.append(a.get('src',''))
        if tag=='link' and a.get('rel')=='stylesheet':self.assets.append(a.get('href',''))
    def handle_endtag(self,tag):
        if tag=='title':self.title_open=False
    def handle_data(self,value):
        self.text.append(value)
        if self.title_open:self.title+=value

def php_command(binary):
    command=[str(binary)]
    modules=subprocess.check_output(command+['-m'],text=True)
    ext=Path(binary).parent/'ext'
    if 'mbstring' not in modules and (ext/'php_mbstring.dll').exists():
        command+=['-d','extension_dir='+str(ext),'-d','extension=mbstring']
    return command

def render(root,url,command):
    parts=urlsplit(url);path=root/unquote(parts.path.lstrip('/'))
    if path.is_dir():path=path/'index.php'
    path=path.resolve()
    if not path.is_relative_to(root.resolve()):
        raise RuntimeError(f'{url}: PHP file resolves outside the website root')
    payload={'file':str(path),'root':str(root),'uri':parts.path+('?' + parts.query if parts.query else ''),
             'query':{k:v[-1] for k,v in parse_qs(parts.query).items()}}
    code="""error_reporting(E_ALL & ~E_DEPRECATED);ini_set('display_errors','stderr');register_shutdown_function(function(){$status=http_response_code()?:200;if($status<200||$status>=300){fwrite(STDERR,'HTTP status '.$status);}});$x=json_decode(stream_get_contents(STDIN),true);$_SERVER['DOCUMENT_ROOT']=$x['root'];$_SERVER['REQUEST_URI']=$x['uri'];$_GET=$x['query'];chdir(dirname($x['file']));require $x['file'];"""
    run=subprocess.run(command+['-r',code],input=json.dumps(payload),text=True,encoding='utf-8',capture_output=True)
    if run.returncode or run.stderr.strip():raise RuntimeError(f'{url}: {run.stderr}')
    page=Page();page.feed(run.stdout)
    return run.stdout,page

def check(root,command):
    origin='https://auspublicexp.org'
    queue=deque(['/','/transparency.php','/search.php']);seen=set();pages={};errors=[];warnings=[]
    while queue:
        url=queue.popleft()
        if url in seen:continue
        seen.add(url)
        try:html,page=render(root,url,command)
        except (RuntimeError,OSError) as exc:errors.append(str(exc));continue
        pages[url]={'title':page.title,'canonical':page.canonical,'tables':page.tables,'images':len(page.images)}
        if len(page.ids)!=len(set(page.ids)):errors.append(f'{url}: duplicate HTML ids')
        if not page.title or not page.meta.get('description'):errors.append(f'{url}: missing title/description')
        if 'apet-main-content' not in page.ids or '#apet-main-content' not in page.links:errors.append(f'{url}: missing skip-link target')
        if page.missing_alt:errors.append(f'{url}: images missing alt attributes: {page.missing_alt}')
        if page.h1!=1:warnings.append(f'{url}: {page.h1} h1 headings (check unavailable/legacy route)')
        for href in page.links+page.assets:
            target=urlsplit(urljoin(origin+url,href))
            if target.scheme not in ['http','https'] or target.netloc!='auspublicexp.org':continue
            local=(root/unquote(target.path.lstrip('/'))).resolve()
            if not local.is_relative_to(root):errors.append(f'{url}: path outside site: {href}');continue
            if not local.exists():errors.append(f'{url}: missing target {href}');continue
            candidate=target.path+('?' + target.query if target.query else '')
            if candidate==url and target.fragment and unquote(target.fragment) not in page.ids:
                errors.append(f'{url}: missing fragment {target.fragment}')
            if local.suffix=='.php' or local.is_dir():
                if ' (1)' in target.path:continue
                if candidate not in seen:queue.append(candidate)
        if len(seen)>600:raise RuntimeError('Unexpectedly large route graph; inspect before continuing.')
    return {'status':'PASS' if not errors else 'FAIL','checked_at_utc':datetime.now(timezone.utc).isoformat(),
            'web_root':str(root),'pages_checked':len(pages),'errors':errors,'warnings':warnings,'pages':pages,
            'limits':['PHP rendering and source/link checks only; no visual, keyboard or screen-reader certification.',
                      'Legacy PHP fgetcsv deprecation notices excluded; other runtime errors fail the check.',
                      'JavaScript-generated results and external link availability require separate checks.']}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--web-root',type=Path,default=Path(__file__).resolve().parents[2]/'website/public_html')
    parser.add_argument('--php',type=Path,default=shutil.which('php'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if not args.php:parser.error('Specify a PHP executable using --php.')
    result=check(args.web_root.resolve(),php_command(args.php.resolve()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='pages'},indent=2))
    return 0 if result['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
