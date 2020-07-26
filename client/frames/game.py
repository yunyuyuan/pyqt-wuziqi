import PyQt5.Qt as qt
import asyncio
import websockets
from re import match, sub
from threading import Event, Thread
from requests.utils import dict_from_cookiejar

from frames import config, session, AsyncRequest
from components import CommonDialog, CommonHBox, CommonVBox, CommonBtn
from components.avatar_label import AvatarLabel
from components.pop_dialog import PopDialog
from components.ico_button import IcoButton

uri = sub('https?(://)', 'ws\\1', config['server']) + "/game"
chess_radius = 40


class GameThread(qt.QThread):
    def __init__(self, top, game, func, *args, **kwargs):
        super().__init__(top)
        self.game = game
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.loop = asyncio.new_event_loop()

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.func(*self.args, **self.kwargs))

    def shutdown(self):
        if not self.game.head_frm.dialog.isHidden():
            self.game.head_frm.dialog.close()
        self.terminate()


class Game(qt.QFrame):
    def __init__(self, top):
        super().__init__(parent=top)
        self.top = top
        self.game_id = None
        self.p_what = 0
        self.put_event = Event()
        self.setObjectName('game')
        self.thread = None
        self.websocket = None
        self.win_dialog = None

        layer = CommonVBox()

        self.head_frm = Head(self, top)
        self.body_frm = Body(self, top)
        self.footer_frm = Footer(self, top)

        layer.addWidget(self.head_frm)
        layer.addWidget(self.body_frm)
        layer.addWidget(self.footer_frm)
        self.setLayout(layer)

    # 刷新游戏
    def refresh(self):
        # 设置头部显示创建/加入
        self.head_frm.toggle_playing(False)
        # 清空棋盘信息
        self.body_frm.reset()
        # 去除p2栏信息
        self.footer_frm.reset()

    def run_game(self, type_):
        if self.thread:
            self.thread.shutdown()
        self.thread = GameThread(self.top, self, self.websocket_handle, type_)
        self.thread.start()

    async def websocket_handle(self, type_):
        # 清空棋子
        self.body_frm.reset()
        # 加入cookie (包含session
        cookie = ''
        for c in session.cookies:
            cookie += c.name+'='+c.value
        async with websockets.connect(uri, extra_headers={'cookie': cookie}) as self.websocket:
            pop_dialog = self.head_frm.dialog
        # ---- 创建房间 ----
            if type_ == 'create':
                # 发送创建请求
                pop_dialog.create_state.setText('创建中...')
                await self.websocket.send('create')
                # 接收到返回信息
                res = await self.websocket.recv()
                # 貌似你在这之前就点击了取消!
                if res == 'close':
                    await self.websocket.close()
                else:
                    data = eval(res)
                    if data['state'] == 'suc' and pop_dialog.creating:
                        # 创建成功,等待玩家加入信息
                        pop_dialog.create_state.setText(f'房间号:{data["data"]},等待玩家加入')
                        self.game_id = data["data"]
                        self.p_what = 1
                        res = await self.websocket.recv()
                        pop_dialog.at = 'closed'
                        pop_dialog.close()
                        # 取消
                        if res == 'close':
                            await self.websocket.close()
                        else:
                            player_info = eval(res)
                            if player_info and pop_dialog.creating:
                                self.footer_frm.p2.update_info(player_info)
                                print('game start')
                                self.head_frm.toggle_playing(True)
                                self.body_frm.chessboard.turn_to_me = True
                                while 1:
                                    # 先手下棋
                                    if not await self.send_pos(1):
                                        break
                                    # 接受坐标
                                    if await self.recv_pos():
                                        break
                    else:
                        pop_dialog.create_state.setText('创建失败:'+res)
        # ---- 加入房间 ----
            else:
                # 发送加入请求
                await self.websocket.send(f'join({type_})')
                res = await self.websocket.recv()
                self.head_frm.dialog.join_btn.setEnabled(True)
                if res == 'room closed':
                    self.head_frm.dialog.join_state.setText('房间已经失效了')
                    self.head_frm.dialog.join_btn.setText('查询')
                else:
                    data = eval(res)
                    if data['state'] == 'suc':
                        self.game_id = type_
                        self.p_what = 2
                        print('game start')
                        pop_dialog.close()
                        self.head_frm.toggle_playing(True)
                        self.footer_frm.p2.update_info(False)
                        self.body_frm.chessboard.turn_to_me = False
                        while 1:
                            # 接受坐标
                            if await self.recv_pos():
                                break
                            # 后手下棋
                            if not await self.send_pos(2):
                                break
                    else:
                        self.head_frm.dialog.create_state.setText('加入失败:' + data['data'])
                        self.head_frm.dialog.join_btn.setText('查询')

    async def send_pos(self, what):
        self.footer_frm.turn_signal.emit('me')
        self.put_event.clear()
        self.put_event.wait()
        pos = self.body_frm.put_pos
        self.body_frm.put_event.clear()
        # 发送坐标
        await self.websocket.send(f'p{what}_{self.game_id}(' + str(pos) + ')')
        print('send pos ' + str(pos))
        # 我赢了
        if pos[0] < 0 and pos[1] < 0:
            await self.websocket.close()
            PopDialog(self.top, text='你赢了', captain='游戏结束').exec()
            return False
        return True

    async def recv_pos(self):
        self.footer_frm.turn_signal.emit('other')
        recv_pos = await self.websocket.recv()
        exit_ = False
        if recv_pos == 'exit':
            self.refresh()
            await self.websocket.close()
            exit_ = True
        else:
            pos = eval(recv_pos)
            # 对方赢了
            if pos[0] < 0 and pos[1] < 0:
                pos = [-x for x in pos]
                self.body_frm.put_chess(pos)
                await self.websocket.close()
                PopDialog(self.top, text='你输了', captain='游戏结束').exec()
                exit_ = True
            else:
                self.body_frm.put_chess(pos)
            print('recv pos ' + recv_pos)
        if exit_:
            self.footer_frm.turn_signal.emit('exit')
            self.head_frm.toggle_playing(False)
            self.body_frm.chessboard.turn_to_me = False
        return exit_


