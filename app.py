import cv2
import pytesseract
import pyautogui
import time
import numpy as np
import tkinter as tk
from tkinter import ttk
import sv_ttk
import darkdetect
import sys
import pywinstyles
import json
import os
import webbrowser

CONFIG_FILE = "config.json"

# Criar interface gráfica
root = tk.Tk()
root.title("Hero Zero Bot")
root.geometry("500x650")
root.iconbitmap("icon/icon.ico")
menu_frame = tk.Frame(root)
menu_frame.pack(fill="x")
sv_ttk.set_theme(darkdetect.theme())

# Opções de configuração
config = {
    "usar_timed_missoes": tk.BooleanVar(value=False),
    "usar_combat_missoes": tk.BooleanVar(value=False),
    #"usar_seta": tk.BooleanVar(value=False),
    "xp_minimo": tk.IntVar(value=500),
    "collect_shovels": tk.BooleanVar(value=True),
    "theme": tk.StringVar(value=sv_ttk.get_theme())
}

def load_config():
    """Carrega as configurações do arquivo JSON."""
    if not os.path.exists(CONFIG_FILE):
        # Criar um ficheiro de configuração padrão
        default_config = {
            "usar_timed_missoes": False,
            "usar_combat_missoes": False,
            "collect_shovels": True,
            "xp_minimo": 500,
            "theme": "dark"
        }
        with open(CONFIG_FILE, "w") as file:
            json.dump(default_config, file, indent=4)
        return default_config  # Retorna os valores padrão

    with open(CONFIG_FILE, "r") as file:
        return json.load(file)

def save_config(config):
    """Salva as configurações no arquivo JSON."""
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

# Obter resolução da tela
screen_width, screen_height = pyautogui.size()

# Coordenadas dos botões
START_MISSION_BUTTON = (1280, 934)
NEXT_MISSION_BUTTON = (1497, 448)
CAPTURE_REGION_XP = (1362, 992, 100, 50)
CAPTURE_REGION_ENERGIA = (900, 760, 150, 50)

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
            add_log(f"Missão selecionada com {melhor_ratio:.2f} XP por energia!")
            break
        else:
            add_log("Nenhuma missão atende aos requisitos. Tentando novamente em 5 segundos...")
            time.sleep(5)

def collect_shovels():
    """Verifica e coleta as pás do evento quando disponíveis."""
    shovel_icon = cv2.imread('assets/shovel_button.png', 0)  # Ícone do botão de pegar pás
    add_log("Looking for shovel button...")

    while True:
        screenshot = pyautogui.screenshot(region=(0, 0, 1920, 1080))
        screenshot_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
        result = cv2.matchTemplate(screenshot_gray, shovel_icon, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= 0.8)  # Ajusta a precisão conforme necessário

        if locations[0].size > 0:
            pos = list(zip(*locations[::-1]))[0]  # Obtém a posição do primeiro botão encontrado
            pyautogui.moveTo(pos[0] + 10, pos[1] + 10, duration=0.5)
            pyautogui.click()
            add_log("✅ Shovels collected successfully! Waiting 3 hours before checking again...")
            time.sleep(10800)  # Espera 3 horas
        else:
            add_log("⏳ Button not found. Retrying in 30 seconds...")
            time.sleep(30)  # Aguarda 30 segundos antes de tentar novamente

    #add_log("Monitoring for shovel button stopped.")

def add_log(text):
    """Adiciona uma mensagem ao log da interface gráfica."""
    timestamp = time.strftime("%H:%M:%S", time.localtime())
    log.insert(tk.END,timestamp + " INFO: " + text + "\n")
    log.see(tk.END)
    root.update_idletasks()

def change_theme():
    """Muda o tema da interface gráfica."""
    if sv_ttk.get_theme() == "dark":
        sv_ttk.set_theme("light")
    else:
        sv_ttk.set_theme("dark")
    apply_theme_to_titlebar(root)

def apply_theme_to_titlebar(root):
    version = sys.getwindowsversion()

    if version.major == 10 and version.build >= 22000:
        # Set the title bar color to the background color on Windows 11 for better appearance
        pywinstyles.change_header_color(root, "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa")
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark" if sv_ttk.get_theme() == "dark" else "normal")

        # A hacky way to update the title bar's color on Windows 10 (it doesn't update instantly like on Windows 11)
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)

def open_github():
    """Abre o link do GitHub no navegador."""
    webbrowser.open("https://github.com/Lou-ey/hero-zero-bot")

