import os
import subprocess
import json

from Main.datalogrulemapper import DatalogRuleMapper


def run_souffe_program():
    path = os.getcwd()
    print("Current PATH:", path)

    # command = '../souffle-master/build/src/souffle -F../souffle/input -D../souffle/output ../souffle/input/souffle-example.dl -p ../souffle/output/souffle-log.json'
    command = '../souffle-master/build/src/souffle -F../souffle/input -D../souffle/output ../souffle/input/ancestor2.dl -p ../souffle/output/souffle-log.json'

    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    with open('../souffle/output/souffle-log.json') as f:
        data = json.load(f)
        start = data['root']['program']['runtime']['start']
        end = data['root']['program']['runtime']['end']
        program_duration = end - start
        print(f'Souffle execution took {program_duration} microseconds')  # check if really microseconds
        timepoints = data['root']['program']['usage']['timepoint'].values()
        max_rss_list = [timepoint['maxRSS'] for timepoint in timepoints]
        max_rss = max(max_rss_list)/1024/1024
        print(f'Souffle execution took maximum RSS (Resident Set Size) of {max_rss} MB')


ruleMapper = DatalogRuleMapper()
RuleParser, Rule = ruleMapper.start_jvm()
rulewerk_rules = """%data as facts
father(Bob, David).
mother(Bob, Anna).
father(Anna, Richard).
mother(Richard, Lucy).
father(Alice, Bob).
mother(Alice, Brenda).
father(Josh, David).
mother(Josh, Paula).

%rules
ancestor(?X, ?Y) :- parent(?X, ?Z), ancestor(?Z, ?Y).

%To query
result(?Y) :-  ancestor(Alice, ?Y).
"""
# rule_law = "ancestor(?X,?Y) :- parent(?X,?Z), ancestor(?Z,?Y)."

for rulewerk_rule in rulewerk_rules.split('\n'):
    print("Rulewerk rule: ", rulewerk_rule)
    if '%' in rulewerk_rule:
        souffle_rule = rulewerk_rule.replace('%', '//')
    else:
        souffle_rule = ruleMapper.rulewerk_to_souffle(rulewerk_rule, RuleParser)
    print("Souffle Rule: ", souffle_rule)




