from .database import Database, list_no_hidden
from .analysis import FlyDetector, InspectDetectedFlies
from .stats_and_plots import StatsPlotter

import os
from typing import List, Optional


CROPPING_BUFFER_ZONE = 50
MIN_DISTANCE = 25
THRESHOLD = 0.25
MIN_CLIMBING_HEIGHT = 600 


class API:
    
    def __init__(self, root_dir: str):
        self.database = Database(root_dir)
        

    def detect_flies(self, 
                     file_ids: List,
                     cropping_buffer_zone: int=CROPPING_BUFFER_ZONE, 
                     min_climbing_height: int=MIN_CLIMBING_HEIGHT, 
                     threshold: float=THRESHOLD, 
                     min_distance: int=MIN_DISTANCE,
                     overwrite: bool=False,
                     quick_view: bool=False):
        
        for file_id in file_ids:
            fly_detector = FlyDetector(file_id = file_id, 
                                       database = self.database,
                                       cropping_buffer_zone = cropping_buffer_zone, 
                                       min_climbing_height = min_climbing_height, 
                                       threshold = threshold, 
                                       min_distance = min_distance,
                                       overwrite = overwrite,
                                       quick_view = quick_view)
            self.database = fly_detector.run()

            
    def inspect_detection_quality(self, index: Optional[str]=None, file_id: Optional[str]=None, time_passed: Optional[int]=None):
        if type(index) == str:
            self.index = index
        elif (type(file_id) == str) & (type(time_passed) == int):
            temp_file_info = self.database.get_file_info_df(file_id = file_id)
            self.index = temp_file_info['index'][temp_file_info['time_passed'].index(time_passed)]
        else:
            raise TypeError('Either "index" or "file_id" and "time_passed" have to be provided')
            
        inspect_detected_flies = InspectDetectedFlies(index = self.index, database = self.database)
        inspect_detected_flies.plot_results()
            
    
    def plot_results(self, save: bool=False, show: bool=True):
        stats_plotter = StatsPlotter(database = self.database)
        stats_plotter.show_results(save=save, show=show)
    
    
    def save_results(self, prefix: str=''):
        self.database.save_file_infos(prefix = prefix)
        
    def load_results(self):
        self.database.load_file_infos()