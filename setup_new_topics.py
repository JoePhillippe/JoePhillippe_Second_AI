"""
Setup script to create protocol definitions and basic concept groups
for all 33 CCNA topics from the new test bank files.
"""
import json
import os
import sys

sys.path.insert(0, 'ccna-tutor')
from utils.question_parser import QuestionParser

PROTOCOLS_DIR = os.path.join("ccna-tutor", "data", "protocols")
CONCEPT_GROUPS_DIR = os.path.join("ccna-tutor", "data", "concept_groups")
TEST_BANK_DIR = os.path.join("ccna-tutor", "data", "test_bank")

# All 33 topics with their metadata
# slug must match the CCNA_{slug}.txt filename in test_bank
TOPICS = {
    "acl": {
        "name": "ACLs",
        "category": "Security",
        "description": "Access Control Lists (ACLs) filter network traffic by permitting or denying packets based on criteria like source/destination IP, protocol, and port numbers.",
        "exam_weight": "High"
    },
    "arp": {
        "name": "ARP",
        "category": "Layer 2 Technologies",
        "description": "Address Resolution Protocol (ARP) maps IP addresses to MAC addresses on local network segments.",
        "exam_weight": "Medium"
    },
    "bgp": {
        "name": "BGP",
        "category": "Routing Protocols",
        "description": "Border Gateway Protocol (BGP) is the path-vector routing protocol used between autonomous systems on the internet.",
        "exam_weight": "Medium"
    },
    "cdp-lldp": {
        "name": "CDP and LLDP",
        "category": "Network Services",
        "description": "Cisco Discovery Protocol (CDP) and Link Layer Discovery Protocol (LLDP) discover and share information about directly connected network devices.",
        "exam_weight": "Medium"
    },
    "cloud": {
        "name": "Cloud and Virtualization",
        "category": "Architecture",
        "description": "Cloud computing models (IaaS, PaaS, SaaS), virtualization technologies, hypervisors, and virtual machines in network environments.",
        "exam_weight": "Medium"
    },
    "dhcp": {
        "name": "DHCP",
        "category": "Network Services",
        "description": "Dynamic Host Configuration Protocol (DHCP) automatically assigns IP addresses and network configuration to devices.",
        "exam_weight": "High"
    },
    "dns": {
        "name": "DNS",
        "category": "Network Services",
        "description": "Domain Name System (DNS) translates domain names to IP addresses, enabling name-based network communication.",
        "exam_weight": "Medium"
    },
    "eigrp": {
        "name": "EIGRP",
        "category": "Routing Protocols",
        "description": "Enhanced Interior Gateway Routing Protocol (EIGRP) is a Cisco advanced distance-vector routing protocol using DUAL algorithm.",
        "exam_weight": "High"
    },
    "etherchannel": {
        "name": "EtherChannel",
        "category": "Layer 2 Technologies",
        "description": "EtherChannel bundles multiple physical links into one logical link for increased bandwidth and redundancy using LACP or PAgP.",
        "exam_weight": "High"
    },
    "fhrp": {
        "name": "FHRP",
        "category": "Infrastructure Services",
        "description": "First Hop Redundancy Protocols (HSRP, VRRP, GLBP) provide default gateway redundancy for hosts.",
        "exam_weight": "Medium"
    },
    "ipv6": {
        "name": "IPv6",
        "category": "IP Services",
        "description": "Internet Protocol version 6 with 128-bit addressing, including address types, autoconfiguration, and transition mechanisms.",
        "exam_weight": "High"
    },
    "nat": {
        "name": "NAT and PAT",
        "category": "IP Services",
        "description": "Network Address Translation (NAT) and Port Address Translation (PAT) translate private IP addresses to public for internet access.",
        "exam_weight": "High"
    },
    "network-architecture": {
        "name": "Network Architecture",
        "category": "Architecture",
        "description": "Network design architectures including spine-leaf, three-tier, collapsed core, and campus network designs.",
        "exam_weight": "Medium"
    },
    "network-security": {
        "name": "Network Security",
        "category": "Security",
        "description": "AAA, port security, 802.1X, DHCP snooping, DAI, threat types, firewalls, and IPS/IDS security concepts.",
        "exam_weight": "High"
    },
    "ntp": {
        "name": "NTP",
        "category": "Network Services",
        "description": "Network Time Protocol (NTP) synchronizes clocks across network devices for consistent logging and authentication.",
        "exam_weight": "Low"
    },
    "ospf": {
        "name": "OSPF",
        "category": "Routing Protocols",
        "description": "Open Shortest Path First (OSPF) is a link-state routing protocol using Dijkstra's SPF algorithm for shortest path calculation.",
        "exam_weight": "High"
    },
    "physical-layer": {
        "name": "Physical Layer and Cabling",
        "category": "Infrastructure",
        "description": "Physical layer concepts including copper and fiber cabling types, connectors, standards, and specifications.",
        "exam_weight": "Medium"
    },
    "poe": {
        "name": "PoE",
        "category": "Infrastructure",
        "description": "Power over Ethernet (PoE) delivers electrical power over network cables to devices like APs, IP phones, and cameras.",
        "exam_weight": "Low"
    },
    "qos": {
        "name": "QoS",
        "category": "IP Services",
        "description": "Quality of Service (QoS) mechanisms for traffic classification, marking, queuing, and policing to prioritize network traffic.",
        "exam_weight": "Medium"
    },
    "rip": {
        "name": "RIP",
        "category": "Routing Protocols",
        "description": "Routing Information Protocol (RIP) is a distance-vector routing protocol using hop count as its metric.",
        "exam_weight": "Low"
    },
    "sdn": {
        "name": "SDN and Automation",
        "category": "Automation",
        "description": "Software-Defined Networking, REST APIs, configuration management (Ansible, Puppet, Chef), JSON/YAML, and Cisco DNA Center.",
        "exam_weight": "High"
    },
    "snmp-syslog": {
        "name": "SNMP, Syslog, NetFlow",
        "category": "Network Services",
        "description": "Network monitoring and management using SNMP, Syslog logging levels, and NetFlow traffic analysis.",
        "exam_weight": "Medium"
    },
    "ssh": {
        "name": "SSH and Remote Access",
        "category": "Security",
        "description": "Secure Shell (SSH), Telnet, console access, VTY lines, and device management access methods.",
        "exam_weight": "High"
    },
    "static-routing": {
        "name": "Static and Default Routing",
        "category": "Routing Protocols",
        "description": "Static routes, default routes, floating static routes, and route selection based on administrative distance.",
        "exam_weight": "High"
    },
    "stp": {
        "name": "STP",
        "category": "Layer 2 Technologies",
        "description": "Spanning Tree Protocol (STP/RSTP/PVST+) prevents Layer 2 loops by blocking redundant paths in switched networks.",
        "exam_weight": "High"
    },
    "subnetting": {
        "name": "Subnetting and IP Addressing",
        "category": "IP Services",
        "description": "IPv4 subnetting, CIDR notation, VLSM, address classes, private vs public addresses, and subnet calculations.",
        "exam_weight": "High"
    },
    "switching": {
        "name": "Switching Fundamentals",
        "category": "Layer 2 Technologies",
        "description": "Layer 2 switching concepts including MAC address table, frame forwarding, switch port types, and duplex settings.",
        "exam_weight": "High"
    },
    "tcp-ip": {
        "name": "TCP/UDP and Transport",
        "category": "IP Services",
        "description": "Transport layer protocols TCP and UDP, port numbers, three-way handshake, and connection-oriented vs connectionless communication.",
        "exam_weight": "High"
    },
    "uncategorized": {
        "name": "Mixed Topics",
        "category": "General",
        "description": "General CCNA questions covering multiple topics and cross-domain concepts.",
        "exam_weight": "Medium"
    },
    "vlan": {
        "name": "VLANs and Trunking",
        "category": "Layer 2 Technologies",
        "description": "Virtual LANs, 802.1Q trunking, native VLANs, inter-VLAN routing, and DTP (Dynamic Trunking Protocol).",
        "exam_weight": "High"
    },
    "vpn": {
        "name": "VPN and Tunneling",
        "category": "Security",
        "description": "Virtual Private Networks, IPsec, GRE tunnels, site-to-site VPNs, and remote access VPN technologies.",
        "exam_weight": "Medium"
    },
    "wan": {
        "name": "WAN Technologies",
        "category": "Infrastructure",
        "description": "Wide Area Network technologies including MPLS, broadband, Metro Ethernet, PPP, and WAN architecture options.",
        "exam_weight": "Medium"
    },
    "wireless": {
        "name": "Wireless and WLAN",
        "category": "Wireless",
        "description": "Wireless LAN technologies, 802.11 standards, WLC architecture, SSID, channels, security (WPA2/WPA3), and AP modes.",
        "exam_weight": "High"
    },
}


