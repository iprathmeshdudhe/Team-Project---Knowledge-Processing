import os
import subprocess
import psutil
import time 

#change to directory containing the rule file and rulewerk jar file
os.chdir("../rulewerk-example")

currPath = os.getcwd()

#file to store the query results
resFile = open(currPath+ "/" + "result.txt", 'w+')

#run the rule file and query through rulewerk command line
command = "java -jar rulewerk.jar materialize --rule-file=doid.rls --query=humansWhoDiedOfNoncancer(?X) --print-query-result-size=false --print-complete-query-result"


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

#output the measures to the terminal
print("Memory usage:",  memory_info.rss, "bytes")
print("CPU Runtime:", cpu_runtime, "seconds")
print("Overall Runtime:", overall_runtime, "seconds")