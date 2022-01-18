from .database import Database, list_no_hidden
from .analysis import FlyDetector

import os
from typing import List


class API:
    
    def __init__(self, root_dir: str):
        self.database = Database(root_dir)
        

    def detect_flies(self, file_ids: List):
        for file_id in file_ids:
            self.database = FlyDetector(file_id = file_id, database = self.database)
