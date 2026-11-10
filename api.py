"""Accès HTTP aux API publiques et extraction sécurisée des archives GPU.

Aucune dépendance Python externe : urllib, json et zipfile suffisent.
"""
import json
import os
import re
import shutil
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

GPU = 'https://www.geoportail-urbanisme.gouv.fr'
GEO = 'https://geo.api.gouv.fr'
CARTO = 'https://apicarto.ign.fr/api/gpu'
HEADERS = {'User-Agent': 'QGIS-GPU-PLU-Downloader/0.1', 'Accept': 'application/json'}


def get_json(url, params=None):
    """Effectue une requête JSON avec timeout et messages d'erreur exploitables."""
    if params:
        url += ('&' if '?' in url else '?') + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=35) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read(4000).decode('utf-8', errors='replace')
        raise ValueError('API HTTP {} : {}'.format(exc.code, detail)) from exc


def locate_places(term, mode):
    """Résout une commune via nom/code INSEE/code postal, ou un EPCI via SIREN.

    Les codes postaux ne sont pas des identifiants uniques de commune.
    """
    term = term.strip()
    if re.fullmatch(r'\d{5}', term):
        # Recherche d'abord par code INSEE, puis par code postal.
        try:
            one = get_json(GEO + '/communes/' + term, {'fields': 'nom,code,codesPostaux'})
            if isinstance(one, dict) and one.get('code'):
                return [{'nom': one['nom'], 'code': one['code'], 'kind': 'commune'}]
        except Exception:
            pass
        data = get_json(GEO + '/communes', {'codePostal': term, 'fields': 'nom,code,codesPostaux', 'limit': 100})
    else:
        data = get_json(GEO + '/communes', {'nom': term, 'fields': 'nom,code,codesPostaux', 'boost': 'population', 'limit': 30})
    return [{'nom': x['nom'], 'code': x['code'], 'kind': 'commune'} for x in data]


def _items(payload):
    """Tolère plusieurs enveloppes JSON possibles ; refuse les réponses inconnues."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ('results', 'documents', 'items', 'data'):
            if isinstance(payload.get(key), list):
                return payload[key]
        if isinstance(payload.get('features'), list):
            return [f.get('properties', f) for f in payload['features']]
    raise ValueError('Format de réponse API Document non reconnu ; vérifier la documentation actuelle.')


def find_documents(code, kind='commune'):
    """Recherche PLU/PLUi au centre communal via le module officiel API Carto.

    Version de test : un point central ne garantit pas toute la couverture d'une
    commune. Aucun repli silencieux n'est fait si le service géographique échoue.
    """
    commune = get_json(GEO + '/communes/' + urllib.parse.quote(code, safe=''),
                       {'fields': 'nom,code,centre'})
    centre = commune.get('centre')
    if not isinstance(centre, dict) or centre.get('type') != 'Point':
        raise ValueError('Centre géographique de la commune indisponible.')
    payload = get_json(CARTO + '/document', {'geom': json.dumps(centre)})
    result, seen = [], set()
    for row in _items(payload):
        if not isinstance(row, dict):
            continue
        if row.get('du_type') not in ('PLU', 'PLUi'):
            continue
        if row.get('gpu_status') != 'production':
            continue
        ident = row.get('gpu_doc_id') or row.get('id')
        if not ident or ident in seen:
            continue
        seen.add(ident)
        result.append({'id': ident, 'name': row.get('grid_title') or row.get('name'),
                       'documentType': row['du_type'], 'partition': row.get('partition'),
                       'publicationDate': row.get('gpu_timestamp', '')[:10]})
    return result


def document_details(doc):
    """Retourne la route officielle de téléchargement (redirection vers le ZIP)."""
    ident = doc.get('id') or doc.get('documentId')
    if not ident:
        raise ValueError('Identifiant du document absent de la réponse GPU.')
    return GPU + '/api/document/' + urllib.parse.quote(str(ident), safe='') + '/download'


def download_extract(url, target, progress=None):
    """Télécharge puis extrait un ZIP en empêchant la traversée de répertoires.

    Refuse les liens symboliques et limite la taille décompressée à 4 Gio.
    Ne supprime pas les archives ni les dossiers existants de l'utilisateur.
    """
    target = Path(target).resolve()
    if not target.is_dir():
        raise ValueError('Le dossier de destination doit déjà exister.')
    if any(target.iterdir()):
        raise ValueError('Choisissez un dossier vide dédié à ce téléchargement.')
    fd, tmp = tempfile.mkstemp(prefix='gpu_', suffix='.zip', dir=str(target))
    os.close(fd)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': HEADERS['User-Agent']})
        with urllib.request.urlopen(req, timeout=90) as resp, open(tmp, 'wb') as out:
            total = int(resp.headers.get('Content-Length', 0))
            done = 0
            while True:
                block = resp.read(1024 * 1024)
                if not block:
                    break
                out.write(block)
                done += len(block)
                if progress and total:
                    progress(min(90, int(done * 90 / total)))
        with zipfile.ZipFile(tmp) as z:
            infos = z.infolist()
            if sum(i.file_size for i in infos) > 4 * 1024**3:
                raise ValueError('Archive décompressée supérieure à 4 Gio.')
            for info in infos:
                name = info.filename.replace('\\', '/')
                p = Path(name)
                if p.is_absolute() or '..' in p.parts or re.match(r'^[A-Za-z]:', name):
                    raise ValueError('Chemin dangereux dans le ZIP : ' + name)
                if (info.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError('Lien symbolique refusé dans le ZIP.')
                dest = (target / p).resolve()
                if not dest.is_relative_to(target):
                    raise ValueError('Extraction hors destination refusée.')
                if dest.exists() and not info.is_dir():
                    raise ValueError('Un fichier existe déjà : ' + str(dest))
            z.extractall(target)
        if progress:
            progress(100)
        return target
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def shapefiles(folder):
    """Recherche récursivement les SHP sous Donnees_geographiques seulement."""
    roots = [p for p in Path(folder).rglob('*') if p.is_dir() and p.name.lower() == 'donnees_geographiques']
    return sorted({str(shp) for root in roots for shp in root.rglob('*') if shp.is_file() and shp.suffix.lower() == '.shp'})
