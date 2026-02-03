
import math
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class Tracker:
    """Traccia gli oggetti rilevati da un frame all'altro usando distanza euclidea"""
    
    DEFAULT_MAX_DISTANCE = 120  # Aumentato per movimenti veloci
    DEFAULT_MAX_AGE = 30

    def __init__(self, max_distance: float = DEFAULT_MAX_DISTANCE, max_age: int = DEFAULT_MAX_AGE):
        """
        Args:
            max_distance: Distanza massima per associare una detection a un track
            max_age: Numero di frame prima di eliminare un track non aggiornato
        """
        if max_distance <= 0:
            raise ValueError(f"max_distance deve essere positivo, ricevuto: {max_distance}")
        if max_age <= 0:
            raise ValueError(f"max_age deve essere positivo, ricevuto: {max_age}")
        
        self.next_id = 0
        self.tracks: Dict[int, Dict] = {}  # {id: {"position": (x, y), "velocity": (vx, vy), "age": 0}}
        self.max_distance = max_distance
        self.max_age = max_age
        logger.info(f"Tracker inizializzato con max_distance={max_distance}, max_age={max_age}")

    def _calcola_centro(self, x_inizio: float, y_inizio: float, x_fine: float, y_fine: float) -> Tuple[float, float]:
        """
        Calcola il centro del riquadro di delimitazione
        
        Args:
            x_inizio, y_inizio: Coordinate angolo superiore sinistro
            x_fine, y_fine: Coordinate angolo inferiore destro
            
        Returns:
            Tuple (centro_x, centro_y) del centro
        """
        return (x_inizio + x_fine) / 2, (y_inizio + y_fine) / 2

    def _trova_traccia_piu_vicina(self, centro_x: float, centro_y: float) -> Tuple[int | None, float]:
        """
        Trova la traccia più vicina al rilevamento corrente
        Usa predizione di movimento per anticipare la posizione
        
        Args:
            centro_x, centro_y: Coordinate del centro del rilevamento
            
        Returns:
            Tuple (id_traccia, distanza) o (None, inf) se nessuna traccia è sufficientemente vicina
        """
        id_traccia_piu_vicina = None
        distanza_minima = float('inf')

        for id_traccia, dati_traccia in self.tracks.items():
            traccia_x, traccia_y = dati_traccia["position"]
            # Predizione: aggiungi velocità per anticipare il movimento
            velocita_x, velocita_y = dati_traccia.get("velocity", (0, 0))
            pos_predetta_x = traccia_x + velocita_x
            pos_predetta_y = traccia_y + velocita_y
            
            distanza = math.hypot(centro_x - pos_predetta_x, centro_y - pos_predetta_y)
            
            if distanza < distanza_minima and distanza < self.max_distance:
                distanza_minima = distanza
                id_traccia_piu_vicina = id_traccia

        return id_traccia_piu_vicina, distanza_minima

    def _pulisci_tracce_vecchie(self) -> None:
        """Rimuove le tracce che non sono state aggiornate per troppi fotogrammi"""
        id_tracce_da_rimuovere = [
            id_traccia for id_traccia, dati_traccia in self.tracks.items()
            if dati_traccia["age"] > self.max_age
        ]
        
        for id_traccia in id_tracce_da_rimuovere:
            del self.tracks[id_traccia]
            logger.debug(f"Traccia ID {id_traccia} rimossa (troppo vecchia)")

    def update(self, rilevamenti: List[List[float]]) -> List[List]:
        """
        Aggiorna le tracce in base ai nuovi rilevamenti
        
        Args:
            rilevamenti: Lista di [x_inizio, y_inizio, x_fine, y_fine, confidenza]
            
        Returns:
            Lista di tracce aggiornate [x_inizio, y_inizio, x_fine, y_fine, id_traccia]
        """
        tracce_aggiornate = []
        id_tracce_aggiornate = set()

        for rilevamento in rilevamenti:
            x_inizio, y_inizio, x_fine, y_fine, confidenza = rilevamento
            centro_x, centro_y = self._calcola_centro(x_inizio, y_inizio, x_fine, y_fine)

            # Trova la traccia più vicina
            id_traccia_assegnato, distanza_minima = self._trova_traccia_piu_vicina(centro_x, centro_y)

            # Se nessuna traccia disponibile, crea una nuova
            if id_traccia_assegnato is None:
                id_traccia_assegnato = self.next_id
                self.next_id += 1
                logger.debug(f"Nuova traccia creata: ID {id_traccia_assegnato}")
                self.tracks[id_traccia_assegnato] = {"position": (centro_x, centro_y), "velocity": (0, 0), "age": 0}
            else:
                # Calcola velocità per predizione futura
                pos_precedente_x, pos_precedente_y = self.tracks[id_traccia_assegnato]["position"]
                velocita_x = centro_x - pos_precedente_x
                velocita_y = centro_y - pos_precedente_y
                self.tracks[id_traccia_assegnato] = {"position": (centro_x, centro_y), "velocity": (velocita_x, velocita_y), "age": 0}

            id_tracce_aggiornate.add(id_traccia_assegnato)
            tracce_aggiornate.append([x_inizio, y_inizio, x_fine, y_fine, id_traccia_assegnato])

        # Incrementa l'age delle tracce non aggiornate
        for id_traccia in self.tracks:
            if id_traccia not in id_tracce_aggiornate:
                self.tracks[id_traccia]["age"] += 1

        # Rimuovi le tracce troppo vecchie
        self._pulisci_tracce_vecchie()

        return tracce_aggiornate

    def get_stats(self) -> Dict[str, int]:
        """
        Restituisce le statistiche attuali del tracker
        
        Returns:
            Dizionario con numero di track attivi e prossimo ID
        """
        return {
            "active_tracks": len(self.tracks),
            "next_id": self.next_id
        }

    def reset(self) -> None:
        """Resetta il tracker eliminando tutti i track"""
        self.tracks.clear()
        self.next_id = 0
        logger.info("Tracker resettato")
