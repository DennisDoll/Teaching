import ipywidgets as w
from ipyfilechooser import FileChooser
from IPython.display import display

from methodscourse.api import API
import os

from typing import List


def launch():
    display(Gui().widget)


class GUI:
    
    def __init__(self):
        self.please_specify_root_dir = w.Label(value='Please specify the root directory for this experiment:')
        if os.path.isdir('/home/pi/Desktop/'):
            default_path = '/home/pi/Desktop/'
        else:
            default_path = '/mnt/c/Users/dsege/OneDrive/Desktop/'
        
        self.file_chooser = FileChooser(default_path)
        self.file_chooser.show_only_dirs = True
        
        self.confirm_root_dir_button = w.Button(description='confirm path')
        self.confirm_root_dir_button.on_click(self.build_remaining_gui)
        
        self.widget = w.VBox([self.please_specify_root_dir,
                              w.HBox([self.file_chooser, self.confirm_root_dir_button])])


    def build_remaining_gui(self, b):
        
        self.api = API(root_dir = self.file_chooser.selected_path + '/')
        
        self.recordings_tab = RecordingsTab(api = self.api)
        self.analysis_tab = AnalysisTab(api = self.api)
        self.plotting_tab = PlottingTab(api = self.api)
        
        self.navigator = Navigator(parent_widget = self.widget,
                                   parent_recordings_tab = self.recordings_tab,
                                   parent_analysis_tab = self.analysis_tab, 
                                   parent_plotting_tab = self.plotting_tab)
        
        self.widget.children = (self.navigator.widget, )
        
       
    
class Navigator:
    
    def __init__(self, parent_widget, parent_recordings_tab, parent_analysis_tab, parent_plotting_tab):
        self.parent_widget = parent_widget
        self.parent_recordings_tab = parent_recordings_tab
        self.parent_analysis_tab = parent_analysis_tab
        self.parent_plotting_tab = parent_plotting_tab
        
        self.record_button = w.Button(description='1. Recordings', style={'button_color': 'lightgray'})
        self.analyze_button = w.Button(description='2. Analysis', style={'button_color': 'lightgray'})
        self.plot_button = w.Button(description='3. Plotting', style={'button_color': 'lightgray'})
        self.widget = w.HBox([self.record_button, self.analyze_button, self.plot_button])
        
        self.record_button.on_click(self.record_button_clicked)
        self.analyze_button.on_click(self.analyze_button_clicked)
        self.plot_button.on_click(self.plot_button_clicked)
        
    def record_button_clicked(self, b):
        self.record_button.style.button_color = 'lightblue'
        self.analyze_button.style.button_color = 'lightgray'
        self.plot_button.style.button_color = 'lightgray'
        self.switch_interface(b, new_widget=self.parent_recordings_tab.widget)
    
    
    def analyze_button_clicked(self, b):
        self.record_button.style.button_color = 'lightgray'
        self.analyze_button.style.button_color = 'lightblue'
        self.plot_button.style.button_color = 'lightgray'
        self.switch_interface(b, new_widget=self.parent_analysis_tab.widget)
        
        
    def plot_button_clicked(self, b):
        self.record_button.style.button_color = 'lightgray'
        self.analyze_button.style.button_color = 'lightgray'
        self.plot_button.style.button_color = 'lightblue'
        self.switch_interface(b, new_widget=self.parent_plotting_tab.widget)
    
    
    def switch_interface(self, b, new_widget):
        self.parent_widget.children = w.VBox([self.widget, new_widget]).children
        


class RecordingsTab:
    
    def __init__(self, api):
        self.api = api
        
        self.please_choose = w.Label(value='Please provide the following details for your experiment:')
        
        self.select_group_id = w.Dropdown(description='Group ID:',
                                          options=['wt', 'tg'],
                                          value='wt',
                                          layout={'width': '30%'},
                                          style={'description_width': 'initial'})
        self.select_stimulus_indicator = w.Dropdown(description='Stimulus indicator:', 
                                                   options=['pre', 'post'],
                                                   value='pre',
                                                   layout={'width': '30%'},
                                                   style={'description_width': 'initial'})
        self.select_vial_id = w.Dropdown(description='Vial ID:',
                                        options=[1, 2, 3, 4],
                                        value=1,
                                        layout={'width': '30%'},
                                        style={'description_width': 'initial'})
        
        self.confirm_selection_button = w.Button(description='confirm selection')
        
        self.trigger_recording_button = w.Button(description='trigger recording',
                                                layout={'visibility': 'hidden'})
        
        self.widget = w.VBox([self.please_choose,
                              w.HBox([self.select_group_id,
                                      self.select_vial_id,
                                      self.select_stimulus_indicator]),
                              w.HBox([self.confirm_selection_button,
                                      self.trigger_recording_button])])
        
        self.confirm_selection_button.on_click(self.confirm_selection_button_clicked)
        self.trigger_recording_button.on_click(self.trigger_recording_button_clicked)
        
    def confirm_selection_button_clicked(self, b):
        self.trigger_recording_button.layout.visibility = 'visible'
        self.confirm_selection_button.layout.visibility = 'hidden'
        
    def trigger_recording_button_clicked(self, b):
        self.trigger_recording_button.layout.visibility = 'hidden'
        self.confirm_selection_button.layout.visibility = 'visible'
        
        group_id = self.select_group_id.value
        vial_id = self.select_vial_id.value
        stimulus_indicator = self.select_stimulus_indicator.value
        
        self.api.record_experiment(group_id = group_id, vial_id = vial_id, stimulus_indicator = stimulus_indicator)



