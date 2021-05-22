import math
import time
import sys
import numpy as np
import operator
import random
import os
from kll import KLL

random.seed(30)

#def get_approx_res(value, i):
def get_approx_res(value, true_median, true_avg, true_tail):
    #global all_median
    #global all_avg
    #global all_tail

    #Using sketch to store digests
    kll = KLL(sketch_size)
    for v in value:
        kll.update(v)

    min_diff_50 = 1000
    min_diff_99 = 1000
    pint_median = 0
    pint_tail = 0
    for (ii, quantile) in kll.cdf():
        diff = quantile - 0.5
        if diff < 0:
            diff = diff * -1
        if diff<min_diff_50:
            min_diff_50 = diff
            pint_median = ii

        diff = quantile - 0.99
        if diff < 0:
            diff = diff * -1
        if diff<min_diff_99:
            min_diff_99 = diff
            pint_tail = ii

    pint_avg=sum(value)/float(len(value))

    #if all_median[i]!=0:
    #    error_median=(all_median[i]-pint_median)/float(all_median[i])*100
    #if all_median[i]==0:
    #    error_median=0
    #error_avg=(all_avg[i]-pint_avg)/float(all_avg[i])*100
    #error_tail=(all_tail[i]-pint_tail)/float(all_tail[i])*100
    if true_median != 0:
        error_median = (true_median-pint_median)/float(true_median)*100
    else:
        error_median = 0
    if true_avg != 0:
        error_avg = (true_avg-pint_avg)/float(true_avg)*100
    else:
        error_avg = 0
    if true_tail != 0:
        error_tail = (true_tail-pint_tail)/float(true_tail)*100
    else:
        error_tail = 0

    if error_median<0:
        error_median=error_median*-1
    if error_avg<0:
        error_avg=error_avg*-1
    if error_tail<0:
        error_tail=error_tail*-1
    return error_median, error_avg, error_tail

def get_final_res(packet_results_res):
    res_map = {}
    for packets in packets_range:
        res_map[packets] = {}
        for ap in all_approx:
            res_map[packets][ap] = 0
    for i in range(5):
        for packets in packets_range:
            for ap in all_approx:
                if ap not in packet_results_res[i][packets]:
                    continue
                res = packet_results_res[i][packets][ap]
                res_map[packets][ap] += (round(sum(res)/float(len(res)),2)) # Average of independently repeating experiments
                #res_map[packets][ap] += np.median(res) # Median of independently repeating experments
    for packets in packets_range:
        for ap in all_approx:
            res_map[packets][ap] = round(res_map[packets][ap]/5.0, 2) # Average relative error
    return res_map

# Constant variables
dint_threshold = 1
#dint_threshold = 5
#dint_threshold = 10
sketch_size=100
#packets_range=list(range(100,1100,100)) # Use 5-hop Fat Tree Topology with one flow
packets_range=[100, 500, 1000, 5000, 10000]
all_approx=set() # Approximate coefficient
approx_map={} # Approximate coefficiet -> bit number
for packets in packets_range:
    for bits in [4,8]:
        if bits==4:
            ap=0.42
        if bits==8:
            ap=0.022
        all_approx.add(ap)
        approx_map[ap]=bits

# dev:packetnum:ap:approximate_values
approx={} 
for i in range(5):
    approx[i] = {}
    for packets in packets_range:
        approx[i][packets]={}
        for ap in all_approx:
            approx[i][packets][ap] = []
# dev:pktnum:ap:relative_errors
packet_results_avg={} 
packet_results_median={}
packet_results_tail={}
for i in range(5):
    packet_results_avg[i] = {}
    packet_results_median[i] = {}
    packet_results_tail[i] = {}
# dev:latencies
all_data = {} 
for i in range(5):
    all_data[i] = []
f=open("experiments/delays/processed_data","r")
for line in f:
    digests=line.strip().split(" ")
    assert(len(digests)>0 and len(digests)<=5)
    iscontinue = False
    for digest in digests:
        if int(digest) < 0:
            iscontinue = True
            break
    if iscontinue:
        continue

    for i in range(len(digests)):
        all_data[i].append(int(digests[i]))
f.close()

all_median, all_avg, all_tail = [], [], []
for i in range(5):
    all_data[i] = sorted(all_data[i])
    all_median.append(np.median(all_data[i]))
    all_avg.append(sum(all_data[i])/float(len(all_data[i])))
    all_tail.append(np.percentile(all_data[i],99))

