#!/usr/bin/env python3

'''
This script evaulates the log file generated by the perf script.
It is useful when evaulating the PW latency statistics.
'''

import sys
import statistics

if len(sys.argv) < 1:
    sys.exit(-1)
if len(sys.argv) != 2:
    print("Usage:", sys.argv[0], "[perf.log]")
    sys.exit(-1)

input = sys.argv[1]
file = []
with open(input) as infile:
    for line in infile:
        file.append(line)

valid_cols = ["dtlb_load_misses.walk_completed", "dtlb_load_misses.walk_pending", "dtlb_load_misses.walk_active",
              "dtlb_store_misses.walk_completed", "dtlb_store_misses.walk_pending", "dtlb_store_misses.walk_active",
              "itlb_misses.walk_completed", "itlb_misses.walk_pending", "itlb_misses.walk_active",
              "cycles:ukhHG"]

'''
Read a line in the perf file.

Args:
A line in the perf file.

Returns:
If the line contains valid data, return the 3 columns of interest (len = 3)
If the line contains benchmark result, return the result (len = 1)
If the line is invalid, return an empty list (len = 0)
'''
def read_line(line):
    time = 0.0
    counts = 0
    col = 0
    components = line.split(" ")
    if components[0] == "Took:":
        return [float(components[1].split('\n')[0])]
    for component in components:
        if component == "" or component == "msec":
            continue
        try:
            if col == 0:
                time = float(component)
                col += 1
            elif col == 1:
                component = component.replace(",", "")
                counts = int(component)
                col += 1
            elif col == 2:
                if component in valid_cols:
                    return [time, counts, component]
                else:
                    return []
        except:
            return []
    return []

'''
Calculate the page walk latency.

Args:
Counts of columns of interest from one run.

Returns:
Page walk latency.
'''
def get_pw_latency(event_counts):
    pending = event_counts[valid_cols.index("dtlb_load_misses.walk_pending")] +\
        event_counts[valid_cols.index("dtlb_store_misses.walk_pending")] +\
        event_counts[valid_cols.index("itlb_misses.walk_pending")]
    completed = event_counts[valid_cols.index("dtlb_load_misses.walk_completed")] +\
        event_counts[valid_cols.index("dtlb_store_misses.walk_completed")] +\
        event_counts[valid_cols.index("itlb_misses.walk_completed")]
    if not completed:
        print("Warning: divide by zero")
        return 0.0
    return pending / completed


'''
Read one run in the perf file.

Args:
A line number in the perf file.

Returns:
A list contains a line number, runtime, PW latency, and columns of interest, accumulated.
If the run is the last run, the line number will be 0.
If the run is not the last run, the line number will be the begining of the next run.
'''
def read_run(line_num):
    end_time = 0.0
    end_linenum = 0
    next_linenum = 0
    runtime = 0.0
    pw_latency = 0.0
    event_counts = [0] * len(valid_cols)
    for i in range(line_num, len(file) - 1):
        cols = read_line(file[i])
        if len(cols) == 3:
            if cols[0] >= end_time:
                end_time = cols[0]
                end_linenum = i
                event_counts[valid_cols.index(cols[2])] += cols[1]
            elif cols[0] < end_time:
                next_linenum = i
                break
        elif len(cols) == 1:
            runtime = cols[0]
    pw_latency = get_pw_latency(event_counts)
    print("Runtime:", runtime)
    print("Page walk latency:", pw_latency)
    print("Evaulation duration: ", end_time, ", ", line_num + 1, " -> ", end_linenum + 1, sep="")
    for i in range(len(valid_cols)):
        print(valid_cols[i], event_counts[i], sep=": ")
    return [next_linenum, runtime, pw_latency] + event_counts

line_num = 0
run_count = 1
this_runtime = 0.0
this_latency = 0.0
runtime = list()
pw_latency = list()
while True:
    print("Run", run_count)
    line_num, this_runtime, this_latency = read_run(line_num)[0:3]
    runtime += [this_runtime]
    pw_latency += [this_latency]
    print("")
    if not line_num:
        break
    run_count += 1
print("Average runtime:", statistics.mean(runtime))
print("Average page walk latency:", statistics.mean(pw_latency))
