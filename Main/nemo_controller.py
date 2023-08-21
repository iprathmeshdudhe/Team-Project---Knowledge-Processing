import os
import time
import psutil
import nmo_python
import json
import subprocess


class NemoController:
    def runNemo(self, rls_file_list):
        print("----------------Starting Nemo---------------")

        start_time = time.time()

        # convert 2D list to json to pass as arguments to subprocess "nemo-reasoning.py"
        list_json = json.dumps(rls_file_list)
        subprocess_command = ["python", "nemo_reasoning.py", list_json]
        process = subprocess.Popen(subprocess_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process_id = process.pid

        memory_usage = psutil.Process(process_id).memory_info().rss / 1024 / 1024
        stdout, stderr = process.communicate()
        if not stdout.decode() == "":
            result_count = stdout.decode()

        if stderr:
            # print(stderr.decode())
            raise RuntimeError(stderr.decode())

        execution_time = (time.time() - start_time) * 1000

        print("<-------------------- Process Completed! ----------------------->")
        print(f"Execution Time: {execution_time} ms")
        print(f"Memory usage: {memory_usage} MB")

        return execution_time, memory_usage, result_count
