from .database import Database, list_no_hidden
from .analysis import FlyDetector

import os
from typing import List


class API:
    
    def __init__(self, root_dir: str):
        self.database = Database(root_dir)
        

    def detect_flies(self, file_ids: List):
        for file_id in file_ids:
            fly_detector = FlyDetector(file_id = file_id, database = self.database)
            self.database = fly_detector.run()
            
    def save_results(self, prefix: str):
        self.database.save_file_infos(prefix = prefix)
        
    def load_results(self):
        self.database.load_file_infos()
