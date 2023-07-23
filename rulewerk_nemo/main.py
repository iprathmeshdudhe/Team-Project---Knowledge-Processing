import os
import subprocess
import psutil
import time 
import nmo_python
import jpype
import jpype.imports
from jpype.types import *
from datalogrulemapper import *

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
        print(query)
        toQuery = toQuery + "--query=" + str(query) + " "
    print(toQuery)
    #run the rule file and query through rulewerk command line
    command = "java -jar ..\\rulewerk.jar materialize --rule-file={} {} --print-query-result-size=false --print-complete-query-result".format(ruleFileName, toQuery)

    process = psutil.Process()

    process_start_time = time.process_time()
    start_time = time.time()

    #run the rulewerk command and store command prompt output to resFile
    output = subprocess.run(command, capture_output=True, text=True)
    print(output.stdout)
    print(output.stderr)

    end_time = time.time()
    process_end_time = time.process_time()
    #memory usage of the program
    memory_info = process.memory_info()

    #cpu runtime and overall runtime of the program
    cpu_runtime = process_end_time - process_start_time
    overall_runtime = end_time - start_time

    # outputlines = output.split("\n")
    # print("Output lines:", outputlines)
    printFlag = False
    output = output.stdout.split("\n")
    for line in output:
        if line != "":
            print(line)
            if(line.split()[0]=="Answers"):
                printFlag = True
                queryName = line.split()[3].split("(")[0]
                queryResFile = open(currPath +R"\{}.txt".format(queryName), 'w')
                queryResFile.close()
                continue

            if(line.split()[0]=="Query"):
                printFlag = False
                queryName = line.split()[3].split("(")[0]
                continue
        
            if printFlag==True:
                queryResFile = open(currPath +R"\{}.txt".format(queryName), 'a')
                queryResFile.write(line+"\n")
                queryResFile.close()

    #output the measures to the result file
    benchFile = open(bench, 'w+')
    benchFile.write("Memory usage: \n CPU Runtime: {} seconds\n Overall Runtime: {} seconds".format(cpu_runtime, overall_runtime))
    benchFile.close()

    print("Query complete")
    os.chdir(owd)

def rulewerkBench():
    ruleMapper = DatalogRuleMapper()
    parser, Rule, Literal = ruleMapper.start_jvm()
    # runRulewerk(parser, Rule, Literal, "rulewerk-examples\\ancestor", "ancestor.rls")
    for root, dirs, files in os.walk('rulewerk-examples'):
        for rlsFile in files:
            if rlsFile.endswith(".rls"):
                print(root, rlsFile)
                runRulewerk(parser, Rule, Literal, root, rlsFile)
    ruleMapper.stop_jvm()            

def runNemo(ruleFilePath, ruleFileName):
    owd = os.getcwd()
    os.chdir(ruleFilePath)
    currPath = os.getcwd()
    process = psutil.Process()
    process_start_time = time.process_time()
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
    process_end_time = time.process_time()

    # memory usage of the program
    memory_info = process.memory_info()

    #cpu runtime and overall runtime of the program
    cpu_runtime = process_end_time - process_start_time
    overall_runtime = end_time - start_time

    #output the measures to the result file
    resFile = open("{}/{}/benches.txt".format(currPath, ruleFileName.split(".")[0]), "w")
    resFile.write("Memory usage: {} \n CPU Runtime: {} seconds\n Overall Runtime: {} seconds".format(memory_info.rss/1024/1024, cpu_runtime, overall_runtime))
    resFile.close()

    print("Query results processed!")
    os.chdir(owd)
    
def NemoBench():
    for root, dirs, files in os.walk('nemo_examples'):
        for rlsFile in files:
            if rlsFile.endswith(".rls"):
                print(root, rlsFile)
                runNemo(root, rlsFile)


if __name__=='__main__':
    # rulewerkBench()
    NemoBench()