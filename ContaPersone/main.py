import cv2
import logging
import sys
import requests
import time
import threading  # Importato per l'invio asincrono
from pathlib import Path

from cod.detector import PersonDetector
from cod.tracker import Tracker
from cod.counter import PeopleCounter

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurazione
VIDEO_SOURCE = 0  # 0 per webcam, oppure path a file video
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "yolov8n.pt"
LINE_Y = 250
WINDOW_NAME = "PeopleCounterFiera"
DETECTION_CONFIDENCE = 0.3
ESC_KEY = 27

def check_model_exists(model_path: str) -> bool:
    """Verifica se il modello esiste"""
    return Path(model_path).exists()

def invia_dati(stats):
    """Invia i dati al server (eseguita in un thread separato)"""
    url = "https://contapersone.ittvive.it/api_update.php"
    
    payload = {
        "entrate": stats["entered"],
        "uscite": stats["exited"],
        "presenti": stats["entered"] - stats["exited"],
        "key": "CHIAVE_SEGRETA"
    }
    
    try:
        # Il timeout qui non bloccherà più il video principale
        response = requests.post(url, data=payload, timeout=5)
        if response.status_code == 200:
            logger.info(f"✅ Dati inviati: entrate={payload['entrate']}, uscite={payload['uscite']}")
        else:
            logger.warning(f"⚠️ Errore HTTP {response.status_code}: {response.text}")
        
    except Exception as e:
        logger.warning(f"❌ Errore invio dati: {e}")

def main():
    """Funzione principale dell'applicazione"""
    
    if not check_model_exists(MODEL_PATH):
        logger.error(f"Modello non trovato: {MODEL_PATH}")
        sys.exit(1)
    
    try:
        logger.info("Inizializzazione componenti...")
        detector = PersonDetector(MODEL_PATH)
        tracker = Tracker()
        counter = PeopleCounter(LINE_Y)
        
        cattura_video = cv2.VideoCapture(VIDEO_SOURCE)
        if not cattura_video.isOpened():
            logger.error(f"Impossibile aprire sorgente video: {VIDEO_SOURCE}")
            sys.exit(1)
        
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        logger.info("Avvio elaborazione video... (Premi ESC per uscire)")
        
        ultimo_invio = time.time()
        numero_fotogrammi = 0

        while True:
            lettura_riuscita, fotogramma = cattura_video.read()
            if not lettura_riuscita:
                logger.warning("Fine del video raggiunta")
                break
            
            numero_fotogrammi += 1
            
            # Elaborazione AI
            rilevamenti = detector.detect(fotogramma, confidenza_min=DETECTION_CONFIDENCE)
            
            oggetti_tracciati = tracker.update(rilevamenti)
            
            counter.update(oggetti_tracciati)
          
            

            # Invio dati ogni 5 secondi senza bloccare il video
            if time.time() - ultimo_invio > 5:
                statistiche = counter.get_stats()
                # Creiamo un thread per gestire l'invio in background
                thread_invio = threading.Thread(target=invia_dati, args=(statistiche,))
                thread_invio.daemon = True
                thread_invio.start()
                
                ultimo_invio = time.time()

            # Disegno e visualizzazione
            counter.draw(fotogramma)
            detector.draw_detections(fotogramma, oggetti_tracciati)
            cv2.imshow(WINDOW_NAME, fotogramma)
            
            if cv2.waitKey(1) & 0xFF == ESC_KEY:
                logger.info("Interruzione da parte dell'utente")
                break
        
        logger.info(f"Fine: {counter.get_stats()}")
        
    except Exception as e:
        logger.error(f"Errore: {e}", exc_info=True)
    
    finally:
        cattura_video.release()
        cv2.destroyAllWindows()
        logger.info("Risorse liberate")

if __name__ == "__main__":
    main()
