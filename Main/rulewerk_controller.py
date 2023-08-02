import os
import subprocess
import psutil
import time 
import nmo_python
import jpype
import jpype.imports
from jpype.types import *
# from datalogrulemapper import *
import csv

def measure_usage(processid):

    # Get the CPU and memory usage of the command prompt process
    cpu_usage = psutil.Process(processid).cpu_percent()
    memory_usage = psutil.Process(processid).memory_info().rss /1024/1024
    
    # Get the CPU frequency of the system
    cpu_frequency = psutil.cpu_freq().current

    print(f"CPU Usage: {cpu_usage}%")
    print(f"Memory Usage: {memory_usage} MB")
    print(f"CPU Frequency: {cpu_frequency} MHz")
    return cpu_usage, memory_usage, cpu_frequency

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
    cmd_process = subprocess.Popen(['cmd'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
    cmd_process.stdin.write(command.encode('utf-8') + b'\n')

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
    stdout, stderr = cmd_process.communicate()
    print(stdout.decode())
    print("--------------------------------------------------------------------------------") 
    print("<---------------------Query complete------------------------->")
    #go back to the original/project working directory
    os.chdir(owd)  

def runNemo(rule_file):
    pid = psutil.Process().pid

    owd = os.getcwd()
    rule_file_name = os.path.basename(rule_file)
    rule_file_path = os.path.dirname(rule_file)
    os.chdir(os.path.join(owd, rule_file_path))
    currPath = os.getcwd()

    # using the python nemo bings nmo_python to load the rule file
    rls_file = nmo_python.load_file("{}\{}".format(currPath, rule_file_name))

    # passing the loaded rls file to the nemo engine and running the nemo reasoner
    nemo_rule = nmo_python.NemoEngine(rls_file)
    print("Running the reasoner...")
    nemo_rule.reason()

    # the write_result function accepts parmaters: predicate of the query to  be executed, outfile_manager that takes the NemoOutputManager structure with parameters file dir as string, bool overrite?, bool gzip? 
    # write_result writes the query results of the specified query to the specified output dir
    # for every output predicate in the rulefile, run the query and store results in a file
    for pred in rls_file.output_predicates():
        print(pred)
        nemo_rule.write_result(str(pred), nmo_python.NemoOutputManager(rule_file_name.split(".")[0], True, False)) 

    print("Query results processed!")
    os.chdir(owd)
    

# if __name__=='__main__':
#     rulewerkBench()
#     # NemoBench()