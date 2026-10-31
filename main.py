import json
import math
import random
from array import array
from collections import deque
from pathlib import Path

import pygame

COLUNAS, LINHAS = 30, 20
TAMANHO_INICIAL = 3
FPS = 60
JANELA_INICIAL = (900, 680)
ARQUIVO_RECORDE = Path(__file__).with_name("recorde.json")

INTERVALO_INICIAL = 0.14
INTERVALO_MINIMO = 0.05
FATOR_ACELERACAO = 0.975

DEMO_CRESCIMENTO_MAXIMO = 35

BONUS_CHANCE = 0.25
BONUS_DURACAO = 6.0
BONUS_PONTOS = 5

RELOGIO_CHANCE = 0.15
RELOGIO_DURACAO = 7.0
LENTIDAO_DURACAO = 5.0
LENTIDAO_FATOR = 1.8

FUNDO = (14, 17, 26)
TABULEIRO_A = (27, 32, 47)
TABULEIRO_B = (31, 37, 54)
BORDA = (52, 61, 88)
TEXTO = (236, 239, 246)
TEXTO_SUAVE = (139, 149, 176)
COBRA_CABECA = (134, 239, 128)
COBRA_CAUDA = (24, 132, 98)
COBRA_MORTA = (120, 126, 140)
COMIDA = (242, 82, 96)
FOLHA = (98, 201, 92)
OURO = (255, 202, 64)
GELO = (104, 186, 255)
PERIGO = (240, 84, 96)
PAINEL = (22, 26, 39)
BOTAO = (39, 46, 67)
BOTAO_ATIVO = (66, 168, 104)

CIMA, BAIXO, ESQUERDA, DIREITA = (0, -1), (0, 1), (-1, 0), (1, 0)
TECLAS_DIRECAO = {
    pygame.K_UP: CIMA, pygame.K_w: CIMA,
    pygame.K_DOWN: BAIXO, pygame.K_s: BAIXO,
    pygame.K_LEFT: ESQUERDA, pygame.K_a: ESQUERDA,
    pygame.K_RIGHT: DIREITA, pygame.K_d: DIREITA,
}
TECLAS_CONFIRMAR = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


def lerp(a, b, t):
    return a + (b - a) * t


def misturar_cor(cor_a, cor_b, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(cor_a, cor_b))


def oposta(direcao):
    return (-direcao[0], -direcao[1])


_fontes = {}


def fonte(tamanho, negrito=True):
    tamanho = max(12, int(tamanho))
    chave = (tamanho, negrito)
    if chave not in _fontes:
        _fontes[chave] = pygame.font.SysFont("segoeui,trebuchetms,arial", tamanho, bold=negrito)
    return _fontes[chave]


def desenhar_texto(superficie, conteudo, tamanho, cor, posicao, ancora="center", negrito=True, sombra=True):
    f = fonte(tamanho, negrito)
    imagem = f.render(conteudo, True, cor)
    retangulo = imagem.get_rect(**{ancora: posicao})
    if sombra:
        imagem_sombra = f.render(conteudo, True, (0, 0, 0))
        imagem_sombra.set_alpha(110)
        superficie.blit(imagem_sombra, retangulo.move(2, 3))
    superficie.blit(imagem, retangulo)
    return retangulo


_brilhos = {}


def brilho(raio, cor):
    raio = max(2, int(raio))
    chave = (raio, cor)
    if chave not in _brilhos:
        superficie = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
        for r in range(raio, 0, -1):
            alfa = int(70 * (1 - r / raio) ** 1.6)
            pygame.draw.circle(superficie, (*cor, alfa), (raio, raio), r)
        _brilhos[chave] = superficie
    return _brilhos[chave]


def pontos_estrela(cx, cy, raio_externo, raio_interno, angulo):
    pontos = []
    for k in range(10):
        raio = raio_externo if k % 2 == 0 else raio_interno
        a = angulo + k * math.pi / 5 - math.pi / 2
        pontos.append((cx + math.cos(a) * raio, cy + math.sin(a) * raio))
    return pontos


def carregar_recorde():
    try:
        return int(json.loads(ARQUIVO_RECORDE.read_text(encoding="utf-8"))["recorde"])
    except (OSError, ValueError, KeyError, TypeError):
        return 0


def salvar_recorde(valor):
    try:
        ARQUIVO_RECORDE.write_text(json.dumps({"recorde": valor}), encoding="utf-8")
    except OSError:
        pass


def criar_icone():
    icone = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.rect(icone, COBRA_CABECA, (2, 2, 28, 28), border_radius=9)
    for x in (11, 21):
        pygame.draw.circle(icone, (255, 255, 255), (x, 13), 4)
        pygame.draw.circle(icone, (20, 24, 34), (x + 1, 13), 2)
    return icone


class Sons:
    def __init__(self):
        self.ligado = True
        self.sons = {}
        config = pygame.mixer.get_init()
        if not config:
            return
        frequencia, _, canais = config
        try:
            self.sons = {
                "comer": self._criar(frequencia, canais, [(520, 900, 0.07)], 0.30),
                "bonus": self._criar(frequencia, canais, [(660, 660, 0.06), (880, 880, 0.06), (1320, 1320, 0.10)], 0.25),
                "lento": self._criar(frequencia, canais, [(1100, 900, 0.08), (700, 260, 0.40)], 0.28),
                "morte":self._criar(frequencia, canais, [(320, 60, 0.50)], 0.30, quadrada=True),
                "clique": self._criar(frequencia, canais, [(750, 750, 0.03)], 0.18),
            }
        except pygame.error:
            self.sons = {}

    @staticmethod
    def _criar(frequencia, canais, notas, volume, quadrada=False):
        amostras = array("h")
        for freq_inicial, freq_final, duracao in notas:
            total = int(frequencia * duracao)
            fase = 0.0
            for i in range(total):
                progresso = i / total
                fase += 2 * math.pi * lerp(freq_inicial, freq_final, progresso) / frequencia
                onda = math.sin(fase)
                if quadrada:
                    onda = 0.5 if onda >= 0 else -0.5
                envelope = min(1.0, i / (frequencia * 0.004)) * (1 - progresso) ** 1.5
                valor = int(32767 * volume * onda * envelope)
                amostras.extend([valor] * canais)
        return pygame.mixer.Sound(buffer=amostras.tobytes())

    def tocar(self, nome):
        if self.ligado and nome in self.sons:
            self.sons[nome].play()

    def alternar(self):
        self.ligado = not self.ligado


