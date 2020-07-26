import PyQt5.Qt as qt
from sys import argv, exit

from frames.home import Home
from frames.rooms import Rooms
from frames.game import Game
from frames import config

class Main(qt.QWidget):
    set_qss = qt.pyqtSignal()

    def __init__(self):
        super().__init__(None)
        self.setObjectName("main")
        # 大小为屏幕一半
        desktop = qt.QApplication.desktop().screen()
        self.desktop_size = (desktop.width(), desktop.height())
        width, height = self.desktop_size
        self.setGeometry(width//4, height//4, width//2, height//2)

        self.login = False
        self.set_qss.connect(self.do_set_qss)

        self.home_frm = Home(self)
        self.rooms_frm = Rooms(self)
        self.game_frm = Game(self)
        self.frm_list = [self.home_frm, self.rooms_frm, self.game_frm]
        # 设置minSize
        for i in self.frm_list:
            size = config['minSize'][i.objectName()]
            i.setMinimumSize(size[0], size[1])

        self.now_frm = self.home_frm
        self.toggle_frm(self.home_frm)

        # iconfont
        self.iconfont = qt.QFont(qt.QFontDatabase.applicationFontFamilies(qt.QFontDatabase.addApplicationFont("static/iconfont.ttf"))[0])

        self.set_ui()
        self.show()

    def set_ui(self):
        self.set_qss.emit()

    # 切换窗口
    def toggle_frm(self, what):
        for i in self.frm_list:
            if i == what:
                i.show()
                i.refresh()
                self.now_frm = i
            else:
                i.hide()
        size = what.minimumSize()
        self.setMinimumSize(size)
        self.resize(size)

    def resizeEvent(self, e):
        self.now_frm.setGeometry(0, 0, self.width(), self.height())

    def do_set_qss(self):
        with open(f'static/style-{config["color"]}.css', encoding='utf-8') as fp:
            self.setStyleSheet(fp.read())

    def close(self):
        from frames import session
        session.close()
        self.game_frm.head_frm.exit_()
        super().close()

app = qt.QApplication(argv)
obj = Main()
exit(app.exec())
