import os
import psutil
import clingo
import subprocess

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