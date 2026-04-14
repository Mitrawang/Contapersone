import cv2
import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

@dataclass
class TrackState:
    """Struttura dati per lo stato della traccia con memoria di movimento"""
    __slots__ = ['last_y', 'cooldown', 'missed', 'state']
    last_y: int
    cooldown: int
    missed: int
    state: str  # "above", "below", "neutral"

class PeopleCounter:
    """Conta le persone con filtraggio del rumore e logica di direzione"""
    
    LINE_COLOR = (0, 0, 255)
    LINE_THICKNESS = 2
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    FONT_SCALE = 0.8
    FONT_COLOR = (0, 255, 0)
    FONT_THICKNESS = 2
    
    # Margine di sicurezza per definire la zona neutra sulla linea
    HYSTERESIS = 5 

    def __init__(self, line_y: int, fps: int = 30):
        if line_y < 0:
            raise ValueError(f"line_y deve essere positivo, ricevuto: {line_y}")
        
        self.line_y = line_y
        self.fps = fps
        
        # Cooldown richiesto di 5 frame
        self.cooldown_frames = 5
        # Timeout per eliminare tracce perse (circa 1 secondo di tolleranza)
        self.max_missed_frames = fps 
        
        self.entered = 0
        self.exited = 0
        self.last_positions: Dict[int, TrackState] = {}
        
        logger.info(f"Counter Ottimizzato: line_y={line_y}, Cooldown={self.cooldown_frames}")

    def update(self, oggetti_tracciati: List[Tuple[float, float, float, float, int]]) -> None:
        """
        Aggiorna i contatori analizzando la traiettoria degli ID tracciati.
        """
        seen_ids = set()

        for x_inizio, y_inizio, x_fine, y_fine, id_traccia in oggetti_tracciati:
            id_traccia = int(id_traccia)
            seen_ids.add(id_traccia)
            
            # Calcolo centro Y
            centro_y = int((y_inizio + y_fine) // 2)
            
            # Determina stato rispetto alla linea
            if centro_y < (self.line_y - self.HYSTERESIS):
                current_state = "above"
            elif centro_y > (self.line_y + self.HYSTERESIS):
                current_state = "below"
            else:
                current_state = "neutral"

            # Inizializzazione nuova traccia
            if id_traccia not in self.last_positions:
                self.last_positions[id_traccia] = TrackState(
                    last_y=centro_y, 
                    cooldown=0, 
                    missed=0, 
                    state=current_state
                )
                continue

            entry = self.last_positions[id_traccia]
            
            # LOGICA DI CONTEGGIO OTTIMIZZATA
            if entry.cooldown <= 0:
                # Caso 1: Entrata (da Sopra a Sotto)
                # Verifica: lo stato precedente era "above" e ora è "below" (o attraversa la zona neutra)
                if entry.state == "above" and centro_y > self.line_y:
                    self.entered += 1
                    entry.cooldown = self.cooldown_frames
                
                # Caso 2: Uscita (da Sotto a Sopra)
                elif entry.state == "below" and centro_y < self.line_y:
                    self.exited += 1
                    entry.cooldown = self.cooldown_frames

            # Aggiornamento stato per il prossimo frame
            entry.last_y = centro_y
            # Aggiorniamo lo stato solo se siamo fuori dalla zona di isteresi
            if current_state != "neutral":
                entry.state = current_state
            
            entry.missed = 0

        # Gestione Cooldown e Pulizia
        for id_t in list(self.last_positions.keys()):
            entry = self.last_positions[id_t]
            
            if entry.cooldown > 0:
                entry.cooldown -= 1
                
            if id_t not in seen_ids:
                entry.missed += 1
                if entry.missed > self.max_missed_frames:
                    del self.last_positions[id_t]

    def draw(self, fotogramma) -> None:
        """Renderizza i dati sul frame"""
        h, w = fotogramma.shape[:2]
        cv2.line(fotogramma, (0, self.line_y), (w, self.line_y), 
                 self.LINE_COLOR, self.LINE_THICKNESS)
        
        # Overlay semi-trasparente per i testi (opzionale, migliora leggibilità)
        stats = [
            f"IN : {self.entered}",
            f"OUT: {self.exited}",
            f"TOT: {self.entered + self.exited}"
        ]
        
        for i, text in enumerate(stats):
            cv2.putText(fotogramma, text, (20, 40 + (i * 35)), 
                        self.FONT, self.FONT_SCALE, self.FONT_COLOR, self.FONT_THICKNESS)

    def get_stats(self) -> Dict[str, int]:
        return {"entered": self.entered, "exited": self.exited, "total": self.entered + self.exited}
