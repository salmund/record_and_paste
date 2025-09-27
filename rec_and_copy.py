import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import keyboard
import tempfile
import os
import platform
import subprocess
import time
from plyer import notification # Import pour les notifications

# --- CONFIGURATION ---
HOTKEY = 'ctrl+alt+r' 
SAMPLE_RATE = 44100
CHANNELS = 1

# --- Variables globales ---
is_recording = False
recorded_frames = []

def send_notification(title, message):
    """Envoie une notification de bureau simple."""
    try:
        notification.notify(
            title=title,
            message=message,
            app_name='Audio Recorder',
            timeout=5 # La notif disparaît après 5 secondes
        )
    except Exception as e:
        print(f"(!) Pas pu envoyer de notif. Erreur: {e}")

def copy_file_to_clipboard(filepath):
    """Copie un fichier dans le presse-papiers (inchangé)."""
    system = platform.system()
    try:
        if system == 'Windows':
            command = f'powershell -command "Set-Clipboard -Path \\"{filepath}\\""'
            subprocess.run(command, check=True)
        elif system == 'Darwin': # macOS
            command = f'osascript -e \'set the clipboard to POSIX file "{filepath}"\''
            subprocess.run(command, shell=True, check=True)
        elif system == 'Linux':
            command = f'xclip -selection clipboard -t text/uri-list -i <<< "file://{filepath}"'
            subprocess.run(command, shell=True, check=True, executable='/bin/bash')
        else:
            print(f"❌ OS non supporté : {system}")
            return False
        return True
    except Exception as e:
        print(f"❌ Erreur en copiant le fichier. Détails : {e}")
        return False

def callback(indata, frames, time, status):
    """Fonction appelée pour chaque bloc audio."""
    if is_recording:
        recorded_frames.append(indata.copy())

def toggle_recording():
    """Gère le début et la fin de l'enregistrement."""
    global is_recording, recorded_frames

    is_recording = not is_recording

    if is_recording:
        recorded_frames = []
        print("🔴 REC ON...")
        send_notification("🔴 Enregistrement démarré", f"Appuie sur {HOTKEY.upper()} pour arrêter.")
    else:
        print("⚫ REC OFF... Traitement en cours...")
        
        if not recorded_frames:
            print("🤔 Rien n'a été enregistré.")
            return

        # 1. Sauvegarder en .wav temporaire
        recording = np.concatenate(recorded_frames, axis=0)
        temp_wav_path = tempfile.mktemp(suffix='.wav', prefix='rec_')
        wav.write(temp_wav_path, SAMPLE_RATE, recording)
        print(f"   Fichier WAV temporaire créé : {os.path.basename(temp_wav_path)}")

        # 2. Convertir le .wav en .m4a avec FFmpeg
        temp_m4a_path = tempfile.mktemp(suffix='.m4a', prefix='vocal_')
        try:
            # -y pour écraser sans demander, -c:a aac pour le codec, -b:a 128k pour la qualité
            command = f'ffmpeg -i "{temp_wav_path}" -y -c:a aac -b:a 128k "{temp_m4a_path}"'
            subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"   Fichier M4A final créé : {os.path.basename(temp_m4a_path)}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print("❌ ERREUR: FFmpeg a planté ou n'est pas installé !")
            print("   Assure-toi que FFmpeg est bien installé et accessible dans ton PATH.")
            send_notification("❌ Erreur d'enregistrement", "La conversion avec FFmpeg a échoué.")
            os.remove(temp_wav_path) # Nettoyage
            return
        finally:
            # 3. Supprimer le .wav temporaire qui ne sert plus à rien
            if os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)

        # 4. Copier le .m4a dans le presse-papiers
        if copy_file_to_clipboard(temp_m4a_path):
            send_notification("✅ Prêt à coller !", f"Ton fichier audio ({os.path.basename(temp_m4a_path)}) est dans le presse-papiers.")
        else:
            send_notification("❌ Erreur de copie", "Le fichier a été créé mais n'a pas pu être copié.")

# --- Programme Principal ---
if __name__ == "__main__":
    print("🚀 Script 2.0 prêt ! En attente du raccourci...")
    print(f"   Appuie sur '{HOTKEY.upper()}' pour démarrer/arrêter.")
    print("   Pour quitter, fais Ctrl+C dans ce terminal.")

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, callback=callback):
        keyboard.add_hotkey(HOTKEY, toggle_recording, suppress=True)
        while True:
            time.sleep(1)
