import cv2
import pytesseract
import pyautogui
import time
import numpy as np
import tkinter as tk
from tkinter import ttk

# Obter resolução da tela
screen_width, screen_height = pyautogui.size()

# Coordenadas dos botões (ajustar conforme necessário)
START_MISSION_BUTTON = (1280, 934)
NEXT_MISSION_BUTTON = (1497, 448)
CAPTURE_REGION_XP = (1362, 992, 100, 50)
CAPTURE_REGION_ENERGIA = (900, 760, 150, 50)

# Criar interface gráfica
root = tk.Tk()
root.title("Configuração do Bot Hero Zero")

# Opções de configuração
config = {
    "usar_timed_missoes": tk.BooleanVar(value=False),
    "usar_combat_missoes": tk.BooleanVar(value=False),
    #"usar_seta": tk.BooleanVar(value=False),
    "xp_minimo": tk.IntVar(value=500),
    "collect_shovels": tk.BooleanVar(value=False),
}

def find_missions():
    """Encontra missões disponíveis na tela e retorna suas posições."""
    missoes = []
    screenshot = pyautogui.screenshot(region=(0, 0, 1920, 1080))
    screenshot_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)

    if config["usar_timed_missoes"].get():
        timed_missao_icon = cv2.imread('assets/timed_mission_icon.png', 0)
        result = cv2.matchTemplate(screenshot_gray, timed_missao_icon, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= 0.8)
        missoes.extend(list(zip(*locations[::-1])))

    if config["usar_combat_missoes"].get():
        combat_missao_icon = cv2.imread('assets/combat_mission_icon.png', 0)
        result = cv2.matchTemplate(screenshot_gray, combat_missao_icon, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= 0.8)
        missoes.extend(list(zip(*locations[::-1])))

    return missoes

def extract_value(region):
    """Captura uma região da tela e extrai um número usando OCR."""
    screenshot = pyautogui.screenshot(region=region)
    screenshot = np.array(screenshot)

    # Converter para escala de cinza
    gray = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)

    # Binarização
    _, thresh_inv = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    # Testar OCR
    config_tesseract = "--psm 6 -c tessedit_char_whitelist=0123456789"
    texto = pytesseract.image_to_string(thresh_inv, config=config_tesseract)

    # Tentar extrair número
    numeros = [int(num) for num in texto.split() if num.isdigit()]
    return numeros[0] if numeros else None

def extract_data():
    """Extrai XP e Energia separadamente."""
    xp = extract_value(CAPTURE_REGION_XP)
    energia = extract_value(CAPTURE_REGION_ENERGIA)
    print(f"XP: {xp}, Energia: {energia}")  # Debug
    return xp, energia

def pick_best_mission():
    """Percorre as missões, analisa XP e Energia, e seleciona a melhor."""
    while True:
        missoes = find_missions()
        if not missoes:
            add_log("Nenhuma missão encontrada. Tentando novamente em 5 segundos...")
            time.sleep(5)
            continue

        melhor_missao = None
        melhor_ratio = 0
        xp_minimo = config["xp_minimo"].get()

        for pos in missoes:
            pyautogui.moveTo(pos[0] + 10, pos[1] + 10, duration=0.5)
            pyautogui.click()
            time.sleep(2)

            xp, energia = extract_data()
            if xp and energia and energia > 0:
                ratio = xp / energia
                if ratio >= xp_minimo and ratio > melhor_ratio:
                    melhor_ratio = ratio
                    melhor_missao = pos

            if config["usar_seta"].get():
                pyautogui.click(NEXT_MISSION_BUTTON)
                time.sleep(1)

        if melhor_missao:
            pyautogui.moveTo(melhor_missao[0] + 10, melhor_missao[1] + 10, duration=0.5)
            pyautogui.click()
            time.sleep(2)
            pyautogui.click(START_MISSION_BUTTON)
            print(f"Missão selecionada com {melhor_ratio:.2f} XP por energia!")
            break
        else:
            print("Nenhuma missão atende aos requisitos. Tentando novamente em 5 segundos...")
            time.sleep(5)

