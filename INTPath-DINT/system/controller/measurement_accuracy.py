#!/usr/bin/env python3

import os
import mmh3
import struct

## Global variables

dirname = "../packet/tmp"
filenames = ["h4_dump.txt", "h6_dump.txt", "h8_dump.txt"]
thresholds = [0, 0, 0, 10] # deiveno, iport, eport, timedelta
statenum = len(thresholds)
hopnum = 3

totalbytes = 1024 * 1024 # 1MB
hashnum = 1
width = int(totalbytes / (2 + 3 + 4) / hashnum)

## Util functions

def init_sketches():
    global hopnum, hashnum, width
    sketches = []
    for _ in range(hopnum):
        sketches.append([])
        sketch = sketches[-1]
        for i in range(hashnum):
            sketch.append([])
            for j in range(width):
                sketch[i].append([-1, -1, -1, -1, -1]) # flowkey, deviceno, iport, eport, timedelta
    return sketches

def hash(flowkey):
    global width
    flowkey_bytes = struct.pack("L", flowkey)
    r = mmh3.hash(flowkey_bytes, signed=False)
    return r % width

def state_load(sketch, flowkey):
    global hashnum
    for row in range(hashnum):
        col = hash(flowkey)
        bucket = sketch[row][col]
        if bucket[0] == flowkey:
            return bucket[1:5]
    return None

def delta_calc(curstates, recstates):
    global thresholds
    results = []
    for i in range(len(curstates)):
        if recstates[i] != -1 and abs(curstates[i] - recstates[i]) <= thresholds[i]:
            results.append(recstates[i])
        else:
            results.append(curstates[i])
    return results

def state_update(sketch, flowkey, outputs):
    global hashnum
    for row in range(hashnum):
        col = hash(flowkey)
        bucket = sketch[row][col]
        bucket[0] = flowkey
        for i in range(len(outputs)):
            bucket[i+1] = outputs[i]

def accuracy_calc(curstates, outputs):
    res = []
    # Only consider dynamic states
    for i in range(len(curstates)):
        if i != len(curstates) - 1:
            if curstates[i] == outputs[i]:
                re = 0.0
            else:
                re = 1.0
            #continue
        else:
            if curstates[i] != 0:
                re = abs(curstates[i] - outputs[i]) / float(curstates[i])
            else:
                if outputs[i] == 0:
                    re = 0.0
                else:
                    re = 1.0
        res.append(re)
    return res

global_res = []
for filename in filenames:
    sketches = init_sketches()
    filepath = os.path.join(dirname, filename)
    fd = open(filepath, "r")
    while True:
        line = fd.readline().strip()
        if line == "":
            break
        entries = line.split(" ")
        for i in range(len(entries)):
            entries[i] = int(entries[i])

        flowkey = entries[0]
        intlist = []
        for idx in range(hopnum):
            base = statenum * idx
            intlist.append([entries[base+1], entries[base+2], entries[base+3], entries[base+4]])

        for idx in range(hopnum):
            sketch = sketches[idx]
            recstates = state_load(sketch, flowkey)
            if recstates is not None:
                outputs = delta_calc(intlist[idx], recstates)
            else:
                outputs = intlist[idx]
            state_update(sketch, flowkey, outputs)
            res = accuracy_calc(intlist[idx], outputs)
            global_res += res

    fd.close()

avg_re = sum(global_res) / float(len(global_res))
print("Average relative error of measurement accuracy of states: {}".format(avg_re))
