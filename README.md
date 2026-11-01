# Disk Juggler 🤹‍♂️🎮

**Disk Juggler** é um gerenciador de cache de jogos via CLI (Command Line Interface) construído em Python. Ele permite que você armazene toda a sua biblioteca de jogos pesados em um HD de grande capacidade e mova apenas o jogo que você quer jogar no momento para o seu SSD rápido (NVMe/SATA), de forma automática e segura.

O grande diferencial? **Nenhum Launcher percebe a mudança.** O script usa Links Simbólicos (Junction Points) nativos do Windows. Para a Steam, Epic Games, EA App ou Rockstar Launcher, o jogo nunca saiu do HD.

## ✨ Principais Funcionalidades

- **Links Simbólicos Automáticos:** Cria um `mklink /J` transparente. Os launchers não perdem o rastro do jogo.
- **Background Transfer (Engavetamento Silencioso):** Libera a "Luz Verde" para você abrir o seu jogo no SSD enquanto move os jogos antigos de volta para o HD em segundo plano.
- **Transferência Robusta (Robocopy):** Usa o `robocopy` nativo do Windows com suporte a múltiplas threads (velocidade máxima na ida para o SSD) e limitação de uso de CPU/Disco (na devolução para o HD).
- **Proteção de Espaço (Stuttering-free):** Verifica o armazenamento antes de mover. Nunca deixa o seu SSD lotar (mantém uma margem de segurança configurável, padrão de 10GB) para evitar lentidão no Windows.
- **Resiliência a Quedas (Fallback):** Se você fechar o terminal ou faltar luz no meio de uma transferência, não há corrupção. Ao rodar novamente, ele retoma exatamente de onde parou.

## 🛠️ Pré-requisitos

- **Sistema Operacional:** Windows 10 ou 11 (necessário para o `robocopy` e `mklink`).
- **Python:** Versão 3.8 ou superior.
- **Permissões:** O script precisa ser executado como **Administrador** (obrigatório do Windows para criar links simbólicos).

## 🚀 Instalação

1. Clone o repositório:
```cmd
git clone https://github.com/EduardoReolon/disk-juggler.git
cd disk-juggler

```

2. Crie um ambiente virtual e ative-o:

```cmd
python -m venv venv
venv\Scripts\activate

```

3. Instale as dependências:

```cmd
pip install -r requirements.txt

```

4. Crie o arquivo de configuração:
Copie o arquivo `.env.example` e renomeie para `.env`.

## ⚙️ Configuração (.env)

Abra o arquivo `.env` e configure os caminhos dos seus discos:

```env
# Pasta raiz onde sua biblioteca inteira de jogos fica armazenada (HD)
HD_GAMES_DIR=D:\jogos

# Pasta temporária onde o jogo ativo vai rodar (SSD NVMe)
SSD_GAMES_DIR=C:\jogos

# Controle de performance na devolução (HD) para não causar lag no seu jogo atual
# MT = Multi-Threading (1 usa baixo processamento)
ROBOCOPY_MT=1
# IPG = Inter-Packet Gap (Em milissegundos. Aumente se o jogo atual estiver engasgando)
ROBOCOPY_IPG=0

```

## 🎮 Como usar

Para iniciar o Disk Juggler, basta clicar com o botão direito no arquivo **`iniciar.bat`** e selecionar **Executar como Administrador**.

*(Nota: O arquivo `.bat` já possui um sistema que ativa o ambiente virtual automaticamente.)*

### O Fluxo:

1. O script listará os jogos detectados no seu HD.
2. Você digita o número do jogo que quer jogar agora.
3. O script move o jogo para o SSD na velocidade máxima.
4. **Luz Verde!** O script avisa que você já pode abrir o jogo.
5. Em seguida, ele listará os jogos antigos que ficaram "esquecidos" no SSD e perguntará quais você deseja "engavetar" (devolver para o HD).
6. Você escolhe, e ele faz a devolução de forma silenciosa em segundo plano enquanto você joga.

## ⚠️ Observações Importantes

* **Saves:** O script move os arquivos do jogo. A grande maioria dos launchers salva o progresso do jogador na nuvem ou na pasta `Documentos` do Windows, portanto seus *saves* estão seguros.
* **Nunca use "Copiar/Colar" manualmente** para voltar um jogo pro HD. Use sempre o Passo 2 do script para "engavetar", pois ele remove o atalho corretamente antes de devolver os arquivos, evitando loops de cópia.

## 🤝 Contribuindo

Sinta-se à vontade para abrir *Issues* ou enviar *Pull Requests* com melhorias!

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](https://www.google.com/search?q=LICENSE) para mais detalhes.