import os
import pandas as pd
import pickle
from math import isnan


from skimage.io import imread, imsave

from typing import Dict, List, Tuple, Optional


TIMEPOINTS_TO_ANALYZE = [1, 2, 3, 4, 5]


def list_no_hidden(filepath: str) -> List[str]:
    return [elem for elem in os.listdir(filepath) if elem.startswith('.') == False]


class Database:
    
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.create_subdirs()        
        self.templates_dir = f'{root_dir}templates/'
        self.foam_template = imread(f'{self.templates_dir}foam/001_foam.png')
        self.file_id_tracker_for_recordings = 0
        
    
    def create_subdirs(self):
        if os.path.isdir(f'{self.root_dir}recorded_videos/') == False:
            os.mkdir(f'{self.root_dir}recorded_videos/')
        self.recordings_dir = f'{self.root_dir}recorded_videos/'
        
        if os.path.isdir(f'{self.root_dir}results/') == False:
            os.mkdir(f'{self.root_dir}results/')
        self.results_dir = f'{self.root_dir}results/'
        

    def prepare_database_for_analysis(self):
        self.files = list_no_hidden(self.recordings_dir)
        self.files = [filename for filename in self.files if filename.endswith('mp4')]
        self.files.sort()
        self.file_infos = self.create_file_infos()
    
    
    def create_file_infos(self) -> Dict:
        file_infos = {'index': list(),
                      'file_id': list(),
                      'group_id': list(),
                      'stimulus_indicator': list(),
                      'vial_id': list(),
                      'time_passed': list(),
                      'all_detected_flies': list(),
                      'all_fly_coords': list(),
                      'vial_cropping_coords': list(),
                      'corrected_detected_flies': list(),
                      'corrected_fly_coords': list(),
                      'video_filepath': list(),
                      'detection_configs': list()}
        index_count = 0
        for filename in self.files:
            for time_passed in TIMEPOINTS_TO_ANALYZE:
                file_infos['index'].append(str(index_count).zfill(4))
                file_infos['file_id'].append(filename[:4])
                file_infos['group_id'].append(filename[5:7])
                file_infos['stimulus_indicator'].append(filename[8:filename.find('_light')])
                file_infos['vial_id'].append(filename[filename.rfind('_'):filename.find('.mp4')])
                file_infos['video_filepath'].append(self.recordings_dir + filename)
                file_infos['time_passed'].append(time_passed)
                for key in ['all_detected_flies', 'all_fly_coords', 
                            'vial_cropping_coords', 'corrected_detected_flies', 'corrected_fly_coords',
                            'detection_configs']:
                    file_infos[key].append(None)
                index_count += 1
        return file_infos
    
    
    def get_file_info_df(self, index: Optional[str]=None, file_id: Optional[str]=None) -> Dict:
        file_info_df = pd.DataFrame(data=self.file_infos)
        if index != None:
            file_info_df = file_info_df.loc[file_info_df['index'] == index]
        elif file_id != None:
            file_info_df = file_info_df.loc[file_info_df['file_id'] == file_id]
        return file_info_df.to_dict('list')
    
    
    def add_detected_flies(self, file_id: str, time_passed: int, all_fly_coords: List, vial_cropping_coords: Tuple, corrected_fly_coords: List, detection_configs: Dict):
        
        for i in range(len(self.file_infos['file_id'])):
            if (self.file_infos['file_id'][i] == file_id) & (self.file_infos['time_passed'][i] == time_passed):
                entry_index = i
        
        self.file_infos['all_detected_flies'][entry_index] = len(all_fly_coords)
        self.file_infos['all_fly_coords'][entry_index] = all_fly_coords
        self.file_infos['vial_cropping_coords'][entry_index] = vial_cropping_coords
        self.file_infos['corrected_detected_flies'][entry_index] = len(corrected_fly_coords)
        self.file_infos['corrected_fly_coords'][entry_index] = corrected_fly_coords
        self.file_infos['detection_configs'][entry_index] = detection_configs
        

    def save_file_infos(self, prefix: str):
        with open(f'{self.results_dir}{prefix}file_info_results.p', 'wb') as io:
            pickle.dump(self.file_infos, io)

        
    def load_file_infos(self):
        result_files = [filename for filename in list_no_hidden(self.results_dir) if filename.endswith('file_info_results.p')]
        
        for file in result_files:
            with open(self.results_dir + file, 'rb') as io:
                results = pickle.load(io)
            
            ids_of_entries_with_results = list()
            for i in range(len(results['index'])):
                if results['all_detected_flies'][i] != None:
                    if isnan(results['all_detected_flies'][i]) == False:
                        ids_of_entries_with_results.append(i)

            for index in ids_of_entries_with_results:
                if self.file_infos['all_detected_flies'][index] == None:
                    no_results_present = True
                elif isnan(self.file_infos['all_detected_flies'][index]):
                    no_results_present = True

                if no_results_present:
                    for key in ['all_detected_flies', 'all_fly_coords', 
                                'vial_cropping_coords', 'corrected_detected_flies', 'corrected_fly_coords',
                                'detection_configs']:

                        self.file_infos[key][index] = results[key][index]
                
                
            

            
            
            
        