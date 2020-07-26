import PyQt5.Qt as qt
from . import CommonHBox

__all__ = ['SuperInput']

# 好看的LineEdit
class SuperInput(qt.QFrame):
    def __init__(self, parent, placeholder=None, ico=None):
        super().__init__(parent=parent)
        self.setProperty("class", "super-input")

        layer = CommonHBox()
        self.ico = qt.QLabel(chr(ico), self)
        self.input = Input(self, placeholder)

        layer.addWidget(self.ico)
        layer.addWidget(self.input, 1)
        self.setLayout(layer)

    def text(self):
        return self.input.text()

    def setText(self, s):
        self.input.setText(s)


class Input(qt.QLineEdit):
    def __init__(self, parent, placeholder=None):
        super().__init__(parent=parent)
        self.setPlaceholderText(placeholder)
        self.bl = BottomLine(self)

    def focusInEvent(self, e):
        self.bl.spread()
        super().focusInEvent(e)

    def focusOutEvent(self, e):
        self.bl.contract()
        super().focusOutEvent(e)


class BottomLine(qt.QLabel):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.animate = qt.QPropertyAnimation(self, b"geometry")
        self.animate.setDuration(100)
        self.setGeometry(0, self.parent().height()-2, 0, 4)

    def spread(self):
        self.animate.setKeyValueAt(0, qt.QRect(self.parent().width()//2, self.parent().height()-2, 0, 2))
        self.animate.setKeyValueAt(1, qt.QRect(0, self.parent().height()-2, self.parent().width(), 2))
        self.animate.start()

    def contract(self):
        self.animate.setKeyValueAt(0, qt.QRect(0, self.parent().height()-2, self.parent().width(), 2))
        self.animate.setKeyValueAt(1, qt.QRect(self.parent().width()//2, self.parent().height()-2, 0, 2))
        self.animate.start()
