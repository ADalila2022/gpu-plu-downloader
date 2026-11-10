"""Intégration du plugin dans QGIS : menu, action et dialogue."""
from qgis.PyQt.QtWidgets import QAction
from .gpu_plu_downloader_dialog import DownloadDialog


class GPUPlugin:
    """Intègre l'outil dans le menu Extensions et la barre d'outils QGIS."""
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dialog = None

    def initGui(self):
        self.action = QAction('Télécharger PLU / PLUi (GPU)', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu('GPU PLU Downloader', self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removePluginMenu('GPU PLU Downloader', self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        if self.dialog is not None and self.dialog.isVisible():
            self.dialog.raise_()
            self.dialog.activateWindow()
            return
        self.dialog = DownloadDialog(self.iface.mainWindow())
        self.dialog.show()
