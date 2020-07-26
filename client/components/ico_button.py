import PyQt5.Qt as qt
from . import CommonHBox, CommonBtn


class IcoButton(CommonBtn):
    def __init__(self, top, parent=None, text=None, ico=None):
        super().__init__(parent=parent)
        self.setProperty("class", "icon-btn")
        self.setCursor(qt.Qt.PointingHandCursor)
        main_layer = CommonHBox()

        contain = qt.QFrame(self)
        layer = CommonHBox()
        if ico:
            icon = qt.QLabel(chr(ico), self)
            icon.setProperty('class', 'icon')
            icon.setAlignment(qt.Qt.AlignCenter)
            layer.addWidget(icon, qt.Qt.AlignCenter)
        if text:
            self.text_ = qt.QLabel(text, self)
            self.text_.setProperty('class', 'text')
            if not ico:
                self.text_.setAlignment(qt.Qt.AlignCenter)
            layer.addWidget(self.text_, qt.Qt.AlignCenter)
        contain.setLayout(layer)
        main_layer.addWidget(contain, qt.Qt.AlignCenter)
        self.setLayout(main_layer)
        self.setFixedSize(contain.size())
        self.setMaximumSize(*top.desktop_size)

    def text(self):
        return self.text_.text()

    def setText(self, text):
        self.text_.setText(text)
