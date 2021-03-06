from pathlib import Path
import os, sys
import click
from qtpy.QtCore import QUrl
from qtpy.QtGui import QGuiApplication, QIcon
from qtpy.QtQml import QQmlApplicationEngine
from .label_backend import LabelBackend, QtUtils
import logging
log = logging.getLogger(__name__)

DIR_SOURCE =  Path(__file__).parent
DIR_RESOURCES = DIR_SOURCE / 'resources'
CONFIG_DEFAULT = DIR_RESOURCES / 'config' / 'default_classes.json'

@click.command()
@click.option('--config', type=click.Path(exists=True, dir_okay=False, file_okay=True))
@click.option('--dir', type=click.Path(exists=True, dir_okay=True, file_okay=False), help='Start in this directory')
# @click.option('--dir_in', type=click.Path(exists=True, dir_okay=False, path_type=Path), default=None)
# @click.option('--dir_out', type=click.Path(file_okay=False, dir_okay=True, path_type=Path), default=None)
def run(config=None, dir=None):


	try:
		config, start_dir = get_config_and_start_dir(config=config, dir=dir)
		config = config or CONFIG_DEFAULT

		# Set default style to "fusion"
		# https://doc.qt.io/qt-5/qtquickcontrols2-styles.html#using-styles-in-qt-quick-controls-2
		os.environ.setdefault('QT_QUICK_CONTROLS_STYLE', 'Fusion')

		qt_app = QGuiApplication(sys.argv)
		qt_app.setOrganizationName("EPFL")
		qt_app.setOrganizationDomain("ch")

		qt_app.setWindowIcon(QIcon(str(DIR_RESOURCES / 'label-grab-icon.svg')))

		# Init QML
		qml_engine = QQmlApplicationEngine()

		# tell it the location of qml files
		qml_engine.addImportPath(str(DIR_RESOURCES))

		# Register backend classes
		backend = LabelBackend()
		backend.load_config(Path(config))
		backend.set_starting_directory(start_dir)
		backend.set_image_path(DIR_RESOURCES / 'images' / 'test.jpg')
		qml_engine.rootContext().setContextProperty('backend', backend)

		qtutils = QtUtils()
		qml_engine.rootContext().setContextProperty('utils', qtutils)

		# QML loads image from the backend using an image provider
		qml_engine.addImageProvider('backend', backend.image_provider)

		# Load main window
		qml_engine.load(QUrl.fromLocalFile(str(DIR_RESOURCES / 'qml' / 'main.qml')))
		#qml_engine.load('qml/main.qml')

		if qml_engine.rootObjects():
			exit_code = qt_app.exec_()
			del qml_engine
			sys.exit(exit_code)
		else:
			log.error('QML failed to load')
			sys.exit(1)
	except Exception as e:
		log.exception('Exception in main application')
		sys.exit(1)


def get_config_and_start_dir(config=None, dir=None):
	if dir is not None:
		dir = Path(dir)

		if dir.is_dir():
			# try to find config automatically
			if config is None:
				for file_in_dir in dir.iterdir():
					if file_in_dir.is_file() and file_in_dir.suffix == '.json':
						config = file_in_dir

		else:
			dir = ''
	else:
		dir = ''

	return (config, dir)

