import socket
import pygame as pg

pg.init()


my_name = 'LilDron'
GRID_COLOR = (150,150,150)
WIDTH,HEIGHT = 700,500

server_ip = 'localhost'
# server_ip = '188.120.240.232'
def find(s):
    #поиск содержимого в строке
    otkr=None
    for i in range(len(s)):
        if s[i]=='<':
            otkr=i
        if s[i]=='>' and otkr!=None:
            zakr=i
            res=s[otkr+1:zakr]
            return res
    return ''

#прикрепляем имя к кругу
def write_name(x,y,r,name):
    font = pg.font.Font(None,r)
    text = font.render(name,True,(0,0,0))
    rect = text.get_rect(center = (x,y))
    screen.blit(text,rect)

#рисуем всех врагов
def draw_opponents(data):
    for i in range(len(data)):
        j = data[i].split(' ')
        x = WIDTH//2 + int(j[0])
        y = HEIGHT//2 + int(j[1])
        r = int(j[2])
        color = COLORS[j[3]]
        pg.draw.circle(screen,color,(x,y),r)

        if len(j)==5:
            write_name(x,y,r,j[-1])

#Класс для круга "себя"
class Me():
    def __init__(self,data,) -> None:
        data = data.split()
        self.r = int(data[0])
        self.color = data[1]

    #обновление радиуса
    def update(self,new_r):
        self.r = new_r

    #отрисовк круга
    def draw(self):
        if self.r!=0:
            pg.draw.circle(screen,COLORS[self.color],(WIDTH//2,HEIGHT//2),self.r)
            write_name(WIDTH//2,HEIGHT//2,self.r,my_name )

#класс сетки поля
class Grid():
    def __init__(self,screen) -> None:
        self.screen = screen
        self.x = 0
        self.y = 0
        self.start_size = 200
        self.size = self.start_size

#Обновление сетки
    def update(self,r_x,r_y,L):
        self.size = self.start_size//L
        self.x = -self.size + (-r_x) % self.size
        self.y = -self.size + (-r_y)%self.size
#Отрисовка сетки поля
    def draw(self):
        for i in range(WIDTH//self.size+2):
            pg.draw.line(self.screen,GRID_COLOR,
                         [self.x + i *self.size,0],
                         [self.x + i *self.size, HEIGHT],1)
        for j in range(HEIGHT//self.size+2):
            pg.draw.line(self.screen,GRID_COLOR,
                         [0,self.y + j *self.size],
                         [WIDTH,self.y + j *self.size],1)
#Создание экрана игры:
COLORS = {'0':(255,0,0),'1':(0,255,0),'2':(0,0,255),'3':(120,120,120),'4':(150,150,150),'5':(0,150,150),'6':(150,0,150),
            '7':(0,90,120),'8':(90,90,90),'9':(30,120,40)}

screen = pg.display.set_mode((WIDTH,HEIGHT))
pg.display.set_caption('AgarIO')
        

#Подключение к серверу
sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY,1)
sock.connect((server_ip,10000))


#Отправляем серверу свой ник и размеры окна
sock.send((f'.{my_name} {str(WIDTH)} {str(HEIGHT)}.').encode())

#Получаем свой размер и цвет
data = sock.recv(64).decode()

#Отправляем потверждение
sock.send('!'.encode())

me = Me(data)
grid = Grid(screen)

#Основной цикл игры
running = True
old_v = (0,0)
v = (0,0)
while running:
    #Обработка событий
    for event in pg.event.get():
        if event.type == pg.QUIT:
            
            running = False

    #Считываем положение мыши
    if pg.mouse.get_focused():
        pos=pg.mouse.get_pos()
        v=(pos[0]-WIDTH//2,pos[1]-HEIGHT//2)
 
        if (v[0])**2+(v[1])**2<=me.r**2:
            v=(0,0)
    
    

    #Отправляем вектор на сервер, если он изменился
 
    if v!=old_v:
        old_v = v
        message = '<'+str(v[0])+','+str(v[1])+'>'
        sock.send(message.encode())
        # print(v)
        
        # print(v)

    #Получаем от сервера состояние игрового поля
    try:
        data = sock.recv(2**20)
    except:
        running = False
        continue

    data = data.decode()
    data = find(data)
    data = data.split(',')



    
    #обработка сообщения с сервера
    if data!=['']:
        parametrs = list(map(int, data[0].split(' ')))
        me.update(parametrs[0])
        grid.update(parametrs[1],parametrs[2],parametrs[3])
        #Рисуем состояние игрового поля
        screen.fill('grey25')
        grid.draw()
        draw_opponents(data[1:])

        me.draw()

    pg.display.update()

pg.quit()  

