# DeltaINT on Mininet

- Simulation for path tracing and latency measurement
- Please see the original README file [PINT_README.md](./PINT_README.md) for more details like requirements

## Path tracing

- Run `python3 topo_allocator.py 5` to generate topology
- Run `sudo python3 -m p4utils.p4run --config p4app.json` to setup Mininet with bmv2
- Run `sudo python3 exp.py 5` to configure match action tables, and launch senders and receivers
- Run `sudo python3 generate_results.py 5` to evaluate convergence
- Run `sudo python3 generate_results_avgbit.py 5` to evaluate average bit cost

## Latency measurement

- Read trace file
	+ Run `cd ../HPCC-DINT/analysis`
	+ Run `./trace_reader wb.tr >wb_trace.out 2>&1` for web search workload
		* Hadoop workload is similar
- Run `sudo python3 generate_delay_data.py ../HPCC-DINT/analysis/wb_trace.out`
- Run `sudo python3 generate_delay_results_PINT.py`
- Run `sudo python3 generate_delay_results_DINT.py`
