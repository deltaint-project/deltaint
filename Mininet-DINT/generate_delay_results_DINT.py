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
                res_map[packets][ap] += (round(sum(res)/float(len(res)),2))
    for packets in packets_range:
        for ap in all_approx:
            res_map[packets][ap] = round(res_map[packets][ap]/5.0, 2)
    return res_map

# Constant variables
dint_threshold = 1
#dint_threshold = 5
#dint_threshold = 10
sketch_size=100
#packets_range=list(range(100,1100,100))
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

#dint_pktnum = {} # dev:pktnum
#pint_pktnum = {} # dev:pktnum
#dint_savenum = {} # dev:ap:savenum
#for i in range(5):
#    dint_pktnum[i] = 0
#    pint_pktnum[i] = 0
#    dint_savenum[i] = {}
#    for ap in all_approx:
#        dint_savenum[i][ap] = 0

total_pktnum = 0
total_dintbits = {}
total_pintbits = {}
for ap in all_approx:
    total_dintbits[ap] = 0
    total_pintbits[ap] = 0

# Average relative errors of all states for measurement accuracy evaluation
avg_res = {}
for ap in all_approx:
    avg_res[ap] = []

for packets in packets_range:
    for i in range(5):
        if packets not in packet_results_avg[i]:
            packet_results_avg[i][packets]={}
        if packets not in packet_results_median[i]:
            packet_results_median[i][packets]={}
        if packets not in packet_results_tail[i]:
            packet_results_tail[i][packets]={}

    truth = {}
    dint_prev = {}
    #dint_prev1, dint_prev2 = {}, {}
    for i in range(5):
        truth[i] = []
        #dint_prev1[i], dint_prev2[i] = 0, 0
        dint_prev[i] = 0

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

        tmp_dintbits = {}
        tmp_dintbits_sum = {}
        tmp_pintbits = {}
        tmp_pintbits_sum = {}
        for ap in all_approx:
            tmp_dintbits[ap] = 0
            tmp_dintbits_sum[ap] = 0
            tmp_pintbits[ap] = 0
            tmp_pintbits_sum[ap] = 0
        total_pktnum += 1
        is_sample = False
        for i in range(len(digests)):
            #dint_pktnum[i] += 1
            digest = int(digests[i])
            if not is_sample:
                if (random.randint(1, 2) == 1) or (i==len(digests)-1): # Sampling by global hashing for PINT
                    is_sample = True
            if is_sample:
                #pint_pktnum[i] += 1
                for ap in all_approx:
                    tmp_pintbits[ap] += approx_map[ap]
                    tmp_pintbits_sum[ap] += tmp_pintbits[ap]

            # DINT
            truth[i].append(digest)
            for ap in all_approx: # Value approximation
                if digest==0: # Use threshold 0 for this specific situation for high ARE
                    #if abs(dint_prev1[i] - digest) > dint_threshold:
                    if dint_prev[i] != 0:
                        approx[i][packets][ap].append(digest)
                        dint_prev[i] = 0
                        tmp_dintbits[ap] += (1+approx_map[ap])
                    else:
                        approx[i][packets][ap].append(dint_prev[i])
                        tmp_dintbits[ap] += 1
                        #dint_savenum[i][ap] += 1
                    avg_res[ap].append(0.0)
                    tmp_dintbits_sum[ap] += tmp_dintbits[ap]
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
                    if abs(int(approx_value_1) - dint_prev[i]) > dint_threshold:
                        approx[i][packets][ap].append(int(approx_value_1))
                        dint_prev[i] = int(approx_value_1)
                        avg_res[ap].append(0.0)
                        tmp_dintbits[ap] += (1+approx_map[ap])
                    else:
                        approx[i][packets][ap].append(dint_prev[i])
                        tmp_dintbits[ap] += 1
                        #dint_savenum[i][ap] += 1
                        avg_res[ap].append(abs(int(approx_value_1) - dint_prev[i]) / float(int(approx_value_1)))
                if diff_1>diff_2:
                    if abs(int(approx_value_2) - dint_prev[i]) > dint_threshold:
                        approx[i][packets][ap].append(int(approx_value_2))
                        dint_prev[i] = int(approx_value_2)
                        avg_res[ap].append(0.0)
                        tmp_dintbits[ap] += (1+approx_map[ap])
                    else:
                        approx[i][packets][ap].append(dint_prev[i])
                        tmp_dintbits[ap] += 1
                        #dint_savenum[i][ap] += 1
                        avg_res[ap].append(abs(int(approx_value_2) - dint_prev[i]) / float(int(approx_value_2)))
                tmp_dintbits_sum[ap] += tmp_dintbits[ap]

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
                truth[i]=[]
        for ap in all_approx:
            total_pintbits[ap] += (tmp_pintbits_sum[ap]/float(len(digests)))
            total_dintbits[ap] += (tmp_dintbits_sum[ap]/float(len(digests)))
            #if approx_map[ap]==8:
            #    print(len(digests), tmp_pintbits_sum[ap], tmp_pintbits_sum[ap]/float(len(digests)), total_pintbits[ap])
    f.close()

