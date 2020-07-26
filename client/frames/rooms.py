from re import match
from math import ceil

import PyQt5.Qt as qt

from components import CommonGrid, CommonHBox, CommonVBox, CommonBtn
from components.pop_dialog import PopDialog
from components.ico_button import IcoButton
from frames import AsyncRequest

Item_Num_One_Page = 15


class Rooms(qt.QFrame):
    def __init__(self, top):
        super().__init__(parent=top)
        self.top = top
        self.setObjectName('rooms')
        layer = CommonVBox()

        self.head = Head(self, self.top)
        self.body = Body(self, self.top)
        self.turn_page = TurnPage(self, self.top)

        layer.addWidget(self.head, 0)
        layer.addWidget(self.body, 1)
        layer.addWidget(self.turn_page, 0)
        self.setLayout(layer)

    def refresh(self):
        self.head.refresh()


'''
    顶部信息
'''
class Head(qt.QFrame):
    def __init__(self, parent, top):
        super().__init__(parent=parent)
        self.top = top
        self.setFixedHeight(46)
        self.setProperty('class', 'head')

        self.back_btn = IcoButton(top, self, ico=0xe011)
        self.back_btn.setProperty('what', 'back')
        self.back_btn.clicked.connect(self.back_home)
        self.refresh_btn = IcoButton(top, self, text='刷新', ico=0xe012)
        self.refresh_btn.setProperty('what', 'refresh')
        self.refresh_btn.clicked.connect(self.refresh)

        layer = CommonHBox()
        layer.addWidget(self.back_btn)
        layer.addStretch(2)
        layer.addWidget(self.refresh_btn)
        self.setLayout(layer)

    def back_home(self):
        self.top.toggle_frm(self.top.home_frm)

    def refresh(self):
        self.parent().turn_page.turn_page(1, True)


'''
    房间列表
'''


class Body(qt.QFrame):
    def __init__(self, parent, top):
        super().__init__(parent=parent)
        self.top = top
        self.setProperty('class', 'body')
        self.room_list = []

        self.layer = CommonGrid()
        self.setLayout(self.layer)

    # 刷新房间列表
    def refresh(self, lis):
        while self.layer.count():
            self.layer.itemAt(0).widget().setParent(None)
        for i in range(len(lis) - 1, -1, -1):
            item = lis[i]
            self.layer.addWidget(TheRoom(self, self.top, item['game_id'], item['cover'], item['nick']), i // 5, i % 5)


class TheRoom(qt.QFrame):
    def __init__(self, parent, top, g_id, cover, nick):
        super().__init__(parent)
        self.top = top
        self.setProperty('class', 'the-room')
        self.setFixedSize(140, 150)
        self.g_id = g_id

        layer = CommonVBox()
        h_layer = CommonHBox()

        id_label = qt.QLabel(str(g_id), self)
        id_label.setAlignment(qt.Qt.AlignCenter)
        id_label.setProperty('class', 'id')
        cover_img = qt.QLabel(self)
        cover_img.setProperty('class', 'cover')
        cover_img.setFixedSize(66, 60)
        cover_img.setScaledContents(True)
        cover_img.setPixmap(qt.QPixmap(f'./static/avatar/{cover}.png'))
        join_btn = CommonBtn('加入', self)
        join_btn.clicked.connect(self.join_room)

        h_layer.addWidget(cover_img)
        nick_ = qt.QLabel(nick, self)
        nick_.setProperty('class', 'nick')
        nick_.setWordWrap(True)
        h_layer.addWidget(nick_)

        layer.addWidget(id_label, 0)
        layer.addLayout(h_layer, 2)
        layer.addWidget(join_btn, 0)
        self.setLayout(layer)

    def join_room(self):
        self.top.toggle_frm(self.top.game_frm)
        self.top.game_frm.run_game(self.g_id)


class TurnPage(qt.QFrame):
    list_signal = qt.pyqtSignal(dict, int)
    dialog_signal = qt.pyqtSignal(str)

    def __init__(self, parent, top):
        super().__init__(parent)
        self.top = top
        self.setFixedHeight(50)
        self.setProperty('class', 'turn-page')

        self.dialog = None
        self.is_req = False
        self.init_page_ = False
        self.btn_lis = []

        self.layer = CommonHBox()
        self.setLayout(self.layer)

        self.dialog_signal.connect(self.dialog_click)
        self.list_signal.connect(self.list_result)

    # 重置页码信息
    def init_page(self, page_count):
        while self.layer.count():
            self.layer.itemAt(0).widget().setParent(None)
        self.btn_lis.clear()
        for i in range(1, page_count + 1):
            btn = CommonBtn(str(i), self)
            btn.setFixedSize(46, 36)
            btn.clicked.connect(self.click_page_btn)
            if i == 1:
                btn.setProperty('class', 'active')
            self.btn_lis.append(btn)
            self.layer.addWidget(btn)
        self.top.set_qss.emit()

    # 点击翻页按钮
    def click_page_btn(self):
        self.turn_page(int(self.sender().text()))

    # 翻页操作
    def turn_page(self, p, init_page=False):
        self.init_page_ = init_page
        self.dialog = PopDialog(self.top, self.dialog_signal, captain='查询中', text='正在请求服务器', btn_list=['取消'])
        thread = AsyncRequest(self.top, url='/room_list', data={'page': p - 1, 'count': Item_Num_One_Page},
                              signal=self.list_signal, req_id=p)
        thread.start()
        self.is_req = True
        self.dialog.exec()

    def list_result(self, dic, req_id):
        if self.is_req:
            if dic['state'] == 'suc':
                info = dic['data']
                count = info['count']
                page_num = ceil(count / Item_Num_One_Page)
                # 修改btn样式
                for i in self.btn_lis:
                    if i.text() == str(req_id):
                        i.setProperty('class', 'active')
                    else:
                        i.setProperty('class', '')
                self.top.set_qss.emit()
                # 修改info_label和列表
                self.parent().body.refresh(info['lis'])
                if self.init_page_:
                    self.init_page(page_num)
                self.dialog.close()
            else:
                self.dialog.set_text('错误:' + dic['data'])
                self.dialog.set_btn('取消', '关闭')

    def dialog_click(self, s):
        self.is_req = False
        self.dialog.close()
