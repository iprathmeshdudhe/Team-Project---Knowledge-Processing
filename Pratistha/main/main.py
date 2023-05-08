import os
import subprocess

#change to directory containing the rule file and rulewerk jar file
os.chdir("../rulewerk-example")
currPath = os.getcwd()
resFile = open(currPath+ "/" + "result.txt", 'w+')
#run the rule file and query through rulewerk command line

command = "java -jar rulewerk.jar materialize --rule-file=doid.rls --query=humansWhoDiedOfNoncancer(?X) --print-query-result-size=false --print-complete-query-result"

subprocess.run(command, shell=True, stdout=resFile)
resFile.close()