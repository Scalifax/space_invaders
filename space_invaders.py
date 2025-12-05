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
PLAYER_SPAWN_OFFSET = 3*32
PLAYER_BULLET_SPEED = 16

ENEMY_SIZE = 32
ENEMY_ROWS = 3
ENEMY_COLS = 10
ENEMY_SPACING_X = 60
ENEMY_SPACING_Y = 60
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
FLAMENGO_IMAGE = "gifs/flamengo.gif"
PALMEIRAS_IMAGE = "gifs/palmeiras.gif"
GRAMA_IMAGE = "gifs/grama.gif"

STATE = None  # usado apenas para callbacks do teclado

# Variáveis globais que definem a cor das balas
player_bullet_color = "yellow"
enemy_bullet_color = "red"

# =========================
# Top Resultados (Highscores)
# =========================
def ler_highscores(filename):
    with open(filename, "r") as f:
        lines = f.read().splitlines()

    highscores = []
    for line in lines:
        if ":" in line:
            name, score = line.split(":", 1)
            highscores.append((name, int(score)))

    highscores.sort(key=lambda x: x[1], reverse=True)

    return highscores[:TOP_N]

def atualizar_highscores(filename, score):
    highscores = ler_highscores(filename)

    if len(highscores) < TOP_N or score > highscores[-1][1]:
        name = input("Parabéns, novo highscore! Digite o seu nome: ")

        if name:
            highscores.append((name, score))
            highscores.sort(key=lambda x: x[1], reverse=True)

            highscores = highscores[:TOP_N]

            with open(filename, "w") as f:
                for name_h, points in highscores:
                    f.write(f"{name_h}:{points}\n")

# =========================
# Guardar / Carregar estado (texto)
# =========================
def guardar_estado_txt(filename, state):
    with open(filename, "w") as f:

        # player
        if state["player"] is not None:
            p = state["player"]
            f.write(f"player:{p.xcor()},{p.ycor()}\n")
        else:
            f.write("player:none\n")

        # enemies
        f.write("enemies:")
        for e in state["enemies"]:
            f.write(f"{e.xcor()},{e.ycor()};")
        f.write("\n")

        # enemy_moves
        f.write("enemy_moves:" + ",".join(map(str, state["enemy_moves"])) + "\n")

        # player_bullets
        f.write("player_bullets:" + ";".join(
            f"{b.xcor()},{b.ycor()}" for b in state["player_bullets"]
        ) + "\n")

        # enemy_bullets
        f.write("enemy_bullets:" + ";".join(
            f"{b.xcor()},{b.ycor()}" for b in state["enemy_bullets"]
        ) + "\n")

        # score
        f.write(f"score:{state['score']}\n")

        # frame
        f.write(f"frame:{state['frame']}\n")

        # files
        f.write(f"highscores:{state['files']['highscores']}\n")
        f.write(f"save:{state['files']['save']}\n")

def carregar_estado_txt(filename):
    try:
        with open(filename, "r") as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        return None

    data = {}
    for line in lines:
        key, value = line.split(":", 1)
        data[key] = value

    # player
    player = data["player"]

    # enemies
    enemies = []
    if data["enemies"].strip() != "":
        enemies = [item for item in data["enemies"].split(";") if item.strip()]

    # enemy_moves
    enemy_moves = list(map(int, data["enemy_moves"].split(","))) if data["enemy_moves"] else []

    # player_bullets
    player_bullets = []
    if data["player_bullets"].strip() != "":
        player_bullets = [item for item in data["player_bullets"].split(";") if item.strip()]

    # enemy_bullets
    enemy_bullets = []
    if data["enemy_bullets"].strip() != "":
        enemy_bullets = [item for item in data["enemy_bullets"].split(";") if item.strip()]

    # score
    score = int(data["score"])

    # frame
    frame = int(data["frame"])

    # files
    files = {
        "highscores": data["highscores"],
        "save": data["save"]
    }

    return {
        "screen": None,
        "player": player,
        "enemies": enemies,
        "enemy_moves": enemy_moves,
        "player_bullets": player_bullets,
        "enemy_bullets": enemy_bullets,
        "score": score,
        "frame": frame,
        "files": files
    }
    
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
            t.color(player_bullet_color)
            t.setheading(90)
        case "enemy":
            t.shape("square")
            t.color(enemy_bullet_color)
            t.setheading(270)
        case _:
            print("Shape not specified.")
            return None

    t.penup()
    t.goto(x, y)

    t.showturtle()
    return t

