import turtle
import random
import time
import os
import sys

# =========================
# Parâmetros / Constantes
# =========================
LARGURA, ALTURA = 600, 900
BORDA_X = (LARGURA // 2) - 20
BORDA_Y = (ALTURA // 2) - 10

PLAYER_SPEED = 20
PLAYER_BULLET_SPEED = 16

ENEMY_ROWS = 3
ENEMY_COLS = 10
ENEMY_SPACING_X = 60
ENEMY_SPACING_Y = 60
ENEMY_SIZE = 32
ENEMY_START_X = BORDA_X - ENEMY_SPACING_X/5
ENEMY_START_Y = BORDA_Y - ENEMY_SIZE
ENEMY_FALL_SPEED = 0.5
ENEMY_BULLET_SPEED = 8
ENEMY_FIRE_CHANCE = 0.006
ENEMY_DRIFT_STEP = 2
ENEMY_INVERT_CHANCE = 0.05
ENEMY_DRIFT_CHANCE = 0.5

BULLET_SPAWN_OFFSET = 15
COLLISION_RADIUS = 10
TOP_N = 10

HIGHSCORES_FILE = "files/highscores.txt"
SAVE_FILE = "files/savegame.txt"
PLAYER_IMAGE = "gifs/player.gif"
ENEMY_IMAGE = "gifs/enemy.gif"

STATE = None  # usado apenas para callbacks do teclado

# =========================
# Top Resultados (Highscores)
# =========================
def ler_highscores(filename):
    print("[ler_highscores] por implementar")

def atualizar_highscores(filename, score):
    print("[atualizar_highscores] por implementar")

# =========================
# Guardar / Carregar estado (texto)
# =========================
def guardar_estado_txt(filename, state):
    print("[guardar_estado_txt] por implementar")

def carregar_estado_txt(filename):
    print("[carregar_estado_txt] por implementar")
    
# =========================
# Criação de entidades (jogador, inimigo e balas)
# =========================
def criar_entidade(x, y, tipo="enemy"):
    t = turtle.Turtle(visible=False)
    
    match tipo:
        case "player":
            t.shape(PLAYER_IMAGE)
        case "enemy":
            t.shape(ENEMY_IMAGE)
        case _:
            print("Shape not specified.")
            return None

    t.penup()
    t.goto(x, y)
    
    t.showturtle()
    return t

def criar_bala(x, y, tipo):
    t = turtle.Turtle(visible=False)
    t.shapesize(0.2, 0.6)
    
    match tipo:
        case "player":
            t.shape("square")
            t.color("yellow")
            t.setheading(90)
        case "enemy":
            t.shape("square")
            t.color("red")
            t.setheading(270)
        case _:
            print("Shape not specified.")
            return None

    t.penup()
    t.goto(x, y)

    t.showturtle()
    return t

def spawn_inimigos_em_grelha(state, posicoes_existentes, dirs_existentes=None):
    current_enemy_x = ENEMY_START_X
    current_enemy_y = ENEMY_START_Y

    for i in range(0, ENEMY_ROWS):
        for j in range(0, ENEMY_COLS):
            enemy = criar_entidade(current_enemy_x, current_enemy_y, "enemy")
            state["enemies"].append(enemy)
            state["enemy_moves"].append(random.randint(0,1))
            current_enemy_x -= ENEMY_SPACING_X
        current_enemy_y -= ENEMY_SPACING_Y
        current_enemy_x = ENEMY_START_X
            
    print("Inimigos criados:")
    print(state["enemies"])

def restaurar_balas(state, lista_pos, tipo):
    print("[restaurar_balas] por implementar")

# =========================
# Handlers de tecla 
# =========================
def mover_esquerda_handler():
    player = STATE["player"]
    
    if player.xcor() > -(BORDA_X):
        player.setheading(180)
        player.forward(PLAYER_SPEED)

def mover_direita_handler():
    player = STATE["player"]

    if player.xcor() < BORDA_X:
        player.setheading(0)
        player.forward(PLAYER_SPEED)

def disparar_handler():
    player = STATE["player"]
    pos_x, pos_y = player.xcor(), player.ycor()
    STATE["player_bullets"].append(criar_bala(pos_x, pos_y + BULLET_SPAWN_OFFSET, "player"))

def gravar_handler():
    print("[gravar_handler] por implementar")

def terminar_handler():
    screen = STATE["screen"]
    screen.bye()

# =========================
# Atualizações e colisões
# =========================
def atualizar_balas_player(state):
    for bullet in state["player_bullets"][:]:
        bullet.forward(PLAYER_BULLET_SPEED)

        if bullet.ycor() > BORDA_Y:
            bullet.clear()
            bullet.hideturtle()
            state["player_bullets"].remove(bullet)
            del bullet

def atualizar_balas_inimigos(state):
    for bullet in state["enemy_bullets"][:]:
        bullet.forward(ENEMY_BULLET_SPEED)

        if bullet.ycor() < -BORDA_Y:
            bullet.clear()
            bullet.hideturtle()
            state["enemy_bullets"].remove(bullet)
            del bullet

def atualizar_inimigos(state):
    for i, enemy in enumerate(state["enemies"]):
        
        enemy_pos_x, enemy_pos_y = enemy.xcor(), enemy.ycor()
        enemy.setheading(270)
        enemy.forward(ENEMY_FALL_SPEED)

        if random.random() <= ENEMY_DRIFT_CHANCE:
            if state["enemy_moves"][i] == 0:
                enemy.setheading(180)
            else:
                enemy.setheading(0)
            enemy.forward(ENEMY_DRIFT_STEP)

        if enemy_pos_x >= BORDA_X:
            state["enemy_moves"][i] = 0
        elif enemy_pos_x <= -BORDA_X:
            state["enemy_moves"][i] = 1
        else:
            if random.random() <= ENEMY_INVERT_CHANCE:
                state["enemy_moves"][i] = 1 - state["enemy_moves"][i]

def inimigos_disparam(state):
    for enemy in state["enemies"]:
        if random.random() <= ENEMY_FIRE_CHANCE:
            pos_x, pos_y = enemy.xcor(), enemy.ycor()
            state["enemy_bullets"].append(criar_bala(pos_x, pos_y - BULLET_SPAWN_OFFSET, "enemy"))

def verificar_colisoes_player_bullets(state):
    for bullet in state["player_bullets"][:]:
        
        bullet_pos_x, bullet_pos_y = bullet.xcor(), bullet.ycor()

        for enemy in state["enemies"]:
            enemy_pos_x, enemy_pos_y = enemy.xcor(), enemy.ycor()
            
            enemy_area_x = [enemy_pos_x - ENEMY_SIZE/2, enemy_pos_x + ENEMY_SIZE/2]
            enemy_area_y = [enemy_pos_y - ENEMY_SIZE/2, enemy_pos_y + ENEMY_SIZE/2]

            if enemy_area_x[0] <= bullet_pos_x <= enemy_area_x[1] and enemy_area_y[0] <= bullet_pos_y <= enemy_area_y[1]:
                bullet.clear()
                bullet.hideturtle()
                state["player_bullets"].remove(bullet)
                del bullet
                
                enemy.clear()
                enemy.hideturtle()
                state["enemies"].remove(enemy)
                del enemy

                break

def verificar_colisoes_enemy_bullets(state):
    for bullet in state["enemy_bullets"]:
        
        bullet_pos_x, bullet_pos_y = bullet.xcor(), bullet.ycor()
        player_pos_x, player_pos_y = state["player"].xcor(), state["player"].ycor()

        player_area_x = [player_pos_x - 10, player_pos_x + 10]
        player_area_y = [player_pos_y - 10, player_pos_y + 10]

        if player_area_x[0] <= bullet_pos_x <= player_area_x[1] and player_area_y[0] <= bullet_pos_y <= player_area_y[1]:
            return 1
    
    return 0

def inimigo_chegou_ao_fundo(state):
    for enemy in state["enemies"]:
        if enemy.ycor() <= -(BORDA_Y):
            return 1
    return 0

def verificar_colisao_player_com_inimigos(state):
    for enemy in state["enemies"]:

        enemy_pos_x, enemy_pos_y = enemy.xcor(), enemy.ycor()
        player_pos_x, player_pos_y = state["player"].xcor(), state["player"].ycor()

        player_area_x = [player_pos_x - 10, player_pos_x + 10]
        player_area_y = [player_pos_y - 10, player_pos_y + 10]

        if player_area_x[0] <= enemy_pos_x <= player_area_x[1] and player_area_y[0] <= enemy_pos_y <= player_area_y[1]:
            return 1
        
    return 0

# =========================
# Execução principal
# =========================
if __name__ == "__main__":
    # Pergunta inicial: carregar?
    filename = input("Carregar jogo? Se sim, escreva nome do ficheiro, senão carregue Return: ").strip()
    loaded = carregar_estado_txt(filename)

    # Ecrã
    screen = turtle.Screen()
    screen.title("Space Invaders IPRP")
    screen.bgcolor("black")
    screen.setup(width=LARGURA, height=ALTURA)
    screen.tracer(0)

    # Imagens obrigatórias
    for img in [PLAYER_IMAGE, ENEMY_IMAGE]:
        if not os.path.exists(img):
            print("ERRO: imagem '" + img + "' não encontrada.")
            sys.exit(1)
        screen.addshape(img)

    # Estado base
    state = {
        "screen": screen,
        "player": None,
        "enemies": [],
        "enemy_moves": [],      # 0 -> esquerda | 1 -> direita
        "player_bullets": [],
        "enemy_bullets": [],
        "score": 0,
        "frame": 0,
        "files": {"highscores": HIGHSCORES_FILE, "save": SAVE_FILE}
    }

    # Construção inicial
    if loaded:
        print("[loaded=True] por implementar")
    else:
        print("New game!")
        state["player"] = criar_entidade(0, -350, "player")
        spawn_inimigos_em_grelha(state, None, None)

    # Variavel global para os keyboard key handlers
    STATE = state

    # Teclas
    screen.listen()
    screen.onkeypress(mover_esquerda_handler, "Left")
    screen.onkeypress(mover_direita_handler, "Right")
    screen.onkeypress(disparar_handler, "space")
    screen.onkeypress(gravar_handler, "g")
    screen.onkeypress(terminar_handler, "Escape")

    # Loop principal
    while True:
        atualizar_balas_player(STATE)
        atualizar_inimigos(STATE)
        inimigos_disparam(STATE)
        atualizar_balas_inimigos(STATE)
        verificar_colisoes_player_bullets(STATE)
        
        if verificar_colisao_player_com_inimigos(STATE):
            print("Colisão direta com inimigo! Game Over")
            terminar_handler()
        
        if verificar_colisoes_enemy_bullets(STATE):
            print("Atingido por inimigo! Game Over")
            terminar_handler()

        if inimigo_chegou_ao_fundo(STATE):
            print("Um inimigo chegou ao fundo! Game Over")
            terminar_handler()

        if len(STATE["enemies"]) == 0:
            print("Vitória! Todos os inimigos foram destruídos.")
            terminar_handler()

        STATE["frame"] += 1
        screen.update()
        time.sleep(0.016)
