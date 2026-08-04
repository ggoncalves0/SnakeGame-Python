import pygame
import random

pygame.init()
pygame.display.set_caption("Snake Game Python")

largura, altura = 800, 600
tela = pygame.display.set_mode((largura, altura), pygame.RESIZABLE)
relogio = pygame.time.Clock()

preta = (0, 0, 0)
branca = (255, 255, 255)
vermelho = (255, 0, 0)
verde = (0, 255, 0)

tamanho_quadrado = 20
velocidade = 15

tela_cheia = False
tamanho_janela_anterior = (largura, altura)


def alternar_tela_cheia():
    global tela, tela_cheia, largura, altura, tamanho_janela_anterior
    tela_cheia = not tela_cheia
    if tela_cheia:
        tamanho_janela_anterior = (largura, altura)
        info = pygame.display.Info()
        largura, altura = info.current_w, info.current_h
        tela = pygame.display.set_mode((largura, altura), pygame.FULLSCREEN)
    else:
        largura, altura = tamanho_janela_anterior
        tela = pygame.display.set_mode((largura, altura), pygame.RESIZABLE)


def gerar_comida():
    comida_x = round(random.randrange(0, largura - tamanho_quadrado) / tamanho_quadrado) * tamanho_quadrado
    comida_y = round(random.randrange(0, altura - tamanho_quadrado) / tamanho_quadrado) * tamanho_quadrado
    return comida_x, comida_y


def desenhar_comida(comida_x, comida_y):
    pygame.draw.rect(tela, vermelho, [comida_x, comida_y, tamanho_quadrado, tamanho_quadrado])


def desenhar_cobra(tamanho_quadrado, pixeis_cobra):
    for pixel in pixeis_cobra:
        pygame.draw.rect(tela, verde, [pixel[0], pixel[1], tamanho_quadrado, tamanho_quadrado])


def desenhar_pontuacao(pontuacao):
    fonte = pygame.font.SysFont(None, 35)
    texto = fonte.render("Pontuação: " + str(pontuacao), True, branca)
    posicao_x = largura // 2 - texto.get_width() // 2
    tela.blit(texto, [posicao_x, 10])


def desenhar_pausa():
    overlay = pygame.Surface((largura, altura))
    overlay.set_alpha(180)
    overlay.fill(preta)
    tela.blit(overlay, (0, 0))

    fonte_grande = pygame.font.SysFont(None, 60)
    fonte_pequena = pygame.font.SysFont(None, 30)

    texto_pausa = fonte_grande.render("PAUSADO", True, branca)
    texto_dica = fonte_pequena.render("Pressione ESC para continuar", True, branca)

    tela.blit(texto_pausa, [largura // 2 - texto_pausa.get_width() // 2, altura // 2 - 40])
    tela.blit(texto_dica, [largura // 2 - texto_dica.get_width() // 2, altura // 2 + 20])


def verificar_colisao_corpo(x, y, pixeis_cobra):
    corpo_sem_cabeca = pixeis_cobra[:-1]
    for pixel in corpo_sem_cabeca:
        if pixel == [x, y]:
            return True
    return False


def verificar_colisao_parede(x, y):
    return x < 0 or x >= largura or y < 0 or y >= altura


def selecionar_velocidade(tecla, velocidade_x_atual, velocidade_y_atual):
    velocidade_x, velocidade_y = velocidade_x_atual, velocidade_y_atual

    if tecla in (pygame.K_LEFT, pygame.K_a) and velocidade_x_atual == 0:
        velocidade_x, velocidade_y = -tamanho_quadrado, 0
    elif tecla in (pygame.K_RIGHT, pygame.K_d) and velocidade_x_atual == 0:
        velocidade_x, velocidade_y = tamanho_quadrado, 0
    elif tecla in (pygame.K_UP, pygame.K_w) and velocidade_y_atual == 0:
        velocidade_x, velocidade_y = 0, -tamanho_quadrado
    elif tecla in (pygame.K_DOWN, pygame.K_s) and velocidade_y_atual == 0:
        velocidade_x, velocidade_y = 0, tamanho_quadrado

    return velocidade_x, velocidade_y


def rodar_game():
    global largura, altura, tela

    fim_de_jogo = False
    pausado = False

    x = largura / 2
    y = altura / 2

    velocidade_x = 0
    velocidade_y = 0

    tamanho_cobra = 1
    pixeis_cobra = []

    comida_x, comida_y = gerar_comida()

    while not fim_de_jogo:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                fim_de_jogo = True
            elif evento.type == pygame.VIDEORESIZE and not tela_cheia:
                largura, altura = evento.w, evento.h
                tela = pygame.display.set_mode((largura, altura), pygame.RESIZABLE)
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    pausado = not pausado
                elif evento.key == pygame.K_F11:
                    alternar_tela_cheia()
                elif not pausado:
                    velocidade_x, velocidade_y = selecionar_velocidade(evento.key, velocidade_x, velocidade_y)

        if not pausado:
            x += velocidade_x
            y += velocidade_y

            if verificar_colisao_parede(x, y):
                fim_de_jogo = True

            pixeis_cobra.append([x, y])
            if len(pixeis_cobra) > tamanho_cobra:
                del pixeis_cobra[0]

            if verificar_colisao_corpo(x, y, pixeis_cobra):
                fim_de_jogo = True

            if x == comida_x and y == comida_y:
                comida_x, comida_y = gerar_comida()
                tamanho_cobra += 1

        tela.fill(preta)
        desenhar_comida(comida_x, comida_y)
        desenhar_cobra(tamanho_quadrado, pixeis_cobra)
        desenhar_pontuacao(tamanho_cobra - 1)

        if pausado:
            desenhar_pausa()

        pygame.display.update()
        relogio.tick(velocidade)

    pygame.quit()


if __name__ == '__main__':
    rodar_game()