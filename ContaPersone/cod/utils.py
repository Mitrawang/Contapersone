import cv2
import logging
from typing import Tuple, List

logger = logging.getLogger(__name__)


def get_bbox_center(x1: float, y1: float, x2: float, y2: float) -> Tuple[float, float]:
    """
    Calcola il centro di un bounding box
    
    Args:
        x1, y1: Angolo superiore sinistro
        x2, y2: Angolo inferiore destro
        
    Returns:
        Tuple (cx, cy) del centro
    """
    return (x1 + x2) / 2, (y1 + y2) / 2


def get_bbox_height(y1: float, y2: float) -> float:
    """
    Calcola l'altezza di un bounding box
    
    Args:
        y1: Coordinata Y superiore
        y2: Coordinata Y inferiore
        
    Returns:
        Altezza del bounding box
    """
    return y2 - y1


def get_bbox_width(x1: float, x2: float) -> float:
    """
    Calcola la larghezza di un bounding box
    
    Args:
        x1: Coordinata X sinistra
        x2: Coordinata X destra
        
    Returns:
        Larghezza del bounding box
    """
    return x2 - x1


def get_bbox_area(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Calcola l'area di un bounding box
    
    Args:
        x1, y1, x2, y2: Coordinate del bounding box
        
    Returns:
        Area del bounding box
    """
    width = get_bbox_width(x1, x2)
    height = get_bbox_height(y1, y2)
    return width * height


def filter_detections_by_area(
    detections: List[List[float]], 
    min_area: float = 0, 
    max_area: float = float('inf')
) -> List[List[float]]:
    """
    Filtra le detections per area
    
    Args:
        detections: Lista di [x1, y1, x2, y2, confidence]
        min_area: Area minima (pixel²)
        max_area: Area massima (pixel²)
        
    Returns:
        Lista di detections filtrate
    """
    filtered = []
    for det in detections:
        x1, y1, x2, y2, conf = det
        area = get_bbox_area(x1, y1, x2, y2)
        
        if min_area <= area <= max_area:
            filtered.append(det)
    
    return filtered


def filter_detections_by_confidence(
    detections: List[List[float]], 
    min_conf: float = 0.0
) -> List[List[float]]:
    """
    Filtra le detections per confidence
    
    Args:
        detections: Lista di [x1, y1, x2, y2, confidence]
        min_conf: Confidence minima (0-1)
        
    Returns:
        Lista di detections filtrate
    """
    return [det for det in detections if det[4] >= min_conf]


def draw_bbox(
    frame,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    label: str = "",
    color: Tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2
) -> None:
    """
    Disegna un rettangolo con etichetta su un frame
    
    Args:
        frame: Frame OpenCV
        x1, y1, x2, y2: Coordinate del bbox
        label: Testo da visualizzare
        color: Colore BGR
        thickness: Spessore linea
    """
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
    
    if label:
        cv2.putText(
            frame, label, (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2
        )


def draw_line(
    frame,
    y: int,
    color: Tuple[int, int, int] = (0, 0, 255),
    thickness: int = 2
) -> None:
    """
    Disegna una linea orizzontale su un frame
    
    Args:
        frame: Frame OpenCV
        y: Coordinata Y della linea
        color: Colore BGR
        thickness: Spessore linea
    """
    height, width = frame.shape[:2]
    cv2.line(frame, (0, y), (width, y), color, thickness)


def draw_text(
    frame,
    text: str,
    x: int,
    y: int,
    color: Tuple[int, int, int] = (0, 255, 0),
    font_scale: float = 1,
    thickness: int = 2
) -> None:
    """
    Disegna testo su un frame
    
    Args:
        frame: Frame OpenCV
        text: Testo da visualizzare
        x, y: Coordinata di posizionamento
        color: Colore BGR
        font_scale: Scala del font
        thickness: Spessore del testo
    """
    cv2.putText(
        frame, text, (x, y),
        cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness
    )

