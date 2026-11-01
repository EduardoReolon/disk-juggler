import os
import sys
import ctypes
import subprocess
import threading
import time
import shutil
from dotenv import load_dotenv
from colorama import init, Fore, Style

# Inicializa o colorama para as cores no terminal
init(autoreset=True)

# Variáveis globais para armazenar os tamanhos em background
tamanhos_jogos = {}
tamanhos_lock = threading.Lock()

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def format_bytes(size):
    # Converte bytes para GB
    return f"{size / (1024 ** 3):.2f} GB"

def get_free_space(path):
    # Solução nativa do Python, sem riscos de falha de memória do Windows
    return shutil.disk_usage(path).free

def calcular_tamanho_pasta(path):
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir() and not entry.is_symlink():
                total += calcular_tamanho_pasta(entry.path)
    except Exception:
        pass
    return total

def background_reader(hd_dir, ssd_dir, pastas_hd, pastas_ssd):
    for jogo in pastas_ssd:
        caminho = os.path.join(ssd_dir, jogo)
        tamanho = calcular_tamanho_pasta(caminho)
        with tamanhos_lock:
            tamanhos_jogos[jogo] = tamanho

    for jogo in pastas_hd:
        if jogo not in pastas_ssd:
            caminho = os.path.join(hd_dir, jogo)
            tamanho = calcular_tamanho_pasta(caminho)
            with tamanhos_lock:
                tamanhos_jogos[jogo] = tamanho

def listar_jogos(hd_dir, ssd_dir):
    os.makedirs(hd_dir, exist_ok=True)
    os.makedirs(ssd_dir, exist_ok=True)

    hd_items = [d for d in os.listdir(hd_dir) if os.path.isdir(os.path.join(hd_dir, d))]
    ssd_items = [d for d in os.listdir(ssd_dir) if os.path.isdir(os.path.join(ssd_dir, d))]

    jogos = []
    for game in hd_items:
        if game in ssd_items:
            jogos.append({"nome": game, "local": "SSD"})
        else:
            jogos.append({"nome": game, "local": "HD"})
            
    return jogos, hd_items, ssd_items

def mover_para_ssd_thread(nome_jogo, hd_dir, ssd_dir, status_dict):
    origem = os.path.join(hd_dir, nome_jogo)
    destino = os.path.join(ssd_dir, nome_jogo)
    
    cmd = ["robocopy", origem, destino, "/MOVE", "/E", "/MT:16", "/R:0", "/W:0", "/NFL", "/NDL", "/NJH", "/NJS", "/NC", "/NS"]
    subprocess.run(cmd, capture_output=True)
    
    subprocess.run(["cmd", "/c", "mklink", "/J", origem, destino], capture_output=True)
    status_dict['concluido'] = True

def devolver_para_hd(jogos_antigos, hd_dir, ssd_dir, mt, ipg):
    for nome_jogo in jogos_antigos:
        origem_ssd = os.path.join(ssd_dir, nome_jogo)
        destino_hd = os.path.join(hd_dir, nome_jogo)
        
        print(Fore.CYAN + f"\n[Devolvendo {nome_jogo} para o HD...]")
        
        if os.path.exists(destino_hd):
            try:
                os.rmdir(destino_hd)
            except Exception as e:
                print(Fore.RED + f"Erro ao remover a junção no HD para {nome_jogo}: {e}")
                continue

        cmd = ["robocopy", origem_ssd, destino_hd, "/MOVE", "/E", f"/MT:{mt}", f"/IPG:{ipg}", "/R:0", "/W:0"]
        subprocess.run(cmd, capture_output=False)
        print(Fore.GREEN + f"[{nome_jogo} engavetado com sucesso!]")

def aguardar_tamanho(jogo):
    print(Fore.YELLOW + f"Calculando tamanho de '{jogo}', aguarde um instante...")
    while True:
        with tamanhos_lock:
            if jogo in tamanhos_jogos:
                return tamanhos_jogos[jogo]
        time.sleep(0.5)