class AnalysisTab:
    
    def __init__(self, api):
        self.api = api
        
        # Save & load buttons:
        self.save_results_button = w.Button(description='save all results') #Prefix?
        self.load_results_button = w.Button(description='load results')
        self.io_buttons_out = w.Output()
        self.io_buttons_box = w.HBox([self.save_results_button, self.load_results_button, self.io_buttons_out])
        self.save_results_button.on_click(self.save_results_button_clicked)
        self.load_results_button.on_click(self.load_results_button_clicked)
        
        # Fly detection part:
        self.please_select_file_ids = w.Label(value='Please check the file IDs you would like to analyze:')
        self.select_file_ids = self.create_file_id_checkboxes()
        self.please_specify_additional_settings = w.Label(value='Additional settings:')
        self.select_cropping_buffer_zone = w.IntSlider(description='Vial cropping buffer [px]:', 
                                                       value=0, 
                                                       min=-50, 
                                                       max=100,
                                                       style={'description_width': 'initial'},
                                                       layout={'width': '45%'})
        self.select_min_climbing_height = w.IntSlider(description='Min. climbing height [px]:', 
                                                       value=600, 
                                                       min=400, 
                                                       max=1000,
                                                       style={'description_width': 'initial'},
                                                       layout={'width': '45%'})
        self.select_threshold = w.FloatSlider(description='Detection threshold:',
                                              value=0.25,
                                              min=0.0,
                                              max=0.5, 
                                              step=0.01,
                                              style={'description_width': 'initial'},
                                              layout={'width': '45%'})
        self.select_min_distance = w.IntSlider(description='Min. distance between flies [px]:', 
                                                       value=25, 
                                                       min=1, 
                                                       max=100,
                                                       style={'description_width': 'initial'},
                                                       layout={'width': '45%'})
        self.check_overwrite = w.Checkbox(description='Overwrite previous results?', 
                                          value=False,
                                          style={'description_width': 'initial'},
                                          layout={'width': '45%'})
        self.check_quick_view = w.Checkbox(description='Quick view for inspection?', 
                                          value=False,
                                          style={'description_width': 'initial'},
                                          layout={'width': '45%'})
        self.confirm_selection_button = w.Button(description='confirm selection')
        self.trigger_analysis_button = w.Button(description='run fly detection', 
                                                layout={'visibility': 'hidden'})
        self.analyze_out = w.Output()
        self.analyze_widget = w.VBox([self.please_select_file_ids, 
                                      self.select_file_ids,
                                      self.please_specify_additional_settings,
                                      w.HBox([self.select_cropping_buffer_zone, self.select_min_climbing_height]),
                                      w.HBox([self.select_threshold, self.select_min_distance]),
                                      w.HBox([self.check_overwrite, 
                                              self.check_quick_view,
                                              self.confirm_selection_button,
                                              self.trigger_analysis_button]),
                                      self.analyze_out])
        self.confirm_selection_button.on_click(self.confirm_selection_button_clicked)
        self.trigger_analysis_button.on_click(self.trigger_analysis_button_clicked)

        # Inspection part
        inspection_file_ids = list(set(self.api.database.file_infos['file_id']))
        inspection_file_ids.sort()
        self.select_file_id = w.Dropdown(description='Select file ID:', 
                                        options=inspection_file_ids, 
                                        style={'description_width': 'initial'},
                                        layout={'width': '30%'})
        self.select_time_passed = w.IntSlider(description='Time passed:', 
                                              value=1, 
                                              min=1, 
                                              max=5, 
                                              layout={'width': '30%'})
        self.inspect_detection_button = w.Button(description='inspect detection performance', 
                                                 layout={'width': 'auto'})
        self.inspect_out = w.Output()
        self.inspect_widget = w.VBox([w.HBox([self.select_file_id, 
                                              self.select_time_passed, 
                                              self.inspect_detection_button]),
                                      self.inspect_out])
        self.inspect_detection_button.on_click(self.inspect_detection_button_clicked)
        
        # Assemble the whole widget:
        self.accordion = w.Accordion([self.analyze_widget, self.inspect_widget], selected_index=None) 
        self.accordion.set_title(0, 'Detect flies')
        self.accordion.set_title(1, 'Inspect detection quality')
        self.widget = w.VBox([self.io_buttons_box, self.accordion])

        
    def create_file_id_checkboxes(self) -> w.widget_box:
        self.api.database.prepare_database_for_analysis()
        file_ids = list(set(self.api.database.file_infos['file_id']))
        file_ids.sort()
        if len(file_ids) % 4 == 0:
            rows = int(len(file_ids) / 4)
        else:
            rows = int(len(file_ids) / 4) + 1
            
        vbox_children = list()
        i = 0
        for row in range(rows):
            temp_checkboxes = list()
            if i + 4 > len(file_ids):
                for x in range(4):
                    try:
                        checkbox = w.Checkbox(description = file_ids[i + x], value=False)
                    except:
                        checkbox = w.Checkbox(description='none', value=False, layout={'visibility': 'hidden'})
                    finally:
                        temp_checkboxes.append(checkbox)
            else:
                for file_id in file_ids[i:i+4]:
                    temp_checkboxes.append(w.Checkbox(description=file_id, value=False))
            vbox_children.append(w.HBox(temp_checkboxes))
            i += 4
        
        return w.VBox(vbox_children)
    
    
    def get_checked_file_ids(self) -> List:
        checked_file_ids = list()
        for hbox in self.select_file_ids.children:
            for checkbox in hbox.children:
                if checkbox.value:
                    checked_file_ids.append(checkbox.description)
        return checked_file_ids
        
    
    def confirm_selection_button_clicked(self, b):
        self.confirm_selection_button.layout.visibility = 'hidden'
        self.trigger_analysis_button.layout.visibility = 'visible'
     
    
    def trigger_analysis_button_clicked(self, b):
        self.confirm_selection_button.layout.visibility = 'visible'
        self.trigger_analysis_button.layout.visibility = 'hidden'
        with self.analyze_out:
            self.analyze_out.clear_output()
            print('\n \n')
            print('Initializing fly detection...')
            print('This will take several minutes per selected file ID.')
            print('I will let you know once I am done! :-)')
            self.api.detect_flies(file_ids = self.get_checked_file_ids(),
                                  cropping_buffer_zone = self.select_cropping_buffer_zone.value,
                                  min_climbing_height = self.select_min_climbing_height.value,
                                  threshold = self.select_threshold.value,
                                  min_distance = self.select_min_distance.value,
                                  overwrite = self.check_overwrite.value,
                                  quick_view = self.check_quick_view.value)
            print('######################')
            print('#########DONE#########')
            print('######################')
        
        
    def inspect_detection_button_clicked(self, b):
        with self.inspect_out:
            self.inspect_out.clear_output()
            self.api.inspect_detection_quality(file_id = self.select_file_id.value,
                                               time_passed = self.select_time_passed.value)

            
    def save_results_button_clicked(self, b):
        self.api.save_results()# Prefix??
        with self.io_buttons_out:
            self.io_buttons_out.clear_output()
            print('All results were saved.')
        
    def load_results_button_clicked(self, b):
        self.api.load_results()
        with self.io_buttons_out:
            self.io_buttons_out.clear_output()
            print('All results were loaded.')
            
            
            
class PlottingTab:
    
    def __init__(self, api):
        self.api = api
        
        self.please_check_show_and_save = w.Label(value='Please check whether you want to show and/or save the plot:')
        self.check_show = w.Checkbox(description='show', value=True)
        self.check_save = w.Checkbox(description='save', value=False)
        self.run_stats_and_plot_button = w.Button(description='run stats & plot', layout={'width': 'auto'})
        self.out = w.Output()
        self.widget = w.VBox([self.please_check_show_and_save,
                              w.HBox([self.check_show, self.check_save, self.run_stats_and_plot_button]),
                              self.out])
        self.run_stats_and_plot_button.on_click(self.run_stats_and_plot_button_clicked)
        
    
    def run_stats_and_plot_button_clicked(self, b):
        with self.out:
            self.out.clear_output()
            self.api.plot_results(save = self.check_save.value,
                                  show = self.check_show.value)