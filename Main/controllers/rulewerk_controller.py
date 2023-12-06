import os
import subprocess
import psutil
import time
import jpype
import jpype.imports
from jpype.types import *
import csv
import sys
import pandas as pd
from loguru import logger
import platform

sys.tracebacklimit = 0


class RulewerkController:
    def get_rule_file_elements(self, parser, Rule, Literal, rlsFilePath):
        with open(rlsFilePath, "r") as rule_file:
            rls_file = rule_file.read()
            kb = parser.parse(rls_file)
            rules = kb.getRules()
            ruleHeads = []
            pred_names = []
            toQuery = []
            for rule in rules:
                ruleHead = rule.getHead()
                ruleHeadName = ruleHead.getLiterals()[0].getPredicate()
                # to remove redundant query. Queries like Ancestor(?X, ?Y) and Ancestor(?X, ?Z) have same meaning even with different arguments. So, we check only the predicate names
                if str(ruleHeadName) in ruleHeads:
                    pred_name_str = str(ruleHeadName.getName())
                    for i in toQuery:
                        print(type(i))

                    # Construct the regex pattern dynamically
                    pattern = re.compile(fr'{re.escape(pred_name_str)}\(([^)]*)\)')
                    # print('matchlist', matches_list)
                    new_word = str(ruleHead.toString().replace(" ", ""))
                    print(ruleHeadName, new_word, ruleHead)
                    toQuery = [pattern.sub(new_word, s) for s in toQuery]
                    continue
                ruleHeads.append(str(ruleHeadName))
                pred_names.append(ruleHeadName.getName())
                # query command does not accept spaces between arguments, but our rules might have them so we remove them
                toQuery.append(str(ruleHead.toString().replace(" ", "")))
                
            print(f'toQuery: {toQuery}')   
        return toQuery, pred_names


    def count_rulewerk_results(self, query_dict):
        result_count = 0
        for rls_file, to_query in query_dict.items():
            file_name = os.path.basename(rls_file)
            file_path = os.path.dirname(rls_file)
            for pred_name in to_query[1]:
                res_dir = file_path.split(".")[0]
                f_name = file_name.split(".")[0]
                cd = os.getcwd()
                dir_name = os.path.join(cd, "rulewerk", f_name)
                try:
                    result_csv = pd.read_csv(os.path.join(dir_name, f"{pred_name}.csv"))
                    result_count = (
                        result_count + len(result_csv) + 1
                    )  # count total numebr of rows in each result csv file; +1 because we do not have header in our result csv
                except pd.errors.EmptyDataError:
                    result_count = result_count
        return result_count

    def get_rulewerk_commands(self, task, rule_file_path, query_dict):
        system = platform.system()
        commands = []
        result_count = 0

        logger.info("Running Rulewerk")

        if system == "Windows":
            start_command = "java -jar lib/rulewerk-client/rulewerk.jar"

            #commented this out only for linux...work in progress
            commands.append(start_command)
        

            for rls_file, to_query in query_dict.items():
                file_name = os.path.basename(rls_file)
                file_path = os.path.dirname(rls_file)

                cd = str(os.getcwd()).replace("\\", "/")
                file_path = str(file_path).replace("\\", "/")

                load_command = f"@load '{cd}/{file_path}/{file_name}'"
                commands.append(load_command)
                reason_command = "@reason"
                commands.append(reason_command)
                for query, pred_name in zip(to_query[0], to_query[1]):
                    dir_name = str(file_name).split(".")[0]
                    res_dir_name = f"rulewerk/{dir_name}"

                    if not os.path.exists(res_dir_name):
                        os.makedirs(res_dir_name)

                    query_command = "@query {} EXPORTCSV '{}/{}.csv'".format(query, res_dir_name, pred_name)
                    commands.append(query_command)

                clear_command = "@clear ALL".format(query, res_dir_name, pred_name)
                commands.append(clear_command)

            return commands
        elif system == "Linux":
            lin_commands = [] #without memusage, for exec time measurement
            lin_mem_commands = [] #for ones with memusage 
            for rls_file, to_query in query_dict.items():
                        
                file_name = os.path.basename(rls_file)
                file_path = os.path.dirname(rls_file)

                cd = str(os.getcwd()).replace("\\", "/")
                file_path = str(file_path).replace("\\", "/")

                dir_name = str(file_name).split(".")[0]
                res_dir_name = f"rulewerk/{dir_name}"

                toQuery = ""
                for query in to_query[0]:
                    query_str = query.replace("(", "\(").replace(")", "\)")
                    toQuery = toQuery + "--query=" + str(query_str) + " "

                cd_rls_command = f"cd {cd}/{file_path}"

                lin_commands.append(cd_rls_command)
                lin_mem_commands.append(cd_rls_command)

                start_command = f"java -jar ../../lib/rulewerk-client/rulewerk-0.6.0.jar materialize --rule-file={file_name} {toQuery} --print-query-result-size=false --print-complete-query-result=true" #putting this inside the for loop for linux to make it similar to other tools (do for each file separately and then get their aggregate in bench csv)
                lin_commands.append(start_command)

                mem_start_command = f"memusage --data={cd}/{res_dir_name}/{task}.dat --png={cd}/{res_dir_name}/{task}.png java -jar ../../lib/rulewerk-client/rulewerk-0.6.0.jar materialize --rule-file={file_name} {toQuery} --print-query-result-size=false --print-complete-query-result=true" 
                lin_mem_commands.append(mem_start_command)

                cd_owd_command = f"cd {cd}"
                lin_commands.append(cd_owd_command)
                lin_mem_commands.append(cd_owd_command)

        return lin_commands, lin_mem_commands

    def rulewerk_lin_write_output(self, output):
        printFlag = False
        output = output.split("\n")
        dir_name = ''
        for line in output:
            if '--rule-file' in line:
                file_name = str(line.split()[1]).split('.')[0]
                if not os.path.exists(f'rulewerk/{file_name}'):
                    os.makedirs(f'rulewerk/{file_name}')
                dir_name=f'rulewerk/{file_name}'
            if line != "" and not line.isspace():
                if(line.split()[0]=="Answers"):
                    printFlag = True
                    queryName = line.split()[3].split("(")[0]
                    # queryResFile = open(currPath +R"\{}.txt".format(queryName), 'w')
                    queryResFile = open(f"{dir_name}/{queryName}.csv", 'w')
                    queryResFile.close()
                    continue

                if(line.split()[0]=="Query"):
                    printFlag = False
                    queryName = line.split()[3].split("(")[0]
                    continue
        
                if printFlag==True:                
                    # queryResFile = open(currPath +R"\{}.csv".format(queryName), 'a')
                    results = line.replace('[', "-").replace(']', '-').split('-')[3].split(',')
                    with open(f"{dir_name}/{queryName}.csv", 'a', newline='') as queryResFile:
                        writer = csv.writer(queryResFile)
                        writer.writerow(results)
                    queryResFile.close()
