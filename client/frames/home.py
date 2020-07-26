from re import sub, match
from os import listdir

import PyQt5.Qt as qt

from components.ico_button import IcoButton
from components.pop_dialog import PopDialog
from components.super_input import SuperInput
from frames import AsyncRequest, check_legal
from frames.set_about import SetAndAbout
from components import CommonDialog, CommonGrid, CommonHBox, CommonVBox, CommonBtn


class Home(qt.QFrame):
    def __init__(self, top):
        super().__init__(parent=top)
        self.setObjectName("home")
        layer = CommonHBox()

        self.player_frm = Player(top, self)
        self.room_frm = RoomFrame(top, self)

        layer.addWidget(self.player_frm)
        layer.addWidget(self.room_frm)
        self.setLayout(layer)

    def refresh(self):
        pass


'''
    左边账号选项
'''
class Player(qt.QFrame):
    def __init__(self, top, home):
        super().__init__(parent=home)
        self.setProperty("class", "player")
        self.setFixedSize(350, 400)
        layer = CommonVBox()

        self.login_frm = Login(self, top)
        self.info_frm = ActInfo(self, top)
        self.info_frm.hide()
        layer.addWidget(self.login_frm)
        layer.addWidget(self.info_frm)
        self.setLayout(layer)


#  登录
class Login(qt.QFrame):
    submit_signal = qt.pyqtSignal(dict, int)
    dialog_click = qt.pyqtSignal(str)

    def __init__(self, player, top):
        super().__init__(parent=player)
        self.setProperty("class", "login")
        self.top = top
        self.dialog = None
        self.req_id = 0

        layer = CommonVBox()

        toggle_layer = CommonHBox()
        self.toggle_frm = ToggleLogin(self, top)
        toggle_layer.addWidget(self.toggle_frm)
        layer.addLayout(toggle_layer)

        mid_frame = qt.QFrame(self)
        input_layer = qt.QVBoxLayout()
        self.nick_ipt = SuperInput(self, placeholder="昵称", ico=0xe007)
        self.nick_ipt.hide()
        self.act_ipt = SuperInput(self, placeholder="账号", ico=0xe006)
        self.pwd_ipt = SuperInput(self, placeholder="密码", ico=0xe008)
        input_layer.addWidget(self.nick_ipt)
        input_layer.addWidget(self.act_ipt)
        input_layer.addWidget(self.pwd_ipt)
        mid_frame.setLayout(input_layer)
        layer.addWidget(mid_frame, 1)

        self.submit = IcoButton(self.top, parent=self, text="登录", ico=0xe001)
        self.submit.clicked.connect(self.click_submit)
        layer.addWidget(self.submit, alignment=qt.Qt.AlignHCenter)

        self.setLayout(layer)

        self.submit_signal.connect(self.result)
        self.dialog_click.connect(self.dialog_btn_click)

    def toggle(self, is_login):
        if is_login:
            self.nick_ipt.hide()
            self.submit.setText('登录')
        else:
            self.nick_ipt.show()
            self.submit.setText('注册')

    def click_submit(self):
        nick, act, pwd = self.nick_ipt.text(), self.act_ipt.text(), self.pwd_ipt.text()
        if check_legal(act) and check_legal(pwd) and (
                # 登录
                (self.is_login() and (not nick or check_legal(nick))) or
                # 注册
                (not self.is_login() and check_legal(nick))):
            self.dialog = PopDialog(self.top, text='正在请求服务器', btn_list=['取消'], click_signal=self.dialog_click, captain='登录中')
            self.dialog.finished.connect(self.cancel_req)
            self.req_id += 1
            AsyncRequest(self.top, url='/login', data={'type': ('login' if self.is_login() else 'register'), 'nick': nick, 'act': act, 'pwd': pwd},
                         signal=self.submit_signal, req_id=self.req_id).start()
            self.dialog.exec()
        else:
            self.dialog = PopDialog(self.top, text='昵称,账号和密码必须是1-16位汉字,字母,数字或下划线', btn_list=['确认'], click_signal=self.dialog_click, captain='错误')
            self.dialog.exec()

    # dialog点击
    def dialog_btn_click(self, text):
        if text == '取消' or text == '收到' or text == 'closeEvent':
            self.cancel_req()
        else:
            self.dialog.close()

    # 终止请求
    def cancel_req(self):
        self.req_id += 1
        if not self.dialog.isHidden():
            self.dialog.close()

    # 请求结果
    def result(self, dic, req_id):
        if req_id == self.req_id:
            # 登录
            if self.is_login():
                if dic['state'] == 'suc':
                    self.dialog.close()
                    self.top.login = dic['data']['id']
                    self.parent().info_frm.show()
                    # 传递个人信息
                    self.parent().info_frm.set_info(dic['data'])
                    self.top.game_frm.footer_frm.p1.update_info(dic['data'])
                    self.hide()
                elif dic['state'] == 'warn':
                    self.dialog.set_text('账号不存在或密码错误')
                else:
                    self.dialog.set_text('错误:'+dic['data'])
            else:
                if dic['state'] == 'suc':
                    self.dialog.set_text('注册成功!')
                elif dic['state'] == 'warn':
                    self.dialog.set_text('账号已被注册!')
                else:
                    self.dialog.set_text('错误:'+dic['data'])
            self.dialog.set_btn('取消', '收到')

    def is_login(self):
        return self.submit.text() == '登录'

