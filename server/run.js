const {check_legal} = require("./util");

const fs = require('fs');
const app = require('express')();
const bodyParser = require('body-parser');
const session = require('express-session');
const mysql = require('mysql');
const expressWs = require('express-ws')(app);
const events = require('events');


let config = JSON.parse(fs.readFileSync('../client/config.json').toString());
const pool = mysql.createPool({
    host: '127.0.0.1',
    user: 'root',
    password: config.database.pwd,
    database: config.database.db
});

app.use(session({secret: 'keyboard cat'}));
app.use(bodyParser.urlencoded({extended: false}));
app.use(bodyParser.json());


// 登录 | 注册
app.post('/login', (req, res) => {
    try {
        let type = req.body['type'],
            nick = req.body['nick'],
            act = req.body['act'],
            pwd = req.body['pwd'];
        if (!(check_legal(act) && check_legal(pwd)) || (type === 'register' && !check_legal(nick))) {
            res.json({state: 'err', data: '非法字符'});
            return
        }
        let session = req.session;
        let sql = (type === 'login') ? `select id, act, nick, pwd, game_num, win_num, cover from player where act='${act}' and pwd='${pwd}'`
            : `insert into player(act, nick, pwd) VALUES ('${act}', '${nick}', '${pwd}')`;
        pool.query(sql, (err, r) => {
            if (err) {
                // 账号已注册
                if (type === 'register' && err.code === 'ER_DUP_ENTRY') {
                    res.json({state: 'warn', data: ''})
                } else {
                    res.json({state: 'err', data: err.code})
                }
            } else if (type === 'register') {
                pool.query('select last_insert_id() as id', (err, r) => {
                    if (err) {
                        res.json({state: 'err', data: err.code})
                    } else {
                        res.json({state: 'suc', data: ''})
                    }
                });
            } else {
                if (r[0].id) {
                    session.login = r[0].id;
                    res.json({state: 'suc', data: r[0]})
                } else {
                    res.json({state: 'warn', data: ''})
                }
            }
        });
    } catch (e) {
        res.json({state: 'err', data: e.toString()})
    }
});
// 修改信息
app.post('/modify_info', (req, res) => {
    try {
        let session = req.session,
            cover = req.body['cover'],
            nick = req.body['nick'],
            pwd = req.body['pwd'];
        if (!(check_legal(nick) && check_legal(pwd))) {
            res.json({state: 'err', data: '非法字符'});
            return
        }
        if (session.login) {
            pool.query(`update player set nick='${nick}',pwd='${pwd}',cover=${cover} where id=${session.login}`, (err, r) => {
                if (err) {
                    res.json({state: 'err', data: err.code})
                } else {
                    res.json({state: 'suc', data: ''})
                }
            })
        } else {
            res.json({state: 'err', data: '未登录'})
        }
    } catch (e) {
        res.json({state: 'err', data: e.toString()})
    }
});


// 房间列表
app.post('/room_list', (req, res) => {
    try {
        let count = +req.body['count'],
            page = +req.body['page'];
        if (req.session.login) {
            // 总数
            pool.query('select count(*) as c from game where p2=-1', (err, r) => {
                if (err) {
                    res.json({state: 'err', data: err.code});
                } else {
                    let re = {count: r[0].c, lis: []};
                    // 一页
                    pool.query(`select p1,id from game where p2=-1 order by id desc limit ${page * count},${count}`, (err, r) => {
                        if (err) {
                            res.json({state: 'err', data: err.code});
                        } else {
                            function get_info() {
                                if (r.length) {
                                    let info = r.pop();
                                    // 对应玩家的信息
                                    pool.query(`select nick,cover from player where id=${info.p1}`, (err, r) => {
                                        re.lis.push({
                                            game_id: info.id,
                                            nick: r[0].nick,
                                            cover: r[0].cover
                                        });
                                        get_info();
                                    })
                                } else {
                                    res.json({state: 'suc', data: re});
                                }
                            }

                            get_info()
                        }
                    })
                }
            });
        } else {
            res.json({state: 'err', data: '未登录'})
        }
    } catch (e) {
        res.json({state: 'err', data: e.toString()})
    }
});


