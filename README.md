# A Benchmarking System for Datalog Reasoners


Welcome to the GitHub repository for our Master's Team project, a Datalog benchmarking tool developing under the guidance of our esteemed professors at TU Dresden: **Markus Krötsch, Stefan 
Ellmauthaler, Lukas Gerlach.** 

Datalog is a popular rule language, which is widely used in data management, knowledge representation, logic programming, and data analytics. Many different implementations have been developed. 
Due to the different input formats, features, and APIs, it is difficult to compare these implementations. Our team aims to fill this gap by developing a tool to compare different Datalog implementations.  

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

## Dependencies

* Python 3.9 or higher   
* Java 
* Rulewerk reasoner 0.9.0 or higher -- see [installation instruction](https://github.com/knowsys/rulewerk).
* Python packages listed in `requirements.txt`, and also Clingo. To do this, run:
```bash
cd Main
make install-requirements
````
* Soufflé tool  -- see  [Build Soufflé](https://souffle-lang.github.io/index.html). As a result of installation, you must have a  "souffle-master" folder installed on your computer  

## Comparison of Datalog Tools
Different tools support more or less features, data types, and  have different notations. This table summarizes the distinction:

|                   **Feature**                   |                            **Rulewerk**                             |       **Nemo (0.2.0)**        |                                           **Soufflé**                                           |                               **Clingo**                               |
|:-----------------------------------------------:|:-------------------------------------------------------------------:|:---------------------:|:-----------------------------------------------------------------------------------------------:|:----------------------------------------------------------------------:|
|      Syntax (illustrated by rule example)       | `selfPortrait(?Art,?Creator) :- painting(?Art,?Creator,?Creator) .` |   Same as Rulewerk    |     <br/>`CanRenovate(person, building) :- Owner(person, building) , !Heritage(building).`      |      `innocent(Suspect) :- motive(Suspect), not guilty(Suspect).`      |
| Notation for (universally quantified) variables |                       VarName preceded by '?'                       |   VarName preceded by '?'    |                               Written as is, lower or upper case                                |                 First letter captalized: `Myvariable`                  |
|             Notation for constants              |             quotes optional: type(?VarName, MyConstant)             |   Same as Rulewerk    |                         double quotes, lower or upper case: letter("a")                         |             Only lowercase, no quotation marks: myconstant             |
    |              Support for negation               |  Yes, stratified negation, with `~`: `∼painting(?Art,?By,"knife")`  | Yes, Same as Rulewerk |                               Yes, with `!`: `!samePerson(X, Y)`                                | Yes, classical & stratified negation: `not samePerson` / `~samePerson` |`
    | Support for exstentially quantified varibables  |          Yes (in rule head), with `!`: `type(!New,?Class)`          |          yes, Same as Rulewerk          |                                               No                                                |                                   No                                   |
|             Support for comparison              |                                 No                                  |          Yes, <=, <, >=, > for integer type          |                                               Yes                                               |                                  Yes                                   |
|                CSV input support                |                                 Yes                                 |          Yes          |                             No (need transformation into .csv file)                             |      No (need transformation into a list of facts in a rule file)      |
|                RDF input support                |                                 No                                  |          Yes          |                                               No                                                |      No |
|     Support of diferent varibale data types     |                                 No                                  |           Yes: 3 Datatypes (`integer`, `float64`, `any` - default)           | Yes: 4 primitive data types (`symbol`, `number`, `unsigned`, and `float`) and custom data types |                                   ?                                    |

Respectively, our benchmarking is aimed mostly on translating the rulewerk examples that are supported among all respective tools. 

## Souffle
[Documentation](https://souffle-lang.github.io/index.html)

## Tool usage
Before using the tool:
* Go to Main/src/config.py and set up the environment variables for your computer.
* Place Rulewerk examples you want to run into Rulewerk_Rules directory. Please follow the same directory structure and the one on the given examples already.
* Configure the tasks and the solvers you want to run in the config.json file. In "solvers", write a list of tools you want to run or write ["all"] to run all available tools

To Run the tool, run the main.py script using the command:

```bash
cd Main
python main.py --config_file config.json
```

## Tool flow
<img src="./Tool flow.png"> 