'''
    头部，创建/加入
'''
class Head(qt.QFrame):
    def __init__(self, parent, top):
        super().__init__(parent)
        self.top = top
        self.setProperty('class', 'head')
        self.dialog = HeadDialog(self, top)
        self.setFixedHeight(50)
        layer = CommonHBox()

        self.back_btn = IcoButton(self.top, self, ico=0xe011)
        self.back_btn.clicked.connect(self.back_home)
        btn_layer = CommonHBox()
        self.create_btn = IcoButton(self.top, self, text='创建房间', ico=0xe013)
        self.create_btn.clicked.connect(self.create_)
        self.create_btn.setFixedWidth(140)
        self.join_btn = IcoButton(self.top, self, text='加入房间', ico=0xe004)
        self.join_btn.clicked.connect(self.join_)
        self.join_btn.setFixedWidth(140)
        self.exit_btn = IcoButton(self.top, self, text='退出游戏', ico=0xe009)
        self.exit_btn.clicked.connect(self.exit_)
        self.exit_btn.setFixedWidth(140)
        self.exit_btn.hide()

        layer.addWidget(self.back_btn, 0)
        btn_layer.addWidget(self.create_btn, alignment=qt.Qt.AlignHCenter)
        btn_layer.addWidget(self.join_btn, alignment=qt.Qt.AlignHCenter)
        btn_layer.addWidget(self.exit_btn, alignment=qt.Qt.AlignHCenter)
        layer.addLayout(btn_layer, 1)
        self.setLayout(layer)

    def back_home(self):
        self.top.toggle_frm(self.top.home_frm)
        self.exit_()

    def create_(self):
        self.dialog.show_create()

    def join_(self):
        self.dialog.show_join()

    def exit_(self):
        if self.top.game_frm.game_id:
            AsyncRequest(self.top, url='/exit_room', data={'id': self.top.game_frm.game_id}).start()
            self.top.game_frm.refresh()
            if self.top.game_frm.thread:
                self.top.game_frm.thread.shutdown()

    def toggle_playing(self, b):
        if b:
            self.create_btn.hide()
            self.join_btn.hide()
            self.exit_btn.show()
        else:
            self.create_btn.show()
            self.join_btn.show()
            self.exit_btn.hide()


