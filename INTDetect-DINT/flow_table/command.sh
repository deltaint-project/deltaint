curdir=$(cd $(dirname $0); pwd)
sudo $curdir/simple_switch_CLI --thrift-port 9090 <$curdir/flow_table/s1_s1.txt
sudo $curdir/simple_switch_CLI --thrift-port 9091 <$curdir/flow_table/s1_s2.txt
sudo $curdir/simple_switch_CLI --thrift-port 9092 <$curdir/flow_table/s2_s1.txt
sudo $curdir/simple_switch_CLI --thrift-port 9093 <$curdir/flow_table/s2_s2.txt
sudo $curdir/simple_switch_CLI --thrift-port 9094 <$curdir/flow_table/p1_l1.txt
sudo $curdir/simple_switch_CLI --thrift-port 9095 <$curdir/flow_table/p1_l2.txt
sudo $curdir/simple_switch_CLI --thrift-port 9096 <$curdir/flow_table/p2_l1.txt
sudo $curdir/simple_switch_CLI --thrift-port 9097 <$curdir/flow_table/p2_l2.txt
sudo $curdir/simple_switch_CLI --thrift-port 9098 <$curdir/flow_table/p1_t1.txt
sudo $curdir/simple_switch_CLI --thrift-port 9099 <$curdir/flow_table/p1_t2.txt
sudo $curdir/simple_switch_CLI --thrift-port 9100 <$curdir/flow_table/p2_t1.txt
sudo $curdir/simple_switch_CLI --thrift-port 9101 <$curdir/flow_table/p2_t2.txt
