# Snake Game 🐍

Um jogo da cobrinha (Snake) feito em Python com Pygame, com suporte a tela cheia, redimensionamento de janela, pausa e tela de game over.

## Tecnologias

- Python 3
- Pygame

## Instalação

1. Clone o repositório:
```
git clone https://github.com/SEU_USUARIO/NOME_DO_REPO.git
cd NOME_DO_REPO
```

2. Crie um ambiente virtual (opcional, mas recomendado):
```
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. Instale as dependências:
```
pip install -r requirements.txt
```

4. Execute o jogo:
```
python main.py
```

## Como jogar

O objetivo é controlar a cobra, comer o máximo de comidas possível e evitar colidir com as paredes ou com o próprio corpo. A cada comida, a cobra cresce e a pontuação aumenta.

### Controles

| Tecla | Ação |
|---|---|
| `↑` `↓` `←` `→` ou `W` `A` `S` `D` | Mover a cobra |
| `ESC` | Pausar / despausar |
| `F11` | Alternar entre tela cheia e janela |
| Arrastar a borda da janela | Redimensionar |

### Game Over

Ao colidir com a parede ou com o próprio corpo, o jogo exibe a pontuação final e dois botões:
- **Jogar novamente** — reinicia a partida
- **Sair** — encerra o jogo

## Observações

- O jogo se adapta a diferentes resoluções de tela, tanto em modo janela quanto em tela cheia.
- Projeto criado para fins de estudo/portfólio.

## 👨‍💻 Autor

Gabriel Gonçalves de Oliveira
📧 ggoncalvesy03@gmail.com