def iniciar_bot():
    """Inicia o bot com as configurações escolhidas."""
    # se nenhuma configuração estiver marcada, exibir mensagem de erro
    if not config["usar_timed_missoes"].get() and not config["usar_combat_missoes"].get() and not config["collect_shovels"].get():
        add_log("ERRO: None of the config options are selected. Please select at least one option.")
        return
    add_log("Inicializing bot with the following settings:")
    add_log(f"  - Timed Missions: {config['usar_timed_missoes'].get()}")
    add_log(f"  - Combat Missions: {config['usar_combat_missoes'].get()}")
    #print(f"  - Usar seta: {config['usar_seta'].get()}")
    add_log(f"  - Min XP per energy: {config['xp_minimo'].get()}")
    add_log(f"  - Collect shovels: {config['collect_shovels'].get()}")

    if config["collect_shovels"].get():
        add_log("Collecting shovels mode enabled!")
        collect_shovels()

    if config["usar_timed_missoes"].get() or config["usar_combat_missoes"].get():
        pick_best_mission()

def parar_bot():
    """Para o bot."""
    add_log("Bot stopped.")
    root.quit()

# Interface gráfica

# Botão de Preferências (Menubutton)
preferences_button = ttk.Menubutton(menu_frame, text="⚙ Preferences", direction="below")
preferences_button.pack(side="right", padx=10, pady=5, ipadx=5, ipady=3)

# Criar menu suspenso
menu = tk.Menu(preferences_button, tearoff=0)
menu.add_command(label="Change Theme", command=change_theme)
menu.add_separator()
menu.add_command(label="Exit", command=root.quit)
preferences_button["menu"] = menu

# Botão de saída mais estilizado
#exit_button = ttk.Button(menu_frame, text="❌ Exit", command=root.quit)
#exit_button.pack(side="right", padx=10, pady=5, ipadx=5, ipady=3)

# Seção de Configurações
config_frame = ttk.LabelFrame(root, text="Configurações")
config_frame.pack(fill="both", padx=10, pady=10)

# Configurações de Missão
ttk.Label(config_frame, text="Missões:", font=("Arial", 10, "bold")).pack(anchor="w", padx=5, pady=2)
ttk.Checkbutton(config_frame, text="Procurar Missões Cronometradas (!!! Não funcional !!!)", variable=config["usar_timed_missoes"]).pack(anchor="w", padx=10)
ttk.Checkbutton(config_frame, text="Procurar Missões de Combate (!!! Não funcional !!!)", variable=config["usar_combat_missoes"]).pack(anchor="w", padx=10)

# XP mínimo
frame_xp = ttk.Frame(config_frame)
frame_xp.pack(pady=5, fill="x", padx=10)
ttk.Label(frame_xp, text="XP mínimo por energia:").pack(side="left", padx=5)
xp_entry = ttk.Entry(frame_xp, textvariable=config["xp_minimo"], width=10)
xp_entry.pack(side="left")

# Configurações de Evento
ttk.Label(config_frame, text="Eventos:", font=("Arial", 10, "bold")).pack(anchor="w", padx=5, pady=2)
ttk.Checkbutton(config_frame, text="Pegar Pás do Evento das Toupeiras", variable=config["collect_shovels"]).pack(anchor="w", padx=10)

# Frame de Botões
buttons_frame = ttk.Frame(root)
buttons_frame.pack(fill="x", padx=10, pady=10)

# Botões de controle do bot
ttk.Button(buttons_frame, text="▶ Iniciar Bot", command=iniciar_bot).pack(side="left", expand=True, padx=5, pady=5, ipadx=5, ipady=3)
ttk.Button(buttons_frame, text="⏹ Parar Bot", command=parar_bot).pack(side="left", expand=True, padx=5, pady=5, ipadx=5, ipady=3)

# Frame do Log
log_frame = ttk.LabelFrame(root, text="Log")
log_frame.pack(fill="both", expand=True, padx=10, pady=10)

# Caixa de Log
log = tk.Text(log_frame, height=10, wrap="word", state="normal", bg="#1e1e1e", fg="#dcdcdc", font=("Consolas", 10))
log.pack(padx=5, pady=5, fill="both", expand=True)

# Botão para limpar o log
ttk.Button(log_frame, text="🧹 Clear Log", command=lambda: log.delete(1.0, tk.END)).pack(pady=5)

# Rodapé (Criador e Link)
footer_frame = ttk.Frame(root)
footer_frame.pack(fill="x", pady=5)

ttk.Label(footer_frame, text="Created by: @Lou-ey", font=("Arial", 8)).pack(pady=2)
github_link = ttk.Label(footer_frame, text="🔗 GitHub: Hero Zero Bot", font=("Arial", 8), foreground="blue", cursor="hand2")
github_link.pack(pady=2)
github_link.bind("<Button-1>", lambda e: open_github())

apply_theme_to_titlebar(root)
root.mainloop()






