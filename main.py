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

tamanho_quadrado = 20
velocidade = 15


def gerar_comida():
    comida_x = round(random.randrange(0, largura - tamanho_quadrado) / 20.0) * 20.0
    comida_y = round(random.randrange(0, altura - tamanho_quadrado) / 20.0) * 20.0
    return comida_x, comida_y


def desenhar_comida(comida_x, comida_y):
    pygame.draw.rect(tela, vermelho, [comida_x, comida_y, tamanho_quadrado, tamanho_quadrado])


def desenhar_cobra(tamanho_quadrado, pixeis_cobra):
    for pixel in pixeis_cobra:
        pygame.draw.rect(tela, verde, [pixel[0], pixel[1], tamanho_quadrado, tamanho_quadrado])


def desenhar_pontuacao(pontuacao):
    fonte = pygame.font.SysFont(None, 35)
    texto = fonte.render("Pontuação: " + str(pontuacao), True, branca)
    tela.blit(texto, [330, 0])


def rodar_game():
    fim_de_jogo = False

    x = largura / 2
    y = altura / 2

    velocidade_x = 0
    velocidade_y = 0

    tamanho_cobra = 1
    pixeis_cobra = []

    comida_x, comida_y = gerar_comida()

    while not fim_de_jogo:
        tela.fill(preta)
        desenhar_comida(comida_x, comida_y)
        pixeis_cobra.append([x, y])
        if len(pixeis_cobra) > tamanho_cobra:
            del pixeis_cobra[0]

        for pixel in pixeis_cobra:
            if pixel == [x, y] and pixel != pixeis_cobra[-1]:
                fim_de_jogo = True

        desenhar_cobra(tamanho_quadrado, pixeis_cobra)
        desenhar_pontuacao(tamanho_cobra - 1)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                fim_de_jogo = True

        pygame.display.update()
        if x == comida_x and y == comida_y:
            comida_x, comida_y = gerar_comida()
            tamanho_cobra += 1
        relogio.tick(velocidade)


rodar_game()