def collect_shovels():
    """Verifica e coleta as pás do evento quando disponíveis."""
    shovel_icon = cv2.imread('assets/shovel_button.png', 0)  # Ícone do botão de pegar pás
    add_log("Looking for shovel button...")

    while config["collect_shovels"].get():  # Apenas se a opção estiver ativada
        screenshot = pyautogui.screenshot(region=(0, 0, 1920, 1080))
        screenshot_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
        result = cv2.matchTemplate(screenshot_gray, shovel_icon, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= 0.8)  # Ajustar a sensibilidade se necessário

        if locations[0].size > 0:
            pos = list(zip(*locations[::-1]))[0]  # Obtém a posição do primeiro botão encontrado
            pyautogui.moveTo(pos[0] + 10, pos[1] + 10, duration=0.5)
            pyautogui.click()
            add_log("Shovels collected!")
            break  # Sai do loop após coletar
        else:
            add_log("Button not found. Retrying in 30 seconds...")
            time.sleep(30)  # Ajusta o tempo conforme necessário

    add_log("Monitoring for shovel button stopped.")

def add_log(text):
    """Adiciona uma mensagem ao log da interface gráfica."""
    log.insert(tk.END, text + "\n")
    log.see(tk.END)
    root.update_idletasks()

def iniciar_bot():
    """Inicia o bot com as configurações escolhidas."""
    add_log("Inicializing bot with the following settings:")
    add_log(f"  - Timed Missions: {config['usar_timed_missoes'].get()}")
    add_log(f"  - Combat Missions: {config['usar_combat_missoes'].get()}")
    #print(f"  - Usar seta: {config['usar_seta'].get()}")
    add_log(f"  - Min XP per energy: {config['xp_minimo'].get()}")
    add_log(f"  - Collect shovels: {config['collect_shovels'].get()}")

    if config["collect_shovels"].get():
        collect_shovels()

    if config["usar_timed_missoes"].get() or config["usar_combat_missoes"].get():
        pick_best_mission()

def parar_bot():
    """Para o bot."""
    add_log("Bot parado.")
    root.quit()

# Interface gráfica
ttk.Label(root, text="Configs:", font=("Arial", 12, "bold")).pack(pady=5)

ttk.Label(root, text="Mission configs:", font=("Arial", 10, "bold")).pack(anchor="w")
ttk.Checkbutton(root, text="Procurar Missões Cronometradas", variable=config["usar_timed_missoes"]).pack(anchor="w")
ttk.Checkbutton(root, text="Procurar Missões de Combate", variable=config["usar_combat_missoes"]).pack(anchor="w")
#ttk.Checkbutton(root, text="Usar Seta para Trocar de Missão", variable=config["usar_seta"]).pack(anchor="w")

# Campo para XP mínimo
frame_xp = ttk.Frame(root)
frame_xp.pack(pady=5, fill="x")
ttk.Label(frame_xp, text="XP mínimo por energia:").pack(side="left", padx=5)
xp_entry = ttk.Entry(frame_xp, textvariable=config["xp_minimo"], width=10)
xp_entry.pack(side="left")

ttk.Label(root, text="Event Configs:", font=("Arial", 10, "bold")).pack(anchor="w")
ttk.Checkbutton(root, text="Pegar Pás do Evento das Toupeiras", variable=config["collect_shovels"]).pack(anchor="w")

# Botões
ttk.Button(root, text="Iniciar Bot", command=iniciar_bot).pack(pady=10)
ttk.Button(root, text="Parar Bot", command=parar_bot).pack(pady=10)

log = tk.Text(root, height=10, width=50)
log.pack(pady=5, fill="both")
log.insert(tk.END, "Log de eventos:\n")

# created by
ttk.Label(root, text="Created by: @Lou-ey", font=("Arial", 8)).pack(pady=5)

# link to github
ttk.Label(root, text="https://github.com/Lou-ey/hero-zero-bot", font=("Arial", 8)).pack(pady=5)

# Rodar interface
root.mainloop()