class HeadDialog(CommonDialog):
    search_signal = qt.pyqtSignal(dict, int)

    def __init__(self, head, top):
        super().__init__(top)
        self.head = head
        self.top = top
        self.setProperty('class', 'game-head-dialog')
        self.at = 'c'
        # 等待创建,为取消做标志物
        self.creating = False
        self.join_id = None

        layer = CommonVBox()

        self.create_frm = qt.QFrame(self)
        create_layer = CommonVBox()
        self.create_state = qt.QLabel('创建中...', self.create_frm)
        self.cancel_create = CommonBtn('取消', self.create_frm)
        self.cancel_create.clicked.connect(self.close)
        create_layer.addWidget(self.create_state)
        create_layer.addWidget(self.cancel_create)
        self.create_frm.setLayout(create_layer)

        self.join_frm = qt.QFrame(self)
        join_layer = CommonVBox()
        self.join_state = qt.QLabel('输入房间号(数字)', self.join_frm)
        self.join_input = qt.QLineEdit(self.join_frm)
        self.join_btn = CommonBtn('查询', self.join_frm)
        self.join_btn.clicked.connect(self.do_join)
        join_layer.addWidget(self.join_state)
        join_layer.addWidget(self.join_input)
        join_layer.addWidget(self.join_btn)
        self.join_frm.setLayout(join_layer)

        layer.addWidget(self.create_frm)
        layer.addWidget(self.join_frm)
        self.setLayout(layer)

        self.search_signal.connect(self.search_result)

    def closeEvent(self, e):
        if self.at == 'c':
            # 终止等待玩家加入
            AsyncRequest(self.top, url='/del_room', data={}).start()
        else:
            self.join_id = None

    def show_create(self):
        self.at = 'c'
        self.creating = True
        self.create_frm.show()
        self.join_frm.hide()
        self.top.game_frm.run_game('create')
        self.exec()

    def show_join(self):
        self.at = 'j'
        self.join_state.setText('输入房间号(数字)')
        self.join_btn.setText('查询')
        self.join_btn.setEnabled(True)
        self.create_frm.hide()
        self.join_frm.show()
        self.exec()

    def do_join(self):
        self.join_btn.setEnabled(False)
        if self.join_btn.text() == '查询':
            room_id = self.join_input.text()
            if match('^[0-9]+$', room_id):
                self.join_id = room_id
                self.join_btn.setText('查询中')
                AsyncRequest(self.top, url='/search_room', data={'id': room_id}, signal=self.search_signal).start()
            else:
                self.join_state.setText('房间号为数字!')
                self.join_btn.setEnabled(True)
        elif self.join_btn.text() == '加入':
            self.top.game_frm.run_game(self.join_id)

    def search_result(self, dic, req_id):
        if self.join_id:
            self.join_btn.setEnabled(True)
            if dic['state'] == 'suc':
                state = '找到房间'
                self.top.game_frm.footer_frm.p2.preserve_info(dic['data'])
                btn = '加入'
            else:
                btn = '查询'
                if dic['state'] == 'warn':
                    state = '未找到房间!'
                else:
                    state = '错误:'+dic['data']
            self.join_state.setText(state)
            self.join_btn.setText(btn)

'''
    游戏主体
'''
class Body(qt.QFrame):
    def __init__(self, parent, top):
        super().__init__(parent)
        self.setProperty('class', 'body')
        self.top = top
        self.put_event = Event()
        self.put_pos = []

        layer = CommonHBox()
        self.chessboard = ChessBoard(self, top)
        layer.addWidget(self.chessboard, qt.Qt.AlignCenter)
        self.setLayout(layer)
        self.setMouseTracking(True)

    def mouseMoveEvent(self, e):
        if not self.chessboard.hover_label.isHidden():
            self.chessboard.hover_label.hide()
            self.chessboard.hover_pos = [-1, -1]

    # 放置棋子
    def put_chess(self, pos):
        self.chessboard.boardlines.add_chess(pos, self.chessboard.turn_to_me)
        self.chessboard.turn_to_me = True

    def reset(self):
        # 清空棋子
        self.chessboard.boardlines.exist_pos.clear()
        self.chessboard.boardlines.update()
        self.chessboard.turn_to_me = False