for packets in packets_range:
    for i in range(5):
        if packets not in packet_results_avg[i]:
            packet_results_avg[i][packets]={}
        if packets not in packet_results_median[i]:
            packet_results_median[i][packets]={}
        if packets not in packet_results_tail[i]:
            packet_results_tail[i][packets]={}

    truth, pint, dint_prev1, dint_prev2 = {}, {}, {}, {}
    for i in range(5):
        truth[i] = []
        #pint[i] = []
        dint_prev1[i], dint_prev2[i] = 0, 0

    f=open("experiments/delays/processed_data","r")
    for line in f:
        digests=line.strip().split(" ")
        assert(len(digests)>0 and len(digests)<=5)
        iscontinue = False
        for digest in digests:
            if int(digest) < 0:
                iscontinue = True
                break
        if iscontinue:
            continue

        for i in range(len(digests)):
            digest = int(digests[i])
            truth[i].append(digest)
            if (random.randint(1, 2) == 1) or (i==len(digests)-1): # Sampling by global hashing for PINT
                # PINT
                #pint[i].append(digest)
                for ap in all_approx: # Value approximation
                    if digest==0:
                        approx[i][packets][ap].append(0)
                        continue

                    range_1=int(math.log(digest, (1+ap)**2))
                    range_2=int(math.log(digest, (1+ap)**2)+0.5)

                    approx_value_1=(1+ap)**(2*range_1)
                    approx_value_2=(1+ap)**(2*range_2)

                    diff_1=digest-approx_value_1
                    if diff_1<0:
                        diff_1=-1*diff_1

                    diff_2=digest-approx_value_2
                    if diff_2<0:
                        diff_2=-1*diff_2

                    if diff_1<=diff_2:
                        approx[i][packets][ap].append(int(approx_value_1))
                    if diff_1>diff_2:
                        approx[i][packets][ap].append(int(approx_value_2))

            #if len(pint[i])==packets: # E.g., Collect every 100 packets for dev i
        if len(truth[0])==packets: # E.g., Collect every 100 INT events
            for i in range(len(digests)):
                true_median=np.median(truth[i])
                true_avg=sum(truth[i])/float(len(truth[i]))
                true_tail=np.percentile(truth[i],99)

                for ap in all_approx:
                    value=sorted(approx[i][packets][ap])
                    if len(value)<=1:
                        continue
                    ##error_median, error_avg, error_tail = get_approx_res(value, i)
                    error_median, error_avg, error_tail = get_approx_res(value, true_median, true_avg, true_tail)
                    #error_median, error_avg, error_tail = get_approx_res(value, all_median[i], all_avg[i], all_tail[i])

                    if ap not in packet_results_avg[i][packets]:
                        packet_results_avg[i][packets][ap]=[]
                    packet_results_avg[i][packets][ap].append(error_avg)

                    if ap not in packet_results_median[i][packets]:
                        packet_results_median[i][packets][ap]=[]
                    packet_results_median[i][packets][ap].append(error_median)

                    if ap not in packet_results_tail[i][packets]:
                        packet_results_tail[i][packets][ap]=[]
                    packet_results_tail[i][packets][ap].append(error_tail)

                approx[i][packets]={}
                for ap in all_approx:
                    approx[i][packets][ap]=[]
                #pint[i]=[]
                truth[i] = []
    f.close()

avg_map = get_final_res(packet_results_avg)
os.system("mkdir -p final_results/delays_PINT/")
fw=open("final_results/delays_PINT/avg_delay","w")
fw.write("# of packets,PINT4,value,PINT8,value\n")
for k,v in avg_map.items():
    packets = k
    write_string=str(packets)
    for ap,res in v.items():
        write_string=write_string+","+"PINT"+str(approx_map[ap])+","+str(res)
    fw.write(write_string+"\n")
fw.close()


median_map = get_final_res(packet_results_median)
fw=open("final_results/delays_PINT/median_delay","w")
fw.write("# of packets,PINT4,value,PINT8,value\n")
for k,v in median_map.items():
    packets=k
    write_string=str(packets)
    for ap,res in v.items():
        write_string=write_string+","+"PINT"+str(approx_map[ap])+","+str(res)
    fw.write(write_string+"\n")
fw.close()


tail_map = get_final_res(packet_results_tail)
#packet_results_tail=sorted(packet_results_tail.items(),key=operator.itemgetter(0))
fw=open("final_results/delays_PINT/tail_delay","w")
fw.write("# of packets,PINT4,value,PINT8,value\n")
for k,v in tail_map.items():
    packets=k
    write_string=str(packets)
    for ap,res in v.items():
        write_string=write_string+","+"PINT"+str(approx_map[ap])+","+str(res)
    fw.write(write_string+"\n")
fw.close()
