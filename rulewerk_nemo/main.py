import os
import subprocess
import psutil
import time 
# from datalogrulemapper import *
import nmo_python
import jpype
import jpype.imports
from jpype.types import *



def runRulewerk():
    #change to directory containing the rule file and rulewerk jar file
    os.chdir("rulewerk-examples")

    ruleFilePath = R'ancestor\ancestor.rls'

    currPath = os.getcwd()

    #file to store the query results
    bench = currPath +R"\ancestor\queryBench.txt"

    #run the rule file and query through rulewerk command line
    command = "java -jar rulewerk.jar materialize --rule-file="+ruleFilePath+" --query=ancestor(?X,?Y) --print-query-result-size=false --print-complete-query-result"


    process = psutil.Process()

    process_start_time = time.process_time()
    start_time = time.time()

    #run the rulewerk command and store command prompt output to resFile
    output = subprocess.run(command, capture_output=True, text=True).stdout

    end_time = time.time()
    process_end_time = time.process_time()
    #memory usage of the program
    memory_info = process.memory_info()

    #cpu runtime and overall runtime of the program
    cpu_runtime = process_end_time - process_start_time
    overall_runtime = end_time - start_time

    outputlines = output.split("\n")
    printFlag = False
    for line in outputlines:
        if line != "":
            print(line)
            if(line.split()[0]=="Answers"):
                printFlag = True
                queryName = line.split()[3].split("(")[0]
                queryResFile = open(currPath +R"\ancestor\{}.txt".format(queryName), 'w')
                queryResFile.close()
                continue

            if(line.split()[0]=="Query"):
                printFlag = False
                queryName = line.split()[3].split("(")[0]
                continue
        
            if printFlag==True:
                queryResFile = open(currPath +R"\ancestor\{}.txt".format(queryName), 'a')
                queryResFile.write(line+"\n")
                queryResFile.close()

    #output the measures to the result file
    benchFile = open(bench, 'w+')
    benchFile.write("Memory usage: {} \n CPU Runtime: {} seconds\n Overall Runtime: {} seconds".format(memory_info.rss/1024/1024, cpu_runtime, overall_runtime))
    benchFile.close()

    print("Query complete")



def runNemo():
    os.chdir("nemo_examples/example2")
    currDir = os.getcwd()
    ruleFileName = "ancestor"
    process = psutil.Process()
    process_start_time = time.process_time()
    start_time = time.time()

    # using the python nemo bings nmo_python to load the rule file
    ruleFile = nmo_python.load_file("{}\{}.rls".format(currDir, ruleFileName))

    # passing the loaded rls file to the nemo engine and running the nemo reasoner
    nemoRule = nmo_python.NemoEngine(ruleFile)
    print("Running the reasoner...")
    nemoRule.reason()
    # results = nemoRule.result("oldLime")

    # # print all the query results
    # for res in results:
    #     print(res)

    # the write_result function accepts parmaters: predicate of the query to  be executed, outfile_manager that takes the NemoOutputManager structure with parameters file dir as string, bool overrite?, bool gzip? 
    # write_result writes the query results of the specified query to the specified output dir
    # for every output predicate in the rulefile, run the query and store results in a file
    for pred in ruleFile.output_predicates():
        print(pred)
        nemoRule.write_result(str(pred), nmo_python.NemoOutputManager(ruleFileName, True, False))
    
    end_time = time.time()
    process_end_time = time.process_time()

    # memory usage of the program
    memory_info = process.memory_info()

    #cpu runtime and overall runtime of the program
    cpu_runtime = process_end_time - process_start_time
    overall_runtime = end_time - start_time

    #output the measures to the result file
    resFile = open("{}/{}/benches.txt".format(currDir, ruleFileName), "w")
    resFile.write("Memory usage: {} \n CPU Runtime: {} seconds\n Overall Runtime: {} seconds".format(memory_info.rss/1024/1024, cpu_runtime, overall_runtime))
    resFile.close()

    print("Query results processed!")
    

# def main():
#     ruleMapper = DatalogRuleMapper()
#     parser, Rule = ruleMapper.start_jvm()
#     with open(R"C:\Users\kansa\Desktop\Team Project TUD SoSe23\Team-Project---Knowledge-Processing\Pratistha\rulewerk\example1\doid.rls", 'r') as rule_file:
#         kb = parser.parse(rule_file.read())

#         #Getting facts from the Rule File
#         #facts = kb.getFacts()
#         #facts_list = [str(facts[i].toString()).lower() for i in range(len(facts))]
        
#         #Getting datasources from the Rule File
        
#         data_sources = kb.getDataSourceDeclarations()   # will return list of datasources
        

#         for src in data_sources:
#             predicate = src.getPredicate()
#             source = src.getDataSource()
#             print("Predicate Name: ", predicate.getName()," Arity: ", predicate.getArity())  
#             print(source.getDeclarationFact().getArguments())
#     ruleMapper.stop_jvm()

if __name__=='__main__':
    runRulewerk()