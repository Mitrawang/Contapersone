import cv2
import logging
import sys
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
MODEL_PATH = "models/yolov8n.pt"
LINE_Y = 300
WINDOW_NAME = "PeopleCounterFiera"
DETECTION_CONFIDENCE = 0.3
ESC_KEY = 27


def check_model_exists(model_path: str) -> bool:
    """Verifica se il modello esiste"""
    return Path(model_path).exists()


def main():
    """Funzione principale dell'applicazione"""
    
    # Verifica modello
    if not check_model_exists(MODEL_PATH):
        logger.error(f"Modello non trovato: {MODEL_PATH}")
        sys.exit(1)
    
    try:
        # Inizializza componenti
        logger.info("Inizializzazione componenti...")
        detector = PersonDetector(MODEL_PATH)
        tracker = Tracker()
        counter = PeopleCounter(LINE_Y)
        
        # Apri sorgente video
        cattura_video = cv2.VideoCapture(VIDEO_SOURCE)
        if not cattura_video.isOpened():
            logger.error(f"Impossibile aprire sorgente video: {VIDEO_SOURCE}")
            sys.exit(1)
        
        # Imposta risoluzione e fullscreen
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        logger.info("Avvio elaborazione video... (Premi ESC per uscire)")
        numero_fotogrammi = 0
        
        # Loop principale
        while True:
            lettura_riuscita, fotogramma = cattura_video.read()
            if not lettura_riuscita:
                logger.warning("Fine del video raggiunta")
                break
            
            numero_fotogrammi += 1
            
            # Elaborazione fotogramma
            rilevamenti = detector.detect(fotogramma, confidenza_min=DETECTION_CONFIDENCE)
            oggetti_tracciati = tracker.update(rilevamenti)
            counter.update(oggetti_tracciati)
            
            # Disegna risultati
            counter.draw(fotogramma)
            detector.draw_detections(fotogramma, oggetti_tracciati)
            
            # Mostra fotogramma
            cv2.imshow(WINDOW_NAME, fotogramma)
            
            # Controlla input utente
            if cv2.waitKey(1) & 0xFF == ESC_KEY:
                logger.info("Interruzione da parte dell'utente")
                break
        
        # Statistiche finali
        statistiche = counter.get_stats()
        logger.info(f"Elaborazione completata: {numero_fotogrammi} fotogrammi processati")
        logger.info(f"Statistiche finali: {statistiche}")
        
    except Exception as e:
        logger.error(f"Errore durante l'elaborazione: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        # Pulizia risorse
        cattura_video.release()
        cv2.destroyAllWindows()
        logger.info("Risorse liberate")


if __name__ == "__main__":
    main()
