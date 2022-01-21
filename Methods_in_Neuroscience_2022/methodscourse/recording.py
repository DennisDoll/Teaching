from picamera import PiCamera
from time import sleep
import os

from .database import Database


class Recorder:
    
    def __init__(self, database: Database):
        self.database = database
    
    
    def start_recording(self, group_id: str, vial_id: int, stimulus_indicator: str):
        file_id = self.database.file_id_tracker_for_recordings
        filepath = f'{self.database.recordings_dir}{str(file_id).zfill(4)}_{group_id}_{stimulus_indicator}_light_{str(vial_id).zfill(3)}.h264'
        if os.path.isfile(filepath):
            raise InputError('The specified recording already exists! Please check your inputs again.')

        with PiCamera() as camera:
            #camera.vflip = True
            camera.start_preview()
            sleep(2)
            camera.start_recording(filepath)
            sleep(8)
            camera.stop_preview()
        self.database.file_id_tracker_for_recordings += 1
        
        return self.database