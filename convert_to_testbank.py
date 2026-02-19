"""
Convert extracted CCNA docx text files to test bank format.
New format uses 'Question NNN', 'Answer: X' lines, and separator bars.
Output uses asterisk (*) marking for correct answers (Format B).
"""
import os
import re
import glob

EXTRACTED_DIR = "extracted_text"
OUTPUT_DIR = os.path.join("ccna-tutor", "data", "test_bank")

# Map filenames to clean topic names and protocol slugs
TOPIC_MAP = {
    "CCNA_ACLs": ("ACLs - Access Control Lists", "acl"),
    "CCNA_ARP": ("ARP - Address Resolution Protocol", "arp"),
    "CCNA_BGP": ("BGP - Border Gateway Protocol", "bgp"),
    "CCNA_CDP_and_LLDP": ("CDP and LLDP - Discovery Protocols", "cdp-lldp"),
    "CCNA_Cloud_and_Virtualization": ("Cloud and Virtualization", "cloud"),
    "CCNA_DHCP": ("DHCP - Dynamic Host Configuration Protocol", "dhcp"),
    "CCNA_DNS": ("DNS - Domain Name System", "dns"),
    "CCNA_EIGRP": ("EIGRP - Enhanced Interior Gateway Routing Protocol", "eigrp"),
    "CCNA_EtherChannel": ("EtherChannel - Link Aggregation", "etherchannel"),
    "CCNA_FHRP": ("FHRP - First Hop Redundancy Protocols", "fhrp"),
    "CCNA_IPv6": ("IPv6 - Internet Protocol Version 6", "ipv6"),
    "CCNA_NAT_and_PAT": ("NAT and PAT - Network Address Translation", "nat"),
    "CCNA_Network_Architecture": ("Network Architecture", "network-architecture"),
    "CCNA_Network_Security": ("Network Security - AAA, Port Security, 802.1X", "network-security"),
    "CCNA_NTP": ("NTP - Network Time Protocol", "ntp"),
    "CCNA_OSPF": ("OSPF - Open Shortest Path First", "ospf"),
    "CCNA_Physical_Layer_and_Cabling": ("Physical Layer and Cabling", "physical-layer"),
    "CCNA_PoE": ("PoE - Power over Ethernet", "poe"),
    "CCNA_QoS": ("QoS - Quality of Service", "qos"),
    "CCNA_RIP": ("RIP - Routing Information Protocol", "rip"),
    "CCNA_SDN_and_Automation": ("SDN and Network Automation", "sdn"),
    "CCNA_SNMP_Syslog_NetFlow": ("SNMP, Syslog, and NetFlow", "snmp-syslog"),
    "CCNA_SSH_and_Remote_Access": ("SSH and Remote Access", "ssh"),
    "CCNA_Static_and_Default_Routing": ("Static and Default Routing", "static-routing"),
    "CCNA_STP": ("STP - Spanning Tree Protocol", "stp"),
    "CCNA_Subnetting_and_IP_Addressing": ("Subnetting and IP Addressing", "subnetting"),
    "CCNA_Switching_Fundamentals": ("Switching Fundamentals", "switching"),
    "CCNA_TCP_UDP_and_Transport": ("TCP/UDP and Transport Layer", "tcp-ip"),
    "CCNA_Uncategorized": ("Uncategorized - Mixed Topics", "uncategorized"),
    "CCNA_VLANs_and_Trunking": ("VLANs and Trunking", "vlan"),
    "CCNA_VPN_and_Tunneling": ("VPN and Tunneling", "vpn"),
    "CCNA_WAN_Technologies": ("WAN Technologies", "wan"),
    "CCNA_Wireless_and_WLAN": ("Wireless and WLAN", "wireless"),
}

SEPARATOR = "──────────────────────────────────────────────────"


