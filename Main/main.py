import os
import psutil
import clingo
import subprocess
from datalogrulemapper import DatalogRuleMapper


def runClingo():
    # Get the current PATH environment variable value
    path = os.getcwd()
    print("Current PATH:", path)

    # Run a command on the command prompt with the new PATH environment variable
    command = "clingo clingo.lp"
    
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
    rule_file_path = '../rulewerk_examples/relations.rls'


    ruleMapper = DatalogRuleMapper()
    RuleParser, Rule = ruleMapper.start_jvm()

    #Converting Rulewerk Rule file into Clingo rules file
    facts_list, rules_list, query_pred = ruleMapper.rulewerk_to_clingo(rule_file_path, RuleParser)

    #Writing the Facts, rules and Query in the Clingo input file
    with open('clingo.lp', 'w') as clingo_file:
        clingo_file.writelines('\n'.join(facts_list))
        clingo_file.write('\n')
        clingo_file.writelines('\n'.join(rules_list))
        clingo_file.write('\n#show '+ str(query_pred) + "/1.")

    type_declarations, facts_list, rules_list, query = ruleMapper.rulewerk_to_souffle(rule_file_path, RuleParser)

    with open('souffle-example.dl', 'w') as output_file:
        output_file.write('// Declarations\n')
        output_file.writelines('\n'.join(type_declarations))
        output_file.write('\n\n')
        output_file.write('// Facts\n')
        output_file.writelines('\n'.join(facts_list))
        output_file.write('\n\n')
        output_file.write('// Rules\n')
        output_file.writelines('\n'.join(rules_list))
        output_file.write('\n\n')
        output_file.write('// Query\n')
        output_file.writelines('\n'.join(query))
        output_file.write('\n\n')



    ruleMapper.stop_jvm()

if __name__ == '__main__':
    main()
    # runClingo()

