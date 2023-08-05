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
* clingo                --  ```pip install clingo``` or  ```conda install -c conda-forge clingo```
* psutil                --  ```pip install psutil```
* Soufflé tool  -- see  [Build Soufflé](https://souffle-lang.github.io/index.html). As a result of installation, you must have a  "souffle-master" folder installed on your computer  

## Comparison of Datalog Tools
Different tools support more or less features, data types, and  have different notations. This table summarizes the distinction:

|                    **Tool**                     |                            **Rulewerk**                             |       **Nemo**        |                                                                                    **Soufflé**                                                                                     |                             **Clingo**                             |
|:-----------------------------------------------:|:-------------------------------------------------------------------:|:---------------------:|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------:|:------------------------------------------------------------------:|
|                  Rule example                   | `selfPortrait(?Art,?Creator) :- painting(?Art,?Creator,?Creator) .` |   Same as Rulewerk    |                                                 `CanRenovate(person, building) :- Owner(person, building) , !Heritage(building).`                                                  |    `innocent(Suspect) :- motive(Suspect), not guilty(Suspect).`    |
| Notation for (universally quantified) variables |                       Starts with a `?` mark                        |   Same as Rulewerk    |                                                                         Written as is, lower or upper case                                                                         |               First letter captalized: `Myvariable`                |
|             Notation for constants              |               double quotes: type(?Motive, "island")                |   Same as Rulewerk    |                                                                  double quotes, lower or upper case: letter("a")                                                                   |           Only lowercase, no quotation marks: myconstant           |
    |              Support for negation               |       Yes, stratified, with `~`: `∼painting(?Art,?By,"knife")`        | Yes, Same as Rulewerk |                                                                         Yes, with `!`: `!samePerson(X, Y)`                                                                         | Yes, classical & stratified negation: `not samePerson` / `~samePerson` |`
    |  Support for exstentially quanified varibables  |                 Yes, with `!`: `type(!New,?Class)`                  |          Yes          |                                                                                         No                                                                                         |                                 No                                 |
|      comparison > < for numeric variables       |                                 No                                  |          Yes          |                                                                                        Yes                                                                                         |                                Yes                                 |
|                CSV input support                |                                 Yes                                 |          Yes          |                                                                                        Yes                                                                                         |                                 No                                 |
|     Support of diferent varibale data types     |                                 No                                  |           ?           |                                              Yes: 4 primitive data types (`symbol`, `number`, `unsigned`, and `float`) and custom data types                                               |                                 ?                                  |
|           Support of float data type            |                                 Yes                                 |           ?           |                                                                                        Yes                                                                                         |                                 No                                 |

Respectively, our benchmarking tool only translate the ruleverk exampless that are supported in the respective tools and throws and error otherwise. 

## Souffle
[Documentation](https://souffle-lang.github.io/index.html)

## Tool usage

To Run the tool, we just need to the run main.py script using the command:

```bash
python -m main --solver clingo --input_dir /path/to/rule/files --task_name name_of_the_task
```
For other solvers, you may simply modify the arguments `--solver` accordingly with the options: `clingo`, `nemo`, `souflle`, `all`.

Replace /path/to/rule/files with the directory containing the Rulewerk rule files which we use as starting point.

<img src="./Tool diagram.png"> #TODO : Add image

