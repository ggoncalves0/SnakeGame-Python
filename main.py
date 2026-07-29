import pygame
import random

pygame.init()
pygame.display.set_caption("Snake Game Python")
largura, altura = 800, 600
tela = pygame.display.set_mode((largura, altura))
relogio = pygame.time.Clock()

preta = (0, 0, 0)
branca = (255, 255, 255)
vermelho = (255, 0, 0)
verde = (0, 255, 0)

tamanho_quadro = 20
velocidade = 15


def gerar_comida():
    comida_x = round(random.randrange(0, largura - tamanho_quadro) / 20.0) * 20.0
    comida_y = round(random.randrange(0, altura - tamanho_quadro) / 20.0) * 20.0
    return comida_x, comida_y


def rodar_game():
    fim_de_jogo = False

    x = largura / 2
    y = altura / 2

    velocidade_x = 0
    velocidade_y = 0

    tamanho_cobra = 1
    pixeis_cobra = []

    comida_x = gerar_comida()
    comida_y = gerar_comida()

    while not fim_de_jogo:
        tela.fill(preta)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                fim_de_jogo = True


rodar_game