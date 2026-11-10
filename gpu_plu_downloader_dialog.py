"""Boîte de dialogue de recherche et téléchargement GPU."""
from qgis.PyQt.QtCore import QThread
from qgis.PyQt.QtWidgets import (QComboBox, QDialog, QFileDialog, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QProgressBar, QVBoxLayout, QWidget)
from qgis.core import QgsProject, QgsVectorLayer
from . import api
from .worker import Worker


class DownloadDialog(QDialog):
    """Recherche en deux étapes pour désambiguïser commune et document."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Télécharger un PLU / PLUi depuis le GPU')
        self.resize(620, 430)
        self.thread = None
        self.worker = None
        self.places = []
        self.docs = []

        # Étape 1 : saisir un territoire, puis lancer immédiatement sa recherche.
        # Chaque action est placée immédiatement après les champs concernés.
        self.mode = QComboBox()
        self.mode.addItems(['Commune'])
        self.query = QLineEdit()
        self.place = QComboBox()
        self.doc = QComboBox()
        self.folder = QLineEdit()
        self.folder.setReadOnly(True)

        browse = QPushButton('Parcourir…')
        browse.clicked.connect(self.browse)
        folder_row = QWidget()
        row = QHBoxLayout(folder_row)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.folder)
        row.addWidget(browse)

        self.search_label = QLabel('Nom de commune, code INSEE ou code postal')
        self.search_btn = QPushButton('1. Rechercher la commune')
        self.docs_btn = QPushButton('2. Rechercher les documents GPU')
        self.load_btn = QPushButton('3. Télécharger et charger les SHP')
        self.search_btn.clicked.connect(self.search_places)
        self.docs_btn.clicked.connect(self.search_docs)
        self.load_btn.clicked.connect(self.download)
        self.progress = QProgressBar()
        self.status = QLabel('Saisissez un territoire pour commencer.')

        layout = QVBoxLayout(self)
        layout.addWidget(self.search_label)
        layout.addWidget(self.query)
        layout.addWidget(self.search_btn)
        layout.addWidget(QLabel('Territoire correspondant'))
        layout.addWidget(self.place)
        layout.addWidget(self.docs_btn)
        layout.addWidget(QLabel('Documents publiés'))
        layout.addWidget(self.doc)
        layout.addWidget(QLabel('Dossier de destination existant et vide'))
        layout.addWidget(folder_row)
        layout.addWidget(self.load_btn)
        layout.addWidget(self.progress)
        layout.addWidget(self.status)

        # Les étapes suivantes restent inaccessibles tant que leurs données manquent.
        self.mode.currentIndexChanged.connect(self.on_mode_changed)
        self.query.textChanged.connect(self.reset_results)
        self.place.currentIndexChanged.connect(self.reset_documents)
        self.doc.currentIndexChanged.connect(self.update_buttons)
        self.folder.textChanged.connect(self.update_buttons)
        self.on_mode_changed()

    def on_mode_changed(self, *_):
        """Adapte le libellé de recherche au territoire sélectionné."""
        self.search_label.setText('Nom de commune, code INSEE ou code postal')
        self.query.setPlaceholderText('Ex. : Châteauroux, 36044 ou 36000')
        self.search_btn.setText('1. Rechercher la commune')
        self.reset_results()

    def reset_results(self, *_):
        """Efface les résultats devenus obsolètes après une nouvelle saisie."""
        self.place.clear()
        self.places = []
        self.reset_documents()
        self.update_buttons()

    def reset_documents(self, *_):
        """Efface les documents si le territoire sélectionné change."""
        self.doc.clear()
        self.docs = []
        self.update_buttons()

    def update_buttons(self, *_):
        """Active les boutons selon l'avancement réel de la recherche."""
        busy = self.thread is not None
        self.search_btn.setEnabled(not busy and bool(self.query.text().strip()))
        self.docs_btn.setEnabled(not busy and 0 <= self.place.currentIndex() < len(self.places))
        self.load_btn.setEnabled(not busy and
                                 0 <= self.doc.currentIndex() < len(self.docs) and
                                 bool(self.folder.text()))

    def browse(self):
        path = QFileDialog.getExistingDirectory(self, 'Choisir un dossier déjà créé')
        if path:
            self.folder.setText(path)

    def busy(self, state):
        for widget in (self.query, self.place, self.doc):
            widget.setEnabled(not state)
        if state:
            for button in (self.search_btn, self.docs_btn, self.load_btn):
                button.setEnabled(False)
        else:
            self.update_buttons()

    def start(self, job, args, callback):
        """Garde les références QThread vivantes jusqu'à sa terminaison."""
        if self.thread is not None:
            return
        self.busy(True)
        self.thread = QThread(self)
        self.worker = Worker(job, *args)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished.connect(callback)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.error)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.done_thread)
        self.thread.start()

    def done_thread(self):
        self.thread = None
        self.worker = None
        self.busy(False)

    def reject(self):
        if self.thread is not None:
            self.status.setText('Veuillez attendre la fin de l’opération avant de fermer.')
            return
        super().reject()

    def closeEvent(self, event):
        if self.thread is not None:
            event.ignore()
            self.status.setText('Veuillez attendre la fin de l’opération avant de fermer.')
        else:
            super().closeEvent(event)

    def error(self, message):
        self.status.setText('Erreur : ' + message)
        QMessageBox.warning(self, 'GPU : erreur', message)

    def search_places(self):
        self.reset_results()
        term = self.query.text().strip()
        if not term:
            return self.error('Saisissez un nom, un code INSEE, un code postal.')
        self.status.setText('Recherche du territoire…')
        self.start('places', (term, 'commune'), self.got_places)

    def got_places(self, places):
        self.places = places
        for p in places:
            self.place.addItem('{} ({})'.format(p['nom'], p['code']))
        self.status.setText('{} territoire(s) trouvé(s).'.format(len(places)) if places else 'Aucun territoire trouvé.')
        self.update_buttons()

    def search_docs(self):
        i = self.place.currentIndex()
        if i < 0 or i >= len(self.places):
            return self.error('Choisissez une commune.')
        self.doc.clear()
        self.docs = []
        place = self.places[i]
        self.status.setText('Interrogation de l’API GPU…')
        self.start('documents', (place['code'], place['kind']), self.got_docs)

    def got_docs(self, docs):
        self.docs = docs
        for d in docs:
            label = str(d.get('documentType', '')) + ' - ' + str(d.get('name') or d.get('title') or d.get('documentType') or 'Document')
            date = str(d.get('publicationDate') or d.get('date') or '')
            self.doc.addItem('{} — {} — ID {}'.format(label, date, d.get('id', '?')))
        self.status.setText('{} document(s) publié(s). Vérifiez le type PLU/PLUi avant téléchargement.'.format(len(docs)) if docs else 'Aucun PLU/PLUi publié trouvé au centre de cette commune.')
        self.update_buttons()

    def download(self):
        i = self.doc.currentIndex()
        if i < 0 or i >= len(self.docs):
            return self.error('Sélectionnez un document publié.')
        if not self.folder.text():
            return self.error('Choisissez un dossier de destination existant.')
        self.progress.setValue(0)
        self.status.setText('Téléchargement puis extraction…')
        self.start('download', (self.docs[i], self.folder.text()), self.got_archive)

    def got_archive(self, path):
        files = api.shapefiles(path)
        if not files:
            return self.error('Archive extraite, mais aucun SHP dans Donnees_geographiques.')
        project = QgsProject.instance()
        group_name = 'GPU - ' + self.place.currentText()
        group = project.layerTreeRoot().addGroup(group_name)
        loaded = 0
        for shp in files:
            layer = QgsVectorLayer(shp, shp.rsplit('/', 1)[-1].rsplit('\\', 1)[-1][:-4], 'ogr')
            if layer.isValid():
                project.addMapLayer(layer, False)
                group.addLayer(layer)
                loaded += 1
        self.status.setText('{} couche(s) SHP chargée(s) sur {}.'.format(loaded, len(files)))
        QMessageBox.information(self, 'GPU : terminé', self.status.text())