class Jogo:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption("Snake Game Python")
        pygame.display.set_icon(criar_icone())

        self.tela = pygame.display.set_mode(JANELA_INICIAL, pygame.RESIZABLE)
        self.relogio = pygame.time.Clock()
        self.sons = Sons()
        self.recorde = carregar_recorde()

        self.tela_cheia = False
        self.tamanho_janela = JANELA_INICIAL
        self.tamanho_layout = None

        self.rodando = True
        self.tempo = 0.0
        self.botoes = []
        self.selecionado = 0

        self.demo = True
        self.iniciar_demo()
        self.ir_para("menu")

    def atualizar_layout(self):
        self.tela = pygame.display.get_surface()
        largura, altura = self.tela.get_size()
        if (largura, altura) == self.tamanho_layout:
            return
        self.tamanho_layout = (largura, altura)

        self.escala = max(0.4, min(largura / JANELA_INICIAL[0], altura / JANELA_INICIAL[1]))
        altura_hud = int(70 * self.escala)
        margem = int(18 * self.escala)
        self.celula = max(6, min((largura - 2 * margem) // COLUNAS, (altura - altura_hud - 2 * margem) // LINHAS))

        largura_tab, altura_tab = self.celula * COLUNAS, self.celula * LINHAS
        x = (largura - largura_tab) // 2
        y = altura_hud + (altura - altura_hud - altura_tab) // 2
        self.tabuleiro = pygame.Rect(x, y, largura_tab, altura_tab)
        self.altura_hud = altura_hud

        self.fundo_tabuleiro = self._criar_fundo_tabuleiro()
        self.tinta_lentidao = pygame.Surface(self.tabuleiro.size)
        self.tinta_lentidao.fill(GELO)
        self.escurecer = pygame.Surface((largura, altura))
        self.escurecer.fill((8, 10, 16))
        self.escurecer.set_alpha(175)
        self.escurecer_menu = pygame.Surface((largura, altura))
        self.escurecer_menu.fill((8, 10, 16))
        self.escurecer_menu.set_alpha(150)

    def _criar_fundo_tabuleiro(self):
        c = self.celula
        borda = max(3, c // 4)
        superficie = pygame.Surface((self.tabuleiro.w + borda * 2, self.tabuleiro.h + borda * 2), pygame.SRCALPHA)
        pygame.draw.rect(superficie, BORDA, superficie.get_rect(), border_radius=borda * 2)
        area = pygame.Rect(borda, borda, self.tabuleiro.w, self.tabuleiro.h)
        pygame.draw.rect(superficie, TABULEIRO_A, area, border_radius=borda)
        for linha in range(LINHAS):
            for coluna in range(COLUNAS):
                if (linha + coluna) % 2:
                    pygame.draw.rect(superficie, TABULEIRO_B, (borda + coluna * c, borda + linha * c, c, c))
        return superficie

    def alternar_tela_cheia(self):
        self.tela_cheia = not self.tela_cheia
        if self.tela_cheia:
            self.tamanho_janela = self.tela.get_size()
            tamanho = pygame.display.get_desktop_sizes()[0]
            self.tela = pygame.display.set_mode(tamanho, pygame.NOFRAME)
            self._posicionar_janela((0, 0))
        else:
            self.tela = pygame.display.set_mode(self.tamanho_janela, pygame.RESIZABLE)
            self._posicionar_janela(pygame.WINDOWPOS_CENTERED)
        self.atualizar_layout()

    @staticmethod
    def _posicionar_janela(posicao):
        try:
            pygame.Window.from_display_module().position = posicao
        except (AttributeError, pygame.error):
            pass

    def centro_celula(self, x, y, deslocamento=(0, 0)):
        c = self.celula
        return (
            self.tabuleiro.x + (x + 0.5) * c + deslocamento[0],
            self.tabuleiro.y + (y + 0.5) * c + deslocamento[1],
        )

    def ir_para(self, estado):
        self.estado = estado
        self.selecionado = 0
        self.botoes = []

    def nova_partida(self):
        self.reiniciar_cobra()
        self.demo = False
        self.ir_para("jogando")

    def iniciar_demo(self):
        self.reiniciar_cobra()
        self.demo = True
        self.aguardando = False

    def reiniciar_cobra(self):
        cx, cy = COLUNAS // 2 - 4, LINHAS // 2
        self.cobra = [(cx - i, cy) for i in range(TAMANHO_INICIAL)]
        self.anterior = list(self.cobra)
        self.cresceu = False
        self.crescer = 0
        self.direcao = DIREITA
        self.fila_direcoes = deque()
        self.aguardando = True
        self.acumulador = 0.0

        self.pontos = 0
        self.novo_recorde = False

        self.bonus = None
        self.bonus_tempo = 0.0
        self.item_lento = None
        self.item_lento_tempo = 0.0
        self.lentidao = 0.0
        self.comida = None
        self.comida = self.sortear_celula()
        self.tempo_comida = 0.0

        self.particulas = []
        self.tremor = 0.0
        self.tempo_morte = 0.0

    @property
    def crescimento(self):
        return len(self.cobra) - TAMANHO_INICIAL

    @property
    def intervalo(self):
        base = max(INTERVALO_MINIMO, INTERVALO_INICIAL * FATOR_ACELERACAO ** self.crescimento)
        return base * (1 + (LENTIDAO_FATOR - 1) * self.intensidade_lentidao)

    @property
    def intensidade_lentidao(self):
        return min(1.0, self.lentidao / 0.6)

    @property
    def multiplicador_velocidade(self):
        return INTERVALO_INICIAL / self.intervalo

    @property
    def em_movimento(self):
        if self.demo:
            return self.estado in ("menu", "ajuda")
        return self.estado == "jogando" and not self.aguardando

    def sortear_celula(self):
        ocupadas = set(self.cobra)
        ocupadas.add(self.comida)
        ocupadas.add(self.bonus)
        ocupadas.add(self.item_lento)
        livres = [(x, y) for x in range(COLUNAS) for y in range(LINHAS) if (x, y) not in ocupadas]
        return random.choice(livres) if livres else None

    def tocar(self, nome):
        if not self.demo:
            self.sons.tocar(nome)

    @staticmethod
    def dentro(celula):
        return 0 <= celula[0] < COLUNAS and 0 <= celula[1] < LINHAS

    def area_alcancavel(self, inicio, bloqueadas, limite):
        vistas = {inicio}
        pilha = [inicio]
        while pilha and len(vistas) < limite:
            x, y = pilha.pop()
            for dx, dy in (CIMA, BAIXO, ESQUERDA, DIREITA):
                vizinha = (x + dx, y + dy)
                if vizinha not in vistas and vizinha not in bloqueadas and self.dentro(vizinha):
                    vistas.add(vizinha)
                    pilha.append(vizinha)
        return len(vistas)

    def escolher_direcao_demo(self):
        cabeca = self.cobra[0]
        alvo = self.bonus or self.item_lento or self.comida or cabeca
        corpo = set(self.cobra[:-1])
        opcoes = []
        for direcao in (CIMA, BAIXO, ESQUERDA, DIREITA):
            if direcao == oposta(self.direcao):
                continue
            vizinha = (cabeca[0] + direcao[0], cabeca[1] + direcao[1])
            if not self.dentro(vizinha) or vizinha in corpo:
                continue
            espaco = self.area_alcancavel(vizinha, corpo, len(self.cobra) + 2)
            distancia = abs(vizinha[0] - alvo[0]) + abs(vizinha[1] - alvo[1])
            opcoes.append((espaco <= len(self.cobra), distancia, random.random(), direcao))
        return min(opcoes)[3] if opcoes else self.direcao

    def enfileirar_direcao(self, nova):
        if self.aguardando:
            if nova == oposta(self.direcao):
                return
            self.aguardando = False
        ultima = self.fila_direcoes[-1] if self.fila_direcoes else self.direcao
        if nova in (ultima, oposta(ultima)) or len(self.fila_direcoes) >= 3:
            return
        self.fila_direcoes.append(nova)

    def passo(self):
        if self.demo:
            self.direcao = self.escolher_direcao_demo()
        elif self.fila_direcoes:
            self.direcao = self.fila_direcoes.popleft()

        cabeca_x, cabeca_y = self.cobra[0]
        nova = (cabeca_x + self.direcao[0], cabeca_y + self.direcao[1])
        vai_crescer = self.crescer > 0
        corpo = self.cobra if vai_crescer else self.cobra[:-1]

        if not (0 <= nova[0] < COLUNAS and 0 <= nova[1] < LINHAS) or nova in corpo:
            self.morrer()
            return

        self.anterior = list(self.cobra)
        self.cobra.insert(0, nova)
        self.cresceu = vai_crescer
        if vai_crescer:
            self.crescer -= 1
        else:
            self.cobra.pop()

        if nova == self.comida:
            self.comer()
        elif nova == self.bonus:
            self.comer_bonus()
        elif nova == self.item_lento:
            self.pegar_relogio()

        if self.demo and self.crescimento >= DEMO_CRESCIMENTO_MAXIMO:
            self.iniciar_demo()

    def comer(self):
        self.pontos += 1
        self.crescer += 1
        self.tocar("comer")
        self.explodir(self.comida, COMIDA, 14)
        self.comida = self.sortear_celula()
        self.tempo_comida = 0.0
        if self.comida is None:
            self.morrer()
            return
        if self.bonus is None and random.random() < BONUS_CHANCE:
            self.bonus = self.sortear_celula()
            self.bonus_tempo = BONUS_DURACAO
        if self.item_lento is None and self.lentidao <= 0 and random.random() < RELOGIO_CHANCE:
            self.item_lento = self.sortear_celula()
            self.item_lento_tempo = RELOGIO_DURACAO

    def pegar_relogio(self):
        self.lentidao = LENTIDAO_DURACAO
        self.tocar("lento")
        self.explodir(self.item_lento, GELO, 24)
        self.item_lento = None

    def comer_bonus(self):
        self.pontos += BONUS_PONTOS
        self.crescer += 2
        self.tocar("bonus")
        self.explodir(self.bonus, OURO, 24)
        self.bonus = None

    def morrer(self):
        if self.demo:
            cabeca = self.cobra[0]
            self.iniciar_demo()
            self.explodir(cabeca, PERIGO, 20)
            return
        self.anterior = list(self.cobra)
        self.cresceu = False
        self.tremor = 0.35
        self.tempo_morte = 0.9
        self.sons.tocar("morte")
        self.explodir(self.cobra[0], PERIGO, 20)
        if self.pontos > self.recorde:
            self.recorde = self.pontos
            self.novo_recorde = True
            salvar_recorde(self.recorde)
        self.ir_para("morrendo")

    def explodir(self, celula, cor, quantidade):
        x, y = celula[0] + 0.5, celula[1] + 0.5
        for _ in range(quantidade):
            angulo = random.uniform(0, math.tau)
            velocidade = random.uniform(2, 7)
            vida = random.uniform(0.35, 0.7)
            self.particulas.append([x, y, math.cos(angulo) * velocidade, math.sin(angulo) * velocidade, vida, vida, cor])

    def atualizar(self, dt):
        self.tempo += dt
        if self.estado == "pausado":
            return

        if self.em_movimento:
            self.acumulador += dt
            while self.em_movimento and self.acumulador >= self.intervalo:
                self.acumulador -= self.intervalo
                self.passo()
            if self.bonus is not None:
                self.bonus_tempo -= dt
                if self.bonus_tempo <= 0:
                    self.bonus = None
            if self.item_lento is not None:
                self.item_lento_tempo -= dt
                if self.item_lento_tempo <= 0:
                    self.item_lento = None
            self.lentidao = max(0.0, self.lentidao - dt)
        elif self.estado == "morrendo":
            self.tempo_morte -= dt
            if self.tempo_morte <= 0:
                self.ir_para("game_over")

        self.tempo_comida += dt
        self.tremor = max(0.0, self.tremor - dt)
        for p in self.particulas:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[2] *= 0.92
            p[3] *= 0.92
            p[4] -= dt
        self.particulas = [p for p in self.particulas if p[4] > 0]

    def tratar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.rodando = False
            elif evento.type in (pygame.VIDEORESIZE, pygame.WINDOWSIZECHANGED):
                self.atualizar_layout()
            elif evento.type == pygame.WINDOWFOCUSLOST and self.estado == "jogando":
                self.ir_para("pausado")
            elif evento.type == pygame.KEYDOWN:
                self.tratar_tecla(evento.key)
            elif evento.type == pygame.MOUSEMOTION:
                for indice, (retangulo, _) in enumerate(self.botoes):
                    if retangulo.collidepoint(evento.pos):
                        self.selecionado = indice
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                for retangulo, acao in self.botoes:
                    if retangulo.collidepoint(evento.pos):
                        self.executar(acao)
                        break

    def tratar_tecla(self, tecla):
        if tecla == pygame.K_F11:
            self.alternar_tela_cheia()
            return
        if tecla == pygame.K_m:
            self.sons.alternar()
            return

        if self.estado == "jogando":
            if tecla in (pygame.K_ESCAPE, pygame.K_p):
                self.ir_para("pausado")
            elif tecla in TECLAS_DIRECAO:
                self.enfileirar_direcao(TECLAS_DIRECAO[tecla])
        elif self.estado in ("menu", "ajuda", "game_over", "pausado"):
            if tecla in TECLAS_CONFIRMAR and self.botoes:
                self.executar(self.botoes[self.selecionado][1])
            elif self.estado == "pausado" and tecla in (pygame.K_ESCAPE, pygame.K_p):
                self.executar("continuar")
            elif self.estado == "pausado" and tecla == pygame.K_q:
                self.executar("menu")
            elif tecla == pygame.K_ESCAPE:
                self.executar("sair" if self.estado == "menu" else "menu")
            elif tecla in TECLAS_DIRECAO or tecla == pygame.K_TAB:
                passo = -1 if TECLAS_DIRECAO.get(tecla) in (ESQUERDA, CIMA) else 1
                if self.botoes:
                    self.selecionado = (self.selecionado + passo) % len(self.botoes)
                    self.sons.tocar("clique")

    def executar(self, acao):
        self.sons.tocar("clique")
        if acao in ("jogar", "reiniciar"):
            self.nova_partida()
        elif acao == "continuar":
            self.ir_para("jogando")
        elif acao == "menu":
            if not self.demo:
                self.iniciar_demo()
            self.ir_para("menu")
        elif acao == "ajuda":
            self.ir_para("ajuda")
        elif acao == "som":
            self.sons.alternar()
        elif acao == "sair":
            self.rodando = False

    def desenhar(self):
        self.tela.fill(FUNDO)
        self.botoes = []

        deslocamento = (0, 0)
        if self.tremor > 0:
            forca = self.tremor * self.celula * 0.8
            deslocamento = (random.uniform(-forca, forca), random.uniform(-forca, forca))

        if not self.demo:
            self.desenhar_hud()
        self.desenhar_tabuleiro(deslocamento)
        self.desenhar_efeito_lentidao()
        self.desenhar_comida(deslocamento)
        self.desenhar_bonus(deslocamento)
        self.desenhar_item_lento(deslocamento)
        self.desenhar_cobra(deslocamento)
        self.desenhar_particulas(deslocamento)
        self.desenhar_barra_lentidao()

        if self.estado == "menu":
            self.desenhar_menu()
        elif self.estado == "ajuda":
            self.desenhar_ajuda()
        elif self.estado == "jogando" and self.aguardando:
            self.desenhar_dica_inicio()
        elif self.estado == "pausado":
            self.desenhar_pausa()
        elif self.estado == "game_over":
            self.desenhar_game_over()

    def desenhar_tabuleiro(self, deslocamento):
        borda = max(3, self.celula // 4)
        self.tela.blit(self.fundo_tabuleiro, (self.tabuleiro.x - borda + deslocamento[0], self.tabuleiro.y - borda + deslocamento[1]))

    def desenhar_hud(self):
        u = self.escala
        y = self.tabuleiro.top - self.altura_hud // 2
        esquerda, direita = self.tabuleiro.left + 4, self.tabuleiro.right - 4

        desenhar_texto(self.tela, "PONTOS", 15 * u, TEXTO_SUAVE, (esquerda, y - 13 * u), "midleft", sombra=False)
        desenhar_texto(self.tela, str(self.pontos), 30 * u, TEXTO, (esquerda, y + 10 * u), "midleft")

        desenhar_texto(self.tela, "RECORDE", 15 * u, TEXTO_SUAVE, (direita, y - 13 * u), "midright", sombra=False)
        desenhar_texto(self.tela, str(self.recorde), 30 * u, OURO, (direita, y + 10 * u), "midright")

        centro = self.tela.get_width() // 2
        maximo = INTERVALO_INICIAL / INTERVALO_MINIMO
        fracao = min(1.0, max(0.0, (self.multiplicador_velocidade - 1) / (maximo - 1)))
        if self.lentidao > 0:
            cor = GELO
        elif fracao < 0.5:
            cor = misturar_cor(COBRA_CABECA, OURO, fracao * 2)
        else:
            cor = misturar_cor(OURO, PERIGO, fracao * 2 - 1)
        desenhar_texto(self.tela, "VELOCIDADE", 15 * u, TEXTO_SUAVE, (centro, y - 13 * u), sombra=False)
        desenhar_texto(self.tela, f"{self.multiplicador_velocidade:.1f}x", 30 * u, cor, (centro, y + 10 * u))
        if not self.sons.ligado:
            desenhar_texto(self.tela, "som desligado (M)", 13 * u, TEXTO_SUAVE, (centro + 70 * u, y + 10 * u), "midleft", negrito=False, sombra=False)

    def caminho_cobra(self):
        if self.em_movimento:
            t = min(1.0, self.acumulador / self.intervalo)
        else:
            t = 1.0
        cabeca = (lerp(self.anterior[0][0], self.cobra[0][0], t), lerp(self.anterior[0][1], self.cobra[0][1], t))
        if len(self.cobra) == 1:
            return [cabeca]
        if self.cresceu:
            cauda = self.cobra[-1]
        else:
            cauda = (lerp(self.anterior[-1][0], self.cobra[-1][0], t), lerp(self.anterior[-1][1], self.cobra[-1][1], t))
        return [cabeca, *self.cobra[1:-1], cauda]

    def desenhar_cobra(self, deslocamento):
        c = self.celula
        pontos = [self.centro_celula(x, y, deslocamento) for x, y in self.caminho_cobra()]
        total = len(pontos)
        morta = self.estado in ("morrendo", "game_over")
        piscando = self.estado == "morrendo" and int(self.tempo * 12) % 2 == 0

        for i in range(total - 2, -1, -1):
            progresso = i / max(1, total - 1)
            if morta:
                cor = PERIGO if piscando else misturar_cor(COBRA_MORTA, (70, 74, 86), progresso)
            else:
                cor = misturar_cor(COBRA_CABECA, COBRA_CAUDA, progresso)
            espessura = c * lerp(0.84, 0.5, progresso)
            (x1, y1), (x2, y2) = pontos[i], pontos[i + 1]
            retangulo = pygame.Rect(0, 0, abs(x2 - x1) + espessura, abs(y2 - y1) + espessura)
            retangulo.center = ((x1 + x2) / 2, (y1 + y2) / 2)
            pygame.draw.rect(self.tela, cor, retangulo, border_radius=int(espessura / 2))

        self.desenhar_cabeca(pontos[0], morta, piscando)

    def desenhar_cabeca(self, posicao, morta, piscando):
        c = self.celula
        hx, hy = posicao
        dx, dy = self.direcao
        px, py = -dy, dx

        cor = (PERIGO if piscando else COBRA_MORTA) if morta else COBRA_CABECA
        if not morta:
            halo = brilho(c * 1.1, COBRA_CABECA)
            self.tela.blit(halo, halo.get_rect(center=(hx, hy)))
        pygame.draw.circle(self.tela, cor, (hx, hy), c * 0.47)

        for lado in (-1, 1):
            ox = hx + dx * c * 0.14 + px * c * 0.21 * lado
            oy = hy + dy * c * 0.14 + py * c * 0.21 * lado
            if morta:
                r = c * 0.09
                pygame.draw.line(self.tela, (30, 32, 40), (ox - r, oy - r), (ox + r, oy + r), max(1, c // 12))
                pygame.draw.line(self.tela, (30, 32, 40), (ox - r, oy + r), (ox + r, oy - r), max(1, c // 12))
            else:
                pygame.draw.circle(self.tela, (255, 255, 255), (ox, oy), c * 0.13)
                pygame.draw.circle(self.tela, (20, 24, 34), (ox + dx * c * 0.05, oy + dy * c * 0.05), c * 0.07)

    def desenhar_comida(self, deslocamento):
        if self.comida is None:
            return
        surgimento = min(1.0, self.tempo_comida / 0.25)
        surgimento = 1 - (1 - surgimento) ** 3
        self.desenhar_maca(self.centro_celula(*self.comida, deslocamento), self.celula, surgimento)

    def desenhar_maca(self, centro, tamanho, escala=1.0):
        cx, cy = centro
        pulso = 1 + 0.07 * math.sin(self.tempo * 5)
        raio = tamanho * 0.36 * pulso * escala

        halo = brilho(tamanho * 1.2, COMIDA)
        self.tela.blit(halo, halo.get_rect(center=(cx, cy)))
        pygame.draw.circle(self.tela, COMIDA, (cx, cy + raio * 0.08), raio)
        pygame.draw.circle(self.tela, (255, 170, 176), (cx - raio * 0.38, cy - raio * 0.3), raio * 0.24)
        pygame.draw.line(self.tela, (110, 72, 44), (cx, cy - raio * 0.75), (cx + raio * 0.15, cy - raio * 1.2), max(1, int(tamanho) // 12))
        folha = pygame.Rect(0, 0, raio * 0.7, raio * 0.38)
        folha.midleft = (cx + raio * 0.1, cy - raio * 1.0)
        pygame.draw.ellipse(self.tela, FOLHA, folha)

    def desenhar_estrela(self, centro, tamanho):
        cx, cy = centro
        halo = brilho(tamanho * 1.4, OURO)
        self.tela.blit(halo, halo.get_rect(center=(cx, cy)))
        pulso = 1 + 0.1 * math.sin(self.tempo * 7)
        pygame.draw.polygon(self.tela, OURO, pontos_estrela(cx, cy, tamanho * 0.45 * pulso, tamanho * 0.2 * pulso, self.tempo * 1.5))

    def desenhar_bonus(self, deslocamento):
        if self.bonus is None:
            return
        if self.bonus_tempo < 1.5 and int(self.tempo * 10) % 2 == 0:
            return
        c = self.celula
        cx, cy = self.centro_celula(*self.bonus, deslocamento)
        self.desenhar_estrela((cx, cy), c)

        fracao = max(0.0, self.bonus_tempo / BONUS_DURACAO)
        anel = pygame.Rect(0, 0, c * 1.3, c * 1.3)
        anel.center = (cx, cy)
        pygame.draw.arc(self.tela, OURO, anel, math.pi / 2, math.pi / 2 + math.tau * fracao, max(2, c // 10))

    def desenhar_relogio(self, centro, tamanho):
        cx, cy = centro
        halo = brilho(tamanho * 1.3, GELO)
        self.tela.blit(halo, halo.get_rect(center=(cx, cy)))
        raio = tamanho * 0.4 * (1 + 0.06 * math.sin(self.tempo * 4))
        pygame.draw.rect(self.tela, GELO, (cx - raio * 0.25, cy - raio * 1.32, raio * 0.5, raio * 0.3), border_radius=max(1, int(raio * 0.1)))
        pygame.draw.circle(self.tela, GELO, (cx, cy), raio)
        pygame.draw.circle(self.tela, (20, 36, 62), (cx, cy), raio * 0.78)
        espessura = max(1, int(tamanho / 14))
        angulo_minutos = self.tempo * 2.2
        angulo_horas = self.tempo * 0.4
        pygame.draw.line(self.tela, (235, 245, 255), (cx, cy), (cx + math.sin(angulo_minutos) * raio * 0.62, cy - math.cos(angulo_minutos) * raio * 0.62), espessura)
        pygame.draw.line(self.tela, GELO, (cx, cy), (cx + math.sin(angulo_horas) * raio * 0.42, cy - math.cos(angulo_horas) * raio * 0.42), espessura + 1)
        pygame.draw.circle(self.tela, (235, 245, 255), (cx, cy), max(1, raio * 0.1))

    def desenhar_item_lento(self, deslocamento):
        if self.item_lento is None:
            return
        if self.item_lento_tempo < 1.5 and int(self.tempo * 10) % 2 == 0:
            return
        c = self.celula
        cx, cy = self.centro_celula(*self.item_lento, deslocamento)
        self.desenhar_relogio((cx, cy), c)
        fracao = max(0.0, self.item_lento_tempo / RELOGIO_DURACAO)
        anel = pygame.Rect(0, 0, c * 1.3, c * 1.3)
        anel.center = (cx, cy)
        pygame.draw.arc(self.tela, GELO, anel, math.pi / 2, math.pi / 2 + math.tau * fracao, max(2, c // 10))

    def desenhar_efeito_lentidao(self):
        if self.lentidao <= 0:
            return
        intensidade = self.intensidade_lentidao
        self.tinta_lentidao.set_alpha(int(38 * intensidade))
        self.tela.blit(self.tinta_lentidao, self.tabuleiro)
        pulso = 0.6 + 0.4 * math.sin(self.tempo * 5)
        cor = misturar_cor(BORDA, GELO, intensidade * pulso)
        borda = max(3, self.celula // 4)
        pygame.draw.rect(self.tela, cor, self.tabuleiro.inflate(borda * 2, borda * 2), borda, border_radius=borda * 2)

    def desenhar_barra_lentidao(self):
        if self.lentidao <= 0 or self.demo:
            return
        u = self.escala
        caixa = pygame.Rect(0, 0, 210 * u, 28 * u)
        caixa.center = (self.tabuleiro.centerx, self.tabuleiro.top + 26 * u)
        pygame.draw.rect(self.tela, PAINEL, caixa, border_radius=caixa.h // 2)
        pygame.draw.rect(self.tela, GELO, caixa, max(1, int(2 * u)), border_radius=caixa.h // 2)
        self.desenhar_relogio((caixa.left + 18 * u, caixa.centery), 26 * u)
        trilho = pygame.Rect(caixa.left + 38 * u, 0, caixa.w - 52 * u, 8 * u)
        trilho.centery = caixa.centery
        pygame.draw.rect(self.tela, BOTAO, trilho, border_radius=trilho.h // 2)
        cheio = trilho.copy()
        cheio.w = max(cheio.h, trilho.w * self.lentidao / LENTIDAO_DURACAO)
        pygame.draw.rect(self.tela, GELO, cheio, border_radius=trilho.h // 2)

    def desenhar_particulas(self, deslocamento):
        for x, y, _, _, vida, vida_total, cor in self.particulas:
            px = self.tabuleiro.x + x * self.celula + deslocamento[0]
            py = self.tabuleiro.y + y * self.celula + deslocamento[1]
            pygame.draw.circle(self.tela, cor, (px, py), self.celula * 0.16 * (vida / vida_total))

    def desenhar_botoes(self, opcoes, centro_y, vertical=False):
        u = self.escala
        if vertical:
            largura_minima, altura, espaco = 300 * u, 50 * u, 12 * u
        else:
            largura_minima, altura, espaco = 220 * u, 56 * u, 20 * u

        tamanho_icone, folga = 18 * u, 12 * u
        conteudos = [tamanho_icone + folga + fonte(23 * u).size(rotulo)[0] for rotulo, _ in opcoes]
        larguras = [max(largura_minima, conteudo + 56 * u) for conteudo in conteudos]
        if vertical:
            larguras = [max(larguras)] * len(larguras)
            x = self.tela.get_width() / 2 - larguras[0] / 2
        else:
            x = self.tela.get_width() / 2 - (sum(larguras) + (len(opcoes) - 1) * espaco) / 2

        for indice, ((rotulo, acao), largura, largura_conteudo) in enumerate(zip(opcoes, larguras, conteudos)):
            ativo = indice == self.selecionado
            retangulo = pygame.Rect(0, 0, largura, altura)
            retangulo.center = (x + largura / 2, centro_y)
            if ativo:
                retangulo.inflate_ip(10 * u, 6 * u)
            raio = int(14 * u)
            sombra = retangulo.move(0, 5 * u)
            pygame.draw.rect(self.tela, (6, 8, 12), sombra, border_radius=raio)
            pygame.draw.rect(self.tela, BOTAO_ATIVO if ativo else BOTAO, retangulo, border_radius=raio)
            pygame.draw.rect(self.tela, COBRA_CABECA if ativo else BORDA, retangulo, max(2, int(2 * u)), border_radius=raio)
            cor_icone = TEXTO if ativo else TEXTO_SUAVE
            inicio = retangulo.centerx - largura_conteudo / 2
            self.desenhar_icone(acao, (inicio + tamanho_icone / 2, retangulo.centery), tamanho_icone, cor_icone)
            desenhar_texto(self.tela, rotulo, 23 * u, TEXTO, (inicio + tamanho_icone + folga, retangulo.centery), "midleft")
            if ativo and vertical:
                deslize = 4 * u * math.sin(self.tempo * 6)
                ponta = retangulo.left - 14 * u + deslize
                pygame.draw.polygon(self.tela, COBRA_CABECA, [
                    (ponta, retangulo.centery),
                    (ponta - 12 * u, retangulo.centery - 9 * u),
                    (ponta - 12 * u, retangulo.centery + 9 * u),
                ])
            self.botoes.append((retangulo, acao))
            if vertical:
                centro_y += altura + espaco
            else:
                x += largura + espaco

    def desenhar_icone(self, nome, centro, tamanho, cor):
        cx, cy = centro
        r = tamanho / 2
        espessura = max(2, int(tamanho / 8))
        if nome in ("jogar", "continuar"):
            pygame.draw.polygon(self.tela, cor, [(cx - r * 0.6, cy - r), (cx - r * 0.6, cy + r), (cx + r, cy)])
        elif nome == "ajuda":
            pygame.draw.circle(self.tela, cor, (cx, cy), r + 1, espessura)
            desenhar_texto(self.tela, "?", tamanho * 0.95, cor, (cx, cy), sombra=False)
        elif nome == "som":
            pygame.draw.polygon(self.tela, cor, [
                (cx - r, cy - r * 0.35), (cx - r * 0.45, cy - r * 0.35), (cx + r * 0.1, cy - r),
                (cx + r * 0.1, cy + r), (cx - r * 0.45, cy + r * 0.35), (cx - r, cy + r * 0.35),
            ])
            if self.sons.ligado:
                arco = pygame.Rect(0, 0, r * 1.4, r * 1.6)
                arco.center = (cx + r * 0.2, cy)
                pygame.draw.arc(self.tela, cor, arco, -math.pi / 3, math.pi / 3, espessura)
            else:
                pygame.draw.line(self.tela, PERIGO, (cx + r * 0.35, cy - r * 0.45), (cx + r * 1.1, cy + r * 0.45), espessura)
                pygame.draw.line(self.tela, PERIGO, (cx + r * 0.35, cy + r * 0.45), (cx + r * 1.1, cy - r * 0.45), espessura)
        elif nome == "sair":
            pygame.draw.line(self.tela, cor, (cx - r * 0.75, cy - r * 0.75), (cx + r * 0.75, cy + r * 0.75), espessura + 1)
            pygame.draw.line(self.tela, cor, (cx - r * 0.75, cy + r * 0.75), (cx + r * 0.75, cy - r * 0.75), espessura + 1)
        elif nome == "menu":
            for dy in (-r * 0.65, 0, r * 0.65):
                pygame.draw.line(self.tela, cor, (cx - r * 0.8, cy + dy), (cx + r * 0.8, cy + dy), espessura)
        elif nome == "reiniciar":
            arco = pygame.Rect(0, 0, r * 1.8, r * 1.8)
            arco.center = (cx, cy)
            pygame.draw.arc(self.tela, cor, arco, math.pi * 0.1, math.pi * 1.75, espessura)
            ponta = (cx + r * 0.9 * math.cos(math.pi * 0.1), cy - r * 0.9 * math.sin(math.pi * 0.1))
            pygame.draw.polygon(self.tela, cor, [
                (ponta[0] - r * 0.45, ponta[1] - r * 0.15),
                (ponta[0] + r * 0.45, ponta[1] - r * 0.15),
                (ponta[0], ponta[1] + r * 0.45),
            ])

    def desenhar_cartao(self, rotulo, valor, cor, centro, largura):
        u = self.escala
        cartao = pygame.Rect(0, 0, largura, 66 * u)
        cartao.center = centro
        pygame.draw.rect(self.tela, BOTAO, cartao, border_radius=int(12 * u))
        pygame.draw.rect(self.tela, BORDA, cartao, max(1, int(2 * u)), border_radius=int(12 * u))
        desenhar_texto(self.tela, rotulo, 13 * u, TEXTO_SUAVE, (cartao.centerx, cartao.top + 18 * u), sombra=False)
        desenhar_texto(self.tela, valor, 26 * u, cor, (cartao.centerx, cartao.bottom - 23 * u))

    def desenhar_painel(self, largura, altura):
        painel = pygame.Rect(0, 0, largura, altura)
        painel.center = self.tabuleiro.center
        raio = int(22 * self.escala)
        pygame.draw.rect(self.tela, (6, 8, 12), painel.move(0, 8 * self.escala), border_radius=raio)
        pygame.draw.rect(self.tela, PAINEL, painel, border_radius=raio)
        pygame.draw.rect(self.tela, BORDA, painel, max(2, int(2 * self.escala)), border_radius=raio)
        return painel

    def desenhar_dica_inicio(self):
        u = self.escala
        alfa = int(160 + 95 * math.sin(self.tempo * 4))
        cx, cy = self.tabuleiro.centerx, self.tabuleiro.bottom - 50 * u
        texto = fonte(22 * u).render("Use as setas ou WASD para começar", True, TEXTO)
        texto.set_alpha(alfa)
        fundo = texto.get_rect(center=(cx, cy)).inflate(36 * u, 18 * u)
        pygame.draw.rect(self.tela, PAINEL, fundo, border_radius=int(fundo.h / 2))
        self.tela.blit(texto, texto.get_rect(center=(cx, cy)))

    def desenhar_pausa(self):
        u = self.escala
        self.tela.blit(self.escurecer, (0, 0))
        largura = min(self.tela.get_width() * 0.92, 470 * u)
        painel = self.desenhar_painel(largura, min(self.tela.get_height() * 0.95, 500 * u))
        cx = painel.centerx

        titulo_y = painel.top + 50 * u
        texto = fonte(44 * u).render("PAUSADO", True, TEXTO)
        largura_bloco = 30 * u + 16 * u + texto.get_width()
        inicio = cx - largura_bloco / 2
        alfa = 0.75 + 0.25 * math.sin(self.tempo * 3)
        cor_barras = misturar_cor(COBRA_CAUDA, COBRA_CABECA, alfa)
        for dx in (0, 18 * u):
            barra = pygame.Rect(inicio + dx, titulo_y - 16 * u, 11 * u, 32 * u)
            pygame.draw.rect(self.tela, cor_barras, barra, border_radius=int(4 * u))
        desenhar_texto(self.tela, "PAUSADO", 44 * u, TEXTO, (inicio + 46 * u, titulo_y), "midleft")

        largura_cartao = (largura - 80 * u) / 3
        cartoes_y = painel.top + 125 * u
        resumo = [
            ("PONTOS", str(self.pontos), TEXTO),
            ("TAMANHO", str(len(self.cobra)), COBRA_CABECA),
            ("VELOCIDADE", f"{self.multiplicador_velocidade:.1f}x", OURO),
        ]
        for i, (rotulo, valor, cor) in enumerate(resumo):
            x = painel.left + 28 * u + largura_cartao / 2 + i * (largura_cartao + 12 * u)
            self.desenhar_cartao(rotulo, valor, cor, (x, cartoes_y), largura_cartao)

        som = "Som: ligado" if self.sons.ligado else "Som: desligado"
        opcoes = [("Continuar", "continuar"), ("Reiniciar", "reiniciar"), (som, "som"), ("Menu", "menu")]
        self.desenhar_botoes(opcoes, painel.top + 212 * u, vertical=True)

        dica = "ESC continuar   ·   Q menu"
        desenhar_texto(self.tela, dica, 15 * u, TEXTO_SUAVE, (cx, painel.bottom - 26 * u), negrito=False, sombra=False)

    def desenhar_game_over(self):
        u = self.escala
        self.tela.blit(self.escurecer, (0, 0))
        painel = self.desenhar_painel(min(self.tela.get_width() * 0.92, 580 * u), 380 * u)
        cx = painel.centerx

        desenhar_texto(self.tela, "GAME OVER", 54 * u, PERIGO, (cx, painel.top + 58 * u))
        desenhar_texto(self.tela, "PONTUAÇÃO", 16 * u, TEXTO_SUAVE, (cx, painel.top + 112 * u), sombra=False)
        desenhar_texto(self.tela, str(self.pontos), 64 * u, TEXTO, (cx, painel.top + 160 * u))

        if self.novo_recorde:
            escala_selo = 1 + 0.06 * math.sin(self.tempo * 6)
            desenhar_texto(self.tela, "NOVO RECORDE!", 24 * u * escala_selo, OURO, (cx, painel.top + 218 * u))
        else:
            desenhar_texto(self.tela, f"Recorde: {self.recorde}", 22 * u, OURO, (cx, painel.top + 218 * u), negrito=False)

        self.desenhar_botoes([("Jogar novamente", "jogar"), ("Menu", "menu")], painel.bottom - 70 * u)

    def desenhar_titulo(self, texto, tamanho, centro):
        f = fonte(tamanho)
        letras = [f.render(letra, True, (0, 0, 0)) for letra in texto]
        espacamento = tamanho * 0.03
        largura_total = sum(letra.get_width() for letra in letras) + espacamento * (len(letras) - 1)
        x = centro[0] - largura_total / 2
        for i, (letra, sombra) in enumerate(zip(texto, letras)):
            progresso = i / max(1, len(texto) - 1)
            cor = misturar_cor(COBRA_CABECA, (80, 214, 176), progresso)
            onda = math.sin(self.tempo * 3 - i * 0.55) * tamanho * 0.06
            imagem = f.render(letra, True, cor)
            retangulo = imagem.get_rect(midleft=(x, centro[1] + onda))
            sombra.set_alpha(130)
            self.tela.blit(sombra, retangulo.move(0, tamanho * 0.06))
            self.tela.blit(imagem, retangulo)
            x += imagem.get_width() + espacamento
        return x

    def desenhar_selo_recorde(self, centro):
        u = self.escala
        texto = fonte(20 * u).render(f"RECORDE   {self.recorde}", True, OURO)
        selo = texto.get_rect(center=centro).inflate(70 * u, 18 * u)
        selo.centerx = centro[0]
        pygame.draw.rect(self.tela, PAINEL, selo, border_radius=selo.h // 2)
        pygame.draw.rect(self.tela, (120, 98, 40), selo, max(2, int(2 * u)), border_radius=selo.h // 2)
        estrela_x = selo.left + 24 * u
        pygame.draw.polygon(self.tela, OURO, pontos_estrela(estrela_x, selo.centery, 10 * u, 4.5 * u, 0))
        self.tela.blit(texto, texto.get_rect(midleft=(estrela_x + 18 * u, selo.centery)))

    def desenhar_menu(self):
        u = self.escala
        largura, altura = self.tela.get_size()
        cx, cy = largura / 2, altura / 2
        self.tela.blit(self.escurecer_menu, (0, 0))

        titulo_y = cy - 185 * u
        halo = brilho(200 * u, COBRA_CABECA)
        self.tela.blit(halo, halo.get_rect(center=(cx, titulo_y)))
        fim_titulo = self.desenhar_titulo("SNAKE", 124 * u, (cx, titulo_y))
        self.desenhar_maca((fim_titulo + 40 * u, titulo_y - 34 * u + 6 * u * math.sin(self.tempo * 2.5)), 56 * u)

        desenhar_texto(self.tela, "coma, cresça e não bata!", 23 * u, TEXTO_SUAVE, (cx, titulo_y + 78 * u), negrito=False)
        self.desenhar_selo_recorde((cx, cy - 52 * u))

        som = "Som: ligado" if self.sons.ligado else "Som: desligado"
        opcoes = [("Jogar", "jogar"), ("Como jogar", "ajuda"), (som, "som"), ("Sair", "sair")]
        self.desenhar_botoes(opcoes, cy + 18 * u, vertical=True)

        dicas = "↑↓ escolher   ·   ENTER confirmar   ·   F11 tela cheia"
        desenhar_texto(self.tela, dicas, 16 * u, TEXTO_SUAVE, (cx, altura - 26 * u), negrito=False, sombra=False)

    def desenhar_tecla(self, rotulo, posicao):
        u = self.escala
        imagem = fonte(16 * u).render(rotulo, True, TEXTO)
        tecla = imagem.get_rect(midleft=posicao).inflate(18 * u, 10 * u)
        tecla.left = posicao[0]
        pygame.draw.rect(self.tela, (8, 10, 16), tecla.move(0, 3 * u), border_radius=int(7 * u))
        pygame.draw.rect(self.tela, BOTAO, tecla, border_radius=int(7 * u))
        pygame.draw.rect(self.tela, BORDA, tecla, max(1, int(2 * u)), border_radius=int(7 * u))
        self.tela.blit(imagem, imagem.get_rect(center=tecla.center))
        return tecla.right

    def desenhar_ajuda(self):
        u = self.escala
        self.tela.blit(self.escurecer, (0, 0))
        painel = pygame.Rect(0, 0, min(self.tela.get_width() * 0.92, 600 * u), min(self.tela.get_height() * 0.95, 600 * u))
        painel.center = (self.tela.get_width() / 2, self.tela.get_height() / 2)
        raio = int(22 * u)
        pygame.draw.rect(self.tela, (6, 8, 12), painel.move(0, 8 * u), border_radius=raio)
        pygame.draw.rect(self.tela, PAINEL, painel, border_radius=raio)
        pygame.draw.rect(self.tela, BORDA, painel, max(2, int(2 * u)), border_radius=raio)

        esquerda = painel.left + 44 * u
        coluna = painel.left + 250 * u
        y = painel.top + 48 * u
        desenhar_texto(self.tela, "COMO JOGAR", 38 * u, COBRA_CABECA, (painel.centerx, y))

        y += 48 * u
        desenhar_texto(self.tela, "CONTROLES", 15 * u, TEXTO_SUAVE, (esquerda, y), "midleft", sombra=False)
        controles = [
            (["W", "A", "S", "D"], "Mover (ou setas)"),
            (["ESC", "P"], "Pausar"),
            (["M"], "Ligar/desligar som"),
            (["F11"], "Tela cheia"),
        ]
        for teclas, descricao in controles:
            y += 36 * u
            x = esquerda
            for tecla in teclas:
                x = self.desenhar_tecla(tecla, (x, y)) + 6 * u
            desenhar_texto(self.tela, descricao, 19 * u, TEXTO, (coluna, y), "midleft", negrito=False, sombra=False)

        y += 46 * u
        desenhar_texto(self.tela, "ITENS", 15 * u, TEXTO_SUAVE, (esquerda, y), "midleft", sombra=False)
        y += 38 * u
        self.desenhar_maca((esquerda + 18 * u, y), 34 * u)
        desenhar_texto(self.tela, "Maçã: +1 ponto, cresce 1", 19 * u, TEXTO, (coluna, y), "midleft", negrito=False, sombra=False)
        y += 42 * u
        self.desenhar_estrela((esquerda + 18 * u, y), 34 * u)
        desenhar_texto(self.tela, f"Estrela: +{BONUS_PONTOS} pontos, some rápido!", 19 * u, TEXTO, (coluna, y), "midleft", negrito=False, sombra=False)
        y += 42 * u
        self.desenhar_relogio((esquerda + 18 * u, y), 34 * u)
        desenhar_texto(self.tela, f"Relógio: câmera lenta por {LENTIDAO_DURACAO:.0f}s", 19 * u, TEXTO, (coluna, y), "midleft", negrito=False, sombra=False)

        y += 46 * u
        desenhar_texto(self.tela, "Quanto maior a cobra, mais rápida ela fica!", 19 * u, OURO, (painel.centerx, y))

        self.desenhar_botoes([("Voltar", "menu")], painel.bottom - 50 * u)

    def rodar(self):
        while self.rodando:
            dt = min(self.relogio.tick(FPS) / 1000, 0.1)
            self.tratar_eventos()
            self.atualizar_layout()
            self.atualizar(dt)
            self.desenhar()
            pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    Jogo().rodar()
