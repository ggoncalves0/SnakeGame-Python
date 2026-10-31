# Snake Game 🐍

Um jogo da cobrinha (Snake) feito em Python com pygame-ce, com visual moderno, animações suaves, sons, comida bônus, recorde salvo e suporte a tela cheia e redimensionamento de janela.

## Tecnologias

- Python 3
- pygame-ce

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

Controle a cobra, coma o máximo de maçãs possível e evite colidir com as paredes ou com o próprio corpo. A cada maçã a cobra cresce e ganha 1 ponto. **Quanto maior a cobra, mais rápida ela fica**: o multiplicador de velocidade aparece no topo da tela e muda de cor de verde para vermelho.

De vez em quando aparecem itens especiais, que somem depois de alguns segundos (o anel ao redor mostra o tempo restante):

- **Estrela dourada**: vale **5 pontos**.
- **Relógio azul**: ativa a **câmera lenta** por 5 segundos, deixando a cobra bem mais devagar. Uma barra no topo do tabuleiro mostra quanto tempo resta.

### Controles

| Tecla | Ação |
|---|---|
| `↑` `↓` `←` `→` ou `W` `A` `S` `D` | Mover a cobra |
| `ESC` ou `P` | Pausar / continuar |
| `Q` (pausado) | Voltar ao menu |
| `M` | Ligar / desligar o som |
| `F11` | Alternar entre tela cheia e janela |
| `ENTER` / `ESPAÇO` | Confirmar opção nos menus |
| Arrastar a borda da janela | Redimensionar |

### Recursos

- Menu animado com uma cobra jogando sozinha ao fundo, tela "Como jogar" e opção de som
- Pausa e tela de game over com botões (mouse ou teclado)
- Movimento suave e velocidade que aumenta com o tamanho da cobra
- Fila de comandos: curvas rápidas não se perdem
- Efeitos de partículas, tremor de tela ao morrer e sons gerados pelo próprio código
- Recorde salvo em `recorde.json`
- O tabuleiro se adapta a qualquer tamanho de janela ou tela cheia, sem reiniciar a partida
- O jogo pausa sozinho quando a janela perde o foco

## Observações

- Projeto criado para fins de estudo/portfólio.

## 👨‍💻 Autor
Gabriel Gonçalves de Oliveira  
📧 ggoncalvesy03@gmail.com