def spawn_inimigos_em_grelha(state, posicoes_existentes=None, dirs_existentes=None):
    # loaded game
    if posicoes_existentes:
        for index, pos_str in enumerate(posicoes_existentes):
            x, y = map(float, pos_str.split(","))
            enemy = criar_entidade(x, y, "enemy")
            state["enemies"].append(enemy)

            if dirs_existentes and index < len(dirs_existentes):
                state["enemy_moves"].append(dirs_existentes[index])
            else:
                state["enemy_moves"].append(random.choice([-1, 1]))

        return

    # new game
    current_enemy_x = ENEMY_START_X
    current_enemy_y = ENEMY_START_Y

    for i in range(ENEMY_ROWS):
        for j in range(ENEMY_COLS):
            enemy = criar_entidade(current_enemy_x, current_enemy_y, "enemy")
            state["enemies"].append(enemy)
            state["enemy_moves"].append(random.choice([-1, 1]))
            current_enemy_x -= ENEMY_SPACING_X

        current_enemy_y -= ENEMY_SPACING_Y
        current_enemy_x = ENEMY_START_X


def restaurar_balas(state, lista_pos, tipo):
    bullet_type_key = "player_bullets" if tipo == "player" else "enemy_bullets"
    
    for pos_str in lista_pos:
        if pos_str.strip() == "":
            continue
        try:
            x, y = map(float, pos_str.split(","))
        except ValueError:
            print(f"[restaurar_balas] Posição inválida: {pos_str}")
            continue

        bala = criar_bala(x, y, tipo)
        state[bullet_type_key].append(bala)

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
    filename = STATE["files"]["save"]
    guardar_estado_txt(filename, STATE)

def terminar_handler():
    if STATE["screen"]:
        STATE["screen"].bye()
    
    atualizar_highscores(STATE["files"]["highscores"], STATE["score"])

# =====================================================
# Extra: easteregg de times brasileiros

is_modo_futebol_on = False

def modo_futebol_handler():
    global player_bullet_color, enemy_bullet_color, is_modo_futebol_on

    if not is_modo_futebol_on:
        screen = STATE["screen"]
        screen.bgpic(GRAMA_IMAGE)

        player = STATE["player"]
        player.shape(FLAMENGO_IMAGE)

        enemies = STATE["enemies"]
        for enemy in enemies:
            enemy.shape(PALMEIRAS_IMAGE)

        player_bullet_color = "red"
        enemy_bullet_color = "white"
        is_modo_futebol_on = True
    else:
        screen = STATE["screen"]
        screen.bgpic("")

        player = STATE["player"]
        player.shape(PLAYER_IMAGE)

        enemies = STATE["enemies"]
        for enemy in enemies:
            enemy.shape(ENEMY_IMAGE)

        player_bullet_color = "yellow"
        enemy_bullet_color = "red"
        is_modo_futebol_on = False
# =====================================================

# =========================
# Atualizações e colisões
# =========================
def atualizar_balas_player(state):
    for bullet in state["player_bullets"]:
        bullet.forward(PLAYER_BULLET_SPEED)

        if bullet.ycor() > BORDA_Y:
            bullet.hideturtle()
            bullet.clear()
            state["player_bullets"].remove(bullet)

def atualizar_balas_inimigos(state):
    for bullet in state["enemy_bullets"]:
        bullet.forward(ENEMY_BULLET_SPEED)

        if bullet.ycor() < -BORDA_Y:
            bullet.hideturtle()
            bullet.clear()
            state["enemy_bullets"].remove(bullet)

def atualizar_inimigos(state):
    for i, enemy in enumerate(state["enemies"]):
        
        enemy_pos_x = enemy.xcor()
        enemy.setheading(270)
        enemy.forward(ENEMY_FALL_SPEED)

        if random.random() <= ENEMY_DRIFT_CHANCE:
            if state["enemy_moves"][i] == -1:
                enemy.setheading(180)
            else:
                enemy.setheading(0)
            enemy.forward(ENEMY_DRIFT_STEP)

        if enemy_pos_x >= BORDA_X:
            state["enemy_moves"][i] = -1
        elif enemy_pos_x <= -BORDA_X:
            state["enemy_moves"][i] = 1
        else:
            if random.random() <= ENEMY_INVERT_CHANCE:
                state["enemy_moves"][i] -= 2*state["enemy_moves"][i]

def inimigos_disparam(state):
    for enemy in state["enemies"]:
        if random.random() <= ENEMY_FIRE_CHANCE:
            pos_x, pos_y = enemy.xcor(), enemy.ycor()
            state["enemy_bullets"].append(criar_bala(pos_x, pos_y - BULLET_SPAWN_OFFSET, "enemy"))

