import socket
import time
import pygame as pg
import random

#поиск содержимого в строке
def find(s:str):
    otkr = None
    for i in range(len(s)):
        if s[i]=='<':
            otkr = i
        if s[i]=='>' and otkr!=None:
            zakr = i
            res = s[otkr+1:zakr]
            res=list(map(int,res.split(',')))
            return res
    return ''

def new_radius(R,r):
    #Функция для вычисления нового радиуса объекта исходя из площадей
    return (R**2 + r**2)**0.5

#Константы
WIDTH_ROOM,HEIGHT_ROOM = 4000,4000
WIDTH_SERVER_WINDOW, HEIGHT_SERVER_WINDOW = 300,300
FPS = 100
START_PLAYER_SIZE = 30
FEED_SIZE = 15
MOBS_QUANTITY = 25
FEED_QUANTITY = (WIDTH_ROOM * HEIGHT_ROOM) // 80000

#Константы для сервера
work_on_server = False
server_ip = 'localhost'
# server_ip = '188.120.240.232'


COLORS = {'0':(255,0,0),'1':(0,255,0),'2':(0,0,255),'3':(120,120,120),'4':(150,150,150),'5':(0,150,150),'6':(150,0,150),
            '7':(0,90,120),'8':(90,90,90),'9':(30,120,40)}
#Создание класса корма
class Feed():
    def __init__(self,x,y,r,color):
        self.x = x
        self.y = y
        self.r = r
        self.color = color

        
#Создание класса игрока
class Player():
    def __init__(self,conn,addr,x,y,radius,color):
        self.conn = conn
        self.addr = addr
        self.x = x
        self.y =y 
        self.r = radius
        self.color = color

        self.name = 'Mob'
        self.L = 1   #масштаб
        self.width_window = 700
        self.height_window = 500

        self.w_vision = 700
        self.h_vision = 500

        self.ready = False
        self.errors = 0
        self.dead = 0

        self.abs_speed = 30/(self.r**0.5)
        self.speed_x = 0
        self.speed_y = 0

#Обновление констант у объъекта
    def update(self):
        #x coord
        if self.x-self.r <= 0 :
            if self.speed_x>=0:
                self.x += self.speed_x
        else:
            if self.x + self.r >=WIDTH_ROOM:
                if self.speed_x<=0:
                    self.x+=self.speed_x
            else:
                self.x+=self.speed_x

        #y coord
        if self.y-self.r <= 0 :
            if self.speed_y>=0:
                self.y += self.speed_y
        else:
            if self.y + self.r >=WIDTH_ROOM:
                if self.speed_y<=0:
                    self.y+=self.speed_y
            else:
                self.y+=self.speed_y
        
        #abs_speed
        if self.r!=0:
            self.abs_speed = 30/(self.r**0.5)
        else:
            self.abs_speed = 0

        #size
        #наш шарик уменьшается, в зависимости от размеров
        if self.r>=100:
            self.r-=self.r/20000

        #L
        if self.r>=self.w_vision/4 or self.r>=self.h_vision/4:
            if self.w_vision<=WIDTH_ROOM or self.h_vision<=HEIGHT_ROOM:
                self.L *= 2
                self.w_vision = self.width_window * self.L
                self.h_vision = self.height_window * self.L
        if self.r < self.w_vision/8 and self.r < self.h_vision/8:
            if self.L>1:
                self.L//=2
                self.w_vision = self.width_window * self.L
                self.h_vision = self.height_window * self.L

#Установка параметров для объекта
    def set_options(self,data):
        data = data[1:-1].split(' ')
        self.name = data[0]
        self.width_window = int(data[1])
        self.height_window = int(data[2])
        self.w_vision = int(data[1])
        self.h_vision= int(data[2])
        print(self.name, self.width_window, self.height_window)


#Изменение скорости
    def change_speed(self,v):
        
        if (v[0]==0) and (v[1]==0):
            self.speed_x = 0
            self.speed_y = 0
        else:
            lenv=(v[0]**2+v[1]**2)**0.5
            v=(v[0]/lenv,v[1]/lenv)
            v=(v[0]*self.abs_speed,v[1]*self.abs_speed)
            self.speed_x,self.speed_y=v[0],v[1]

