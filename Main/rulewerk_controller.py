import os
import subprocess
import psutil
import time 
import nmo_python
import jpype
import jpype.imports
from jpype.types import *
from memory_profiler import memory_usage, profile
import csv
import json

def measure_usage(processid):

    # Get the memory usage of a process
    memory_usage = psutil.Process(processid).memory_info().rss /1024/1024
    
    print(f"Memory Usage: {memory_usage} MB")
    return memory_usage

def rulefileElements(parser, Rule, Literal, rlsFilePath):
    with open(rlsFilePath, 'r') as rule_file: 
    # with open(R"C:\Users\kansa\Desktop\Team Project TUD SoSe23\Team-Project---Knowledge-Processing\Main\{}".format(rlsFilePath), 'r') as rule_file:
        kb = parser.parse(rule_file.read())
        rules = kb.getRules()
        ruleHeads=[]
        pred_names=[]
        toQuery=[]
        for rule in rules:
            ruleHead = rule.getHead()
            ruleHeadName = ruleHead.getLiterals()[0].getPredicate()
            #to remove redundant query. Queries like Ancestor(?X, ?Y) and Ancestor(?X, ?Z) have same meaning even with different arguments. So, we check only the predicate names
            if ruleHeadName in ruleHeads:
                continue
            ruleHeads.append(ruleHeadName)
            pred_names.append(ruleHeadName.getName())
            #query command does not accept spaces between arguments, but our rules might have them so we remove them
            toQuery.append(ruleHead.toString().replace(" ",""))
    return toQuery, pred_names

    
def runRulewerk(rule_file_path, query_dict):
    owd = os.getcwd()
    # go to the user input rls file directory which contains the rulewerk-client.jar to run rulewerk
    os.chdir(os.path.join(owd, rule_file_path))
    command = "java -jar rulewerk-client.jar"

    memory_usage()
    start_mem = memory_usage()[0]
    cmd_process = subprocess.Popen(['cmd'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
    process_id = cmd_process.pid
    cmd_process.stdin.write(command.encode('utf-8') + b'\n')

    start_time = time.time()

    for rls_file, to_query in query_dict.items():
        file_name = os.path.basename(rls_file)
        file_path = os.path.dirname(rls_file)
        os.chdir(os.path.join(owd, file_path))
        cd = str(os.getcwd()).replace("\\", "/") #the direct parent directory of the .rls file

        load_command = "@load '{}/{}'".format(cd,file_name)
        reason_command = "@reason"     
        cmd_process.stdin.write(load_command.encode('utf-8') + b'\n')
        cmd_process.stdin.write(reason_command.encode('utf-8') + b'\n')
        for (query, pred_name) in zip(to_query[0], to_query[1]):
            res_dir_name = str(file_name).split('.')[0]
            if not os.path.exists(res_dir_name):
                os.mkdir(res_dir_name)
            query_command = "@query {} EXPORTCSV '{}/{}/{}.csv'".format(query, cd, res_dir_name, pred_name)
            cmd_process.stdin.write(query_command.encode('utf-8') + b'\n')
        #go back to the directory with rulewerk-client.jar
        os.chdir(owd)
        os.chdir(os.path.join(owd, rule_file_path))
    end_mem = memory_usage()[0]
    print("mem_usgae", (end_mem-start_mem)*1.048576)
    #measure usage of the process
    memory_info = measure_usage(process_id)

    stdout, stderr = cmd_process.communicate()

    execution_time = (time.time() - start_time)*1000
    
    print("<-------------------- Process Completed! ----------------------->")
    print(f"Execution Time: {execution_time} ms")
    print(f"Memory usage: {memory_info} MB")
    #go back to the original/project working directory
    os.chdir(owd)  
    return execution_time, memory_info

# @profile 
def runNemo(rls_file_list):

    owd = os.getcwd()
    pid = os.getpid()
    
    start_time = time.time()

    #get memory usage of processing all rls files using nemo
    memory_usage()
    mem_usage_start = memory_usage()[0]
    mem_usage_end = memory_usage()[0]
    
    #convert 2D list to json to pass as arguments to subprocess "nemo-reasoning.py"
    list_json = json.dumps(rls_file_list)
    subprocess_command = ["python", "nemo_reasoning.py", owd, list_json]
    process = subprocess.Popen(subprocess_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process_id = process.pid

    process_memory = measure_usage(process_id)
    stdout, stderr = process.communicate()
    # print(stdout.decode())
    # print(stderr.decode())
    execution_time = (time.time() - start_time)*1000
    
    print("<-------------------- Process Completed! ----------------------->")
    print(f"Execution Time: {execution_time} ms")
    print(f"Memory usage: {process_memory} MB")
        
    return execution_time, process_memory

