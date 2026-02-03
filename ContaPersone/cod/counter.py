import cv2
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class PeopleCounter:
    """Conta le persone che attraversano una linea di demarcazione"""
    
    LINE_COLOR = (0, 0, 255)  # Rosso in RGB
    LINE_THICKNESS = 2
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    FONT_SCALE = 1
    FONT_COLOR = (0, 255, 0)  # Verde in RGB
    FONT_THICKNESS = 2
    TEXT_ENTERED_X = 10
    TEXT_ENTERED_Y = 25
    TEXT_EXITED_X = 10
    TEXT_EXITED_Y = 55
    TEXT_TOTAL_X = 10
    TEXT_TOTAL_Y = 85
    COOLDOWN_FRAMES = 10  # frames to ignore further counts for a track after a crossing
    MAX_MISSED_FRAMES = 5  # frames to wait before removing an unseen track
    HYSTERESIS = 6  # pixels margin to avoid jitter on the counting line

    def __init__(self, line_y: int):
        """
        Args:
            line_y: Coordinata y della linea di conteggio
        """
        if not isinstance(line_y, int) or line_y < 0:
            raise ValueError(f"line_y deve essere un intero positivo, ricevuto: {line_y}")
        
        self.line_y = line_y
        self.entered = 0
        self.exited = 0
        # last_positions: id -> {"y": centro_y, "cooldown": int, "missed": int, "state": "above"|"below"|"on_line"}
        self.last_positions: Dict[int, Dict[str, int]] = {}
        logger.info(f"PeopleCounter inizializzato con line_y={line_y}")

    def _calcola_centro_y(self, y_inizio: float, y_fine: float) -> int:
        """
        Calcola il centro Y del riquadro di delimitazione
        
        Args:
            y_inizio: Coordinata Y superiore
            y_fine: Coordinata Y inferiore
            
        Returns:
            Centro Y come intero
        """
        return int((y_inizio + y_fine) / 2)

    def update(self, oggetti_tracciati: List[Tuple[float, float, float, float, int]]) -> None:
        """
        Aggiorna i contatori in base agli oggetti tracciati
        Implementa deduplicazione per id e una logica a stati (above/on_line/below)
        per evitare conteggi ripetuti dovuti a jitter o a tracce che cambiano ID.

        Args:
            oggetti_tracciati: Lista di (x_inizio, y_inizio, x_fine, y_fine, id_traccia)
        """
        # Deduplica per ID: conserva l'ultimo centro Y osservato per ogni id
        detections_by_id: Dict[int, int] = {}
        for x_inizio, y_inizio, x_fine, y_fine, id_traccia in oggetti_tracciati:
            centro_y = self._calcola_centro_y(y_inizio, y_fine)
            detections_by_id[int(id_traccia)] = centro_y

        seen_ids = set(detections_by_id.keys())

        for id_traccia, centro_y in detections_by_id.items():
            entry = self.last_positions.get(id_traccia)

            if entry is None:
                # Prima volta che vediamo questa traccia: determina stato iniziale con isteresi
                if centro_y < self.line_y - self.HYSTERESIS:
                    stato = "above"
                elif centro_y > self.line_y + self.HYSTERESIS:
                    stato = "below"
                else:
                    stato = "on_line"

                self.last_positions[id_traccia] = {"y": centro_y, "cooldown": 0, "missed": 0, "state": stato}
                continue

            prev_state = entry.get("state", "unknown")
            cooldown = entry.get("cooldown", 0)

            # Determina stato corrente con isteresi
            if centro_y < self.line_y - self.HYSTERESIS:
                current_state = "above"
            elif centro_y > self.line_y + self.HYSTERESIS:
                current_state = "below"
            else:
                current_state = "on_line"

            # Conta solo se non siamo in cooldown e lo stato è passato da above->below o below->above
            if cooldown <= 0:
                if prev_state == "above" and current_state == "below":
                    self.entered += 1
                    entry["cooldown"] = self.COOLDOWN_FRAMES
                    logger.debug(f"Persona ID {id_traccia} entrata (stato: {prev_state} -> {current_state}, y: {entry['y']} -> {centro_y})")
                elif prev_state == "below" and current_state == "above":
                    self.exited += 1
                    entry["cooldown"] = self.COOLDOWN_FRAMES
                    logger.debug(f"Persona ID {id_traccia} uscita (stato: {prev_state} -> {current_state}, y: {entry['y']} -> {centro_y})")

            # Aggiorna dati della traccia
            entry["y"] = centro_y
            entry["state"] = current_state
            entry["missed"] = 0

        # Decrementa i cooldown per tutte le tracce
        for entry in self.last_positions.values():
            if entry.get("cooldown", 0) > 0:
                entry["cooldown"] -= 1

        # Incrementa missed per tracce non viste e rimuovi se troppo vecchie
        ids_da_rimuovere = []
        for id_traccia, entry in list(self.last_positions.items()):
            if id_traccia not in seen_ids:
                entry["missed"] = entry.get("missed", 0) + 1
                if entry["missed"] > self.MAX_MISSED_FRAMES:
                    ids_da_rimuovere.append(id_traccia)

        for id_t in ids_da_rimuovere:
            del self.last_positions[id_t]

    def draw(self, fotogramma) -> None:
        """
        Disegna la linea di conteggio e i contatori
        
        Args:
            fotogramma: Fotogramma OpenCV su cui disegnare
        """
        altezza, larghezza = fotogramma.shape[:2]
        
        # Disegna linea di conteggio
        cv2.line(fotogramma, (0, self.line_y), (larghezza, self.line_y), 
                self.LINE_COLOR, self.LINE_THICKNESS)
        
        # Disegna contatori
        cv2.putText(fotogramma, f"Entrati   {self.entered}", 
                   (self.TEXT_ENTERED_X, self.TEXT_ENTERED_Y),
                   self.FONT, self.FONT_SCALE, self.FONT_COLOR, self.FONT_THICKNESS)
        cv2.putText(fotogramma, f"Usciti    {self.exited}", 
                   (self.TEXT_EXITED_X, self.TEXT_EXITED_Y),
                   self.FONT, self.FONT_SCALE, self.FONT_COLOR, self.FONT_THICKNESS)
        cv2.putText(fotogramma, f"Totale    {self.entered + self.exited}", 
                   (self.TEXT_TOTAL_X, self.TEXT_TOTAL_Y),
                   self.FONT, self.FONT_SCALE, self.FONT_COLOR, self.FONT_THICKNESS)

    def get_stats(self) -> Dict[str, int]:
        """
        Restituisce le statistiche attuali
        
        Returns:
            Dizionario con entered, exited e total
        """
        return {
            "entered": self.entered,
            "exited": self.exited,
            "total": self.entered + self.exited
        }

    def reset(self) -> None:
        """Resetta i contatori e le posizioni tracciati"""
        self.entered = 0
        self.exited = 0
        self.last_positions.clear()
        logger.info("Contatori resettati")
