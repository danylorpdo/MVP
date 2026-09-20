"""Baixa a base pública oficial; verifica ZIP e registra hashes sem credenciais."""
from pathlib import Path
import datetime
import hashlib
import json
import urllib.request
import zipfile
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw'
RAW.mkdir(parents=True,exist_ok=True)
URL='https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce'
archive=RAW/'olist.zip'
if not archive.exists():
    temporary=RAW/'olist.zip.part'
    with urllib.request.urlopen(URL,timeout=90) as response, temporary.open('wb') as output:
        while chunk:=response.read(1024*1024): output.write(chunk)
    if not zipfile.is_zipfile(temporary):
        raise RuntimeError('Resposta não é um ZIP. Verifique acesso público ao Kaggle; nenhum CSV foi substituído.')
    temporary.replace(archive)
with zipfile.ZipFile(archive) as z:
    bad=z.testzip()
    if bad: raise RuntimeError(f'Arquivo corrompido: {bad}')
    for name in z.namelist():
        if name.endswith('.csv') and Path(name).name==name: z.extract(name,RAW)
manifest=RAW/'manifest.json'
if not manifest.exists():
    manifest.write_text(json.dumps({'source':URL,'downloaded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(RAW.iterdir()) if p.is_file() and p.name!='manifest.json'}},indent=2),encoding='utf-8')
else:
    for name, metadata in json.loads(manifest.read_text())['files'].items():
        if hashlib.sha256((RAW/name).read_bytes()).hexdigest()!=metadata['sha256']:
            raise RuntimeError(f'Hash divergente: {name}')
print('ZIP e hashes verificados; CSVs disponíveis em data/raw/.')
