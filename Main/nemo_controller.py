import os
import time
import psutil
import nmo_python
import json
import subprocess
from loguru import logger
import pandas as pd
from pathlib import Path
import ast


class NemoController:
    def runNemo(self, rls_file_list):
        logger.info("Running Nemo")
        result_count = 0
        
        # convert 2D list to json to pass as arguments to subprocess "nemo-reasoning.py"
        list_json = json.dumps(rls_file_list)
        subprocess_command = ["python", "nemo_reasoning.py", list_json]
        start_time = time.time()
        process = subprocess.Popen(subprocess_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process_id = process.pid
        process_memory = psutil.Process(process_id).memory_info().rss 
        stdout, stderr = process.communicate()

        execution_time = round((time.time() - start_time) * 1000, 2)
        memory_usage = round(process_memory / 1024 / 1024, 2)

        if not stdout.decode() == "":
            result_csv_files = ast.literal_eval(stdout.decode())
            for csv in result_csv_files:
                print("csv", csv)
                try:
                    result_csv = pd.read_csv(csv)
                    result_count = result_count + len(result_csv) + 1
                except pd.errors.EmptyDataError:
                    result_count = result_count
            print("Count: ", result_count)
        if stderr:
            raise RuntimeError(stderr.decode())

        
        logger.info("Nemo processing complete")
        print(f"Execution Time: {execution_time} ms")
        print(f"Memory usage: {memory_usage} MB")

        return execution_time, memory_usage, result_count
