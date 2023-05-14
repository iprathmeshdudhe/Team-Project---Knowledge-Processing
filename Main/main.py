import os
import psutil
import clingo
import subprocess
from datalogrulemapper import *


def runClingo():
    # Get the current PATH environment variable value
    path = os.getcwd()
    print("Current PATH:", path)

    # Run a command on the command prompt with the new PATH environment variable
    command = "clingo ../clingo-5.6.2/examples/gringo/queens/queens1.lp"
    
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

    #Converting Output from bytes to string
    outputString = output.decode("utf-8")

    #outputString = outputString.splitlines()

    # Print the output
    print("Output: \n" + outputString)

    #Saving the output to Text File
    outputFile = open("output.txt", "w")
    outputFile.write(outputString)
    outputFile.close()


def main():
    ruleMapper = DatalogRuleMapper()
    RuleParser, Rule = ruleMapper.start_jvm()
    rule_raw = "ancestor(?X,?Y) :- parent(?X,?Z), ancestor(?Z,?Y)."
    clingo_rule = ruleMapper.rulewerk_to_clingo(rule_raw, RuleParser)
    print("Clingo Rule: ", clingo_rule)
    ruleMapper.stop_jvm()

if __name__ == '__main__':
    main()
    runClingo()
