"""Opérations réseau exécutées hors du thread graphique."""
from qgis.PyQt.QtCore import QObject, pyqtSignal
from . import api


class Worker(QObject):
    """Exécute les appels réseau hors du thread graphique QGIS."""
    finished = pyqtSignal(object)
    failed = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, job, *args):
        super().__init__()
        self.job, self.args = job, args

    def run(self):
        try:
            if self.job == 'places':
                result = api.locate_places(*self.args)
            elif self.job == 'documents':
                result = api.find_documents(*self.args)
            elif self.job == 'download':
                doc, folder = self.args
                url = api.document_details(doc)
                result = api.download_extract(url, folder, self.progress.emit)
            else:
                raise ValueError('Opération inconnue')
            self.finished.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))


