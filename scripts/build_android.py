#!/usr/bin/env python3
"""Build a release APK with official Android tools. No third-party build dependencies."""
import argparse,hashlib,json,os,shutil,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WEB_FILES=['index.html','style.css','app.js','manifest.webmanifest','icon.svg','icon-192.png','icon-512.png']
def run(*args,env=None):
    subprocess.run([str(x) for x in args],check=True,env=env)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--unsigned',action='store_true');args=parser.parse_args()
    sdk=Path(os.environ.get('ANDROID_HOME',os.environ.get('ANDROID_SDK_ROOT',str(Path.home()/'Android/Sdk'))))
    tools=sdk/'build-tools/34.0.0';platform=sdk/'platforms/android-34/android.jar'
    for path in [tools/'aapt2',tools/'d8',tools/'zipalign',tools/'apksigner',platform]:
        if not path.is_file():raise SystemExit(f'Instale Android SDK Platform 34 e Build Tools 34.0.0. Ausente: {path}')
    build=ROOT/'android/build';build.mkdir(exist_ok=True)
    # Only owned output directories; do not collect stale classes or web resources.
    for name in ['assets','classes','dex']:
        folder=build/name
        if folder.exists():shutil.rmtree(folder)
        folder.mkdir()
    www=build/'assets/www';www.mkdir()
    for name in WEB_FILES:shutil.copy2(ROOT/name,www/name)
    shutil.copytree(ROOT/'fonts',www/'fonts')
    run(tools/'aapt2','compile','--dir',ROOT/'android/res','-o',build/'resources.zip')
    run(tools/'aapt2','link','-I',platform,'--manifest',ROOT/'android/AndroidManifest.xml','-A',build/'assets','-o',build/'resources.apk',build/'resources.zip')
    sources=sorted((ROOT/'android/src').rglob('*.java'))
    run('javac','-parameters','-encoding','UTF-8','-source','8','-target','8','-bootclasspath',str(platform)+os.pathsep+str(tools/'core-lambda-stubs.jar'),'-d',build/'classes',*sources)
    classes=sorted((build/'classes').rglob('*.class'))
    run(tools/'d8','--release','--min-api','26','--lib',platform,'--output',build/'dex',*classes)
    shutil.copy2(build/'resources.apk',build/'unaligned.apk')
    with zipfile.ZipFile(build/'unaligned.apk','a',zipfile.ZIP_DEFLATED) as z:
        for dex in (build/'dex').glob('*.dex'):z.write(dex,dex.name)
    run(tools/'zipalign','-f','4',build/'unaligned.apk',build/'unsigned.apk')
    out=ROOT/'releases';out.mkdir(exist_ok=True)
    if args.unsigned:
        target=out/'post-scriptum-0.1.0-unsigned.apk';shutil.copy2(build/'unsigned.apk',target)
    else:
        config_path=Path.home()/'.local/share/postscriptum-signing/signing.json'
        conf=json.loads(config_path.read_text()) if config_path.exists() else {}
        keystore=os.environ.get('POSTSCRIPTUM_KEYSTORE',conf.get('keystore'))
        password=os.environ.get('POSTSCRIPTUM_STORE_PASSWORD',conf.get('password'))
        alias=os.environ.get('POSTSCRIPTUM_KEY_ALIAS',conf.get('alias','postscriptum'))
        if not keystore or not password:raise SystemExit('Configure POSTSCRIPTUM_KEYSTORE e POSTSCRIPTUM_STORE_PASSWORD; a chave privada nunca deve entrar no repositório.')
        env=os.environ.copy();env['POSTSCRIPTUM_STORE_PASSWORD']=password
        target=out/'post-scriptum-0.1.0.apk'
        run(tools/'apksigner','sign','--ks',keystore,'--ks-key-alias',alias,'--ks-pass','env:POSTSCRIPTUM_STORE_PASSWORD','--key-pass','env:POSTSCRIPTUM_STORE_PASSWORD','--out',target,build/'unsigned.apk',env=env)
        run(tools/'apksigner','verify','--verbose','--print-certs',target)
    digest=hashlib.sha256(target.read_bytes()).hexdigest()
    checksum=target.with_suffix('.apk.sha256');checksum.write_text(f'{digest}  {target.name}\n')
    print(f'APK: {target}\nSHA-256: {digest}')
if __name__=='__main__':main()
