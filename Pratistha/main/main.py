import os
import subprocess
import psutil
import time 
from datalogrulemapper import *
import nmo_python


def runRulewerk():
    #change to directory containing the rule file and rulewerk jar file
    os.chdir("../rulewerk")

    currPath = os.getcwd()

    #file to store the query results
    resFilePath = currPath+"/" + "queryResult.txt"
    resFile = open(resFilePath, 'w+')

    #run the rule file and query through rulewerk command line
    command = "java -jar rulewerk.jar materialize --rule-file=example1\doid.rls --query=humansWhoDiedOfNoncancer(?X) --print-query-result-size=false --print-complete-query-result"


    process = psutil.Process()

    process_start_time = time.process_time()
    start_time = time.time()

    #run the rulewerk command and store command prompt outsput to resFile
    subprocess.run(command, shell=True, stdout=resFile)

    end_time = time.time()
    process_end_time = time.process_time()

    resFile.close()

    #memory usage of the program
    memory_info = process.memory_info()

    #cpu runtime and overall runtime of the program
    cpu_runtime = process_end_time - process_start_time
    overall_runtime = end_time - start_time

    #output the measures to the result file
    resFile = open(resFilePath, "a")
    resFile.write("Memory usage: {} bytes\n CPU Runtime: {} seconds\n Overall Runtime: {} seconds".format(memory_info.rss, cpu_runtime, overall_runtime))
    resFile.close()

    print("Query complete")



def runNemo():
    os.chdir("../nemo_examples/example1")
    currDir = os.getcwd()

    process = psutil.Process()
    process_start_time = time.process_time()
    start_time = time.time()

    # using the python nemo bings nmo_python to load the rule file
    ruleFile = nmo_python.load_file("old-lime-trees.rls")

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
        nemoRule.write_result(str(pred), nmo_python.NemoOutputManager("Results", True, False))
    
    end_time = time.time()
    process_end_time = time.process_time()

    # memory usage of the program
    memory_info = process.memory_info()

    #cpu runtime and overall runtime of the program
    cpu_runtime = process_end_time - process_start_time
    overall_runtime = end_time - start_time

    #output the measures to the result file
    resFile = open(currDir+"/benches.txt", "w")
    resFile.write("Memory usage: {} bytes\n CPU Runtime: {} seconds\n Overall Runtime: {} seconds".format(memory_info.rss, cpu_runtime, overall_runtime))
    resFile.close()

    print("Query results processed!")

# def runNemo():
#     #change to directory containing the rule file and rulewerk jar file
    

#     currPath = os.getcwd()

#     #file to store the query results
#     resFilePath = currPath+"/benches/" + "queryResult.txt"
#     resFile = open(resFilePath, 'w+')

#     #run the rule file and query through rulewerk command line
#     command = "nmo benches/bench100.rls"


#     process = psutil.Process()

#     process_start_time = time.process_time()
#     start_time = time.time()

#     #run the rulewerk command and store command prompt outsput to resFile
#     #subprocess.run(command, shell=True, stdout=resFile)

#     end_time = time.time()
#     process_end_time = time.process_time()

#     resFile.close()

#     #memory usage of the program
#     memory_info = process.memory_info()

#     #cpu runtime and overall runtime of the program
#     cpu_runtime = process_end_time - process_start_time
#     overall_runtime = end_time - start_time

#     #output the measures to the result file
#     resFile = open(resFilePath, "a")
#     resFile.write("Memory usage: {} bytes\n CPU Runtime: {} seconds\n Overall Runtime: {} seconds".format(memory_info.rss, cpu_runtime, overall_runtime))
#     resFile.close()

#     print("Query complete")

def main():
    ruleMapper = DatalogRuleMapper()
    RuleParser, Rule = ruleMapper.start_jvm()
    rule_raw = "ancestor(?X,?Y) :- parent(?X,?Z), ancestor(?Z,?Y)."
    clingo_rule = ruleMapper.rulewerk_to_clingo(rule_raw, RuleParser)
    print("Clingo Rule: ", clingo_rule)
    ruleMapper.stop_jvm()

if __name__=='__main__':
    runNemo()