class ChessBoard(qt.QFrame):
    def __init__(self, body, top):
        super().__init__(body)
        self.body = body
        self.top = top
        self.turn_to_me = False
        self.setProperty('class', 'chess-board')
        self.interval = chess_radius
        self.hover_pos = [-1, -1]
        self.setFixedSize(16*self.interval, 16*self.interval)

        self.boardlines = BoardLines(self, top)
        self.hover_label = ChessHover(self)
        self.hover_label.hide()
        self.setMouseTracking(True)

    # 显示鼠标悬浮框
    def mouseMoveEvent(self, e):
        if self.turn_to_me:
            e.accept()
            half = self.interval // 2
            x, y = e.x(), e.y()
            if half < x < 15*self.interval+half and half < y < 15*self.interval+half:
                if self.hover_label.isHidden():
                    self.hover_label.show()
                pos = [(x-half) // self.interval, (y-half) // self.interval]
                if pos not in [[x[0], x[1]] for x in self.boardlines.exist_pos]:
                    self.hover_label.update_pos(pos)
                    self.hover_pos = pos
                else:
                    self.hover_pos = [-1, -1]
                    self.hover_label.hide()

    # 下棋
    def mousePressEvent(self, e):
        if self.turn_to_me and e.button() == qt.Qt.LeftButton and self.hover_pos != [-1, -1]:
            self.body.put_pos = self.hover_pos
            self.boardlines.add_chess(self.hover_pos, self.turn_to_me)
            self.top.game_frm.put_event.set()
            self.hover_label.hide()
            self.turn_to_me = False


class BoardLines(qt.QFrame):
    def __init__(self, chessboard, top):
        super().__init__(chessboard)
        self.top = top
        self.exist_pos = []

        self.setGeometry(0, 0, chessboard.width(), chessboard.height())
        self.setMouseTracking(True)

    # 放棋
    def add_chess(self, pos, is_me):
        self.exist_pos.append([*pos, is_me])
        self.update()
        # 检查获胜
        pure_pos = [[x[0], x[1]] for x in self.exist_pos if x[2]]
        if is_me:
            win = False
            for pos in pure_pos:
                # 水平向右
                if [pos[0]+1, pos[1]] in pure_pos and [pos[0]+2, pos[1]] in pure_pos and [pos[0]+3, pos[1]] in pure_pos and [pos[0]+4, pos[1]] in pure_pos:
                    win = True
                    break
                # 垂直向下
                elif [pos[0], pos[1]+1] in pure_pos and [pos[0], pos[1]+2] in pure_pos and [pos[0], pos[1]+3] in pure_pos and [pos[0], pos[1]+4] in pure_pos:
                    win = True
                    break
                # 斜向右下
                elif [pos[0]+1, pos[1]+1] in pure_pos and [pos[0] + 2, pos[1]+2] in pure_pos and [pos[0] + 3, pos[1]+3] in pure_pos and [pos[0] + 4, pos[1]+4] in pure_pos:
                    win = True
                    break
                # 斜向左下
                elif [pos[0] - 1, pos[1]+1] in pure_pos and [pos[0] - 2, pos[1]+2] in pure_pos and [pos[0] - 3, pos[1]+3] in pure_pos and [pos[0] - 4, pos[1]+4] in pure_pos:
                    win = True
                    break
            if win:
                self.top.game_frm.body_frm.put_pos = [-x for x in self.top.game_frm.body_frm.put_pos]
                self.top.game_frm.head_frm.toggle_playing(False)
                self.top.game_frm.footer_frm.turn_to('exit')

    def paintEvent(self, e):
        painter1 = qt.QPainter(self)
        painter1.setPen(qt.QPen(qt.Qt.black, 1))
        interval = self.parent().interval
        for i in range(15):
            painter1.drawLine(interval, i*interval+interval, 14*interval+interval, i*interval+interval)
            painter1.drawLine(i*interval+interval, interval, i*interval+interval, 14*interval+interval)

        if self.exist_pos:
            painter = qt.QPainter(self)
            painter.setRenderHint(qt.QPainter.Antialiasing)
            painter.setPen(qt.Qt.transparent)
            interval = self.parent().interval
            radius = interval//2
            for pos in self.exist_pos:
                center = (pos[0]*interval+interval, pos[1]*interval+interval)
                radial = qt.QRadialGradient(*center, radius, *center)
                if pos[2]:
                    radial.setColorAt(0, qt.QColor('#4F5150'))
                    radial.setColorAt(0.8, qt.QColor('#333437'))
                    radial.setColorAt(1, qt.QColor('#304242'))
                else:
                    radial.setColorAt(0, qt.QColor('#EEF4F4'))
                    radial.setColorAt(0.8, qt.QColor('#D9DEE1'))
                    radial.setColorAt(1, qt.QColor('#C7D1D3'))
                painter.setBrush(radial)
                painter.drawEllipse(qt.QPoint(*center), radius, radius)

class ChessHover(qt.QLabel):
    def __init__(self, board):
        super().__init__(board)

    def update_pos(self, pos):
        interval = self.parent().interval
        self.setGeometry(pos[0]*interval+interval//2, pos[1]*interval+interval//2, interval, interval)
        self.update()

    def paintEvent(self, e):
        interval = self.parent().interval
        painter = qt.QPainter(self)
        painter.setPen(qt.QPen(qt.Qt.red, 1))
        painter.drawRect(1, 1, interval-2, interval-2)


'''
    游戏信息
'''
class Footer(qt.QFrame):
    turn_signal = qt.pyqtSignal(str)

    def __init__(self, parent, top):
        super().__init__(parent)
        self.setProperty('class', 'footer')
        self.setFixedHeight(100)
        self.top = top
        layer = CommonHBox()

        self.p1 = PlayerInfo(self, top)
        self.middle_frm = qt.QFrame(self)
        self.p2 = PlayerInfo(self, top)

        layer.addWidget(self.p1)
        layer.addWidget(self.middle_frm)
        layer.addWidget(self.p2)
        self.setLayout(layer)

        self.turn_signal.connect(self.turn_to)

    def reset(self):
        self.p2.preserve_info({})
        self.p2.update_info(False)

    def turn_to(self, who):
        if who == 'me':
            self.p1.setProperty('at', 't')
            self.p2.setProperty('at', 'f')
        elif who == 'other':
            self.p2.setProperty('at', 't')
            self.p1.setProperty('at', 'f')
        else:
            self.p2.setProperty('at', 'f')
            self.p1.setProperty('at', 'f')
        self.top.set_qss.emit()

class PlayerInfo(qt.QFrame):
    def __init__(self, parent, top):
        super().__init__(parent)
        self.top = top
        self.preserve = {}
        self.setProperty('class', 'player')
        self.setFixedWidth(240)
        layer = CommonHBox()

        self.base_info = qt.QFrame(self)
        self.base_info.setProperty('class', 'base')
        base_info_layer = CommonVBox()
        self.avatar = AvatarLabel(self.base_info, (66, 66), 8)
        self.avatar.setProperty('class', 'avatar')
        base_info_layer.addWidget(self.avatar)
        self.base_info.setLayout(base_info_layer)

        self.game_info = qt.QFrame(self)
        self.game_info.setProperty('class', 'game')
        game_info_layer = CommonVBox()
        self.nick = qt.QLabel(self.base_info)
        self.nick.setProperty('class', 'nick')
        self.nick.setWordWrap(True)
        self.game_num = qt.QLabel(self.game_info)
        self.game_num.setProperty('class', 'game_num')
        self.win_num = qt.QLabel(self.game_info)
        self.win_num.setProperty('class', 'win_num')
        game_info_layer.addWidget(self.nick)
        game_info_layer.addWidget(self.game_num)
        game_info_layer.addWidget(self.win_num)
        self.game_info.setLayout(game_info_layer)

        layer.addWidget(self.base_info)
        layer.addWidget(self.game_info)
        self.setLayout(layer)

        self.update_info(False)

    def preserve_info(self, info):
        self.preserve = info

    def update_info(self, info):
        if not info:
            info = self.preserve
        self.avatar.set_cover(info.get('cover', 0))
        self.nick.setText(info.get('nick', '未知'))
        self.game_num.setText('游戏场数:<b>'+str(info.get('game_num', 0))+'</b>')
        self.win_num.setText('获胜场数:<b>'+str(info.get('win_num', 0))+'</b>')