#Создание сокета
main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
main_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
main_socket.bind((server_ip,10000))
main_socket.setblocking(0)
main_socket.listen(5)

#Создание окна
pg.init()
if not work_on_server:
    screen = pg.display.set_mode((WIDTH_SERVER_WINDOW,HEIGHT_SERVER_WINDOW))
    pg.display.set_caption('AgarIO')
clock = pg.time.Clock()

#Список игроков
players = [Player(None,None,random.randint(0,WIDTH_ROOM),
                  random.randint(0,HEIGHT_ROOM),
                  random.randint(10,50),
                  str(random.randint(0,len(COLORS)-1))) for _ in range(MOBS_QUANTITY)]

#создание корма
feed = [Feed(random.randint(0,WIDTH_ROOM),
                  random.randint(0,HEIGHT_ROOM),
                  FEED_SIZE,str(random.randint(0,len(COLORS)-1))) for _ in range(FEED_QUANTITY)]

server_works = True
tick = -1

#Основной цикл обработки игры
while server_works:
    tick+=1
    #Проверяем, есть ли желающие войти в игру
    if tick == 50:
        tick = 0
        try:
            new_socket,addr = main_socket.accept()
            # print('Подключился игрок',addr)
            new_socket.setblocking(0)

            #выбираем рандомную бактерию, чтобы игрок не спавнился сразу в мобе
            spawn = random.choice(feed)
            new_player = Player(new_socket,addr,
                                spawn.x,
                                spawn.y,
                                START_PLAYER_SIZE,color=str(random.randint(0,len(COLORS)-1)))
            feed.remove(spawn)

            # message = str(new_player.r) + ' '+ new_player.color
            # new_player.conn.send(message.encode())

            players.append(new_player)
        except:
            pass
        
        #дополняем список мобов
        for i in range(MOBS_QUANTITY-len(players)):
            if len(feed)!=0:
                spawn = random.choice(feed)
                players.append(Player(None,None,spawn.x,spawn.y,
                                    random.randint(10,50),
                    str(random.randint(0,len(COLORS)-1))))
                feed.remove(spawn)
        #Дополняем список feed
        new_feed = [Feed(random.randint(0,WIDTH_ROOM),
                  random.randint(0,HEIGHT_ROOM),
                  FEED_SIZE,str(random.randint(0,len(COLORS)-1))) 
                  for _ in range(FEED_QUANTITY - len(feed))]
        feed = feed + new_feed

    #Считываем команды игроков
    for player in players:
        if player.conn!=None:
            try:
                data = player.conn.recv(1024)
                data = data.decode()
                if data[0]=='!':#пришло сообщение о готовности к диалогу
                    player.ready = True
                else:
                    if data[0]=='.' and data[-1]=='.': #имя и размер окна
                        player.set_options(data)
                        player.conn.send((str(START_PLAYER_SIZE)+' '+player.color).encode())
                    else: #курсов
                        data = find(data)
                        player.change_speed(data)
                
            except:
                pass
        else:
            #Изменяем направление движения врагов
            if tick==30:
                
                data = [random.randint(-2,2),random.randint(-2,2)]

                player.change_speed(data)
        player.update()

    #Определим, что видит каждый игрок
    visible_balls = [[] for _ in range(len(players))]
    for i in range(len(players)):
        #какой корм видит i игрок
        for k in range(len(feed)):
            distance_x = feed[k].x - players[i].x
            distance_y = feed[k].y - players[i].y
            #игрок видит 
            if (abs(distance_x)<=(players[i].w_vision)//2 + feed[k].r) and (abs(distance_y)<=(players[i].h_vision)//2 + feed[k].r):
                #игрок может съесть
                if ((distance_x**2 + distance_y**2)**0.5<=players[i].r):
                    #меняем радиус i игрока
                    players[i].r = new_radius(players[i].r,feed[k].r)
                    feed[k].r = 0 

                if players[i].conn!=None and feed[k].r!=0:
                    x_= str(round(distance_x/players[i].L))
                    y_= str(round(distance_y/players[i].L))
                    r_ = str(round(feed[k].r/players[i].L))
                    c_ = str(feed[k].color)

                    visible_balls[i].append(f'{x_} {y_} {r_} {c_}')



        for j in range(i+1,len(players)):
            #рассмотрим пару i,j игрока
            distance_x = players[j].x - players[i].x
            distance_y = players[j].y - players[i].y

            #i видит j
            if (abs(distance_x)<=(players[i].w_vision)//2 + players[j].r) and (abs(distance_y)<=(players[i].h_vision)//2 + players[j].r):
                #i может съесть j
                if ((distance_x**2 + distance_y**2)**0.5<=players[i].r) and players[i].r > 1.1*players[j].r:
                    #изменить радиус i игрока
                    players[i].r = new_radius(players[i].r,players[j].r)
                    players[j].r, players[j].speed_x, players[j].speed_y = 0,0,0

                #подготавливаем информацию
                if players[i].conn!=None:
                    x_= str(round(distance_x/players[i].L))
                    y_= str(round(distance_y/players[i].L))
                    r_ = str(round(players[j].r/players[i].L))
                    c_ = str(players[j].color)
                    n_ = players[j].name

                    if players[j].r>=30*players[i].L:
                        visible_balls[i].append(f'{x_} {y_} {r_} {c_} {n_}')
                    else:
                        visible_balls[i].append(f'{x_} {y_} {r_} {c_}')

            #j видит i
            if (abs(distance_x)<=(players[j].w_vision)//2 + players[i].r) and (abs(distance_y)<=(players[j].h_vision)//2 + players[i].r):
                #j может съесть i
                if ((distance_x**2 + distance_y**2)**0.5<=players[j].r) and players[j].r > 1.1*players[i].r:
                    #изменить радиус j игрока
                    players[j].r = new_radius(players[j].r,players[i].r)
                    players[i].r, players[i].speed_x, players[i].speed_y = 0,0,0

                if players[j].conn!=None:
                    x_= str(round(-distance_x/players[j].L))
                    y_= str(round(-distance_y/players[j].L))
                    r_ = str(round(players[i].r/players[j].L))
                    c_ = players[i].color
                    n_ = players[i].name

                    if players[i].r>=30*players[j].L:
                        visible_balls[j].append(f'{x_} {y_} {r_} {c_} {n_}')
                    else:
                        visible_balls[j].append(f'{x_} {y_} {r_} {c_}')

    #формируем ответ каждому игроку:
    otvets = ['' for _ in range(len(players))]
    for i in range(len(players)):
        x_ = str(round(players[i].x/players[i].L))
        y_ = str(round(players[i].y/players[i].L))
        L_ =str(round(players[i].L))
        r_ = str(round(players[i].r/players[i].L))
        visible_balls[i] = [f'{r_} {x_} {y_} {L_}']+visible_balls[i]
        otvets[i] = '<' + (','.join(visible_balls[i])) + '>'

    
    #отправляем новое состояние игрового поля
    for i in range(len(players)):
        if players[i].conn!=None and players[i].ready==True:
            try:
                players[i].conn.send(otvets[i].encode())
                players[i].errors = 0
            except:
                players[i].errors+=1

    #Чистим список от неподключенных игроков
    for player in players:
            if player.r==0: 
                if player.conn!=None:
                    player.dead+=1
                else:
                    player.dead+=300
            if player.errors>=500 or player.dead == 300:
                if player.conn!=None:
                    player.conn.close()
                players.remove(player)
                
                # print('Отключился игрок')
            
    #Чистим список от корма
    for a in feed:
        if a.r==0:
            feed.remove(a)

    if not work_on_server:
    #Рисуем состояние игровой комнаты
    
        for event in pg.event.get():
            if event.type == pg.QUIT:
                server_works = False
        screen.fill('BLACK')

        for player in players:
            x = round(player.x*WIDTH_SERVER_WINDOW/WIDTH_ROOM)
            y = round(player.y*HEIGHT_SERVER_WINDOW/HEIGHT_ROOM)
            r = round(player.r*WIDTH_SERVER_WINDOW/WIDTH_ROOM)
            pg.draw.circle(screen,COLORS[player.color], (x,y),r)

        pg.display.update()

    clock.tick(FPS)

pg.quit()
main_socket.close()