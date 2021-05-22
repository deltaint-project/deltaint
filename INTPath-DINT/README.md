# INT-Path based on DeltaINT

Simulation for gray failure detection.

## Step 1: Build INT-Path

Please see the original README of INT-Path [INTPATH_README.md](./INTPATH_README.md).

## Step 2: How to run

- Compile p4 code
	+ Run `cd p4app`
	+ Run `bash run.sh`
- Clean tmp directory if any
	+ Run `sudo rm -r packet/tmp`
	+ Run `sudo rm -r controller/tmp`
- Generate topology
	+ Run`cd conroller`
	+ Run `python3 topo_generate 3`
- Setup mininet
	+ Run `cd controller`
	+ Run `sudo python3 app.py`
- Evaluate average bit cost (must clean tmp directory before running and evaluating)
	+ Run `cd controller`
	+ Run `bash BW_evaluate.sh`
