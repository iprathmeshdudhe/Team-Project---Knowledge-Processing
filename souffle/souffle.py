import os
import subprocess
import json


def run_souffle_program():
    path = os.getcwd()
    print("Current PATH:", path)

    # command = '../souffle-master/build/src/souffle -F../souffle/input -D../souffle/output ../souffle/input/souffle-example.dl -p ../souffle/output/souffle-log.json'
    # command = '../souffle-master/build/src/souffle -F../souffle/input -D../souffle/output ../souffle/input/ancestor2.dl -p ../souffle/output/souffle-log.json'
    command = '../souffle-master/build/src/souffle -F../souffle/input -D../souffle/output ../souffle/input/relations.dl -p ../souffle/output/souffle-log.json'

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


run_souffle_program()

