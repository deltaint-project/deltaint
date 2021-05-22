#ifndef SWITCH_NODE_H
#define SWITCH_NODE_H

#include <unordered_map>
#include <ns3/node.h>
#include <vector>
#include "qbb-net-device.h"
#include "switch-mmu.h"
#include "pint.h"

namespace ns3 {

class Packet;

class Flowkey {
public:
	uint32_t srcip = 0;
	uint32_t dstip = 0;
	uint16_t srcport = 0;
	uint16_t dstport = 0;
	uint8_t protocol = 0;

	Flowkey();
	Flowkey(uint32_t srcip, uint32_t dstip, uint16_t srcport, uint16_t dstport, uint8_t protocol);

	void GetBytes(uint8_t* output);

	bool operator == (Flowkey& other) const;
};

class SwitchNode : public Node{
	static const uint32_t pCnt = 257;	// Number of ports used
	static const uint32_t qCnt = 8;	// Number of queues/priorities used

	static const uint32_t DINT_sketch_bytes = 256 * 1024; // 1 MB 
	static const uint32_t DINT_diff = 1; // Delta threshold
	//static const uint32_t DINT_diff = 5; // Delta threshold
	//static const uint32_t DINT_diff = 10; // Delta threshold
	static const uint32_t DINT_hashnum = 1;

	uint32_t curnode_cntnum = 0;
	static const uint32_t pernode_cntnum = 10000;

	uint32_t m_ecmpSeed;
	std::unordered_map<uint32_t, std::vector<int> > m_rtTable; // map from ip address (u32) to possible ECMP port (index of dev)

	// monitor of PFC
	uint32_t m_bytes[pCnt][pCnt][qCnt]; // m_bytes[inDev][outDev][qidx] is the bytes from inDev enqueued for outDev at qidx
	
	uint64_t m_txBytes[pCnt]; // counter of tx bytes

	uint32_t m_lastPktSize[pCnt];
	uint64_t m_lastPktTs[pCnt]; // ns
	double m_u[pCnt];

protected:
	bool m_ecnEnabled;
	uint32_t m_ccMode;
	uint64_t m_maxRtt;

	uint32_t m_ackHighPrio; // set high priority for ACK/NACK

	// Although we use uint16_t here, it is just for coding convenience. Actually, we only need uint8_t
	std::vector<uint16_t> prev_inputs; 
	std::vector<uint16_t> prev_outputs;
	std::vector<Flowkey> flowkeys;

private:
	int GetOutDev(Ptr<const Packet>, CustomHeader &ch);
	void SendToDev(Ptr<Packet>p, CustomHeader &ch);
	static uint32_t EcmpHash(const uint8_t* key, size_t len, uint32_t seed);
	void CheckAndSendPfc(uint32_t inDev, uint32_t qIndex);
	void CheckAndSendResume(uint32_t inDev, uint32_t qIndex);
public:
	Ptr<SwitchMmu> m_mmu;

	static TypeId GetTypeId (void);
	SwitchNode();
	void SetEcmpSeed(uint32_t seed);
	void AddTableEntry(Ipv4Address &dstAddr, uint32_t intf_idx);
	void ClearTable();
	bool SwitchReceiveFromDevice(Ptr<NetDevice> device, Ptr<Packet> packet, CustomHeader &ch);
	void SwitchNotifyDequeue(uint32_t ifIndex, uint32_t qIndex, Ptr<Packet> p);

	// for approximate calc in PINT
	int logres_shift(int b, int l);
	int log2apprx(int x, int b, int m, int l); // given x of at most b bits, use most significant m bits of x, calc the result in l bits
};

} /* namespace ns3 */

#endif /* SWITCH_NODE_H */
