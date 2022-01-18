import os
import pandas as pd


from skimage.io import imread, imsave

from typing import Dict, List, Tuple


TIMEPOINTS_TO_ANALYZE = [1, 2, 3, 4, 5]


def list_no_hidden(filepath: str) -> List[str]:
    return [elem for elem in os.listdir(filepath) if elem.startswith('.') == False]


class Database:
    
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.recordings_dir = f'{root_dir}recorded_videos/'
        self.files = list_no_hidden(self.recordings_dir)
        self.files.sort()
        self.file_infos = self.create_file_infos()
        self.templates_dir = '/home/pi/methodscourse/templates/'
        self.foam_template = imread(f'{self.templates_dir}foam/001_foam.png')
        
        
    def create_file_infos(self) -> Dict:
        file_infos = {'file_id': list(),
                      'group_id': list(),
                      'stimulus_indicator': list(),
                      'vial_id': list(),
                      'time_passed': list(),
                      'all_detected_flies': list(),
                      'all_fly_coords': list(),
                      'vial_cropping_coords': list(),
                      'corrected_detected_flies': list(),
                      'corrected_fly_coords': list(),
                      'video_filepath': list()}
        for filename in self.files:
            for time_passed in TIMEPOINTS_TO_ANALYZE:
                file_infos['file_id'].append(filename[:4])
                file_infos['group_id'].append(filename[5:7])
                file_infos['stimulus_indicator'].append(filename[8:filename.find('_light')])
                file_infos['vial_id'].append(filename[filename.rfind('_'):filename.find('.mp4')])
                file_infos['video_filepath'].append(self.recordings_dir + filename)
                file_infos['time_passed'].append(time_passed)
                for key in ['all_detected_flies', 'all_fly_coords', 'vial_cropping_coords', 'corrected_detected_flies', 'corrected_fly_coords']:
                    file_infos[key].append(None)
        return file_infos
    
    
    def get_file_info_df(self, file_id: str) -> Dict:
        file_info_df = pd.DataFrame(data=self.file_infos)
        file_info_df = file_info_df.loc[file_info_df['file_id'] == file_id]
        return file_info_df.to_dict('list')
    
    
    def add_detected_flies(self, file_id: str, time_passed: int, all_fly_coords: List, vial_cropping_coords: Tuple, corrected_fly_coords: List):
        entry_index = [i for i in range(len(self.file_infos['file_id'])) if (self.file_infos['file_id'][i] == file_id & 
                                                                             self.file_infos['time_passed'][i] == time_passed)][0]
        self.file_infos['all_detected_flies'][entry_index] = len(all_fly_coords)
        self.file_infos['all_fly_coords'][entry_index] = all_fly_coords
        self.file_infos['vial_cropping_coords'][entry_index] = vial_cropping_coords
        self.file_infos['corrected_detected_flies'][entry_index] = len(corrected_fly_coords)
        self.file_infos['corrected_fly_coords'][entry_index] = corrected_fly_coords
        
        
    
        
         