def create_protocol_files():
    """Create protocol JSON files for topics that don't have one yet."""
    os.makedirs(PROTOCOLS_DIR, exist_ok=True)
    created = 0
    updated = 0

    for slug, meta in TOPICS.items():
        filepath = os.path.join(PROTOCOLS_DIR, f"{slug}.json")

        if os.path.exists(filepath):
            # Check if we need to update
            continue

        protocol_data = {
            "name": meta["name"],
            "slug": slug,
            "category": meta["category"],
            "description": meta["description"],
            "key_topics": [],
            "config_guide_refs": {},
            "exam_weight": meta["exam_weight"],
            "related_protocols": []
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(protocol_data, f, indent=2)
        created += 1

    print(f"Protocol files: {created} created, {len(TOPICS) - created} already existed")

    # Remove old protocol files that don't match new topics
    removed = []
    for f in os.listdir(PROTOCOLS_DIR):
        if f.endswith('.json'):
            slug = f[:-5]
            if slug not in TOPICS:
                # Rename old slugs to new ones
                old_to_new = {
                    "nat-pat": "nat",
                    "ipsec-vpn": "vpn",
                    "ethernet": None,  # covered by switching/physical-layer
                }
                if slug in old_to_new:
                    if old_to_new[slug]:
                        print(f"  Note: Old '{slug}.json' exists, new topic uses '{old_to_new[slug]}'")
                    else:
                        os.remove(os.path.join(PROTOCOLS_DIR, f))
                        removed.append(slug)
                        print(f"  Removed obsolete: {slug}.json")

    return created


def create_concept_groups():
    """Create basic concept groups for all topics based on parsed questions."""
    os.makedirs(CONCEPT_GROUPS_DIR, exist_ok=True)

    parser = QuestionParser(TEST_BANK_DIR)
    created = 0

    for slug in TOPICS:
        test_file = os.path.join(TEST_BANK_DIR, f"CCNA_{slug}.txt")
        if not os.path.exists(test_file):
            print(f"  WARNING: No test bank file for {slug}")
            continue

        questions = parser.parse_file(test_file)
        if not questions:
            print(f"  WARNING: No questions parsed for {slug}")
            continue

        # Create one concept group per question (simple 1:1 mapping)
        # This ensures every question is accessible in the quiz
        # IDs are prefixed with slug in load_all_questions: e.g., "ospf_qb001"
        groups = []
        for i, q in enumerate(questions):
            q_id = f"{slug}_{q['id']}"
            group = {
                "group_id": f"{slug}_q{i+1}",
                "concept": q["question_text"][:80] + ("..." if len(q["question_text"]) > 80 else ""),
                "question_ids": [q_id],
                "group_size": 1,
                "confidence": "INDIVIDUAL"
            }
            groups.append(group)

        concept_data = {
            "protocol": slug,
            "groups": groups,
            "total_groups": len(groups),
            "total_questions": len(questions)
        }

        output_path = os.path.join(CONCEPT_GROUPS_DIR, f"{slug}.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(concept_data, f, indent=2)

        created += 1
        print(f"  {slug}: {len(groups)} concept groups ({len(questions)} questions)")

    print(f"\nConcept groups created: {created}")
    return created


def main():
    print("=== Setting up new CCNA topics ===\n")

    print("1. Creating protocol definition files...")
    create_protocol_files()

    print("\n2. Creating concept groups...")
    create_concept_groups()

    print("\n=== Setup complete! ===")


if __name__ == '__main__':
    main()