for ap in all_approx:
    print("Bit-{}".format(approx_map[ap]))
    avgbit_pint = total_pintbits[ap]/float(total_pktnum)
    avgbit_dint = total_dintbits[ap]/float(total_pktnum)
    print("Avgbit PINT: {}, DINT: {}".format(avgbit_pint, avgbit_dint))

#pint_total_pktnum, dint_total_pktnum = 0, 0
#for i in range(5):
#    print(pint_pktnum[i], dint_pktnum[i])
#    pint_total_pktnum += pint_pktnum[i]
#    dint_total_pktnum += dint_pktnum[i]
#print("PINT total pktnum: {}, DINT total pktnum: {}".format(pint_total_pktnum, dint_total_pktnum))

#dint_total_savenum = {}
#for ap in all_approx:
#    dint_total_savenum[ap] = 0
#for i in range(5):
#    for ap in all_approx:
#        dint_total_savenum[ap] += dint_savenum[i][ap]
#print("DINT-{}: savenum {}".format(approx_map[ap], dint_total_savenum[ap]))

#pint_total_bits, dint_total_bits = {}, {}
#pint_prev_bits, dint_prev_bits = {}, {}
#for ap in all_approx:
#    pint_total_bits[ap], dint_total_bits[ap] = 0, 0
#    pint_prev_bits[ap], dint_prev_bits[ap] = 0, 0
#for i in range(5):
#    for ap in all_approx:
#        pint_prev_bits[ap] += pint_pktnum[i]*approx_map[ap]
#        pint_total_bits[ap] += pint_prev_bits[ap]
#
#        dint_prev_bits[ap] += (dint_pktnum[i] - dint_savenum[i][ap])*(approx_map[ap]+1)
#        dint_prev_bits[ap] += (dint_savenum[i][ap])*1
#        dint_total_bits[ap] += dint_prev_bits[ap]
#for ap in all_approx:
#    pint_avgbit = pint_total_bits[ap] / float(pint_total_pktnum)
#    dint_avgbit = dint_total_bits[ap] / float(dint_total_pktnum)
#    print("PINT-{}: avgbit {}; DINT-{}: avgbit {}".format(approx_map[ap], pint_avgbit, approx_map[ap], dint_avgbit))

avg_map = get_final_res(packet_results_avg)
os.system("mkdir -p final_results/delays_DINT/")
fw=open("final_results/delays_DINT/avg_delay","w")
fw.write("# of packets,DINT4,value,DINT8,value\n")
for k,v in avg_map.items():
    packets = k
    write_string=str(packets)
    for ap,res in v.items():
        write_string=write_string+","+"DINT"+str(approx_map[ap])+","+str(res)
    fw.write(write_string+"\n")
fw.close()


median_map = get_final_res(packet_results_median)
fw=open("final_results/delays_DINT/median_delay","w")
fw.write("# of packets,DINT4,value,DINT8,value\n")
for k,v in median_map.items():
    packets=k
    write_string=str(packets)
    for ap,res in v.items():
        write_string=write_string+","+"DINT"+str(approx_map[ap])+","+str(res)
    fw.write(write_string+"\n")
fw.close()


tail_map = get_final_res(packet_results_tail)
#packet_results_tail=sorted(packet_results_tail.items(),key=operator.itemgetter(0))
fw=open("final_results/delays_DINT/tail_delay","w")
fw.write("# of packets,DINT4,value,DINT8,value\n")
for k,v in tail_map.items():
    packets=k
    write_string=str(packets)
    for ap,res in v.items():
        write_string=write_string+","+"DINT"+str(approx_map[ap])+","+str(res)
    fw.write(write_string+"\n")
fw.close()


print("Average relative error of states for measurement accuracy:\n")
for ap in all_approx:
    avg_re = sum(avg_res[ap]) / float(len(avg_res[ap]))
    print("Bit-{} ARE: {}".format(approx_map[ap], avg_re))
