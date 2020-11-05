from sys import argv, exit

from PyQt5.QtCore import Qt, QSettings, QByteArray
from PyQt5.QtGui import QFont, QCloseEvent
from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, \
    QSpacerItem, QSpinBox, QSlider, QLabel, QLineEdit, QPushButton, QShortcut, QCheckBox, QDialog, \
    QMessageBox, QApplication

from config import get_config
from core import convert

config = get_config()


class _MainWindowContent(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        font_small = QFont()
        font_small.setPointSize(8)
        font_large = QFont()
        font_large.setPointSize(36)

        self.number = QLineEdit(self)
        self.number.setToolTip('Исходное число')
        self.number.setPlaceholderText('Исходное число')
        self.number.textEdited.connect(self.number_edited)
        self.number.returnPressed.connect(self.worker)
        self.base = QSpinBox(self)
        self.base.setFont(font_small)
        self.base.setToolTip('Исходная система счисления')
        self.base.setRange(2, 36)
        self.base.setValue(10)
        self.base.valueChanged.connect(self.number_edited)
        self.swap = QPushButton('⬌', self)
        self.swap.setFont(font_large)
        self.swap.setMaximumSize(60, 60)
        self.swap.setToolTip('Поменять направление перевода')
        self.swap.setEnabled(False)
        self.swap.clicked.connect(self.swap_clicked)
        self.result = QLineEdit(self)
        self.result.setToolTip('Переведённое число')
        self.result.setPlaceholderText('Переведённое число')
        self.result.setReadOnly(True)
        self.result.textChanged.connect(self.result_changed)
        self.result_base = QSpinBox(self)
        self.result_base.setFont(font_small)
        self.result_base.setToolTip('Конечная система счисления')
        self.result_base.setRange(2, 36)
        self.result_base.setValue(10)
        self.result_base.valueChanged.connect(self.number_edited)
        self.precision = QSlider(Qt.Horizontal, self)
        self.precision.setMaximum(15)
        self.precision.setPageStep(2)
        self.precision.setValue(2)
        self.precision.setToolTip('Максимальное количество знаков после запятой')
        self.precision.valueChanged.connect(self._slider_warning)
        self.precision.valueChanged.connect(self.slider_move)
        self.precision_label = QLabel(f'Точность: {self.precision.value()}', self)
        self.precision_label.setAlignment(Qt.AlignCenter)
        self.precision_label.setToolTip('Максимальное количество знаков после запятой')
        self.debug = DebugMenu(*args, **kwargs)
        self.debug_shortcut = QShortcut(Qt.CTRL + Qt.Key_D, self)
        self.debug_shortcut.activated.connect(self._toggle_debug)

        spacer1 = QSpacerItem(0, 20)
        spacer2 = QSpacerItem(0, 20)

        base_layout = QVBoxLayout()
        base_layout.addItem(spacer1)
        base_layout.addWidget(self.base)

        number_layout = QHBoxLayout()
        number_layout.addWidget(self.number)
        number_layout.addLayout(base_layout)

        result_base_layout = QVBoxLayout()
        result_base_layout.addItem(spacer2)
        result_base_layout.addWidget(self.result_base)

        result_layout = QHBoxLayout()
        result_layout.addWidget(self.result)
        result_layout.addLayout(result_base_layout)

        precision_layout = QVBoxLayout()
        precision_layout.addWidget(self.precision_label)
        precision_layout.addWidget(self.precision)

        grid = QGridLayout()
        grid.addLayout(number_layout, 0, 0)
        grid.addWidget(self.swap, 0, 1)
        grid.addLayout(result_layout, 0, 2)
        grid.addLayout(precision_layout, 1, 2)

        layout = QVBoxLayout(self)
        layout.addLayout(grid)

    def _slider_warning(self, value: int):
        if value > 10:
            self.precision_label.setStyleSheet('QLabel { color: #B6B600; }')
            self.precision_label.setToolTip('Максимальное количество знаков после запятой\n'
                                            'ВНИМАНИЕ: При большом количестве знаков после запятой'
                                            ' могут наблюдаться неточности при переводе')
        else:
            self.precision_label.setStyleSheet('QLabel {}')
            self.precision_label.setToolTip('Максимальное количество знаков после запятой')

    def _toggle_debug(self):
        self.debug.show()

    def worker(self, *, ignore_exc: bool = False):
        from_base = self.base.value()
        to_base = self.result_base.value()
        n = self.number.text()
        accuracy = self.precision.value()
        try:
            result = convert(from_base, to_base, n, accuracy)
        except Exception as e:
            if not ignore_exc:
                QMessageBox.critical(self.parent(), 'Произошла ошибка',
                                     f'{e.__class__.__name__}: {e}')
            result = ''
        self.result.setText(str(result))

    def slider_move(self, value: int):
        self.precision_label.setText(f'Точность: {value}')
        if config['ui'].getboolean('auto_convert'):
            self.worker(ignore_exc=True)

    def swap_clicked(self):
        from_base = self.base.value()
        to_base = self.result_base.value()
        number = self.number.text()
        result = self.result.text()
        self.base.setValue(to_base)
        self.result_base.setValue(from_base)
        self.number.setText(result)
        self.result.setText(number)
        self.worker(ignore_exc=True)

    def number_edited(self, number: str):
        if not config['ui'].getboolean('auto_convert'):
            return
        if number == '':
            self.result.setText('')
        else:
            self.worker(ignore_exc=True)

    def result_changed(self, result: str):
        self.swap.setEnabled(result != '')


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimumSize(600, 125)
        self.setMaximumSize(600, 125)
        self.setWindowTitle('BaseConverter')
        self._settings = QSettings('evgfilim1', 'BaseConverter', self)
        self.restoreGeometry(self._settings.value('geometry', type=QByteArray))
        self.restoreState(self._settings.value('winstate', type=QByteArray))
        self.setCentralWidget(_MainWindowContent(self))

    def closeEvent(self, ev: QCloseEvent):
        self._settings.setValue('geometry', self.saveGeometry())
        self._settings.setValue('winstate', self.saveState())
        ev.accept()


class DebugMenu(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.globals = None
        self.setMinimumSize(300, 75)
        self.setWindowTitle('debug')

        self.strip_zeros = QCheckBox('config.strip_zeros', self)
        self.strip_zeros.setToolTip('config.strip_zeros')
        self.strip_zeros.setChecked(config['core'].getboolean('strip_zeros'))
        self.auto_convert = QCheckBox('config.auto_convert', self)
        self.auto_convert.setToolTip('config.auto_convert')
        self.auto_convert.setChecked(config['ui'].getboolean('auto_convert'))
        self.code = QLineEdit(self)
        self.code.setPlaceholderText('eval()')
        self.code.setToolTip('eval()')

        self.strip_zeros.stateChanged.connect(self._strip_zeros)
        self.auto_convert.stateChanged.connect(self._auto_convert)
        self.code.returnPressed.connect(self.eval)

        layout = QVBoxLayout(self)
        layout.addWidget(self.strip_zeros)
        layout.addWidget(self.auto_convert)
        layout.addWidget(self.code)

    @staticmethod
    def _strip_zeros(state: int):
        config['core']['strip_zeros'] = str(bool(state)).lower()

    @staticmethod
    def _auto_convert(state: int):
        config['ui']['auto_convert'] = str(bool(state)).lower()

    def eval(self):
        try:
            result = eval(self.code.text(), self.globals)
            QMessageBox.information(self, 'eval', str(result))
        except Exception as e:
            QMessageBox.critical(self, 'eval', f'{e.__class__.__name__}: {e}')


if __name__ == '__main__':
    app = QApplication(argv)
    window = MainWindow()
    contents = window.centralWidget()
    contents.debug.globals = globals()
    window.show()
    exit(app.exec())
