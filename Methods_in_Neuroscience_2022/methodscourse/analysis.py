import numpy as np
import math

import matplotlib.pyplot as plt
            
import imageio as iio
from skimage.feature import match_template
from skimage.feature import peak_local_max
from skimage.io import imread, imsave
            
from .database import Database, list_no_hidden

from typing import List, Dict, Tuple
            
    

class FlyDetector:
    
    def __init__(self, 
                 file_id: str, database: Database, 
                 cropping_buffer_zone: int, 
                 min_climbing_height: int,
                 threshold: float,
                 min_distance: int,
                 overwrite: bool,
                 quick_view: bool):
        self.file_id = file_id
        self.database = database
        self.cropping_buffer_zone = cropping_buffer_zone
        self.min_climbing_height = min_climbing_height
        self.threshold = threshold
        self.min_distance = min_distance
        self.detection_configs = {'cropping_buffer_zone': cropping_buffer_zone, 
                                  'min_climbing_height' : min_climbing_height, 
                                  'threshold': threshold,
                                  'min_distance': min_distance}
        self.file_info = self.database.get_file_info_df(file_id = self.file_id)
        self.overwrite = overwrite
        self.quick_view = quick_view
        


    def run(self) -> Database:
        times_to_analyze = list()
        for i in range(len(self.file_info['time_passed'])):
            if self.overwrite:
                times_to_analyze.append(self.file_info['time_passed'][i])
            else:
                if (self.file_info['all_detected_flies'][i] == None) or (math.isnan(self.file_info['all_detected_flies'][i])):
                    times_to_analyze.append(self.file_info['time_passed'][i])
            
        if len(times_to_analyze) > 0:
            if self.quick_view:
                times_to_analyze = [times_to_analyze[0]]
            for time_passed in times_to_analyze:
                all_fly_coords, vial_cropping_coords, corrected_fly_coords = self.detect_flies(time_passed = time_passed)
                self.database.add_detected_flies(file_id = self.file_id, 
                                                 time_passed = time_passed, 
                                                 all_fly_coords = all_fly_coords,
                                                 vial_cropping_coords = vial_cropping_coords, 
                                                 corrected_fly_coords = corrected_fly_coords, 
                                                 detection_configs = self.detection_configs)

        else:
            print(f'Flies were already annotated for file_id: {self.file_id} - continue with next file.')
            
        return self.database    
        
            
    def detect_flies(self, time_passed: int) -> Tuple[List, Tuple, List]:
        frame_index = time_passed*30

        reader = iio.get_reader(self.file_info['video_filepath'][0])
        image = reader.get_data(frame_index)
        reader.close()

        min_col_idx, max_col_idx = self.get_vial_cropping_info_from_foam_matching(image, self.database.foam_template)
        vial_cropping_coords = (min_col_idx-self.cropping_buffer_zone, max_col_idx+self.cropping_buffer_zone)
        vial = image[200:1000, vial_cropping_coords[0] - 100 : vial_cropping_coords[1] + 100]
        # make cropping adjustable while displayed item is always 100 pixels more on both sides?

        template_flies = list()
        for filename in list_no_hidden(f'{self.database.templates_dir}flies/'):
            template_flies.append(imread(f'{self.database.templates_dir}flies/{filename}'))
        template_bkgrs = list()
        for filename in list_no_hidden(f'{self.database.templates_dir}backgrounds/'):
            template_bkgrs.append(imread(f'{self.database.templates_dir}backgrounds/{filename}'))

        template_matching_results = {'flies': list(),
                                     'bkgrs': list()}
        for fly in template_flies:
            template_matching_results['flies'].append(match_template(vial, fly)) 
        for bkgr in template_bkgrs:
            template_matching_results['bkgrs'].append(match_template(vial, bkgr)) 
        fly_mean_results = sum(template_matching_results['flies']) / len(template_matching_results['flies'])
        bkgr_mean_results = sum(template_matching_results['bkgrs']) / len(template_matching_results['bkgrs'])
        bkgr_corrected_results = fly_mean_results - bkgr_mean_results

        flies_xy = peak_local_max(bkgr_corrected_results[..., 0], min_distance=self.min_distance, threshold_abs=self.threshold)
        all_fly_coords = flies_xy.copy()
        all_fly_coords[:,0] += 15
        all_fly_coords[:, 1] += 20

        all_fly_coords_as_list = list(all_fly_coords)

        corrected_fly_coords_as_list = all_fly_coords_as_list.copy()
        idx_to_pop = list()
        for fly_index in range(len(corrected_fly_coords_as_list)):
            if 100 < corrected_fly_coords_as_list[fly_index][1] < vial.shape[1] - 100:
                if self.min_climbing_height > corrected_fly_coords_as_list[fly_index][0]:
                    pass
                else: idx_to_pop.append(fly_index)
            else:
                idx_to_pop.append(fly_index)
        idx_to_pop.sort(reverse = True)
        for idx in idx_to_pop:
            corrected_fly_coords_as_list.pop(idx)

        return all_fly_coords_as_list, vial_cropping_coords, corrected_fly_coords_as_list
            
        

        
    def get_vial_cropping_info_from_foam_matching(self, image: np.ndarray, foam_template: np.ndarray) -> Tuple[int, int]:
        foam_results = match_template(image[0:500], foam_template)
        row_idx, col_idx = np.unravel_index(foam_results[...,0].argmax(), foam_results[...,0].shape)
        row = foam_results[...,0][row_idx]
        column = foam_results[...,0][:, col_idx]
        min_col_idx, max_col_idx = self.get_boundaries(row, col_idx)
        # Transform back to original image coordinates
        min_col_idx += int(foam_template.shape[1]/2)
        max_col_idx += int(foam_template.shape[1]/2)
        return min_col_idx, max_col_idx
    
    
    def get_boundaries(self, array: np.ndarray, start_index: int, half_window_size=5, tolerance_factor=10) -> Tuple[int, int]:
        start_mean = array[start_index-half_window_size:start_index+half_window_size].mean()
        tolerance = array[start_index-half_window_size:start_index+half_window_size].std()*tolerance_factor
        if tolerance < 0.05:
            tolerance = 0.05

        # get upper boundary:
        for pixel_idx in range(start_index, array.shape[0]-half_window_size):
            window_mean = array[pixel_idx-half_window_size:pixel_idx+half_window_size].mean()
            if start_mean - window_mean > tolerance:
                    break
        max_idx = pixel_idx + half_window_size

        # get lower boundary:
        for pixel_idx in range(start_index):
            window_mean = array[start_index-pixel_idx-half_window_size:start_index-pixel_idx+half_window_size].mean()
            if start_mean - window_mean > tolerance:
                    break
        min_idx = start_index - pixel_idx - half_window_size

        return min_idx, max_idx
    
    
class InspectDetectedFlies:
    
    def __init__(self, index: str, database: Database):
        self.index = index
        self.database = database        
        self.file_info = self.database.get_file_info_df(index = self.index)
        
    def plot_results(self):
        fly_coords = np.asarray(self.file_info['corrected_fly_coords'][0])
        vial_cropping_coords = self.file_info['vial_cropping_coords'][0]
        frame_index = self.file_info['time_passed'][0]*30
        detection_configs = self.file_info['detection_configs'][0]
        

        reader = iio.get_reader(self.file_info['video_filepath'][0])
        image = reader.get_data(frame_index)
        reader.close()
        
        vial = image[200:1000, vial_cropping_coords[0] - 100 : vial_cropping_coords[1] + 100]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15,15))
        ax1.imshow(vial)
        ax2.imshow(vial)
        ax2.scatter(fly_coords[:, 1], fly_coords[:, 0])
        ax2.vlines(x=[100, vial.shape[1] - 100], 
                   ymin=detection_configs['min_climbing_height'], 
                   ymax=5)
        ax2.hlines(y=[5, detection_configs['min_climbing_height']],
                   xmin=100, 
                   xmax=vial.shape[1] - 100)
        plt.show()
        
        
        