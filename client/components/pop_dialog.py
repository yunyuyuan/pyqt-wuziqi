import PyQt5.Qt as qt
from . import CommonDialog, CommonHBox, CommonVBox, CommonBtn
from frames import config


class PopDialog(CommonDialog):
    def __init__(self, top, click_signal=None, size=(180, 120), text='哈哈呵呵', btn_list=('确定',), captain='一个不知名的弹窗'):
        super().__init__()
        self.setWindowTitle(captain)
        self.top = top
        self.setProperty('class', 'pop-dialog')
        self.click_signal = click_signal

        layer = CommonVBox()
        self.text_label = qt.QLabel(text, self)
        self.text_label.setAlignment(qt.Qt.AlignCenter)
        self.text_label.setWordWrap(True)
        layer.addWidget(self.text_label)

        btn_layer = CommonHBox()
        btn_layer.addStretch(0)
        self.btn_list = []
        for i in btn_list:
            btn = CommonBtn(i, self)
            btn.clicked.connect(self.btn_click)
            self.btn_list.append(btn)
            btn_layer.addWidget(btn)
            btn_layer.addStretch(0)
        layer.addLayout(btn_layer)
        self.setLayout(layer)

        p_size = (self.top.x()+self.top.width()//2, self.top.y()+self.top.height()//2)
        self.setGeometry(p_size[0]-size[0]//2, p_size[1]-size[1]//2, size[0], size[1])
        with open(f'static/dialog-{config["color"]}.css', encoding='utf-8') as fp:
            self.setStyleSheet(fp.read())

    def set_text(self, s):
        self.text_label.setText(s)

    def set_btn(self, s, new_s):
        for i in self.btn_list:
            if s == i.text():
                i.setText(new_s)
                break

    def closeEvent(self, e):
        if self.click_signal:
            self.click_signal.emit('closeEvent')

    def btn_click(self):
        if self.click_signal:
            self.click_signal.emit(self.sender().text())
        else:
            self.close()
