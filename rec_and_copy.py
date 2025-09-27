import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import keyboard
import tempfile
import os
import platform
import subprocess
import time

# --- CONFIGURATION ---
HOTKEY = 'ctrl+alt+r' # Le raccourci pour démarrer/arrêter
SAMPLE_RATE = 44100   # Qualité audio (standard CD)
CHANNELS = 1          # 1 pour mono, 2 pour stéréo

# --- Variables globales pour gérer l'enregistrement ---
is_recording = False
recorded_frames = []

def copy_file_to_clipboard(filepath):
    """
    Copie un fichier dans le presse-papiers.
    La méthode dépend de ton système d'exploitation (OS).
    """
    system = platform.system()
    try:
        if system == 'Windows':
            # Sur Windows, on utilise PowerShell, c'est le plus simple
            command = f'powershell -command "Set-Clipboard -Path \\"{filepath}\\""'
            subprocess.run(command, check=True)
        elif system == 'Darwin': # macOS
            # Sur macOS, on utilise osascript
            command = f'osascript -e \'set the clipboard to POSIX file "{filepath}"\''
            subprocess.run(command, shell=True, check=True)
        elif system == 'Linux':
            # Sur Linux, on utilise xclip. Il faut l'installer (sudo apt-get install xclip)
            command = f'xclip -selection clipboard -t text/uri-list -i <<< "file://{filepath}"'
            subprocess.run(command, shell=True, check=True, executable='/bin/bash')
        else:
            print(f"❌ Système d'exploitation non supporté pour la copie de fichier : {system}")
            return
            
        print(f"✅ Fichier '{os.path.basename(filepath)}' copié dans le presse-papiers !")
        print("   Tu peux le coller où tu veux (Ctrl+V) !")

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"❌ Oups, erreur en copiant le fichier. Détails : {e}")
        if system == 'Linux':
            print("   (Sur Linux, assure-toi d'avoir installé 'xclip' -> sudo apt-get install xclip)")


def callback(indata, frames, time, status):
    """Cette fonction est appelée pour chaque bloc audio enregistré."""
    if status:
        print(status)
    if is_recording:
        recorded_frames.append(indata.copy())

def toggle_recording():
    """Gère le début et la fin de l'enregistrement."""
    global is_recording, recorded_frames

    is_recording = not is_recording

    if is_recording:
        # Début de l'enregistrement
        recorded_frames = []
        print("🔴 REC ON... Appuie à nouveau sur le raccourci pour arrêter.")
    else:
        # Fin de l'enregistrement
        print("⚫ REC OFF... Sauvegarde en cours.")
        
        if not recorded_frames:
            print("🤔 Rien n'a été enregistré. Opération annulée.")
            return

        # Concatène tous les morceaux enregistrés
        recording = np.concatenate(recorded_frames, axis=0)

        # Crée un fichier temporaire pour sauvegarder l'audio
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav', prefix='vocal_')
        filepath = temp_file.name
        temp_file.close() # On le ferme pour que scipy puisse écrire dedans

        # Sauvegarde le fichier WAV
        wav.write(filepath, SAMPLE_RATE, recording)
        print(f"🎧 Fichier audio sauvegardé ici : {filepath}")
        
        # Copie le fichier dans le presse-papiers
        copy_file_to_clipboard(filepath)


# --- Programme Principal ---
if __name__ == "__main__":
    print("🚀 Script prêt ! En attente du raccourci...")
    print(f"   Appuie sur '{HOTKEY.upper()}' pour démarrer/arrêter l'enregistrement.")
    print("   Pour quitter le script, fais Ctrl+C dans ce terminal.")

    # On assigne la fonction au raccourci clavier
    keyboard.add_hotkey(HOTKEY, toggle_recording, suppress=True)

    # On démarre le flux audio en continu
    # Il écoute en permanence mais n'enregistre que quand is_recording = True
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, callback=callback):
        # Le script va attendre ici que tu l'arrêtes (Ctrl+C)
        # keyboard.wait() peut parfois causer des soucis, une boucle infinie est plus stable
        while True:
            time.sleep(1)
