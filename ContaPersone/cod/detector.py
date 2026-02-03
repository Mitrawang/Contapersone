import cv2
from ultralytics import YOLO
import logging

logger = logging.getLogger(__name__)


class PersonDetector:
    """Rileva persone nei frame usando YOLOv8n"""
    
    PERSON_CLASS_ID = 0
    BOX_COLOR = (0, 255, 0)
    BOX_THICKNESS = 2
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    FONT_SCALE = 0.5
    FONT_THICKNESS = 2
    TEXT_OFFSET = 5

    def __init__(self, model_path: str):
        """
        Args:
            model_path: Percorso del modello YOLO
        """
        try:
            self.model = YOLO(model_path)
            logger.info(f"Modello caricato da: {model_path}")
        except FileNotFoundError:
            logger.error(f"Modello non trovato: {model_path}")
            raise

    def detect(self, fotogramma, confidenza_min: float = 0.3) -> list:
        """
        Rileva persone nel fotogramma
        
        Args:
            fotogramma: Fotogramma video da analizzare
            confidenza_min: Soglia minima di confidenza (0-1)
            
        Returns:
            Lista di rilevamenti [x_inizio, y_inizio, x_fine, y_fine, confidenza]
        """
        risultati = self.model(fotogramma, conf=confidenza_min, verbose=False)[0]
        rilevamenti = []

        for casella in risultati.boxes:
            if int(casella.cls[0]) == self.PERSON_CLASS_ID:
                x_inizio, y_inizio, x_fine, y_fine = casella.xyxy[0].tolist()
                punteggio_confidenza = float(casella.conf[0].item())
                rilevamenti.append([x_inizio, y_inizio, x_fine, y_fine, punteggio_confidenza])

        return rilevamenti

    def draw_detections(self, fotogramma, oggetti_tracciati) -> None:
        """
        Disegna i rettangoli e gli ID degli oggetti tracciati
        
        Args:
            fotogramma: Fotogramma video su cui disegnare
            oggetti_tracciati: Lista di oggetti tracciati [x_inizio, y_inizio, x_fine, y_fine, id_traccia]
        """
        for x_inizio, y_inizio, x_fine, y_fine, id_traccia in oggetti_tracciati:
            x_inizio, y_inizio, x_fine, y_fine = int(x_inizio), int(y_inizio), int(x_fine), int(y_fine)
            
            cv2.rectangle(fotogramma, (x_inizio, y_inizio), (x_fine, y_fine), self.BOX_COLOR, self.BOX_THICKNESS)
            cv2.putText(fotogramma, f"ID {int(id_traccia)}", (x_inizio, y_inizio - self.TEXT_OFFSET),
                        self.FONT, self.FONT_SCALE, self.BOX_COLOR, self.FONT_THICKNESS) 
