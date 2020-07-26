import PyQt5.Qt as qt


class CommonDialog(qt.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, flags=qt.Qt.WindowCloseButtonHint, **kwargs)


class CommonVBox(qt.QVBoxLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(0)


class CommonHBox(qt.QHBoxLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(0)


class CommonGrid(qt.QGridLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(0)

class CommonBtn(qt.QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setProperty('common-btn', 't')
        self.setCursor(qt.Qt.PointingHandCursor)