/**
 ** 游戏
 **/

// 查找房间
app.post('/search_room', (req, res) => {
    try {
        let g_id = +req.body['id'];
        if (req.session.login) {
            pool.query(`select nick,cover,game_num,win_num from player where id=(select p1 from game where id=${g_id} and p2=-1)`, (err, r) => {
                if (err) {
                    res.json({state: 'err', data: err.code});
                } else if (r.length) {
                    res.json({state: 'suc', data: r[0]});
                } else {
                    res.json({state: 'warn', data: ''});
                }
            })
        } else {
            res.json({state: 'err', data: '未登录'})
        }
    } catch (e) {
        res.json({state: 'err', data: e.toString()})
    }
});
// 销毁房间
let destroy_room_event = new events.EventEmitter();
app.post('/del_room', (req, res) => {
    try {
        let id = req.session.login;
        if (id) {
            pool.query(`delete from game where p1=${id}`, (err, r) => {
                if (err) {
                    res.json({state: 'err', data: err.code});
                } else {
                    res.json({state: 'suc', data: ''});
                    // 提醒等待加入的ws取消等待
                    destroy_room_event.emit(`stop_wait(${id})`);
                    // 如果取消在创建之前达到，那么提醒创建函数，再别创建了!
                    req.session.stop_create = true;
                }
            })
        } else {
            res.json({state: 'err', data: '未登录'})
        }
    } catch (e) {
        res.json({state: 'err', data: e.toString()})
    }
});

// 玩家加入事件active: -1(等待p2),  1(游戏中),  2(游戏结束)
let player_join_event = new events.EventEmitter();
// 发送坐标事件
let pos_event = new events.EventEmitter();