def main():
    if not is_admin():
        print(Fore.RED + "Erro: O script precisa ser executado como Administrador (para criar mklink).")
        sys.exit(1)

    load_dotenv()
    hd_dir = os.getenv("HD_GAMES_DIR")
    ssd_dir = os.getenv("SSD_GAMES_DIR")
    robocopy_mt = os.getenv("ROBOCOPY_MT", "1")
    robocopy_ipg = os.getenv("ROBOCOPY_IPG", "0")

    if not hd_dir or not ssd_dir:
        print(Fore.RED + "Erro: Variáveis não encontradas no .env.")
        sys.exit(1)

    jogos, pastas_hd, pastas_ssd = listar_jogos(hd_dir, ssd_dir)

    # Trava se a pasta estiver vazia
    if not jogos:
        print(Fore.YELLOW + f"\nAs pastas foram lidas, mas não há nenhum jogo nelas!")
        print(Fore.WHITE + f"Mova a pasta de algum jogo para: {hd_dir}")
        print("E rode o script novamente.")
        input("\nPressione ENTER para sair...")
        sys.exit(0)

    bg_thread = threading.Thread(target=background_reader, args=(hd_dir, ssd_dir, pastas_hd, pastas_ssd), daemon=True)
    bg_thread.start()

    espaco_livre_ssd = get_free_space(ssd_dir)
    tolerancia = 10 * 1024 * 1024 * 1024 # 10 GB em bytes

    # ==========================================
    # PASSO 1: ESCOLHER JOGO PARA JOGAR
    # ==========================================
    print(Fore.CYAN + Style.BRIGHT + "\n--- PASSO 1: Preparar Jogo ---")
    print(f"Espaço livre no SSD: {Fore.GREEN}{format_bytes(espaco_livre_ssd)}")
    
    for i, jogo in enumerate(jogos, 1):
        cor_local = Fore.GREEN if jogo['local'] == 'SSD' else Fore.YELLOW
        print(f"[{i}] {jogo['nome']} {cor_local}(no {jogo['local']})")
    print(Fore.CYAN + "[99] Pular Passo 1 (Apenas engavetar jogos)")
    print("[0] Sair")

    try:
        escolha = int(input("\nDigite o número: "))
    except ValueError:
        print(Fore.RED + "Escolha inválida.")
        sys.exit(1)

    if escolha == 0:
        sys.exit(0)

    passo1_status = {'concluido': False}
    thread_passo1 = None
    jogo_selecionado = None
    novo_espaco_estimado = espaco_livre_ssd

    if escolha == 99:
        print(Fore.YELLOW + "Passo 1 pulado. Indo direto para o engavetamento.")
        passo1_status['concluido'] = True
    elif 1 <= escolha <= len(jogos):
        jogo_selecionado = jogos[escolha - 1]
        nome_jogo_atual = jogo_selecionado['nome']

        if jogo_selecionado['local'] == "SSD":
            print(Fore.GREEN + f"\n{nome_jogo_atual} já está no SSD.")
            passo1_status['concluido'] = True
        else:
            tamanho_jogo = aguardar_tamanho(nome_jogo_atual)
            if (espaco_livre_ssd - tamanho_jogo) < tolerancia:
                print(Fore.RED + Style.BRIGHT + f"\n[!] ESPAÇO INSUFICIENTE [!]")
                print(Fore.RED + f"O jogo tem {format_bytes(tamanho_jogo)}, mas restaria menos de 10 GB no SSD.")
                print(Fore.RED + "Por segurança, o Passo 1 foi cancelado. Engavete jogos no Passo 2 e rode novamente.")
                passo1_status['concluido'] = True
                jogo_selecionado = None
            else:
                novo_espaco_estimado = espaco_livre_ssd - tamanho_jogo
                print(Fore.CYAN + f"\nMovendo {nome_jogo_atual} para o SSD em background...")
                thread_passo1 = threading.Thread(target=mover_para_ssd_thread, args=(nome_jogo_atual, hd_dir, ssd_dir, passo1_status))
                thread_passo1.start()
    else:
        print(Fore.RED + "Opção inválida.")
        sys.exit(1)

    # ==========================================
    # PASSO 2: ENGAVETAR JOGOS
    # ==========================================
    print(Fore.CYAN + Style.BRIGHT + "\n--- PASSO 2: Engavetar para o HD ---")
    jogos_no_ssd = [j for j in os.listdir(ssd_dir) if os.path.isdir(os.path.join(ssd_dir, j))]
    
    if jogo_selecionado and jogo_selecionado['nome'] in jogos_no_ssd:
        jogos_no_ssd.remove(jogo_selecionado['nome'])
    elif jogo_selecionado and jogo_selecionado['local'] == 'HD':
        pass

    jogos_para_engavetar = set()

    if not jogos_no_ssd:
        print(Fore.YELLOW + "Nenhum jogo extra no SSD para engavetar.")
    else:
        for j in jogos_no_ssd:
            if j not in tamanhos_jogos:
                aguardar_tamanho(j)

        while True:
            print(f"\nEspaço livre estimado no SSD (pós Passo 1): {Fore.YELLOW}{format_bytes(novo_espaco_estimado)}")
            print("Selecione os jogos que deseja engavetar (digite o número para marcar/desmarcar):")
            
            for i, j_nome in enumerate(jogos_no_ssd, 1):
                tam = tamanhos_jogos.get(j_nome, 0)
                if j_nome in jogos_para_engavetar:
                    status = Fore.GREEN + "[X]"
                else:
                    status = Fore.WHITE + "[ ]"
                print(f"{i}. {status} {j_nome} ({format_bytes(tam)})")
            
            print(Fore.CYAN + "[0] Confirmar e Prosseguir")
            
            try:
                opc = int(input("\nOpção: "))
            except ValueError:
                continue

            if opc == 0:
                break
            elif 1 <= opc <= len(jogos_no_ssd):
                nome_alvo = jogos_no_ssd[opc - 1]
                if nome_alvo in jogos_para_engavetar:
                    jogos_para_engavetar.remove(nome_alvo)
                else:
                    jogos_para_engavetar.add(nome_alvo)

    # ==========================================
    # LUZ VERDE
    # ==========================================
    if not passo1_status['concluido']:
        print(Fore.YELLOW + "\nAguardando Passo 1 concluir movimentação...")
        if thread_passo1:
            thread_passo1.join()
    
    if jogo_selecionado:
        print(Fore.GREEN + Style.BRIGHT + "\n=======================================================")
        print(Fore.GREEN + Style.BRIGHT + f" LUZ VERDE: O jogo {jogo_selecionado['nome']} está pronto!")
        print(Fore.GREEN + " Você já pode abrir o launcher e iniciar a gameplay.")
        print(Fore.GREEN + Style.BRIGHT + "=======================================================\n")
    
    # ==========================================
    # EXECUÇÃO DO PASSO 2
    # ==========================================
    if jogos_para_engavetar:
        print(Fore.CYAN + "Iniciando devolução dos jogos marcados para o HD (em background)...")
        devolver_para_hd(list(jogos_para_engavetar), hd_dir, ssd_dir, robocopy_mt, robocopy_ipg)
        print(Fore.GREEN + "\nTodas as devoluções foram concluídas.")
    else:
        print(Fore.YELLOW + "Nenhum jogo selecionado para devolução.")

    input(Fore.WHITE + "\nPressione ENTER para fechar...")

if __name__ == "__main__":
    main()