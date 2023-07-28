import os
import subprocess
import psutil
import time 
import nmo_python
import jpype
import jpype.imports
from jpype.types import *
from datalogrulemapper import *
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
    
    with open(R"C:\Users\kansa\Desktop\Team Project TUD SoSe23\Team-Project---Knowledge-Processing\rulewerk_nemo\{}".format(rlsFilePath), 'r') as rule_file:
        kb = parser.parse(rule_file.read())
        rules = kb.getRules()
        ruleHeads=[]
        toQuery=[]
        for rule in rules:
            ruleHead = rule.getHead()
            ruleHeadName = ruleHead.getLiterals()[0].getPredicate()
            #to remove redundant query. Queries like Ancestor(?X, ?Y) and Ancestor(?X, ?Z) have same meaning even with different arguments. So, we check only the predicate names
            if ruleHeadName in ruleHeads:
                continue
            ruleHeads.append(ruleHeadName)
            #query command does not accept spaces between arguments, but our rules might have them so we remove them
            toQuery.append(ruleHead.toString().replace(" ",""))

    return toQuery

        
    
    
def runRulewerk(parser, Rule, Literal, ruleFilePath, ruleFileName):
    owd = os.getcwd()
    #change to directory containing the rule file and rulewerk jar file
    os.chdir(ruleFilePath)

    currPath = os.getcwd()
    ruleFile = "{}\\{}".format(ruleFilePath, ruleFileName)
    #file to store the query results
    bench = currPath+R"\queryBench.txt"

    queries = rulefileElements(parser, Rule, Literal, ruleFile)

    #to query/reasoning for every rule in our rulefile
    toQuery = ""
    for query in queries:
        toQuery = toQuery + "--query=" + str(query) + " "

    start_time = time.time()
    
    #run the rule file and query through rulewerk command line
    command = "java -jar ..\\rulewerk.jar materialize --rule-file={} {} --print-query-result-size=false --print-complete-query-result=true".format(ruleFileName, toQuery)
    # cmd_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    
    
    cmd_process = subprocess.Popen(['cmd'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
    cmd_process.stdin.write(command.encode('utf-8') + b'\n')
    cmd_process.stdin.flush()


    measure_usage(cmd_process.pid)
    cpu_usage, memory_usage, cpu_freq = measure_usage(cmd_process.pid)
    stdout, stderr = cmd_process.communicate()
    cmd_process.stdin.close()
    cmd_process.stdout.close()
    # Calculate the execution time
    execution_time = (time.time() - start_time)*1000
    print(f"Execution Time: {execution_time} ms")

    

    output = stdout.decode()
    printFlag = False
    output = output.split("\n")
    for line in output:
        if line != "" and not line.isspace():
            if(line.split()[0]=="Answers"):
                printFlag = True
                queryName = line.split()[3].split("(")[0]
                # queryResFile = open(currPath +R"\{}.txt".format(queryName), 'w')
                queryResFile = open(currPath +R"\{}.csv".format(queryName), 'w')
                queryResFile.close()
                continue

            if(line.split()[0]=="Query"):
                printFlag = False
                queryName = line.split()[3].split("(")[0]
                continue
        
            if printFlag==True:
                
                # queryResFile = open(currPath +R"\{}.csv".format(queryName), 'a')
                results = line.replace('[', "-").replace(']', '-').split('-')[3].split(',')
                print (results)
                with open(currPath +R"\{}.csv".format(queryName), 'a', newline='') as queryResFile:
                    writer = csv.writer(queryResFile)
                    writer.writerow(results)
                queryResFile.close()

    #output the measures to the result file
    benchFile = open(bench, 'w+')
    benchFile.write("CPU usage: {}%\nMemory Usage: {}MB\nCPU_Frequence = {}MHz\nExecution time: {}ms".format(cpu_usage, memory_usage, cpu_freq, execution_time))
    benchFile.close()

    print("Query complete")
    os.chdir(owd)

def rulewerkBench():
    ruleMapper = DatalogRuleMapper()
    parser, Rule, Literal = ruleMapper.start_jvm()
    # runRulewerk(parser, Rule, Literal, "rulewerk-examples\\ancestor", "ancestor.rls")
    for root, dirs, files in os.walk('examples'):
        for rlsFile in files:
            if rlsFile.endswith(".rls"):
                print(root, rlsFile)
                runRulewerk(parser, Rule, Literal, root, rlsFile)
    ruleMapper.stop_jvm()            

def runNemo(ruleFilePath, ruleFileName):
    pid = psutil.Process().pid

    owd = os.getcwd()
    os.chdir(ruleFilePath)
    currPath = os.getcwd()

    initial_cpu_usage, initial_memory_usage, cpu_freq = measure_usage(pid)

    start_time = time.time()
    # using the python nemo bings nmo_python to load the rule file
    ruleFile = nmo_python.load_file("{}\{}".format(currPath, ruleFileName))

    # passing the loaded rls file to the nemo engine and running the nemo reasoner
    nemoRule = nmo_python.NemoEngine(ruleFile)
    print("Running the reasoner...")
    nemoRule.reason()

    # the write_result function accepts parmaters: predicate of the query to  be executed, outfile_manager that takes the NemoOutputManager structure with parameters file dir as string, bool overrite?, bool gzip? 
    # write_result writes the query results of the specified query to the specified output dir
    # for every output predicate in the rulefile, run the query and store results in a file
    for pred in ruleFile.output_predicates():
        print(pred)
        nemoRule.write_result(str(pred), nmo_python.NemoOutputManager(ruleFileName.split(".")[0], True, False))
    
    end_time = time.time()
    final_cpu_usage, final_memory_usage, cpu_freq = measure_usage(pid)

    cpu_usage = final_cpu_usage -initial_cpu_usage
    memory_usage = final_memory_usage - initial_memory_usage
    execution_time = (end_time - start_time)*1000

    #output the measures to the result file
    resFile = open("{}/{}/benches.txt".format(currPath, ruleFileName.split(".")[0]), "w")
    resFile.write("CPU usage:{}%\nMemory usage: {}MB\nCPU frequency: {}MHz\nExecution time: {}ms".format(cpu_usage, memory_usage, cpu_freq, execution_time))
    resFile.close()

    print("Query results processed!")
    os.chdir(owd)
    
def NemoBench():
    for root, dirs, files in os.walk('examples'):
        for rlsFile in files:
            if rlsFile.endswith(".rls"):
                print(root, rlsFile)
                runNemo(root, rlsFile)


if __name__=='__main__':
    rulewerkBench()
    # NemoBench()