// 游戏
app.ws('/game', function (ws, req) {
    let id = req.session.login,
        game_id = null;
    if (id) {
        ws.on('message', function (msg) {
            if (msg === 'create') {
                // 已经提前点击取消了
                if (req.session.stop_create) {
                    req.session.stop_create = false;
                    if (ws.readyState===1) {
                        ws.send('close');
                    }
                } else {
                    // 不分青红皂白，删除存在的游戏
                    pool.query(`delete from game where p1=${id}`);
                    pool.query(`insert into game(p1, p2) VALUES(${id}, -1)`, (err, r) => {
                        if (err) {
                            if (ws.readyState===1) {
                                ws.send(JSON.stringify({state: 'err', data: err.code}))
                            }
                        } else {
                            pool.query('select id as g_id from game order by id desc limit 0,1', (err, r) => {
                                let g_id = r[0].g_id;
                                // 确定当前websocket的game_id
                                game_id = g_id;
                                // 等待加入
                                if (ws.readyState===1) {
                                    ws.send(JSON.stringify({state: 'suc', data: g_id}));
                                }

                                // 监听"取消创建房间"
                                destroy_room_event.addListener(`stop_wait(${id})`, cancel_create);
                                function cancel_create() {
                                    // 取消成功
                                    // 取消监听 取消 and 加入
                                    destroy_room_event.removeListener(`stop_wait(${id})`, cancel_create);
                                    player_join_event.removeListener(`join(${g_id})`, player_join);
                                    if (ws.readyState===1) {
                                        ws.send('close');
                                    }
                                }

                                // 监听玩家加入
                                function player_join(info){
                                    if (ws.readyState===1) {
                                        ws.send(JSON.stringify(info));
                                    }
                                    // 加入成功
                                    // 取消监听 取消 and 加入
                                    destroy_room_event.removeListener(`stop_wait(${id})`, cancel_create);
                                    player_join_event.removeListener(`join(${g_id})`, player_join);
                                    // 游戏开始，先手
                                    pos_event.addListener(`p2_send_pos(${g_id})`, (pos) => {
                                        if (ws.readyState===1) {
                                            ws.send(JSON.stringify(pos));
                                        }
                                    });
                                    // 房间关闭
                                    pos_event.addListener(`room_close(${g_id})`, () => {
                                        if (ws.readyState===1) {
                                            ws.send('exit');
                                        }
                                    })
                                }
                                player_join_event.addListener(`join(${g_id})`,  player_join)
                            });
                        }
                    })
                }
            } else if (msg.match(/join\(\d+\)/)) {
                let g_id = +msg.replace(/join\((\d+)\)/, '$1');
                // 更新数据库
                pool.query(`update game set p2=${id} where id=${g_id}`, (err, r) => {
                    if (err) {
                        if (ws.readyState===1) {
                            ws.send(JSON.stringify({state: 'err', data: err.code}));
                        }
                    } else if(r.changedRows) {
                        // 把自己的信息传给房主
                        pool.query(`select nick,cover,game_num,win_num from player where id=${id}`, (err, r) => {
                            player_join_event.emit(`join(${g_id})`, r[0]);
                            if (ws.readyState===1) {
                                ws.send(JSON.stringify({state: 'suc', data: ''}));
                            }
                            // 确定当前websocket的game_id
                            game_id = g_id;
                            // 游戏开始,后手
                            pos_event.addListener(`p1_send_pos(${g_id})`, (pos) => {
                                if (ws.readyState===1) {
                                    ws.send(JSON.stringify(pos));
                                }
                            });
                            // 房间关闭
                            pos_event.addListener(`room_close(${g_id})`, () => {
                                if (ws.readyState===1) {
                                    ws.send('exit');
                                }
                            })
                        });
                    }else{
                        if (ws.readyState===1) {
                            ws.send('room closed');
                        }
                    }
                });
            } else {
                // 互传坐标
                let pos = JSON.parse(msg.replace(/^p\d_\d+\((\[.+])\)$/, '$1')),
                    g_id = msg.replace(/^p\d_(\d+).*$/, '$1'),
                    p_what = msg.replace(/^(p\d).*$/, '$1');
                pos_event.emit(`${p_what}_send_pos(${g_id})`, pos);
                if (pos[0] < 0 && pos[1] < 0){
                    pool.query(`update player set game_num=game_num+1,win_num=win_num+1 where id=${id}`);
                    pool.query(`select ${(p_what=='p1')?'p2':'p1'} as i from game where id=${g_id}`, (err, r)=>{
                        pool.query(`update player set game_num=game_num+1 where id=${r[0].i}`);
                    })
                }
            }
        });
        ws.on('close', function () {
            console.log('close');
            // 事件
            if (game_id) {
                player_join_event.removeAllListeners(`join(${game_id})`);
                pos_event.emit(`room_close(${game_id})`);
                pos_event.removeAllListeners(`room_close(${game_id})`);
                pos_event.removeAllListeners(`p1_send_pos(${game_id})`);
                pos_event.removeAllListeners(`p2_send_pos(${game_id})`);
            }
            // 强制删除本id等待中的游戏
            pool.query(`delete from game where p1=${id} and p2=-1`);
        })
    } else {
        ws.send(JSON.stringify({state: 'err', data: '未登录'}))
    }
});
// 中途退出房间
app.post('/exit_room', (req, res)=>{
    try {
        let id = req.session.login,
            g_id = +req.body['id'];
        if (id) {
            console.log('exit');
            // 关闭监听
            pos_event.removeAllListeners(`p1_send_pos(${g_id})`);
            pos_event.removeAllListeners(`p2_send_pos(${g_id})`);
            // 发送消息
            pos_event.emit(`room_close(${g_id})`);
            pos_event.removeAllListeners(`room_close(${g_id})`);
        } else {
            res.json({state: 'err', data: '未登录'})
        }
    }catch (e) {
        res.json({state: 'err', data: e.toString()})
    }
});


app.listen(16074, () => {
    console.log('server started')
});