def verificar_colisoes_player_bullets(state):
    for bullet in state["player_bullets"]:
        
        bullet_pos_x, bullet_pos_y = bullet.xcor(), bullet.ycor()

        for enemy in state["enemies"]:
            enemy_pos_x, enemy_pos_y = enemy.xcor(), enemy.ycor()
            
            enemy_area_x = [enemy_pos_x - ENEMY_SIZE/2, enemy_pos_x + ENEMY_SIZE/2]
            enemy_area_y = [enemy_pos_y - ENEMY_SIZE/2, enemy_pos_y + ENEMY_SIZE/2]

            if enemy_area_x[0] <= bullet_pos_x <= enemy_area_x[1] and enemy_area_y[0] <= bullet_pos_y <= enemy_area_y[1]:
                bullet.hideturtle()
                bullet.clear()
                state["player_bullets"].remove(bullet)

                enemy.hideturtle()
                enemy.clear()
                state["enemies"].remove(enemy)

                state["score"] += 100

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

# =====================================================
# Extra: Game Over and Win Screen
def mostrar_game_over(state):
    # Limpa os elementos existentes
    clean_list = [state["player"]] + state["enemies"] + state["player_bullets"] + state["enemy_bullets"]
    for element in clean_list:
        element.hideturtle()
        element.clear()

    # Constrói a tela de game-over
    screen = state["screen"]
    screen.clear()
    screen.bgcolor("black")

    text = turtle.Turtle()
    text.hideturtle()
    text.color("red")
    text.penup()
    text.goto(0, 0)
    text.write("Game-Over!!", align="center", font=("Arial", 36, "bold"))

def mostrar_win(state):
    # Limpa os elementos existentes
    clean_list = [state["player"]] + state["enemies"] + state["player_bullets"] + state["enemy_bullets"]
    for element in clean_list:
        element.hideturtle()
        element.clear()

    # Constrói a tela de win
    screen = state["screen"]
    screen.clear()
    screen.bgcolor("black")

    text = turtle.Turtle()
    text.hideturtle()
    text.color("green")
    text.penup()
    text.goto(0, 0)
    text.write("Win!!", align="center", font=("Arial", 36, "bold"))
# =====================================================

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
    for img in [PLAYER_IMAGE, ENEMY_IMAGE, FLAMENGO_IMAGE, PALMEIRAS_IMAGE, GRAMA_IMAGE]:
        if not os.path.exists(img):
            print("ERRO: imagem '" + img + "' não encontrada.")
            sys.exit(1)
        screen.addshape(img)

    # Estado base
    state = {
        "screen": screen,
        "player": None,
        "enemies": [],
        "enemy_moves": [],
        "player_bullets": [],
        "enemy_bullets": [],
        "score": 0,
        "frame": 0,
        "files": {"highscores": HIGHSCORES_FILE, "save": filename if filename else SAVE_FILE}
    }

    # Construção inicial
    if loaded:
        # player
        if loaded["player"].strip():
            x, y = map(float, loaded["player"].split(","))
            state["player"] = criar_entidade(x, y, "player")
        else:
            terminar_handler() # Sem player, não possivel jogar

        # enemies
        state["enemies"].clear()
        state["enemy_moves"].clear()
        spawn_inimigos_em_grelha(state, loaded["enemies"], loaded["enemy_moves"])

        # player_bullets
        state["player_bullets"].clear()
        restaurar_balas(state, loaded["player_bullets"], "player")

        # enemy_bullets
        state["enemy_bullets"].clear()
        restaurar_balas(state, loaded["enemy_bullets"], "enemy")

        # score
        state["score"] = loaded["score"]

        # frame
        state["frame"] = loaded["frame"]

        # files
        state["files"] = loaded["files"]
        
    else:
        print("New game!")
        state["player"] = criar_entidade(0, (-BORDA_Y) + PLAYER_SPAWN_OFFSET, "player")
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
    screen.onkeypress(modo_futebol_handler, "f")

    # Loop principal
    while True:
        atualizar_balas_player(STATE)
        atualizar_inimigos(STATE)
        inimigos_disparam(STATE)
        atualizar_balas_inimigos(STATE)
        verificar_colisoes_player_bullets(STATE)
        
        if verificar_colisao_player_com_inimigos(STATE):
            print("Colisão direta com inimigo! Game Over")
            mostrar_game_over(STATE)
            time.sleep(2)
            terminar_handler()
        
        if verificar_colisoes_enemy_bullets(STATE):
            print("Atingido por inimigo! Game Over")
            mostrar_game_over(STATE)
            time.sleep(2)
            terminar_handler()

        if inimigo_chegou_ao_fundo(STATE):
            print("Um inimigo chegou ao fundo! Game Over")
            mostrar_game_over(STATE)
            time.sleep(2)
            terminar_handler()

        if len(STATE["enemies"]) == 0:
            print("Vitória! Todos os inimigos foram destruídos.")
            mostrar_win(STATE)
            time.sleep(2)
            terminar_handler()

        STATE["frame"] += 1
        screen.update()
        time.sleep(0.016)
