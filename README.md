# PyQt5+Nodejs五子棋

### 📃简述
> 项目GUI基于PyQt5，服务端基于Nodejs，使用websocket保持游戏长连接。  
据我所知已经有一个关闭窗口时无法彻底断开连接的Bug。

### 📦python依赖

* PyQt5
* requests
* websocket

### 🗄数据库
```javascript

// game
   id   |    p1    |     p2
--------|----------|-----------
 int(11)|  int(11) |  int(11)

// player
   id   |    act   |    pw    |    nick   | game_num |  win_num |   cover  |
--------|----------|----------|-----------|----------|----------|----------|
 int(11)|  int(16) |  int(16) |varchar(16)|  int(11) |  int(11) |  int(2)  |

```