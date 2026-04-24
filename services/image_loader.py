import os
from pathlib import Path
from PIL import Image
from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool
from utils.logger import get_logger

logger = get_logger(__name__)

class ThumbnailWorker(QRunnable):
    def __init__(self, image_path, cache_dir, signals):
        super().__init__()
        self.image_path = image_path
        self.cache_dir = cache_dir
        self.signals = signals
        self.thumbnail_size = (300, 300)

    def run(self):
        try:
            img_path = Path(self.image_path)
            cache_path = self.cache_dir / f"{img_path.stem}_{img_path.stat().st_size}{img_path.suffix}"
            
            if not cache_path.exists():
                img = Image.open(img_path)
                img.thumbnail(self.thumbnail_size)
                if img.mode in ("RGBA", "P") and cache_path.suffix.lower() in ('.jpg', '.jpeg'):
                    img = img.convert("RGB")
                img.save(cache_path)
                
            self.signals.result.emit(str(cache_path), self.image_path)
        except Exception as e:
            logger.error(f"Failed to generate thumbnail for {self.image_path}: {e}")
            self.signals.result.emit("", self.image_path)

class WorkerSignals(QObject):
    result = Signal(str, str) # thumbnail_path, original_path

class ImageLoader(QObject):
    thumbnail_ready = Signal(str, str)
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.webp'}
    
    def __init__(self, cache_dir="/tmp/fondos_app_cache"):
        super().__init__()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.threadpool = QThreadPool()
        self.active_signals = set()
    
    def get_images_in_folder(self, folder_path):
        path = Path(folder_path)
        if not path.exists() or not path.is_dir():
            return []
        
        images = []
        try:
            for file in path.iterdir():
                if file.is_file() and file.suffix.lower() in self.SUPPORTED_FORMATS:
                    images.append(str(file))
        except Exception as e:
            logger.error(f"Error reading directory {folder_path}: {e}")
        return sorted(images)

    def request_thumbnail(self, image_path):
        signals = WorkerSignals()
        signals.result.connect(self.thumbnail_ready.emit)
        
        # Prevent garbage collection of signals before thread finishes
        self.active_signals.add(signals)
        signals.result.connect(lambda th, org: self.active_signals.discard(signals))
        
        worker = ThumbnailWorker(image_path, self.cache_dir, signals)
        self.threadpool.start(worker)