def parse_question_block(block):
    """Parse a single question block into a structured dict."""
    lines = block.strip().split('\n')
    if not lines:
        return None

    # Find the question header line
    header_match = re.match(
        r'^Question\s+(\d+)\s+\(Topic\s+(\d+)\)\s+.*?(Multiple Choice|Drag & Drop)\s+\[([^\]]+)\]',
        lines[0].strip()
    )
    if not header_match:
        return None

    q_num = header_match.group(1)
    topic = header_match.group(2)
    q_type = header_match.group(3)
    source = header_match.group(4)

    # Skip Drag & Drop questions
    if q_type == "Drag & Drop":
        return None

    # Find answer line
    answer_line_idx = None
    answer_value = None
    for idx, line in enumerate(lines):
        m = re.match(r'^Answer:\s*([A-Fa-f,]+)\s*$', line.strip())
        if m:
            answer_line_idx = idx
            answer_value = m.group(1).upper()
            break

    if answer_value is None:
        return None

    # Extract question text and choices from lines between header and answer
    content_lines = lines[1:answer_line_idx]

    # Separate question text from choices
    question_parts = []
    choices = {}
    current_choice = None
    current_choice_text = []

    # Pattern for choice lines: A.  text or A. text (with 1+ spaces)
    choice_pattern = re.compile(r'^([A-Fa-f])[\.\)]\s{1,4}(.+)$')

    for line in content_lines:
        stripped = line.strip()
        if not stripped:
            continue

        choice_match = choice_pattern.match(stripped)

        if choice_match:
            # Save previous choice if any
            if current_choice:
                choices[current_choice] = ' '.join(current_choice_text).strip()

            current_choice = choice_match.group(1).upper()
            current_choice_text = [choice_match.group(2).strip()]
        elif current_choice:
            # Continuation of current choice text
            current_choice_text.append(stripped)
        else:
            # Part of question text
            question_parts.append(stripped)

    # Save last choice
    if current_choice:
        choices[current_choice] = ' '.join(current_choice_text).strip()

    question_text = ' '.join(question_parts).strip()

    # Clean up exhibit markers
    question_text = re.sub(r'\[See Exhibit Image\]\s*', '', question_text)
    question_text = re.sub(r'Refer to the exhibit\.\s*', '[Exhibit] ', question_text)
    question_text = question_text.strip()

    if not question_text or len(choices) < 2:
        return None

    # Parse answer - handles "B", "BD", "B,D", "A,C" formats
    correct_answers = [c for c in answer_value if c.isalpha()]

    return {
        'q_num': q_num,
        'topic': topic,
        'source': source,
        'question_text': question_text,
        'choices': choices,
        'correct_answers': correct_answers,
        'multi_answer': len(correct_answers) > 1
    }


def convert_file(input_path, output_path, topic_name):
    """Convert a single extracted text file to test bank format."""
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove BOM
    content = content.lstrip('\ufeff')

    # Split by separator
    blocks = content.split(SEPARATOR)

    questions = []
    skipped_dragdrop = 0
    skipped_other = 0

    for block in blocks:
        block = block.strip()
        if not block or not block.startswith('Question'):
            # Check if block contains a question further in
            # Some blocks have header lines before the first question
            q_start = block.find('Question ')
            if q_start == -1:
                continue
            block = block[q_start:]

        result = parse_question_block(block)
        if result:
            questions.append(result)
        elif 'Drag & Drop' in block or 'Drag &' in block:
            skipped_dragdrop += 1
        else:
            skipped_other += 1

    if not questions:
        print(f"  WARNING: No questions parsed from {input_path}")
        return 0, skipped_dragdrop

    # Write output in Format B (asterisk marking)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"CCNA 200-301 - {topic_name}\n")
        f.write("=" * 50 + "\n\n")

        for i, q in enumerate(questions, 1):
            f.write(f"{i}. {q['question_text']}\n")

            # Write choices, marking correct ones with *
            for letter in sorted(q['choices'].keys()):
                prefix = '*' if letter in q['correct_answers'] else ''
                f.write(f"{prefix}{letter}. {q['choices'][letter]}\n")

            f.write("\n")

    return len(questions), skipped_dragdrop


def main():
    total_questions = 0
    total_dragdrop = 0
    file_counts = {}

    # Get all extracted text files
    input_files = sorted(glob.glob(os.path.join(EXTRACTED_DIR, "CCNA_*.txt")))
    print(f"Processing {len(input_files)} topic files...\n")

    for input_path in input_files:
        basename = os.path.splitext(os.path.basename(input_path))[0]

        if basename not in TOPIC_MAP:
            print(f"  SKIP: {basename} - not in topic map")
            continue

        topic_name, slug = TOPIC_MAP[basename]
        output_filename = f"CCNA_{slug}.txt"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        count, dd_count = convert_file(input_path, output_path, topic_name)
        total_questions += count
        total_dragdrop += dd_count
        file_counts[slug] = count

        print(f"  {basename}: {count} MC questions, {dd_count} drag-drop skipped -> {output_filename}")

    print(f"\n{'='*50}")
    print(f"Total multiple-choice questions: {total_questions}")
    print(f"Total drag-drop skipped: {total_dragdrop}")
    print(f"Files created: {len(file_counts)}")
    print(f"\nQuestions per topic:")
    for slug, count in sorted(file_counts.items(), key=lambda x: -x[1]):
        print(f"  {slug}: {count}")


if __name__ == '__main__':
    main()