class ToggleLogin(qt.QFrame):
    def __init__(self, parent, top):
        super().__init__(parent=parent)
        self.top = top
        self.setProperty('class', 'toggle')
        layer = CommonHBox()

        self.login_btn = qt.QPushButton('登录', self)
        self.login_btn.clicked.connect(lambda: self.click(self.login_btn))
        self.login_btn.setProperty('class', 'active')
        self.register_btn = qt.QPushButton('注册', self)
        self.register_btn.setProperty('class', 'reg')
        self.register_btn.clicked.connect(lambda: self.click(self.register_btn))

        layer.addWidget(self.login_btn)
        layer.addWidget(self.register_btn)
        self.setLayout(layer)

    def click(self, what):
        what.setProperty('class', 'active')
        (self.register_btn if what == self.login_btn else self.login_btn).setProperty('class', '')
        self.top.set_qss.emit()
        self.parent().toggle(what.text() == '登录')

# 信息
class ActInfo(qt.QFrame):
    save_signal = qt.pyqtSignal(dict, int)

    def __init__(self, parent, top):
        super().__init__(parent)
        self.top = top
        self.setProperty("class", "act-info")
        layer = qt.QVBoxLayout()

        self.user_info = UserInfo(self, top)
        self.game_num = qt.QLabel(self)
        self.win_num = qt.QLabel(self)
        btn_frm = qt.QFrame(self)
        btn_layer = CommonHBox()
        self.save_btn = IcoButton(self.top, btn_frm, '保存', ico=0xe010)
        self.save_btn.clicked.connect(self.do_save)
        self.exit_btn = IcoButton(self.top, btn_frm, '退出', ico=0xe009)
        self.exit_btn.clicked.connect(self.do_exit)
        btn_layer.addWidget(self.save_btn)
        btn_layer.addWidget(self.exit_btn)
        btn_frm.setLayout(btn_layer)

        layer.addWidget(self.user_info, 3)
        layer.addWidget(self.game_num, 2)
        layer.addWidget(self.win_num, 1)
        layer.addWidget(btn_frm)
        self.setLayout(layer)
        self.save_signal.connect(self.save_result)

    def set_info(self, info):
        self.game_num.setText(f'游戏场数:<b>{info["game_num"]}</b>')
        self.win_num.setText(f'获胜场数:<b>{info["win_num"]}</b>')
        self.user_info.change_info(info)

    def do_save(self):
        nick, pwd = self.user_info.nick.text(), self.user_info.pwd.text()
        if check_legal(nick) and check_legal(pwd):
            self.save_btn.setText('处理中...')
            self.save_btn.setEnabled(False)
            self.exit_btn.setEnabled(False)
            AsyncRequest(self.top, url='/modify_info', signal=self.save_signal, data={'cover': self.user_info.avatar.dialog.i, 'nick': nick, 'pwd': pwd}).start()
        else:
            PopDialog(self.top, text='昵称或密码必须是1-16位汉字,字母,数字或下划线', captain='错误').exec()

    def save_result(self, dic, req_id):
        self.save_btn.setText('保存')
        self.save_btn.setEnabled(True)
        self.exit_btn.setEnabled(True)

    def do_exit(self):
        self.top.login = False
        self.parent().login_frm.show()
        self.hide()


