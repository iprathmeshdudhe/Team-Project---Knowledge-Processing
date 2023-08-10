import os
import subprocess
import psutil
import time 
import jpype
import jpype.imports
from jpype.types import *
import csv
import sys

class RulewerkController:
    def rulefileElements(self, parser, Rule, Literal, rlsFilePath):
        with open(rlsFilePath, 'r') as rule_file: 
    
            
            rls_file = rule_file.read()
            kb = parser.parse(rls_file)                    
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

    def runRulewerk(self, rule_file_path, query_dict):
        owd = os.getcwd()
        # go to the user input rls file directory which contains the rulewerk-client.jar to run rulewerk
        os.chdir(os.path.join(owd, rule_file_path))
        command = "java -jar rulewerk-client.jar"

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

        #measure usage of the process
        memory_usage = psutil.Process(process_id).memory_info().rss /1024/1024
        stdout, stderr = cmd_process.communicate()

        execution_time = (time.time() - start_time)*1000
    
        print("<-------------------- Process Completed! ----------------------->")
        print(f"Execution Time: {execution_time} ms")
        print(f"Memory usage: {memory_usage} MB")
        #go back to the original/project working directory
        os.chdir(owd)  
        return execution_time, memory_usage
    
   