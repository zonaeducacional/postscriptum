import sys,json

from playwright.sync_api import sync_playwright
from pathlib import Path
import os,tempfile,threading,shutil
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
ROOT=Path(__file__).resolve().parents[1]
workspace=tempfile.TemporaryDirectory(prefix='postscriptum-test-')
static=Path(workspace.name)/'postscriptum';static.mkdir()
for name in ['index.html','app.js','style.css','sw.js','manifest.webmanifest','icon.svg','icon-192.png','icon-512.png']:
 shutil.copy2(ROOT/name,static/name)
shutil.copytree(ROOT/'fonts',static/'fonts')
class QuietHandler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=workspace.name))
threading.Thread(target=server.serve_forever,daemon=True).start()
BASE=f'http://127.0.0.1:{server.server_port}/postscriptum/'
out=Path(os.environ.get('POSTSCRIPTUM_TEST_OUTPUT',str(Path(tempfile.mkdtemp(prefix='postscriptum-qa-')))));out.mkdir(exist_ok=True)
with sync_playwright() as p:
 b=p.chromium.launch(**({'executable_path':os.environ['CHROMIUM_PATH']} if os.environ.get('CHROMIUM_PATH') else {}),headless=True)
 c=b.new_context(viewport={'width':390,'height':844},device_scale_factor=1)
 page=c.new_page();errors=[];requests=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('request',lambda r:requests.append(r.url))
 page.goto(BASE);page.get_by_role('heading',name='Fragmentos',exact=True).wait_for()
 page.get_by_role('button',name='Entendi, começar meu caderno').click()
 page.get_by_role('button',name='Escrever',exact=True).click()
 page.locator('#texto').fill('Uma lembrança de teste.');page.get_by_role('status').filter(has_text='Rascunho salvo').wait_for()
 page.reload();page.locator('#texto').wait_for();assert page.locator('#texto').input_value()=='Uma lembrança de teste.'
 page.get_by_role('button',name='Guardar',exact=True).click();page.locator('.item .texto').wait_for()
 assert page.locator('.item .texto').inner_text()=='Uma lembrança de teste.'
 page.get_by_role('button',name='Editar',exact=True).click();page.locator('#texto').fill('Uma lembrança revisada.');page.get_by_role('button',name='Salvar alteração').click()
 assert page.locator('summary').inner_text()=='1 versão anterior'
 page.get_by_role('button',name='Costura',exact=True).click();page.get_by_role('button',name='Montar texto',exact=True).click();page.locator('#montado').fill('Antes disso, pensei.\n\nUma lembrança revisada.\n\nE depois sorri.');page.locator('#titulo').fill('Minha costura');page.get_by_role('button',name='Salvar costura',exact=True).click();page.locator('.costura-salva').wait_for()
 page.get_by_role('button',name='Fragmentos',exact=True).click();assert page.locator('.item .texto').inner_text()=='Uma lembrança revisada.'
 page.get_by_role('button',name='Para a lixeira',exact=True).click();page.get_by_role('status').filter(has_text='Movido para a lixeira').wait_for();assert page.locator('.item').count()==0
 page.get_by_role('button',name='Cuidados e backup').click();page.get_by_role('button',name='Restaurar fragmento').click();page.get_by_role('status').filter(has_text='Registro restaurado').wait_for()
 page.locator('#senha').fill('senha-testes-12345')
 with page.expect_download() as dl:page.get_by_role('button',name='Baixar backup criptografado',exact=True).click()
 dest=out/'test-backup.json';dl.value.save_as(dest);assert 'Uma lembrança' not in dest.read_text()
 page.locator('#arquivo').set_input_files(str(dest));page.locator('#senha-import').fill('senha-errada');page.get_by_role('button',name='Verificar arquivo').click();page.get_by_role('alert').filter(has_text='Senha incorreta').wait_for()
 page.locator('#senha-import').fill('senha-testes-12345');page.get_by_role('button',name='Verificar arquivo').click();page.get_by_role('button',name='Confirmar restauração').wait_for();page.get_by_role('button',name='Confirmar restauração').click();page.get_by_role('status').filter(has_text='Backup restaurado').wait_for()
 page.get_by_role('button',name='Fragmentos',exact=True).click();assert page.locator('.item .texto').inner_text()=='Uma lembrança revisada.'
 page.screenshot(path=str(out/'fragmentos-mobile.png'),full_page=True)
 page.get_by_role('button',name='Costura',exact=True).click();page.get_by_role('button',name='Abrir',exact=True).click();assert 'E depois sorri.' in page.locator('#montado').input_value();page.screenshot(path=str(out/'costura-mobile.png'),full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.evaluate('navigator.serviceWorker.ready');page.reload();c.set_offline(True);page.reload();page.get_by_role('heading',name='Palavras entre fragmentos').wait_for();c.set_offline(False)
 # Failure injection: IndexedDB write throws. Text must remain visible, no false save.
 page.get_by_role('button',name='Escrever',exact=True).click();page.locator('#texto').fill('Não perder na falha.');page.get_by_role('status').filter(has_text='Rascunho salvo').wait_for()
 page.evaluate("() => {window.originalTransaction=IDBDatabase.prototype.transaction; IDBDatabase.prototype.transaction=function(...args){if(args[1]==='readwrite')throw new Error('quota simulada');return window.originalTransaction.apply(this,args)};}")
 page.get_by_role('button',name='Guardar',exact=True).click();page.get_by_role('alert').filter(has_text='Não foi possível gravar').wait_for();assert page.locator('#texto').input_value()=='Não perder na falha.'
 page.evaluate('() => {IDBDatabase.prototype.transaction=window.originalTransaction;}');page.get_by_role('button',name='Guardar',exact=True).click();page.get_by_role('status').filter(has_text='Fragmento guardado').wait_for()
 # Single writer lock.
 other=c.new_page();other.goto(BASE);other.get_by_role('alert').filter(has_text='já está aberto').wait_for();other.close()
 assert not errors,errors
 assert all(x.startswith(BASE) for x in requests),requests
 report={'passed':['separate examples','draft reload','create edit versions','editable independent stitch','trash restore','encrypted backup','wrong password rejected','validated restore','mobile no horizontal overflow','offline reload','write failure preserves text','single-writer lock','no external requests','no JavaScript errors'],'requests':len(requests),'viewport':'390x844'}
 # Native document export adapter (system picker is represented by a test bridge).
 native_context=b.new_context(viewport={'width':360,'height':800})
 native_context.add_init_script("window.PostScriptumAndroid={saveDocument(data,name,type,token){window.testExport={data,name,type};queueMicrotask(()=>window.postScriptumDocumentResult(token,true,'Salvo'));}}")
 native_page=native_context.new_page();native_page.goto(BASE);native_page.get_by_role('heading',name='Fragmentos',exact=True).wait_for()
 native_page.get_by_role('button',name='Cuidados e backup').click();native_page.locator('#senha').fill('senha-native-12345');native_page.get_by_role('button',name='Baixar backup criptografado',exact=True).click();native_page.get_by_role('status').filter(has_text='Arquivo salvo no local escolhido').wait_for()
 assert native_page.evaluate("JSON.parse(window.testExport.data).format")=='post-scriptum-encrypted'
 assert native_page.evaluate("navigator.serviceWorker.getRegistrations().then(x=>x.length)")==0
 assert native_page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 report['passed'].append('native export bridge, no service worker, 360px layout')
 native_context.close()
 (out/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False));b.close()

server.shutdown()
workspace.cleanup()
