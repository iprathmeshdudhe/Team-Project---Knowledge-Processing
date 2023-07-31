# A Benchmarking System for Datalog Reasoners


Welcome to the GitHub repository for our Master's Team project, a Datalog benchmarking tool developing under the guidance of our esteemed professors. 

Datalog is a popular rule language, which is widely used in data management, knowledge representation, logic programming, and data analytics. Many different implementations have been developed, including logic programming engines (such as Clingo), existential rule reasoners (such as VLog and Nemo), and specialised data analytics tools (such as Souffle, for program analytics). Due to the different input formats, features, and APIs, it is difficult to compare these implementations. 

The goal of this team project is to design and develop system for benchmarking various Datalog implementations. The system should be able to conduct experiments with several Datalog engines, collect results and relevant performance metrics (runtimes, memory usage), and store the latter for further analysis. To accomplish this, the system should maintain a library of Datalog benchmarks and test cases in a unified format, and provide functions for translating these logic programs into the formats used by different Datalog systems. Different systems need different translations and to be called in different ways, and the architecture should be designed in a way that makes it easy to add new systems in the future. In addition, it would be useful to provide functionality for managing the test cases and the measured results. Analytical capabilities and visualisations can be added to further enhance this functionality.

## Installation

```shell
git clone https://github.com/iprathmeshdudhe/Team-Project---Knowledge-Processing/tree/main
```

### Dependencies

* Python 3.9 or higher   
* pandas                --  ```pip install pandas```
* clingo                --  ```pip install clingo```
* psutil                --  ```pip install psutil```

## Experiment

To Run the tool, we just need to the run main.py script using the command:

```bash
python -m main --solver clingo --input_dir /path/to/rule/files
```
For other solvers, you may simply modify the arguments `--solver` accordingly with the options [clingo, nemo, souflle].

Replace /path/to/rule/files with the directory containing the Rulewerk rule files which we use as starting point.
