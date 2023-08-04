# A Benchmarking System for Datalog Reasoners


Welcome to the GitHub repository for our Master's Team project, a Datalog benchmarking tool developing under the guidance of our esteemed professors at TU Dresden: **Markus Krötsch, Stefan 
Ellmauthaler, Lukas Gerlach** 

Datalog is a popular rule language, which is widely used in data management, knowledge representation, logic programming, and data analytics. Many different implementations have been developed. Due to the different input formats, features, and APIs, it is difficult to compare these implementations. 

Currently supported languages for benchmarking are:
* Clingo (logic programming engine)
* Nemo (existential rule reasoner)
* Souffle (specialised data analytics tool for program analytics)
* Rulewerk

The system is able to conduct experiments with several Datalog engines, collects results and relevant performance metrics: runtime and memory usage, and stores the results for further analysis in 
a CSV format.

To accomplish this, the system contains a library of Datalog benchmarks (in a folder rulewerk_examples) and test cases in a unified Rulewerk format, and contains functions for translating these 
logic programs into the  formats  used by different Datalog systems. It is possible to add new modules to support other tools in the future.



## Installation

```shell
git clone https://github.com/iprathmeshdudhe/Team-Project---Knowledge-Processing/tree/main
```

### Dependencies

* Python 3.9 or higher   
* pandas                --  ```pip install pandas```
* clingo                --  ```pip install clingo```
* psutil                --  ```pip install psutil```
* Soufflé tool  -- see  [Build Soufflé](https://souffle-lang.github.io/index.html). As a result of installation, you must have a  "souffle-master" folder installed on your computer  


## Souffle
[Documentation](https://souffle-lang.github.io/index.html)

## Tool usage

To Run the tool, we just need to the run main.py script using the command:

```bash
python -m main --solver clingo --input_dir /path/to/rule/files
```
For other solvers, you may simply modify the arguments `--solver` accordingly with the options [clingo, nemo, souflle].

Replace /path/to/rule/files with the directory containing the Rulewerk rule files which we use as starting point.
