"""Point d'entrée du plugin QGIS."""


def classFactory(iface):
    from .gpu_plu_downloader import GPUPlugin
    return GPUPlugin(iface)
