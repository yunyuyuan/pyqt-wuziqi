import PyQt5.Qt as qt
from components import CommonHBox, CommonVBox, CommonBtn, CommonDialog
from frames import config, save_config

"""
    设置和关于
"""
class SetAndAbout(qt.QFrame):
    set_qss = qt.pyqtSignal()

    def __init__(self, parent, top):
        super().__init__(parent)
        self.top = top
        self.setProperty('class', 'set-about')
        self.set_dialog = SetDialog(self, top)
        self.about_dialog = AboutDialog(self, top)

        layer = CommonHBox()
        self.set_btn = CommonBtn(chr(0xe002), self)
        self.set_btn.clicked.connect(self.set_dialog.exec)
        self.about_btn = CommonBtn(chr(0xe003), self)
        self.about_btn.clicked.connect(self.about_dialog.exec)

        layer.addStretch(0)
        layer.addWidget(self.set_btn, alignment=qt.Qt.AlignRight)
        layer.addWidget(self.about_btn, alignment=qt.Qt.AlignRight)
        self.setLayout(layer)

        self.set_qss.connect(self.do_set_qss)
        self.set_qss.emit()

    def do_set_qss(self):
        with open(f'static/set-about-{config["color"]}.css', encoding='utf-8') as fp:
            self.setStyleSheet(fp.read())


class SetDialog(CommonDialog):
    def __init__(self, p, top):
        super().__init__(p)
        self.top = top
        self.choose_color = config['color']
        self.setProperty('class', 'set')
        layer = qt.QVBoxLayout()

        self.server_cfg = qt.QFrame(self)
        layer_1 = CommonHBox()
        layer_1.addWidget(qt.QLabel('服务器', self.server_cfg))
        self.server_input = qt.QLineEdit(config['server'], self.server_cfg)
        layer_1.addWidget(self.server_input)
        self.server_cfg.setLayout(layer_1)

        self.color_cfg = qt.QFrame(self)
        layer_2 = CommonHBox()
        layer_2.addWidget(qt.QLabel('主题', self.server_cfg))
        self.white = qt.QPushButton(self.color_cfg)
        self.white.clicked.connect(self.set_white)
        self.white.setProperty('class', 'white')
        self.dracula = qt.QPushButton(self.color_cfg)
        self.dracula.clicked.connect(self.set_dracula)
        self.dracula.setProperty('class', 'dracula')
        layer_2.addWidget(self.white)
        layer_2.addWidget(self.dracula)
        self.color_cfg.setLayout(layer_2)

        self.save_btn = CommonBtn('保存', self)
        self.save_btn.clicked.connect(self.save)
        layer.addWidget(self.server_cfg)
        layer.addWidget(self.color_cfg)
        layer.addWidget(self.save_btn)
        self.setLayout(layer)

    def set_white(self):
        self.white.setProperty('active', 't')
        self.dracula.setProperty('active', 'f')
        self.choose_color = 'white'
        self.parent().set_qss.emit()

    def set_dracula(self):
        self.white.setProperty('active', 'f')
        self.dracula.setProperty('active', 't')
        self.choose_color = 'dracula'
        self.parent().set_qss.emit()

    def save(self):
        config['color'] = self.choose_color
        config['server'] = self.server_input.text()
        save_config()
        self.parent().set_qss.emit()
        self.top.set_qss.emit()

class AboutDialog(CommonDialog):
    def __init__(self, p, top):
        super().__init__(p)
        self.top = top
        self.setProperty('class', 'about')
