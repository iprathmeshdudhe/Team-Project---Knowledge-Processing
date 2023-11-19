import os
from loguru import logger
import csv


class WriteBench:

    def write_benchmark_results(timestamp, task, tool, execution_time, max_rss, max_vms, count):
        # if not csv file exist create a new one : in which directory?
        # header: timestamp task, tool, execution_time, memory_info
        # row: parameters in order
        # close csv
        flag = os.path.exists("BenchResults.csv")
        logger.info("writing benchmark results to csv file")
        with open("BenchResults.csv", mode="a", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            if flag:
                pass
            else:
                dw = csv.DictWriter(
                    csv_file,
                    delimiter=",",
                    fieldnames=[
                        "Timestamp (YYYY-MM-DD HH:MM:SS)",
                        "Task",
                        "Tool",
                        "Execution Time (ms)",
                        "Max. Resident Set Size (MB)",
                        "Max. Virtual Memory Size (MB)",
                        "Count of grounded Rule Predicates",
                    ],
                )
                dw.writeheader()
            csv_writer.writerow([timestamp, task, tool, execution_time, max_rss, max_vms, count])


    def lin_write_bench_results(timestamp, task, tool, exec_time, result_count, mem_usage_data):
        flag = os.path.exists("../MemUsageResults.csv")
        logger.info("writing memusage results to csv file")

        agg_heap_total =  round(sum(mem_usage_data['heap_total'])/ 1024 / 1024, 2)
        agg_heap_peak = round(sum(mem_usage_data['heap_peak'])/ 1024 / 1024, 2)
        agg_stack_peak = round(sum(mem_usage_data['stack_peak'])/ 1024 / 1024, 2)

        with open("../MemUsageResults.csv", mode="a", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            if flag:
                pass
            else:
                dw = csv.DictWriter(
                    csv_file,
                    delimiter=",",
                    fieldnames=[
                        "Timestamp (YYYY-MM-DD HH:MM:SS)",
                        "Task",
                        "Tool",
                        "Execution Time (ms)",
                        "Result Count",
                        "Heap Total (MB)",
                        "Heap Peak (MB)",
                        "Stack Peak (MB)"
                    ],
                )
                dw.writeheader()
            csv_writer.writerow([timestamp, task, tool, exec_time, result_count, agg_heap_total, agg_heap_peak, agg_stack_peak])
         #take the list of rls files in a task and from the memusage txt file of these rls files extract the info and do avg or max 
         #returns set of max or avg mem info 