import pandas as pd
import pingouin as pg
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict

from .database import Database

class StatsPlotter:
    
    def __init__(self, database: Database):
        self.database = database
        
        
    def show_results(self, save: bool, show: bool):
        df = self.preprocess_dataframe()
        stats = self.compute_stats(df = df)
        self.plot_results(df=df, stats=stats, show=show, save=save)
        
        
    def preprocess_dataframe(self) -> pd.DataFrame:
        df_all = pd.DataFrame(data=self.database.file_infos)
        df = df_all[['group_id', 'stimulus_indicator', 'vial_id', 'time_passed', 'corrected_detected_flies']].copy()
        df['normalized_count'] = np.NaN
        for group_id in df['group_id'].unique():
            for vial_id in df['vial_id'].unique():
                mean_count_pre = df.loc[(df['group_id'] == group_id) & (df['vial_id'] == vial_id) & (df['stimulus_indicator'] == 'pre'), 'corrected_detected_flies'].mean()
                df.loc[(df['group_id'] == group_id) & (df['vial_id'] == vial_id), 'normalized_count'] = df['corrected_detected_flies'] / mean_count_pre * 100
        df['continued_time'] = df['time_passed']
        df.loc[df['stimulus_indicator'] == 'post', 'continued_time'] = df['continued_time'] + 5
        for row in range(df.shape[0]):
            vial_id = df['vial_id'][row]
            vial_id = int(vial_id[1:])
            df.loc[row, 'vial_id'] = vial_id

        max_vial_count_wt = df.loc[df['group_id'] == 'wt', 'vial_id'].max()
        df.loc[df['group_id'] == 'tg', 'vial_id'] = df['vial_id'] + max_vial_count_wt
        return df
    
    def compute_stats(self, df: pd.DataFrame) -> Dict:
        rma_wt_pre_vs_post = pg.rm_anova(data=df[df['group_id'] == 'wt'], dv='normalized_count', within=['stimulus_indicator'], subject='vial_id')
        rma_tg_pre_vs_post = pg.rm_anova(data=df[df['group_id'] == 'tg'], dv='normalized_count', within=['stimulus_indicator'], subject='vial_id')
        mma_wt_vs_tg_all_times = pg.mixed_anova(data=df, dv='normalized_count', within='continued_time', subject='vial_id', between='group_id')
        stats_results = {'rma_wt': rma_wt_pre_vs_post,
                         'rma_tg': rma_tg_pre_vs_post,
                         'mma': mma_wt_vs_tg_all_times}
        for test in ['rma_wt', 'rma_tg', 'mma']:
            pval = stats_results[test]['p-unc'][0]
            if pval < 0.001:
                pval_str = '*** (p < 0.001)'
            elif pval < 0.01:
                pval_str = '** (p < 0.01)'
            elif pval < 0.05:
                pval_str = '* (p < 0.05)'
            else:
                pval_str = f'n.s. (p = {round(pval, 2)})'
            stats_results[test] = pval_str
        return stats_results
    
    
    def plot_results(self, df: pd.DataFrame, stats: Dict, save: bool, show: bool):
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20,5), facecolor='white')

        sns.pointplot(data=df[df['group_id'] == 'wt'], x='time_passed', y='normalized_count', hue='stimulus_indicator', 
                      hue_order = ['pre', 'post'], palette=['lightgreen', 'darkgreen'], dodge=True, ax=ax1)
        sns.pointplot(data=df[df['group_id'] == 'tg'], x='time_passed', y='normalized_count', hue='stimulus_indicator', 
                      hue_order = ['pre', 'post'], palette=['gold', 'darkorange'], dodge=True, ax=ax2)
        sns.pointplot(data=df, x='continued_time', y='normalized_count', hue='group_id', 
                      hue_order = ['wt', 'tg'], palette=['darkgreen', 'darkorange'], dodge=True, ax=ax3, linestyles=['dashed', 'dashed'])
        ymin, ymax = ax3.get_ylim()
        ymax = ymax + ymax * 0.2
        ax3.axvspan(xmin=4.5, xmax=10, color='lightblue')
        ax3.set_ylim(0, ymax)
        ax1.sharey(ax3)
        ax2.sharey(ax3)

        ax1.set_title('wildtype flies: pre vs. post stimulation', fontsize=16)
        ax2.set_title('transgenic flies: pre vs. post stimulation', fontsize=16)
        ax3.set_title('wildtype vs. transgenic flies', fontsize=16)

        ax1.text(x=2, y=ymax*0.95, s=stats['rma_wt'], horizontalalignment='center', verticalalignment='center', fontsize=14, fontstyle='oblique')
        ax2.text(x=2, y=ymax*0.95, s=stats['rma_tg'], horizontalalignment='center', verticalalignment='center', fontsize=14, fontstyle='oblique')
        ax3.text(x=4.5, y=ymax*0.95, s=stats['mma'], horizontalalignment='center', verticalalignment='center', fontsize=14, fontstyle='oblique')
        ax3.text(x=2, y=ymax*0.9, s='pre stim', horizontalalignment='center', verticalalignment='center', fontsize=12, fontstyle='oblique')
        ax3.text(x=7, y=ymax*0.9, s='post stim', horizontalalignment='center', verticalalignment='center', fontsize=12, fontstyle='oblique')

        ax1.set_ylabel('climbing flies \n[% normalized to mean pre stimulation]', fontsize=13)
        ax2.set_ylabel('climbing flies \n[% normalized to mean pre stimulation]', fontsize=13)
        ax3.set_ylabel('climbing flies \n[% normalized to mean pre stimulation]', fontsize=13)

        ax1.set_xlabel('time after start of recording [s]', fontsize=13)
        ax2.set_xlabel('time after start of recording [s]', fontsize=13)
        ax3.set_xlabel('analyzed timepoints \n[1-5: pre stim; 6-10: post stim]', fontsize=13)

        ax1.legend(fontsize=13, loc='upper right')
        ax2.legend(fontsize=13, loc='upper right')
        ax3.legend(fontsize=13, loc='upper right', framealpha=0, edgecolor='black')

        ax1.set_xlim(-0.5, 4.5)
        ax2.set_xlim(-0.5, 4.5)
        ax3.set_xlim(-0.5, 10)

        plt.tight_layout()
        
        if save:
            filepath = f'{self.database.results_dir}statistical_analyses.png'
            plt.savefig(filepath, dpi=300)
        if show:
            plt.show()
        else:
            plt.close()







