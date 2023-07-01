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
    command = "clingo doctors/facts.lp doctors/run-doctors-100k.lp "
    
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

    #Converting Output from bytes to string
    outputString = output.decode("utf-8")

    #outputString = outputString.splitlines()

    #Saving the output to Text File
    with open("doctors/output.txt", "w") as outputFile:
        outputFile.write(outputString)
    
    print("Clingo Output is Saved !!")


def main():
    rule_file_path = 'Rulewerk_Rules/doctors/run-doctors-100k.rls'
    facts_lp_file = 'doctors/run-doctors-100k'


    ruleMapper = DatalogRuleMapper()
    RuleParser, Rule = ruleMapper.start_jvm()

    #Converting Rulewerk Rule file into Clingo rules file
    rules, facts, data_sources = ruleMapper.rulewerktoobject(rule_file_path, RuleParser)
    ruleMapper.rulewerk_to_clingo(rules, facts, data_sources, facts_lp_file)


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

    runClingo()

if __name__ == '__main__':
    main()

