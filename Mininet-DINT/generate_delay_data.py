import sys
import os
file_name=sys.argv[1]

os.system("mkdir -p experiments/delays/")

# Format of each line: time, "n:"node, intf:qidx, qlen, event, "ecn:"ecn, sip, dip, sport, dport, l3port, seq, ts, pg, pktsize(MTU) [payload]
f=open(file_name,"r")
data={} # Flow: [[[Enqu, Dequ]*5]*x]
firstnodes={} # Flow: [[first node]*x]
idxes = {} # Flow: [curpktidx, curdevidx]
valid_linenum = 0
max_linenum = 1000*1000
for line in f:
    elements = line.strip().split(" ")
    time = int(elements[0]) # Unit: ns
    node = elements[1]
    #dev = int(elements[1].split(":")[1])
    #dev = dev%5 # 5-hop Fat Tree Topology
    event = elements[4]
    sip = elements[6]
    dip = elements[7]
    sport = elements[8]
    dport = elements[9]
    seq = elements[11]
    #pkt = "{}-{}-{}-{}-{}".format(sip, dip, sport, dport, seq)
    flow = "{}-{}".format(sip, dip)
    if event == "Enqu":
        if flow not in data:
            data[flow] = []
            data[flow].append([[time, -1]])
            idxes[flow] = [0, 0]
            firstnodes[flow] = node
        #elif len(data[flow][-1]) == 5:
        elif node == firstnodes[flow]:
            data[flow].append([[time, -1]])
        else:
            data[flow][-1].append([time, -1])
        valid_linenum += 1
    elif event == "Dequ":
        if flow not in data:
            continue
        while True:
            curpktidx = idxes[flow][0]
            curdevidx = idxes[flow][1]
            if (curpktidx > len(data[flow])-1) or (curdevidx > len(data[flow][curpktidx])-1):
                break
            elif data[flow][curpktidx][curdevidx][1] == -1:
                data[flow][curpktidx][curdevidx][1] = time
                valid_linenum += 1
                break
            else:
                if idxes[flow][1] == (len(data[flow][curpktidx])-1):
                    idxes[flow][0] += 1
                    idxes[flow][1] = 0
                else:
                    idxes[flow][1] += 1
    else:
        continue
    if valid_linenum >=max_linenum:
        break
print("Valid line number: {}".format(valid_linenum))
f.close()

fw=open("experiments/delays/processed_data","w")
valid_latencynum = 0
for key,value in data.items():
    for pktidx in range(len(value)):
        latency = []
        for devidx in range(len(value[pktidx])):
            if value[pktidx][devidx][1] == -1: # Invalid condition
                break
            latency.append(abs(value[pktidx][devidx][1]-value[pktidx][devidx][0]))
        #dev = key.split("-")[0]
        if len(latency) <= 5 and len(latency) > 0:
            #fw.write("{} {} {} {} {}\n".format(latency[0], latency[1], latency[2], latency[3], latency[4]))
            for latencyidx in range(len(latency)):
                if len(latency) == 1:
                    fw.write("{}\n".format(latency[latencyidx]))
                elif latencyidx == 0:
                    fw.write("{}".format(latency[latencyidx]))
                elif latencyidx == (len(latency)-1):
                    fw.write(" {}\n".format(latency[latencyidx]))
                else:
                    fw.write(" {}".format(latency[latencyidx]))
            valid_latencynum += 1
print("Valid latency number: {}".format(valid_latencynum))
fw.close()
