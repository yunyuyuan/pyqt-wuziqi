import PyQt5.Qt as qt


class AvatarLabel(qt.QLabel):
    def __init__(self, parent, size, round_=5, cover=0):
        super().__init__(parent=parent)
        self.setScaledContents(True)
        self.setFixedSize(*size)
        self.size = size
        self.round = round_
        self.cover = cover
        self.setProperty("class", "avatar-label")

    def set_cover(self, c):
        self.cover = c
        self.update()

    def paintEvent(self, e):
        pix = qt.QPixmap(f'./static/avatar/{self.cover}.png')
        pix = pix.scaled(*self.size)
        painter = qt.QPainter(self)
        painter.setRenderHint(qt.QPainter.Antialiasing)
        painter.setBrush(qt.QBrush(pix))
        painter.drawRoundedRect(0, 0, *self.size, self.round, self.round)
