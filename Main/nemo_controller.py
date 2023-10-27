import os
import time
import psutil
import subprocess
from loguru import logger
import pandas as pd
from pathlib import Path
import ast


class NemoController:
    def get_nemo_commands(self, rls_file_list):
        commands = []
        for rls_file in rls_file_list:
            print("rls file list: {}".format(rls_file))
            cwd = os.path.abspath(os.getcwd())
            cd_rls_command = "cd {}".format(rls_file[1])
            nmo_path = os.path.join(cwd, "lib")
            result_dir_name = str(rls_file[0]).split(".")[0]
            nmo_res_path = os.path.join(cwd, "nemo", result_dir_name)
            nmo_command = "{}\\nmo {} -s -D {} --overwrite-results".format(nmo_path, rls_file[0], nmo_res_path)
            cd_cwd_command = "cd {}".format(cwd)
            commands.append(cd_rls_command)
            commands.append(nmo_command)
            commands.append(cd_cwd_command)
        return commands
    
    def count_results(self, rls_file_list):
        result_count = 0
        for rls_file in rls_file_list:
            cd = os.getcwd()
            dir_name = str(rls_file[0]).split(".")[0] 
            result_dir = os.path.join(cd, "nemo", dir_name)
            for file_name in os.listdir(result_dir):
                rls_file_path = os.path.join(result_dir, file_name)
                if os.path.isfile(rls_file_path):
                    try:

                        result_csv = pd.read_csv(rls_file_path)
                        result_count = (
                            result_count + len(result_csv) + 1
                        )  # count total numebr of rows in each result csv file; +1 because we do not have header in our result csv
                    except pd.errors.EmptyDataError:
                        result_count = result_count
        return result_count





  