class UserInfo(qt.QFrame):
    def __init__(self, parent, top):
        super().__init__(parent)
        self.top = top
        self.setProperty('class', 'user-info')
        layer = CommonHBox()

        self.left_frm = qt.QFrame(self)
        self.left_frm.setProperty('class', 'left')
        left_layer = qt.QVBoxLayout()
        self.avatar = Avatar(self.left_frm, top)
        left_layer.addWidget(self.avatar)
        self.left_frm.setLayout(left_layer)

        self.right_frm = qt.QFrame(self)
        self.right_frm.setProperty('class', 'right')
        right_layer = qt.QVBoxLayout()
        self.nick = SuperInput(self.left_frm, ico=0xe007)
        self.act = SuperInput(self.right_frm, ico=0xe006)
        self.act.input.setEnabled(False)
        self.pwd = SuperInput(self.right_frm, ico=0xe008)
        right_layer.addWidget(self.nick)
        right_layer.addWidget(self.act)
        right_layer.addWidget(self.pwd)
        self.right_frm.setLayout(right_layer)

        layer.addWidget(self.left_frm)
        layer.addWidget(self.right_frm)
        self.setLayout(layer)

    def change_info(self, info):
        self.avatar.change_avatar(info['cover'])
        self.nick.setText(info['nick'])
        self.act.setText(info['act'])
        self.pwd.setText(info['pwd'])


class Avatar(qt.QLabel):
    dialog_signal = qt.pyqtSignal(int)

    def __init__(self, parent, top):
        super().__init__(parent)
        self.setCursor(qt.Qt.PointingHandCursor)
        self.setScaledContents(True)
        self.setFixedSize(70, 70)
        self.dialog = ChooseAvatar(self, top)

        self.dialog_signal.connect(self.submit_change)

    def change_avatar(self, i):
        self.setPixmap(qt.QPixmap(f'./static/avatar/{i}.png'))
        self.dialog.change_default(i)

    def submit_change(self, i):
        pass

    def mousePressEvent(self, e):
        if e.button() == qt.Qt.LeftButton:
            self.dialog.exec()


class ChooseAvatar(CommonDialog):
    def __init__(self, parent, top):
        super().__init__(top)
        self.parent = parent
        self.top = top
        self.i = 0
        self.setWindowTitle('选择头像')
        self.setObjectName('choose-avatar')

        layer = qt.QGridLayout()

        lis = listdir('./static/avatar/')
        self.avatar_lis = []
        for i in range(len(lis)-1):
            avatar = CommonBtn(self)
            avatar.i = i+1
            avatar.setProperty('class', 'avatar')
            avatar.setFixedSize(74, 74)
            avatar.setIcon(qt.QIcon(f'./static/avatar/{i+1}.png'))
            avatar.setIconSize(qt.QSize(70, 70))
            avatar.clicked.connect(self.click_avatar)
            self.avatar_lis.append(avatar)
            layer.addWidget(avatar, i//4, i % 4)
        self.setLayout(layer)

    def change_default(self, i):
        self.i = i
        self.choose(i)

    def click_avatar(self):
        self.choose(self.sender().i)

    def choose(self, i):
        for avatar in self.avatar_lis:
            if avatar.i == i:
                self.i = i
                self.parent.setPixmap(qt.QPixmap(f'./static/avatar/{i}.png'))
                avatar.setProperty('class', 'avatar active')
            else:
                avatar.setProperty('class', 'avatar')
        self.top.set_qss.emit()

'''
    右边房间选项
'''
class RoomFrame(qt.QFrame):
    def __init__(self, top, home):
        super().__init__(parent=home)
        self.top = top
        self.setProperty('class', 'room')
        layer = qt.QVBoxLayout()

        self.set_and_about = SetAndAbout(self, top)

        self.view_room = IcoButton(self.top, self, '浏览房间', ico=0xe005)
        self.view_room.clicked.connect(self.view_room_)
        self.view_room.setFixedHeight(40)
        self.enter_game = IcoButton(self.top, self, '进入游戏', ico=0xe004)
        self.enter_game.clicked.connect(self.enter_game_)
        self.enter_game.setFixedHeight(40)

        layer.addWidget(self.set_and_about)
        layer.addStretch(3)
        layer.addWidget(self.view_room)
        layer.addStretch(1)
        layer.addWidget(self.enter_game)
        layer.addStretch(6)

        self.setLayout(layer)

    def check_login(self):
        if not self.top.login:
            dialog = PopDialog(self.top, text='未登录!', btn_list=['确定'], captain='错误')
            dialog.exec()
            return False
        return True

    def view_room_(self):
        if self.check_login():
            self.top.toggle_frm(self.top.rooms_frm)

    def enter_game_(self):
        if self.check_login():
            self.top.toggle_frm(self.top.game_frm)

