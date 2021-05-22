# HPCC-DeltaINT

Simulation for congestion control.

## Step 1: Build HPCC-PINT

Please follow the original README of HPCC-PINT [PINT_README.d](./PINT_README.md).

## Step 2: Run experiments

- Run `bash build.sh`
- Run experiments on Hadoop Workload
	+ Run `bash run_hpcc_fb.sh` to get results of HPCC
	+ Run `bash run_hpcc_pint1_fb.sh` to get results of PINT
	+ Run `bash run_hpcc_dint1_fb.sh >tmp.out 2>&1` to get results of DeltaINT
- Run Experiments on Websearch Workload
	+ Run `bash run_hpcc_wb.sh` to get results of HPCC
	+ Run `bash run_hpcc_pint1_wb.sh` to get results of PINT
	+ Run `bash run_hpcc_dint1_wb.sh >tmp.ou 2>&1` to get results of DeltaINT
- Run `python3 plothelper.py tmp.out` to get the average bit cost
- Analyze flow completion time
	+ Run `cd analysis`
	+ Run `bash plotDINTVsPINT.sh` to generate figures

## NOTE

To generate trace file for latency measurement, you must launch run.py with `--enable_tr 1`
