import tkinter as tk
import os
import sys
import subprocess
import time
import json
import ssl
import base64
import urllib.request
import urllib.error
from io import BytesIO
try:
    from PIL import ImageGrab
    from winocr import recognize_pil_sync
    from pynput import mouse
except Exception as e:
    print(e)

def ensure_default_env(env_file=".env", defaults=None):
    """
    Erstellt eine .env Datei mit Defaults, falls sie nicht existiert.
    """
    if defaults is None:
        defaults = {
            "API_KEY": "test123",
            "FONT_SIZE": "7",
        }

    if not os.path.exists(env_file):
        with open(env_file, "w", encoding="utf-8") as f:
            f.write("# Auto-generated default .env\n")
            f.write("# Passe Werte an deine Umgebung an.\n\n")
            for k, v in defaults.items():
                # Wenn Leerzeichen oder # enthalten sind: quoten
                vv = v
                if (" " in vv) or ("#" in vv):
                    vv = '"' + vv.replace('"', '\\"') + '"'
                f.write(f"{k}={vv}\n")


def load_env(env_file=".env", overwrite=False):
    """
    Liest .env und setzt Variablen in os.environ.
    Unterstützt:
      - KEY=VALUE
      - export KEY=VALUE
      - Kommentare (# ...) und leere Zeilen
      - Werte in '...' oder "..."
    """
    data = {}

    if not os.path.exists(env_file):
        return data

    with open(env_file, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("export "):
                line = line[7:].strip()

            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Inline-Kommentare entfernen, aber nur wenn nicht gequotet
            if value and value[0] not in ("'", '"') and "#" in value:
                value = value.split("#", 1)[0].strip()

            # Quotes entfernen
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
                # einfache Escape-Unterstützung für \" in doppelten Quotes
                value = value.replace('\\"', '"')

            data[key] = value

            if overwrite or (key not in os.environ):
                os.environ[key] = value

    return data

def init_env(env_file=".env", defaults=None, overwrite=False):
    """
    Kombi: erstellt Default-.env falls nötig, lädt sie dann.
    Rückgabe: dict mit allen geladenen Werten.
    """
    ensure_default_env(env_file, defaults=defaults)
    return load_env(env_file, overwrite=overwrite)

cfg = init_env(".env")

QA = {
    "test est st t": "Windows Updates",
    "During a routine inspection, a technician discovered that software that was installed on a computer was secretly collecting data about websites that were visited by users of the computer. Which type of threat is affecting this computer?": "ftprlad | setnwdtsfeu | sptnfua",
    "Which term refers to a network that provides secure access to the corporate offices by suppliers, customers and collaborators?": "ftprlad | setnwdtsfeu | sptnfua",
    "A large corporation has modified its network to allow users to access network resources from their personal laptops and smart phones. Which networking trend does this describe?": "ftprlad | setnwdtsfeu | sptnfua",
    "What is an ISP?": "ftprlad | setnwdtsfeu | sptnfua",
    "Match the requirements of a reliable network with the supporting network architecture. (Not all options are used.)": "ftprlad | setnwdtsfeu | sptnfua",
    "An employee at a branch office is creating a quote for a customer. In order to do this, the employee needs to access confidential pricing information from internal servers at the Head Office. What type of network would the employee access?": "uses coaxial cable as a medium > cable | nsfhwas | thvlbdt | hbctrotld",
    "Which statement describes the use of powerline networking technology?": "uses coaxial cable as a medium > cable | nsfhwas | thvlbdt | hbctrotld",
    "A networking technician is working on the wireless network at a medical clinic. The technician accidentally sets up the wireless network so that patients can see the medical records data of other patients. Which of the four network characteristics has been violated in this situation?": "uses coaxial cable as a medium > cable | nsfhwas | thvlbdt | hbctrotld",
    "Match each characteristic to its corresponding Internet connectivity type. (Not all options are used.)": "uses coaxial cable as a medium > cable | nsfhwas | thvlbdt | hbctrotld",
    "What two criteria are used to help select a network medium from various network media? (Choose two.)": "first mode > user EXEC mode | second mode > privileged EXEC mode | third mode > global configuration mode | final mode > line configuration mode",
    "What type of network traffic requires QoS?": "first mode > user EXEC mode | second mode > privileged EXEC mode | third mode > global configuration mode | final mode > line configuration mode",
    "A user is implementing security on a small office network. Which two actions would provide the minimum security requirements for this network? (Choose two.)": "first mode > user EXEC mode | second mode > privileged EXEC mode | third mode > global configuration mode | final mode > line configuration mode",
    "Passwords can be used to restrict access to all or parts of the Cisco IOS. Select the modes and interfaces that can be protected with passwords. (Choose three.)": "first mode > user EXEC mode | second mode > privileged EXEC mode | third mode > global configuration mode | final mode > line configuration mode",
    "Which interface allows remote management of a Layer 2 switch?": "first mode > user EXEC mode | second mode > privileged EXEC mode | third mode > global configuration mode | final mode > line configuration mode",
    "What function does pressing the Tab key have when entering a command in IOS?": "first mode > user EXEC mode | second mode > privileged EXEC mode | third mode > global configuration mode | final mode > line configuration mode",
    "While trying to solve a network issue, a technician made multiple changes to the current router configuration file. The changes did not solve the problem and were not saved. What action can the technician take to discard the changes and work with the file in NVRAM?": "first mode > user EXEC mode | second mode > privileged EXEC mode | third mode > global configuration mode | final mode > line configuration mode",
    "An administrator uses the Ctrl-Shift-6 key combination on a switch after issuing the ping command. What is the purpose of using these keystrokes?": "first mode > user EXEC mode | second mode > privileged EXEC mode | third mode > global configuration mode | final mode > line configuration mode",
    "Refer to the exhibit. A network administrator is configuring access control to switch SW1. If the administrator uses a console connection to connect to the switch, which password is needed to access user EXEC mode?": "first mode > user EXEC mode | second mode > privileged EXEC mode | third mode > global configuration mode | final mode > line configuration mode",
    "A technician configures a switch with these commands:": "first mode > user EXEC mode | second mode > privileged EXEC mode | third mode > global configuration mode | final mode > line configuration mode",
    "What is the technician configuring?": "first mode > user EXEC mode | second mode > privileged EXEC mode | third mode > global configuration mode | final mode > line configuration mode",
    "Which command or key combination allows a user to return to the previous level in the command hierarchy?": "first mode > user EXEC mode | second mode > privileged EXEC mode | third mode > global configuration mode | final mode > line configuration mode",
    "What are two characteristics of RAM on a Cisco device? (Choose two.)": "first mode > user EXEC mode | second mode > privileged EXEC mode | third mode > global configuration mode | final mode > line configuration mode",
    "Which two host names follow the guidelines for naming conventions on Cisco IOS devices? (Choose two.)": "first mode > user EXEC mode | second mode > privileged EXEC mode | third mode > global configuration mode | final mode > line configuration mode",
    "How is SSH different from Telnet?": "first mode > user EXEC mode | second mode > privileged EXEC mode | third mode > global configuration mode | final mode > line configuration mode",
    "An administrator is configuring a switch console port with a password. In what order will the administrator travel through the IOS modes of operation in order to reach the mode in which the configuration commands will be entered? (Not all options are used.)": "first mode > user EXEC mode | second mode > privileged EXEC mode | third mode > global configuration mode | final mode > line configuration mode",
    "What are three characteristics of an SVI? (Choose three.)": "provides context-sensitive help > ? | displays the next screen > Space bar | cacapt | sbtpecua | acsatapcs",
    "What command is used to verify the condition of the switch interfaces, including the status of the interfaces and a configured IP address?": "provides context-sensitive help > ? | displays the next screen > Space bar | cacapt | sbtpecua | acsatapcs",
    "Match the description with the associated IOS mode. (Not all options are used.)": "provides context-sensitive help > ? | displays the next screen > Space bar | cacapt | sbtpecua | acsatapcs",
    "Match the definitions to their respective CLI hot keys and shortcuts. (Not all options are used.)": "provides context-sensitive help > ? | displays the next screen > Space bar | cacapt | sbtpecua | acsatapcs",
    "In the show running-config command, which part of the syntax is represented by running-config ?": "a keyword",
    "After making configuration changes on a Cisco switch, a network administrator issues a copy running-config startup-config command. What is the result of issuing this command?": "tncwblitsir",
    "What command will prevent all unencrypted passwords from displaying in plain text in a configuration file?": "(config)# service password-encryption",
    "A network administrator enters the service password-encryption command into the configuration mode of a router. What does this command accomplish?": "tcpsfvtrcp",
    "What method can be used by two computers to ensure that packets are not dropped because too much data is being sent too quickly?": "flow control",
    "Which statement accurately describes a TCP/IP encapsulation process when a PC is sending data to the network?": "sasfttlttil",
    "What three application layer protocols are part of the TCP/IP protocol suite? (Choose three.)": "DHCP | DNS | FTP",
    "Match the description to the organization. (Not all options are used.)": "segment",
    "Which name is assigned to the transport layer PDU?": "segment",
    "When IPv4 addressing is manually configured on a web server, which property of the IPv4 configuration identifies the network and host portion for an IPv4 address?": "subnet mask",
    "What process involves placing one PDU inside of another PDU?": "encapsulation",
    "What layer is responsible for routing messages through an internetwork in the TCP/IP model?": "internet",
    "For the TCP/IP protocol suite, what is the correct order of events when a Telnet message is being prepared to be sent over the network?": "frame",
    "Explanation:": "ttfdipttnlf | The TCP header is added. > Second | The IP header is added. > Third | The Ethernet header is added. > Fourth",
    "Which PDU format is used when bits are received from the network medium by the NIC of a host?": "frame",
    "Refer to the exhibit. ServerB is attempting to contact HostA. Which two statements correctly identify the addressing that ServerB will generate in the process? (Choose two.)": "swgafwtdmaor | swgapwtdiaoh",
    "Which method allows a computer to react accordingly when it requests data from a server and the server takes too long to respond?": "response timeout",
    "A web client is receiving a response for a web page from a web server. From the perspective of the client, what is the correct order of the protocol stack that is used to decode the received transmission?": "Ethernet, IP, TCP, HTTP",
    "Which two OSI model layers have the same functionality as a single layer of the TCP/IP model? (Choose two.)": "data link | physical",
    "At which layer of the OSI model would a logical address be added during encapsulation?": "network layer",
    "What is a characteristic of multicast messages?": "tastasgoh",
    "Which statement is correct about network protocols?": "tdhmaebtsatd",
    "What is the purpose of the OSI physical layer?": "transmitting bits across the local media",
    "Why are two strands of fiber used for a single fiber optic connection?": "They allow for full-duplex connectivity.",
    "Which characteristic describes crosstalk?": "tdottmfsciaw",
    "Which procedure is used to reduce the effect of crosstalk in copper cables?": "tocwpt",
    "Match the situation with the appropriate use of network media.": "taotticctn | ttottictn | tlticbtnondttdic",
    "A network administrator is measuring the transfer of bits across the company backbone for a mission critical financial application. The administrator notices that the network throughput appears lower than the bandwidth expected. Which three factors could influence the differences in throughput? (Choose three.)": "taotticctn | ttottictn | tlticbtnondttdic",
    "What are two characteristics of fiber-optic cable? (Choose two.)": "It is not affected by EMI or RFI. | iimetuci",
    "What is a primary role of the Physical layer in transmitting data on the network?": "ctstrtbiefottm",
    "With the use of unshielded twisted-pair copper wire in a network, what causes crosstalk within the cable pairs?": "tmfatapow",
    "Refer to the graphic. What type of cabling is shown?": "UTP",
    "In addition to the cable length, what two factors could interfere with the communication carried over UTP cables? (Choose two.)": "crosstalk | electromagnetic interference",
    "Which two devices commonly affect wireless networks? (Choose two.)": "cordless phones | microwaves",
    "Which two statements describe the services provided by the data link layer? (Choose two.)": "imtaofttnm | ipvlpiaffticwtni",
    "What is the function of the CRC value that is found in the FCS field of a frame?": "tvtiotrf",
    "What is contained in the trailer of a data-link frame?": "error detection",
    "Which statement describes a characteristic of the frame header fields of the data link layer?": "They vary depending on protocols.",
    "A network team is comparing physical WAN topologies for connecting remote sites to a headquarters building. Which topology provides high availability and connects some, but not all, remote sites?": "partial mesh",
    "Which two fields or features does Ethernet examine to determine if a received frame is passed to the data link layer or discarded by the NIC? (Choose two.)": "Frame Check Sequence | minimum frame size",
    "Which media communication type does not require media arbitration in the data link layer?": "full-duplex",
    "Which statement describes an extended star topology?": "edctacidwitctocid",
    "What is a characteristic of the LLC sublayer?": "ipiitfamlptutsniam",
    "What are three ways that media access control is used in networking? (Choose three.)": "Ethernet utilizes CSMA/CD. | macppodfotm | dllpdtrfatdm",
    "During the encapsulation process, what occurs at the data link layer for a PC connected to an Ethernet network?": "The physical address is added.",
    "What three items are contained in an Ethernet header and trailer? (Choose three.)": "source MAC address | destination MAC address | error-checking information",
    "What type of communication rule would best describe CSMA/CD?": "access method",
    "Which three basic parts are common to all frame types supported by the data link layer? (Choose three.)": "header | data | trailer",
    "Which statement is true about the CSMA/CD access method that is used in Ethernet?": "andmlbt",
    "What is the auto-MDIX feature on a switch?": "tacoaifastoacecc",
    "Refer to the exhibit. What is the destination MAC address of the Ethernet frame as it leaves the web server if the final destination is PC1?": "00-60-2F-3A-07-CC",
    "A Layer 2 switch is used to switch incoming frames from a 1000BASE-T port to a port connected to a 100Base-T network. Which method of memory buffering would work best for this task?": "shared memory buffering",
    "What are two examples of the cut-through switching method? (Choose two.)": "fast-forward switching | fragment-free switching",
    "Which frame forwarding method receives the entire frame and performs a CRC check to detect errors before forwarding the frame?": "store-and-forward switching",
    "What is the purpose of the FCS field in a frame?": "tdieoittar",
    "Which switching method has the lowest level of latency?": "fast-forward",
    "A network administrator is connecting two modern switches using a straight-through cable. The switches are new and have never been configured. Which three statements are correct about the final result of the connection? (Choose three.)": "tlbtswwatfstisbbs | tlbswwafd | tamfwctietnfacc",
    "Which advantage does the store-and-forward switching method have compared with the cut-through switching method?": "frame error checking",
    "When the store-and-forward method of switching is in use, what part of the Ethernet frame is used to perform an error check?": "CRC in the trailer",
    "Which switching method uses the CRC value in a frame?": "store-and-forward",
    "What are two actions performed by a Cisco switch? (Choose two.)": "utsmaoftbamamat | utmattffvtdma",
    "Which two statements describe features or functions of the logical link control sublayer in Ethernet standards? (Choose two.)": "llciiis | tdllultcwtulotps",
    "What is the auto-MDIX feature?": "ieadtacaituastoacc",
    "What is one advantage of using the cut-through switching method instead of the store-and-forward switching method?": "hallafhpca",
    "Which is a multicast MAC address?": "01-00-5E-00-00-03",
    "Refer to the exhibit. What is wrong with the displayed termination?": "tuloewitl",
    "Refer to the exhibit. The PC is connected to the console port of the switch. All the other connections are made through FastEthernet links. Which types of UTP cables can be used to connect the devices?": "Fa0/11",
    "Open the PT Activity. Perform the tasks in the activity instructions and then answer the question.": "Fa0/11",
    "What does the term “attenuation” mean in data communication?": "lossadi",
    "What makes fiber preferable to copper cabling for interconnecting buildings? (Choose three.)": "greater distances per cable run | limited susceptibility to EMI/RFI | greater bandwidth potential",
    "What OSI physical layer term describes the process by which one wave modifies another wave?": "modulation",
    "What OSI physical layer term describes the capacity at which a medium can carry data?": "bandwidth",
    "What OSI physical layer term describes the measure of the transfer of bits across a medium over a given period of time?": "throughput",
    "What OSI physical layer term describes the amount of time, including delays, for data to travel from one point to another?": "latency",
    "What OSI physical layer term describes the measure of usable data transferred over a given period of time?": "goodput",
    "What OSI physical layer term describes the physical medium which uses electrical pulses?": "copper cable",
    "What OSI physical layer term describes the physical medium that uses the propagation of light?": "fiber-optic cable",
    "What OSI physical layer term describes the physical medium for microwave transmissions?": "air",
    "Which two functions are performed at the LLC sublayer of the OSI data link layer? (Choose two.)": "eiaitutsniam | alcitnpd",
    "What action will occur if a switch receives a frame with the destination MAC address FF:FF:FF:FF:FF:FF?": "tsfioapetip",
    "What action will occur if a switch receives a frame with the destination MAC address 01:00:5E:00:00:D9?": "tsfioapetip",
    "What action will occur if a host receives a frame with a destination MAC address of FF:FF:FF:FF:FF:FF?": "The host will process the frame.",
    "What action will occur if a switch receives a frame and does have the source MAC address in the MAC table?": "tsrttote",
    "What action will occur if a host receives a frame with a destination MAC address it does not recognize?": "The host will discard the frame.",
    "Which type of UTP cable is used to connect a PC to a switch port?": "straight-through",
    "What is an advantage of network devices using open standard protocols?": "achaasrdoscsed",
    "Which device performs the function of determining the path that messages should take through internetworks?": "a router",
    "What is the IP address of the switch virtual interface (SVI) on Switch0?": "192.168.5.10",
    "Why would a Layer 2 switch need an IP address?": "tetstbmr",
    "Refer to the exhibit. An administrator is trying to configure the switch but receives the error message that is displayed in the exhibit. What is the problem?": "tamfepembitc",
    "What term describes a network owned by one organization that provides safe and secure access to individuals who work for a different organization?": "extranet",
    "What term describes storing personal files on servers over the internet to provide access anywhere, anytime, and on any device?": "cloud",
    "What term describes a network where one computer can be both client and server?": "peer-to-peer",
    "What term describes a type of network used by people who work from home or from a small remote office?": "SOHO network",
    "What term describes a computing model where server software runs on dedicated computers?": "client/server",
    "What term describes a technology that allows devices to connect to the LAN using an electrical outlet?": "powerline networking",
    "What term describes a policy that allows network devices to manage the flow of data to give priority to voice and video?": "quality of service",
    "What term describes a private collection of LANs and WANs that belongs to an organization?": "intranet",
    "What term describes the ability to use personal devices across a business or campus network?": "BYOD",
    "At which OSI layer is a source IP address added to a PDU during the encapsulation process?": "network layer",
    "At which OSI layer is a destination port number added to a PDU during the encapsulation process?": "transport layer",
    "At which OSI layer is data added to a PDU during the encapsulation process?": "application layer",
    "Which of the following is the name for all computers connected to a network that participate directly in network communication?": "Host",
    "At which OSI layer is a destination IP address added to a PDU during the encapsulation process?": "network layer",
    "At which OSI layer is a source MAC address added to a PDU during the encapsulation process?": "data link layer",
    "At which OSI layer is a source port number added to a PDU during the encapsulation process?": "transport layer",
    "At which OSI layer is a destination MAC address added to a PDU during the encapsulation process?": "data link layer",
    "When data is encoded as pulses of light, which media is being used to transmit the data?": "Fiber optic cable",
    "Which two devices are intermediary devices? (Choose two)": "Router | Switch",
    "A college is building a new dormitory on its campus. Workers are digging in the ground to install a new water pipe for the dormitory. A worker accidentally damages a fiber optic cable that connects two of the existing dormitories to the campus data center. Although the cable has been cut, students in the dormitories only experience a very short interruption of network services. What characteristic of the network is shown here?": "fault tolerance",
    "Which information is used by routers to forward a data packet toward its destination?": "destination IP address",
    "A computer has to send a packet to a destination host in the same LAN. How will the packet be sent?": "The packet will be sent directly to the destination host",
    "A router receives a packet from the Gigabit 0/0 interface and determines that the packet needs to be forwarded out the Gigabit 0/1 interface. What will the router do next?": "create a new Layer 2 Ethernet frame to be sent to the destination",
    "Which IPv4 address can a host use to ping the loopback interface?": "127.0.0.1",
    "A computer can access devices on the same network but cannot access devices on other networks. What is the probable cause of this problem?": "The computer has an invalid default gateway address.",
    "Which statement describes a feature of the IP protocol?": "IP relies on upper layer services to handle situations of missing or out-of-order packets.",
    "Why is NAT not needed in IPv6?": "Any host or user can get a public IPv6 network address because the number of available IPv6 addresses is extremely large.",
    "Which parameter does the router use to choose the path to the destination when there are multiple routes available?": "the lower metric value that is associated with the destination network",
    "What are two services provided by the OSI network layer? (Choose two.)": "routing packets toward the destination & encapsulating PDUs from the transport layer",
    "Within a production network, what is the purpose of configuring a switch with a default gateway address?": "The default gateway address is used to forward packets originating from the switch to remote networks.",
    "What is a basic characteristic of the IP protocol?": "connectionless",
    "Which field in the IPv4 header is used to prevent a packet from traversing a network endlessly?": "Time-to-Live",
    "What is one advantage that the IPv6 simplified header offers over IPv4?": "efficient packet handling",
    "What IPv4 header field identifies the upper layer protocol carried in the packet?": "Protocol",
    "Refer to the exhibit. Match the packets with their destination IP address to the exiting interfaces on the router. (Not all targets are used.)": "15-00 | 8-01 | 20-000 | 5-11 | 10-10",
    "What information does the loopback test provide?": "The TCP/IP stack on the device is working correctly.",
    "What routing table entry has a next hop address associated with a destination network?": "remote routes",
    "How do hosts ensure that their packets are directed to the correct network destination?": "They have to keep their own local routing table that contains a route to the loopback interface, a local network route, and a remote default route.",
    "When transporting data from real-time applications, such as streaming audio and video, which field in the IPv6 header can be used to inform the routers and switches to maintain the same path for the packets in the same conversation?": "Flow Label",
    "What statement describes the function of the Address Resolution Protocol?": "ARP is used to discover the MAC address of any host on the local network.",
    "Under which two circumstances will a switch flood a frame out of every port except the port that the frame was received on? (Choose two.)": "The frame has the broadcast address as the destination address. & The destination address is unknown to the switch.",
    "Which statement describes the treatment of ARP requests on the local link?": "They are received and processed by every device on the local network.",
    "Which destination address is used in an ARP request frame?": "FFFF.FFFF.FFFF",
    "A network technician issues the arp -d * command on a PC after the router that is connected to the LAN is reconfigured. What is the result after this command is issued?": "The ARP cache is cleared.",
    "Refer to the exhibit. The exhibit shows a small switched network and the contents of the MAC address table of the switch. PC1 has sent a frame addressed to PC3. What will the switch do with the frame?": "The switch will forward the frame to all ports except port 4.",
    "Which two types of IPv6 messages are used in place of ARP for address resolution?": "neighbor solicitation & neighbor advertisement",
    "What is the aim of an ARP spoofing attack?": "to associate IP addresses to the wrong MAC address",
    "Refer to the exhibit. PC1 attempts to connect to File_server1 and sends an ARP request to obtain a destination MAC address. Which MAC address will PC1 receive in the ARP reply?": "the MAC address of the G0/0 interface on R1",
    "Where are IPv4 address to Layer 2 Ethernet address mappings maintained on a host computer?": "ARP cache",
    "What important information is examined in the Ethernet frame header by a Layer 2 device in order to forward the data onward?": "destination MAC address",
    "Match the commands to the correct actions. (Not all options are used.)": "psoc-rcpc | canotr-rchc | damaatr-rcbm",
    "A new network administrator has been asked to enter a banner message on a Cisco device. What is the fastest way a network administrator could test whether the banner is properly configured?": "Exit privileged EXEC mode and press Enter",
    "A network administrator requires access to manage routers and switches locally and remotely. Match the description to the access method. (Not all options are used.)": "service password-encryption > R1(config)# | enable > R1> | copy running-config startup-config > R1# | login > R1(config-line)# | ip address 192.168.4.4 255.255.255.0 > R1(config-if)#",
    "What are two functions of NVRAM? (Choose two.)": "to retain contents when power is removed & to store the startup configuration file",
    "A router boots and enters setup mode. What is the reason for this?": "The configuration file is missing from NVRAM.",
    "The global configuration command ip default-gateway 172.16.100.1 is applied to a switch. What is the effect of this command?": "The switch can be remotely managed from a host on another network.",
    "What happens when the transport input ssh command is entered on the switch vty lines?": "Communication between the switch and remote users is encrypted.",
    "Refer to the exhibit. A user PC has successfully transmitted packets to www.cisco.com. Which IP address does the user PC target in order to forward its data off the local network?": "172.20.0.254",
    "Match the configuration mode with the command that is available in that mode. (Not all options are used.)": "R1> > enable | R1(config-line)# > login | R1# > copy running-config startup-config | R1(config)# > interface fastethernet 0/0",
    "Which three commands are used to set up secure access to a router through a connection to the console interface? (Choose three.)": "line console 0 & login & password cisco",
    "Refer to the exhibit. Consider the IP address configuration shown from PC1. What is a description of the default gateway address?": "It is the IP address of the Router1 interface that connects the PC1 LAN to Router1.",
    "Which two functions are primary functions of a router? (Choose two.)": "packet forwarding & path selection",
    "What is the effect of using the Router# copy running-config startup-config command on a router?": "The contents of NVRAM will change",
    "What will happen if the default gateway address is incorrectly configured on a host?": "The host cannot communicate with hosts in other networks.",
    "What are two potential network problems that can result from ARP operation? (Choose two.)": "On large networks with low bandwidth, multiple ARP broadcasts could cause data communication delays. & Network attackers could manipulate MAC address and IP address mappings in ARP messages with the intent of intercepting network traffic.",
    "Open the PT activity. Perform the tasks in the activity instructions and then answer the question.": "R1: G0/0 and S0/0/0 & R2: G0/1 and S0/0/0",
    "Which term describes a field in the IPv4 packet header used to identify the next level protocol?": "protocol",
    "Which term describes a field in the IPv4 packet header that contains an 8-bit binary value used to determine the priority of each packet?": "differentiated services",
    "Which term describes a field in the IPv4 packet header that contains a 32-bit binary value associated with an interface on the sending device?": "source IPv4 address",
    "Which term describes a field in the IPv4 packet header used to detect corruption in the IPv4 header?": "header checksum",
    "Refer to the exhibit. A network administrator is connecting a new host to the Payroll LAN. The host needs to communicate with remote networks. What IP address would be configured as the default gateway on the new host?": "10.27.14.148",
    "Which term describes a field in the IPv4 packet header that contains a unicast, multicast, or broadcast address?": "destination IPv4 address",
    "Which term describes a field in the IPv4 packet header used to limit the lifetime of a packet?": "TTL",
    "Which term describes a field in the IPv4 packet header that contains a 4-bit binary value set to 0100?": "version",
    "What property of ARP causes cached IP-to-MAC mappings to remain in memory longer?": "Entries in an ARP table are time-stamped and are purged after the timeout expires.",
    "What property of ARP allows MAC addresses of frequently used servers to be fixed in the ARP table?": "A static IP-to-MAC address entry can be entered manually into an ARP table.",
    "What property of ARP allows hosts on a LAN to send traffic to remote networks?": "Local hosts learn the MAC address of the default gateway.",
    "Refer to the exhibit. A network administrator is connecting a new host to the Registrar LAN. The host needs to communicate with remote networks. What IP address would be configured as the default gateway on the new host?": "192.168.235.234",
    "What property of ARP forces all Ethernet NICs to process an ARP request?": "The destination MAC address FF-FF-FF-FF-FF-FF appears in the header of the Ethernet frame.",
    "What property of ARP causes a reply only to the source sending an ARP request?": "The source MAC address appears in the header of the Ethernet frame.",
    "What property of ARP causes the request to be flooded out all ports of a switch except for the port receiving the ARP request?": "The destination MAC address FF-FF-FF-FF-FF-FF appears in the header of the Ethernet frame.",
    "What property of ARP causes the NICs receiving an ARP request to pass the data portion of the Ethernet frame to the ARP process?": "The type field 0x806 appears in the header of the Ethernet frame.",
    "Refer to the exhibit. A network administrator is connecting a new host to the Service LAN. The host needs to communicate with remote networks. What IP address would be configured as the default gateway on the new host?": "172.29.157.156",
    "Refer to the exhibit. A network administrator is connecting a new host to the Medical LAN. The host needs to communicate with remote networks. What IP address would be configured as the default gateway on the new host?": "192.168.201.200",
    "What is the prefix length notation for the subnet mask 255.255.255.224?": "Network A > 192.168.0.128 /25 | Network B > 192.168.0.0 /26 | Network C > 192.168.0.96 /27 | Network D > 192.168.0.80 /30",
    "How many valid host addresses are available on an IPv4 subnet that is configured with a /26 mask?": "Network A > 192.168.0.128 /25 | Network B > 192.168.0.0 /26 | Network C > 192.168.0.96 /27 | Network D > 192.168.0.80 /30",
    "Which subnet mask would be used if 5 host bits are available?": "Network A > 192.168.0.128 /25 | Network B > 192.168.0.0 /26 | Network C > 192.168.0.96 /27 | Network D > 192.168.0.80 /30",
    "A network administrator subnets the 192.168.10.0/24 network into subnets with /26 masks. How many equal-sized subnets are created?": "Network A > 192.168.0.128 /25 | Network B > 192.168.0.0 /26 | Network C > 192.168.0.96 /27 | Network D > 192.168.0.80 /30",
    "Match the subnetwork to a host address that would be included within the subnetwork. (Not all options are used.)": "Network A > 192.168.0.128 /25 | Network B > 192.168.0.0 /26 | Network C > 192.168.0.96 /27 | Network D > 192.168.0.80 /30",
    "An administrator wants to create four subnetworks from the network address 192.168.1.0/24. What is the network address and subnet mask of the second useable subnet?": "Network A > 192.168.0.128 /25 | Network B > 192.168.0.0 /26 | Network C > 192.168.0.96 /27 | Network D > 192.168.0.80 /30",
    "How many bits must be borrowed from the host portion of an address to accommodate a router with five connected networks?": "Network A > 192.168.0.128 /25 | Network B > 192.168.0.0 /26 | Network C > 192.168.0.96 /27 | Network D > 192.168.0.80 /30",
    "How many host addresses are available on the 192.168.10.128/26 network?": "Network A > 192.168.0.128 /25 | Network B > 192.168.0.0 /26 | Network C > 192.168.0.96 /27 | Network D > 192.168.0.80 /30",
    "How many host addresses are available on the network 172.16.128.0 with a subnet mask of 255.255.252.0?": "Network A > 192.168.0.128 /25 | Network B > 192.168.0.0 /26 | Network C > 192.168.0.96 /27 | Network D > 192.168.0.80 /30",
    "Match each IPv4 address to the appropriate address category. (Not all options are used.)": "Network A > 192.168.0.128 /25 | Network B > 192.168.0.0 /26 | Network C > 192.168.0.96 /27 | Network D > 192.168.0.80 /30",
    "What three blocks of addresses are defined by RFC 1918 for private network use? (Choose three.)": "Network A > 192.168.0.128 /25 | Network B > 192.168.0.0 /26 | Network C > 192.168.0.96 /27 | Network D > 192.168.0.80 /30",
    "Refer to the exhibit. An administrator must send a message to everyone on the router A network. What is the broadcast address for network 172.16.16.0/22?": "Network A > 192.168.0.128 /25 | Network B > 192.168.0.0 /26 | Network C > 192.168.0.96 /27 | Network D > 192.168.0.80 /30",
    "A site administrator has been told that a particular network at the site must accommodate 126 hosts. Which subnet mask would be used that contains the required number of host bits?": "Network A > 192.168.0.128 /25 | Network B > 192.168.0.0 /26 | Network C > 192.168.0.96 /27 | Network D > 192.168.0.80 /30",
    "Refer to the exhibit. Considering the addresses already used and having to remain within the 10.16.10.0/24 network range, which subnet address could be assigned to the network containing 25 hosts?": "Network A > 192.168.0.128 /25 | Network B > 192.168.0.0 /26 | Network C > 192.168.0.96 /27 | Network D > 192.168.0.80 /30",
    "What is the usable number of host IP addresses on a network that has a /26 mask?": "Network A > 192.168.0.128 /25 | Network B > 192.168.0.0 /26 | Network C > 192.168.0.96 /27 | Network D > 192.168.0.80 /30",
    "Which address prefix range is reserved for IPv4 multicast?": "Network A > 192.168.0.128 /25 | Network B > 192.168.0.0 /26 | Network C > 192.168.0.96 /27 | Network D > 192.168.0.80 /30",
    "Refer to the exhibit. Match the network with the correct IP address and prefix that will satisfy the usable host addressing requirements for each network.": "Network A > 192.168.0.128 /25 | Network B > 192.168.0.0 /26 | Network C > 192.168.0.96 /27 | Network D > 192.168.0.80 /30",
    "A high school in New York (school A) is using videoconferencing technology to establish student interactions with another high school (school B) in Russia. The videoconferencing is conducted between two end devices through the Internet. The network administrator of school A configures the end device with the IP address 209.165.201.10. The administrator sends a request for the IP address for the end device in school B and the response is 192.168.25.10. Neither school is using a VPN. The administrator knows immediately that this IP will not work. Why?": "::1 > loopback | FF02::1 > all node multicast | ffffsnm | 2001:DB8::BAF:3F57:FE94 > global unicast",
    "Which three addresses are valid public addresses? (Choose three.)": "::1 > loopback | FF02::1 > all node multicast | ffffsnm | 2001:DB8::BAF:3F57:FE94 > global unicast",
    "A message is sent to all hosts on a remote network. Which type of message is it?": "::1 > loopback | FF02::1 > all node multicast | ffffsnm | 2001:DB8::BAF:3F57:FE94 > global unicast",
    "A company has a network address of 192.168.1.64 with a subnet mask of 255.255.255.192. The company wants to create two subnetworks that would contain 10 hosts and 18 hosts respectively. Which two networks would achieve that? (Choose two.)": "::1 > loopback | FF02::1 > all node multicast | ffffsnm | 2001:DB8::BAF:3F57:FE94 > global unicast",
    "Which address is a valid IPv6 link-local unicast address?": "::1 > loopback | FF02::1 > all node multicast | ffffsnm | 2001:DB8::BAF:3F57:FE94 > global unicast",
    "Which of these addresses is the shortest abbreviation for the IP address:3FFE:1044:0000:0000:00AB:0000:0000:0057?": "::1 > loopback | FF02::1 > all node multicast | ffffsnm | 2001:DB8::BAF:3F57:FE94 > global unicast",
    "A network administrator has received the IPv6 prefix 2001:DB8::/48 for subnetting. Assuming the administrator does not subnet into the interface ID portion of the address space, how many subnets can the administrator create from the /48 prefix?": "::1 > loopback | FF02::1 > all node multicast | ffffsnm | 2001:DB8::BAF:3F57:FE94 > global unicast",
    "Given IPv6 address prefix 2001:db8::/48, what will be the last subnet that is created if the subnet prefix is changed to /52?": "::1 > loopback | FF02::1 > all node multicast | ffffsnm | 2001:DB8::BAF:3F57:FE94 > global unicast",
    "Consider the following range of addresses:": "::1 > loopback | FF02::1 > all node multicast | ffffsnm | 2001:DB8::BAF:3F57:FE94 > global unicast",
    "The prefix-length for the range of addresses is": "::1 > loopback | FF02::1 > all node multicast | ffffsnm | 2001:DB8::BAF:3F57:FE94 > global unicast",
    "What type of IPv6 address is FE80::1?": "::1 > loopback | FF02::1 > all node multicast | ffffsnm | 2001:DB8::BAF:3F57:FE94 > global unicast",
    "Refer to the exhibit. A company is deploying an IPv6 addressing scheme for its network. The company design document indicates that the subnet portion of the IPv6 addresses is used for the new hierarchical network design, with the site subsection to represent multiple geographical sites of the company, the sub-site section to represent multiple campuses at each site, and the subnet section to indicate each network segment separated by routers. With such a scheme, what is the maximum number of subnets achieved per sub-site?": "::1 > loopback | FF02::1 > all node multicast | ffffsnm | 2001:DB8::BAF:3F57:FE94 > global unicast",
    "Refer to the exhibit. A company is deploying an IPv6 addressing scheme for its network. The company design document indicates that the subnet portion of the IPv6 addresses is used for the new hierarchical network design, with the s ite subsection to represent multiple geographical sites of the company, the s ub-site section to represent multiple campuses at each site, and the s ubnet section to indicate each network segment separated by routers. With such a scheme, what is the maximum number of subnets achieved per sub-site ?": "::1 > loopback | FF02::1 > all node multicast | ffffsnm | 2001:DB8::BAF:3F57:FE94 > global unicast",
    "What is used in the EUI-64 process to create an IPv6 interface ID on an IPv6 enabled interface?": "::1 > loopback | FF02::1 > all node multicast | ffffsnm | 2001:DB8::BAF:3F57:FE94 > global unicast",
    "What is the prefix for the host address 2001:DB8:BC15:A:12AB::1/64?": "::1 > loopback | FF02::1 > all node multicast | ffffsnm | 2001:DB8::BAF:3F57:FE94 > global unicast",
    "An IPv6 enabled device sends a data packet with the destination address of FF02::1. What is the target of this packet?": "::1 > loopback | FF02::1 > all node multicast | ffffsnm | 2001:DB8::BAF:3F57:FE94 > global unicast",
    "Match the IPv6 address with the IPv6 address type. (Not all options are used.)": "::1 > loopback | FF02::1 > all node multicast | ffffsnm | 2001:DB8::BAF:3F57:FE94 > global unicast",
    "Which IPv6 prefix is reserved for communication between devices on the same link?": "tipaipcitsnds | tipitiaipt | ipaciipavvt",
    "Which type of IPv6 address refers to any unicast address that is assigned to multiple hosts?": "tipaipcitsnds | tipitiaipt | ipaciipavvt",
    "What are two types of IPv6 unicast addresses? (Choose two.)": "tipaipcitsnds | tipitiaipt | ipaciipavvt",
    "Which service provides dynamic global IPv6 addressing to end devices without using a server that keeps a record of available IPv6 addresses?": "tipaipcitsnds | tipitiaipt | ipaciipavvt",
    "Which protocol supports Stateless Address Autoconfiguration (SLAAC) for dynamic assignment of IPv6 addresses to a host?": "tipaipcitsnds | tipitiaipt | ipaciipavvt",
    "Three methods allow IPv6 and IPv4 to co-exist. Match each method with its description. (Not all options are used.)": "tipaipcitsnds | tipitiaipt | ipaciipavvt",
    "A technician uses the ping 127.0.0.1 command. What is the technician testing?": "a link-local address > 169.254.1.5 | a TEST-NET address > 192.0.2.123 | an experimental address > 240.2.6.255 | a private address > 172.19.20.5 | a loopback address > 127.0.0.1",
    "Refer to the exhibit. An administrator is trying to troubleshoot connectivity between PC1 and PC2 and uses the tracert command from PC1 to do it. Based on the displayed output, where should the administrator begin troubleshooting?": "a link-local address > 169.254.1.5 | a TEST-NET address > 192.0.2.123 | an experimental address > 240.2.6.255 | a private address > 172.19.20.5 | a loopback address > 127.0.0.1",
    "Which protocol is used by the traceroute command to send and receive echo-requests and echo-replies?": "a link-local address > 169.254.1.5 | a TEST-NET address > 192.0.2.123 | an experimental address > 240.2.6.255 | a private address > 172.19.20.5 | a loopback address > 127.0.0.1",
    "Which ICMPv6 message is sent when the IPv6 hop limit field of a packet is decremented to zero and the packet cannot be forwarded?": "a link-local address > 169.254.1.5 | a TEST-NET address > 192.0.2.123 | an experimental address > 240.2.6.255 | a private address > 172.19.20.5 | a loopback address > 127.0.0.1",
    "A user executes a traceroute over IPv6. At what point would a router in the path to the destination device drop the packet?": "a link-local address > 169.254.1.5 | a TEST-NET address > 192.0.2.123 | an experimental address > 240.2.6.255 | a private address > 172.19.20.5 | a loopback address > 127.0.0.1",
    "What is the purpose of ICMP messages?": "a link-local address > 169.254.1.5 | a TEST-NET address > 192.0.2.123 | an experimental address > 240.2.6.255 | a private address > 172.19.20.5 | a loopback address > 127.0.0.1",
    "What source IP address does a router use by default when the traceroute command is issued?": "a link-local address > 169.254.1.5 | a TEST-NET address > 192.0.2.123 | an experimental address > 240.2.6.255 | a private address > 172.19.20.5 | a loopback address > 127.0.0.1",
    "Match each description with an appropriate IP address. (Not all options are used.)": "a link-local address > 169.254.1.5 | a TEST-NET address > 192.0.2.123 | an experimental address > 240.2.6.255 | a private address > 172.19.20.5 | a loopback address > 127.0.0.1",
    "A user issues a ping 192.135.250.103 command and receives a response that includes a code of 1. What does this code represent?": "host unreachable",
    "Which subnet would include the address 192.168.1.96 as a usable host address?": "192.168.1.64/26",
    "What are the three IPv6 addresses displayed when the route from PC1 to PC2 is traced? (Choose three.)": "2001:DB8:1:1::1 | 2001:DB8:1:2::1 | 2001:DB8:1:3::2",
    "A host is transmitting a broadcast. Which host or hosts will receive it?": "all hosts in the same subnet",
    "A host is transmitting a unicast. Which host or hosts will receive it?": "one specific host",
    "A user issues a ping 2001:db8:FACE:39::10 command and receives a response that includes a code of 3. What does this code represent?": "address unreachable",
    "A host is transmitting a multicast. Which host or hosts will receive it?": "a specially defined group of hosts",
    "Which is the compressed format of the IPv6 address 2001:0db8:0000:0000:0000:a0b0:0008:0001?": "2001:db8::a0b0:8:1",
    "Which is the compressed format of the IPv6 address fe80:09ea:0000:2200:0000:0000:0fe0:0290?": "fe80:9ea:0:2200::fe0:290",
    "Which is the compressed format of the IPv6 address 2002:0042:0010:c400:0000:0000:0000:0909?": "2002:42:10:c400::909",
    "Which is the compressed format of the IPv6 address 2001:0db8:0000:0000:0ab8:0001:0000:1000?": "2001:db8::ab8:1:0:1000",
    "Which is the compressed format of the IPv6 address 2002:0420:00c4:1008:0025:0190:0000:0990?": "2002:420:c4:1008:25:190::990",
    "Which is the compressed format of the IPv6 address fe80:0000:0000:0000:0220:0b3f:f0e0:0029?": "fe80::220:b3f:f0e0:29",
    "A user issues a ping 2001:db8:FACE:39::10 command and receives a response that includes a code of 2. What does this code represent?": "beyond scope of the source address",
    "A user issues a ping fe80:65ab:dcc1::100 command and receives a response that includes a code of 3. What does this code represent?": "address unreachable",
    "A user issues a ping 10.10.14.67 command and receives a response that includes a code of 0. What does this code represent?": "network unreachable",
    "A user issues a ping fe80:65ab:dcc1::100 command and receives a response that includes a code of 4. What does this code represent?": "port unreachable",
    "A user issues a ping 198.133.219.8 command and receives a response that includes a code of 0. What does this code represent?": "network unreachable",
    "A user issues a ping 2001:db8:3040:114::88 command and receives a response that includes a code of 4. What does this code represent?": "port unreachable",
    "Which action is performed by a client when establishing communication with a server via the use of UDP at the transport layer?": "tcrsaspn",
    "Which transport layer feature is used to guarantee session establishment?": "TCP 3-way handshake",
    "What is the complete range of TCP and UDP well-known ports?": "0 to 1023",
    "What is a socket?": "tcoasiaapnoadiaapn",
    "A PC is downloading a large file from a server. The TCP window is 1000 bytes. The server is sending the file using 100-byte segments. How many segments will the server send before it requires an acknowledgment from the PC?": "10 segments",
    "Which factor determines TCP window size?": "taodtdcpaot",
    "What does a client do when it has UDP datagrams to send?": "It just sends the datagrams.",
    "Which three fields are used in a UDP segment header? (Choose three.)": "Length | Source Port | Checksum",
    "What are two roles of the transport layer in data communication on a network? (Choose two.)": "itpafecs | tticbaotsadh",
    "What information is used by TCP to reassemble and reorder received segments?": "sequence numbers",
    "What important information is added to the TCP/IP transport layer header to ensure communication and connectivity with a remote network device?": "destination and source port numbers",
    "Which two characteristics are associated with UDP sessions? (Choose two.)": "ddrtwmd | Received data is unacknowledged.",
    "A client application needs to terminate a TCP communication session with a server. Place the termination process steps in the order that they will occur. (Not all options are used.)": "ACK",
    "Which flag in the TCP header is used in response to a received FIN in order to terminate connectivity between two network devices?": "ACK",
    "Which protocol or service uses UDP for a client-to-server communication and TCP for server-to-server communication?": "DNS",
    "What is a characteristic of UDP?": "urtrditotwr",
    "What kind of port must be requested from IANA in order to be used with a specific application?": "registered port",
    "Which three application layer protocols use TCP? (Choose three.)": "SMTP | FTP | HTTP",
    "Which three statements characterize UDP? (Choose three.)": "upbctlf | uroalpfed | uialoptdnpsofcm",
    "Which two fields are included in the TCP header but not in the UDP header? (Choose two.)": "window | sequence number",
    "Which field in the TCP header indicates the status of the three-way handshake process?": "control bits",
    "Why does HTTP use TCP as the transport layer protocol?": "because HTTP requires reliable delivery",
    "Which two types of applications are best suited for UDP? (Choose two.)": "athrt | atctsdlbrlond",
    "How are port numbers used in the TCP/IP encapsulation process?": "imcotautsstspniutttsc",
    "In what two situations would UDP be better than TCP as the preferred transport protocol? (Choose two.)": "wafdmin | wadnntgdotd",
    "What are three responsibilities of the transport layer? (Choose three.)": "mtrroaia | mmcsfmuoaotsn | itaasotcastshtd",
    "Which three statements describe a DHCP Discover message? (Choose three.)": "tdiai | tmcfacsaia | ahrtmboadsr",
    "Which two protocols may devices use in the application process that sends email? (Choose two.)": "SMTP | DNS",
    "What is true about the Server Message Block protocol?": "cealtcts",
    "What is the function of the HTTP GET message?": "trahpfaws",
    "Which OSI layer provides the interface between the applications used to communicate and the underlying network over which messages are transmitted?": "application",
    "Which networking model is being used when an author uploads one chapter document to a file server of a book publisher?": "client/server",
    "What do the client/server and peer-to-peer network models have in common?": "bmsdisacr",
    "In what networking model would eDonkey, eMule, BitTorrent, Bitcoin, and LionShare be used?": "peer-to-peer",
    "What is a common protocol that is used with peer-to-peer applications such as WireShare, Bearshare, and Shareaza?": "Gnutella",
    "What is a key characteristic of the peer-to-peer networking model?": "rswads",
    "The application layer of the TCP/IP model performs the functions of what three layers of the OSI model? (Choose three.)": "session | presentation | application",
    "What is an example of network communication that uses the client-server model?": "awiadrwtutwccitaboawb",
    "Which layer in the TCP/IP model is used for formatting, compressing, and encrypting data?": "application",
    "What is an advantage of SMB over FTP?": "sccealtctts",
    "A manufacturing company subscribes to certain hosted services from its ISP. The services that are required include hosted world wide web, file transfer, and e-mail. Which protocols represent these three key applications? (Choose three.)": "FTP | HTTP | SMTP",
    "Which application layer protocol uses message types such as GET, PUT, and POST?": "HTTP",
    "What type of information is contained in a DNS MX record?": "tdnmtmes",
    "Which three protocols operate at the application layer of the TCP/IP model? (Choose three.)": "FTP | POP3 | DHCP",
    "Which protocol is used by a client to communicate securely with a web server?": "HTTPS",
    "Which applications or services allow hosts to act as client and server at the same time?": "P2P applications",
    "What are two characteristics of peer-to-peer networks? (Choose two.)": "decentralized resources | rswads",
    "Which scenario describes a function provided by the transport layer?": "ashtwbwoiotatwsttletcwpidttcbw",
    "Which three layers of the OSI model provide similar network services to those provided by the application layer of the TCP/IP model? (Choose three.)": "session layer | application layer | presentation layer",
    "A PC that is communicating with a web server has a TCP window size of 6,000 bytes when sending data and a packet size of 1,500 bytes. Which byte of information will the web server acknowledge after it has received two packets of data from the PC?": "3001",
    "A PC that is communicating with a web server has a TCP window size of 6,000 bytes when sending data and a packet size of 1,500 bytes. Which byte of information will the web server acknowledge after it has received three packets of data from the PC?": "4501",
    "A PC that is communicating with a web server has a TCP window size of 6,000 bytes when sending data and a packet size of 1,500 bytes. Which byte of information will the web server acknowledge after it has received four packets of data from the PC?": "6001",
    "A client creates a packet to send to a server. The client is requesting TFTP service. What number will be used as the destination port number in the sending packet?": "69",
    "A client creates a packet to send to a server. The client is requesting FTP service. What number will be used as the destination port number in the sending packet?": "21",
    "A client creates a packet to send to a server. The client is requesting SSH service. What number will be used as the destination port number in the sending packet?": "22",
    "A client creates a packet to send to a server. The client is requesting HTTP service. What number will be used as the destination port number in the sending packet?": "80",
    "A client creates a packet to send to a server. The client is requesting POP3 service. What number will be used as the destination port number in the sending packet?": "110",
    "A client creates a packet to send to a server. The client is requesting telnet service. What number will be used as the destination port number in the sending packet?": "23",
    "A client creates a packet to send to a server. The client is requesting SNMP service. What number will be used as the destination port number in the sending packet?": "161",
    "A client creates a packet to send to a server. The client is requesting SMTP service. What number will be used as the destination port number in the sending packet?": "25",
    "A client creates a packet to send to a server. The client is requesting HTTPS service. What number will be used as the destination port number in the sending packet?": "443",
    "Which component is designed to protect against unauthorized communications to and from a computer?": "spwtnadnfctiouuatn | cwwiaaloaranednfatomt | twaneietosoandfv",
    "Which command will block login attempts on RouterA for a period of 30 seconds if there are 2 failed login attempts within 10 seconds?": "spwtnadnfctiouuatn | cwwiaaloaranednfatomt | twaneietosoandfv",
    "What is the purpose of the network security accounting function?": "spwtnadnfctiouuatn | cwwiaaloaranednfatomt | twaneietosoandfv",
    "What type of attack may involve the use of tools such as nslookup and fping?": "spwtnadnfctiouuatn | cwwiaaloaranednfatomt | twaneietosoandfv",
    "Match each weakness with an example. (Not all options are used.)": "spwtnadnfctiouuatn | cwwiaaloaranednfatomt | twaneietosoandfv",
    "Match the type of information security threat to the scenario. (Not all options are used.)": "mtwwtllavg",
    "Which example of malicious code would be classified as a Trojan horse?": "mtwwtllavg",
    "What is the difference between a virus and a worm?": "Worms self-replicate but viruses do not.",
    "Which attack involves a compromise of data that occurs between two end points?": "man-in-the-middle attack",
    "Which type of attack involves an adversary attempting to gather information about a network to identify vulnerabilities?": "reconnaissance",
    "Match the description to the type of firewall filtering. (Not all options are used.)": "to require users to prove who they are",
    "What is the purpose of the network security authentication function?": "to require users to prove who they are",
    "Which firewall feature is used to ensure that packets coming into a network are legitimate responses to requests initiated from internal hosts?": "stateful packet inspection",
    "When applied to a router, which command would help mitigate brute-force password attacks against the router?": "login block-for 60 attempts 5 within 60",
    "Identify the steps needed to configure a switch for SSH. The answer order does not matter. (Not all options are used.)": "login information and data encryption",
    "What feature of SSH makes it more secure than Telnet for a device management connection?": "login information and data encryption",
    "What is the advantage of using SSH over Telnet?": "spsctah",
    "What is the role of an IPS?": "daboairt",
    "A user is redesigning a network for a small company and wants to ensure security at a reasonable price. The user deploys a new application-aware firewall with intrusion detection capabilities on the ISP connection. The user installs a second firewall to separate the company network from the public network. Additionally, the user installs an IPS on the internal network of the company. What approach is the user implementing?": "layered",
    "What is an accurate description of redundancy?": "dantumpbstetinspof",
    "A network administrator is upgrading a small business network to give high priority to real-time applications traffic. What two types of network services is the network administrator trying to accommodate? (Choose two.)": "voice | video",
    "What is the purpose of a small company using a protocol analyzer utility to capture network traffic on the network segments where the company is considering a network upgrade?": "tdaantroens",
    "Refer to the exhibit. An administrator is testing connectivity to a remote device with the IP address 10.1.1.1. What does the output of this command indicate?": "aratpdnharttd",
    "Which method is used to send a ping message specifying the source address for the ping?": "itpcwsadia",
    "A network engineer is analyzing reports from a recently performed network baseline. Which situation would depict a possible latency issue?": "aiihthprt",
    "Which statement is true about Cisco IOS ping indicators?": "umitaratpdncarttdaattpwu",
    "A user reports a lack of network connectivity. The technician takes control of the user machine and attempts to ping other computers on the network and these pings fail. The technician pings the default gateway and that also fails. What can be determined for sure by the results of these tests?": "ncbdfsatp",
    "A network technician issues the C:> tracert -6 www.cisco.com command on a Windows PC. What is the purpose of the -6 command option?": "It forces the trace to use IPv6.",
    "Why would a network administrator use the tracert utility?": "tiwapwlodoan",
    "A ping fails when performed from router R1 to directly connected router R2. The network administrator then proceeds to issue the show cdp neighbors command. Why would the network administrator issue this command if the ping failed between the two routers?": "tnawtvlc",
    "A network engineer is troubleshooting connectivity issues among interconnected Cisco routers and switches. Which command should the engineer use to find the IP address information, host name, and IOS version of neighboring network devices?": "show cdp neighbors detail",
    "What information about a Cisco router can be verified using the show version command?": "the value of the configuration register",
    "Which command should be used on a Cisco router or switch to allow log messages to be displayed on remotely connected sessions using Telnet or SSH?": "terminal monitor",
    "Which command can an administrator issue on a Cisco router to send debug messages to the vty lines?": "terminal monitor",
    "By following a structured troubleshooting approach, a network administrator identified a network issue after a conversation with the user. What is the next step that the administrator should take?": "Establish a theory of probable causes.",
    "Users are complaining that they are unable to browse certain websites on the Internet. An administrator can successfully ping a web server via its IP address, but cannot browse to the domain name of the website. Which troubleshooting tool would be most useful in determining where the problem is?": "nslookup",
    "An employee complains that a Windows PC cannot connect to the Internet. A network technician issues the ipconfig command on the PC and is shown an IP address of 169.254.10.3. Which two conclusions can be drawn? (Choose two.)": "The PC cannot contact a DHCP server. | tpictoaiaa",
    "Refer to the exhibit. Host H3 is having trouble communicating with host H1. The network administrator suspects a problem exists with the H3 workstation and wants to prove that there is no problem with the R2 configuration. What tool could the network administrator use on router R2 to prove that communication exists to host H1 from the interface on R2, which is the interface that H3 uses when communicating with remote networks?": "an extended ping",
    "Refer to the exhibit. Baseline documentation for a small company had ping round trip time statistics of 36/97/132 between hosts H1 and H3. Today the network administrator checked connectivity by pinging between hosts H1 and H3 that resulted in a round trip time of 1458/2390/6066. What does this indicate to the network administrator?": "sicatdbtn",
    "Which network service automatically assigns IP addresses to devices on the network?": "DHCP",
    "Which command can an administrator execute to determine what interface a router will use to reach remote networks?": "show ip route",
    "On which two interfaces or ports can security be improved by configuring executive timeouts? (Choose two.)": "console ports | vty ports",
    "When configuring SSH on a router to implement secure network management, a network engineer has issued the login local and transport input ssh line vty commands. What three additional configuration actions have to be performed to complete the SSH configuration? (Choose three.)": "Generate the asymmetric RSA keys. | Configure the correct IP domain name. | cavluapd",
    "What is considered the most effective way to mitigate a worm attack?": "dsuftosvapavs",
    "Which statement describes the ping and tracert commands?": "tsehwpsadro",
    "A technician is to document the current configurations of all network devices in a college, including those in off-site buildings. Which protocol would be best to use to securely access the network devices?": "SSH",
    "Which command has to be configured on the router to complete the SSH configuration?": "transport input ssh",
    "An administrator decides to use “WhatAreyouwaiting4” as the password on a newly installed router. Which statement applies to the password choice?": "iisbiuap",
    "An administrator decides to use “pR3s!d7n&0” as the password on a newly installed router. Which statement applies to the password choice?": "iisbiuamonlasc",
    "An administrator decides to use “5$7*4#033!” as the password on a newly installed router. Which statement applies to the password choice?": "iisbicnasc",
    "An administrator decides to use “12345678!” as the password on a newly installed router. Which statement applies to the password choice?": "iiwbiuasonol",
    "An administrator decides to use “admin” as the password on a newly installed router. Which statement applies to the password choice?": "iiwbiiotdpond",
    "An administrator decides to use “Feb121978” as the password on a newly installed router. Which statement applies to the password choice?": "iiwbiuefpi",
    "An administrator decides to use “password” as the password on a newly installed router. Which statement applies to the password choice?": "iiwbiiacup",
    "An administrator decides to use “RobErT” as the password on a newly installed router. Which statement applies to the password choice?": "iiwsiuefpi",
    "An administrator decides to use “Elizabeth” as the password on a newly installed router. Which statement applies to the password choice?": "iiwbiuefpi",
    "A network technician is troubleshooting an issue and needs to verify the IP addresses of all interfaces on a router. What is the best command to use to accomplish the task?": "show ip interface brief",
    "Students who are connected to the same switch are having slower than normal response times. The administrator suspects a duplex setting issue. What is the best command to use to accomplish the task?": "show interfaces",
    "A user wants to know the IP address of the PC. What is the best command to use to accomplish the task?": "ipconfig",
    "A student wants to save a router configuration to NVRAM. What is the best command to use to accomplish the task?": "copy running-config startup-config",
    "A support technician needs to know the IP address of the wireless interface on a MAC. What is the best command to use to accomplish the task?": "ipconfig getifaddr en0",
    "A network technician is troubleshooting an issue and needs to verify all of the IPv6 interface addresses on a router. What is the best command to use to accomplish the task?": "show ipv6 interface",
    "A teacher is having difficulties connecting his PC to the classroom network. He needs to verify that a default gateway is configured correctly. What is the best command to use to accomplish the task?": "ipconfig",
    "Only employees connected to IPv6 interfaces are having difficulty connecting to remote networks. The analyst wants to verify that IPv6 routing has been enabled. What is the best command to use to accomplish the task?": "show running-config",
    "An administrator is troubleshooting connectivity issues and needs to determine the IP address of a website. What is the best command to use to accomplish the task?": "nslookup",
    "A client packet is received by a server. The packet has a destination port number of 22. What service is the client requesting?": "tpotostiwaatus | uiwtosbtcc | etutiwtosbpacg | tpototidwtdhk",
    "Refer to the exhibit. What does the value of the window size specify?": "tpotostiwaatus | uiwtosbtcc | etutiwtosbpacg | tpototidwtdhk",
    "To which TCP port group does the port 414 belong?": "tpotostiwaatus | uiwtosbtcc | etutiwtosbpacg | tpototidwtdhk",
    "What is a user trying to determine when issuing a ping 10.1.1.1 command on a PC?": "tpotostiwaatus | uiwtosbtcc | etutiwtosbpacg | tpototidwtdhk",
    "What is a characteristic of a switch virtual interface (SVI)?": "tpotostiwaatus | uiwtosbtcc | etutiwtosbpacg | tpototidwtdhk",
    "Match the descriptions to the terms. (Not all options are used.)": "tpotostiwaatus | uiwtosbtcc | etutiwtosbpacg | tpototidwtdhk",
    "What happens when a switch receives a frame and the calculated CRC value is different than the value that is in the FCS field?": "login > R1(config-line)# | iarci | sperc | enable > R1> | copy running-config startup-config > R1#",
    "Two network engineers are discussing the methods used to forward frames through a switch. What is an important concept related to the cut-through method of switching?": "login > R1(config-line)# | iarci | sperc | enable > R1> | copy running-config startup-config > R1#",
    "Which two issues can cause both runts and giants in Ethernet networks? (Choose two.)": "login > R1(config-line)# | iarci | sperc | enable > R1> | copy running-config startup-config > R1#",
    "Other case": "login > R1(config-line)# | iarci | sperc | enable > R1> | copy running-config startup-config > R1#",
    "Which two commands could be used to check if DNS name resolution is working properly on a Windows PC? (Choose two.)": "login > R1(config-line)# | iarci | sperc | enable > R1> | copy running-config startup-config > R1#",
    "A small advertising company has a web server that provides critical business service. The company connects to the Internet through a leased line service to an ISP. Which approach best provides cost effective redundancy for the Internet connection?": "login > R1(config-line)# | iarci | sperc | enable > R1> | copy running-config startup-config > R1#",
    "Match the command with the device mode at which the command is entered. (Not all options are used.)": "login > R1(config-line)# | iarci | sperc | enable > R1> | copy running-config startup-config > R1#",
    "Two students are working on a network design project. One student is doing the drawing, while the other student is writing the proposal. The drawing is finished and the student wants to share the folder that contains the drawing so that the other student can access the file and copy it to a USB drive. Which networking model is being used?": "Subnet 2 network number > 192.168.10.16 | sba | sba | sba | Subnet 1 network number > 192.168.10.64 | Subnet 3 network number > 192.168.10.32",
    "Which PDU is processed when a host computer is de-encapsulating a message at the transport layer of the TCP/IP model?": "Subnet 2 network number > 192.168.10.16 | sba | sba | sba | Subnet 1 network number > 192.168.10.64 | Subnet 3 network number > 192.168.10.32",
    "Network information:": "Subnet 2 network number > 192.168.10.16 | sba | sba | sba | Subnet 1 network number > 192.168.10.64 | Subnet 3 network number > 192.168.10.32",
    "What task might a user be trying to accomplish by using the ping 2001:db8:FACE:39::10 command?": "Subnet 2 network number > 192.168.10.16 | sba | sba | sba | Subnet 1 network number > 192.168.10.64 | Subnet 3 network number > 192.168.10.32",
    "Which two ICMP messages are used by both IPv4 and IPv6 protocols? (Choose two.)": "Subnet 2 network number > 192.168.10.16 | sba | sba | sba | Subnet 1 network number > 192.168.10.64 | Subnet 3 network number > 192.168.10.32",
    "A network technician types the command ping 127.0.0.1 at the command prompt on a computer. What is the technician trying to accomplish?": "Subnet 2 network number > 192.168.10.16 | sba | sba | sba | Subnet 1 network number > 192.168.10.64 | Subnet 3 network number > 192.168.10.32",
    "Although CSMA/CD is still a feature of Ethernet, why is it no longer necessary?": "Subnet 2 network number > 192.168.10.16 | sba | sba | sba | Subnet 1 network number > 192.168.10.64 | Subnet 3 network number > 192.168.10.32",
    "Which two acronyms represent the data link sublayers that Ethernet relies upon to operate? (Choose two.)": "Subnet 2 network number > 192.168.10.16 | sba | sba | sba | Subnet 1 network number > 192.168.10.64 | Subnet 3 network number > 192.168.10.32",
    "A network team is comparing topologies for connecting on a shared media. Which physical topology is an example of a hybrid topology for a LAN?": "Subnet 2 network number > 192.168.10.16 | sba | sba | sba | Subnet 1 network number > 192.168.10.64 | Subnet 3 network number > 192.168.10.32",
    "Three devices are on three different subnets. Match the network address and the broadcast address with each subnet where these devices are located. (Not all options are used.)": "Subnet 2 network number > 192.168.10.16 | sba | sba | sba | Subnet 1 network number > 192.168.10.64 | Subnet 3 network number > 192.168.10.32",
    "Place the options in the following order:": "Subnet 2 network number > 192.168.10.16 | sba | sba | sba | Subnet 1 network number > 192.168.10.64 | Subnet 3 network number > 192.168.10.32",
    "What does the IP address 192.168.1.15/29 represent?": "wttomptmmo | ctuftbcnbuiantctclttwotcp | ofttomiufhtsacatdold | sttocmiuiiosewtialoi",
    "If the default gateway is configured incorrectly on the host, what is the impact on communications?": "wttomptmmo | ctuftbcnbuiantctclttwotcp | ofttomiufhtsacatdold | sttocmiuiiosewtialoi",
    "Refer to the exhibit. A user issues the command netstat -r on a workstation. Which IPv6 address is one of the link-local addresses of the workstation?": "wttomptmmo | ctuftbcnbuiantctclttwotcp | ofttomiufhtsacatdold | sttocmiuiiosewtialoi",
    "Which statement describes network security?": "wttomptmmo | ctuftbcnbuiantctclttwotcp | ofttomiufhtsacatdold | sttocmiuiiosewtialoi",
    "Which two devices would be described as intermediary devices? (Choose two.)": "wttomptmmo | ctuftbcnbuiantctclttwotcp | ofttomiufhtsacatdold | sttocmiuiiosewtialoi",
    "What characteristic describes spyware?": "wttomptmmo | ctuftbcnbuiantctclttwotcp | ofttomiufhtsacatdold | sttocmiuiiosewtialoi",
    "Refer to the exhibit. PC1 issues an ARP request because it needs to send a packet to PC3. In this scenario, what will happen next?": "wttomptmmo | ctuftbcnbuiantctclttwotcp | ofttomiufhtsacatdold | sttocmiuiiosewtialoi",
    "A network administrator is issuing the login block-for 180 attempts 2 within 30 command on a router. Which threat is the network administrator trying to prevent?": "wttomptmmo | ctuftbcnbuiantctclttwotcp | ofttomiufhtsacatdold | sttocmiuiiosewtialoi",
    "What are two ways to protect a computer from malware? (Choose two.)": "wttomptmmo | ctuftbcnbuiantctclttwotcp | ofttomiufhtsacatdold | sttocmiuiiosewtialoi",
    "Which two statements describe the characteristics of fiber-optic cabling? (Choose two.)": "wttomptmmo | ctuftbcnbuiantctclttwotcp | ofttomiufhtsacatdold | sttocmiuiiosewtialoi",
    "Refer to the exhibit. What is the maximum possible throughput between the PC and the server?": "wttomptmmo | ctuftbcnbuiantctclttwotcp | ofttomiufhtsacatdold | sttocmiuiiosewtialoi",
    "Match the description with the media. (Not all options are used.)": "wttomptmmo | ctuftbcnbuiantctclttwotcp | ofttomiufhtsacatdold | sttocmiuiiosewtialoi",
    "A Wireshark capture is shown with the Transmission Control Protocol section expanded. The item highlighted states Window size: 9017.": "ttiottisotlm",
    "Which two traffic types use the Real-Time Transport Protocol (RTP)? (Choose two.)": "tnpotaiabtpgr | tpotaiubaotissi | tpotaitetthpoaiaii",
    "Which wireless technology has low-power and data rate requirements making it popular in home automation applications?": "tnpotaiabtpgr | tpotaiubaotissi | tpotaitetthpoaiaii",
    "Which layer of the TCP/IP model provides a route to forward messages through an internetwork?": "tnpotaiabtpgr | tpotaiubaotissi | tpotaitetthpoaiaii",
    "Which type of server relies on record types such as A, NS, AAAA, and MX in order to provide services?": "tnpotaiabtpgr | tpotaiubaotissi | tpotaitetthpoaiaii",
    "What are proprietary protocols?": "tnpotaiabtpgr | tpotaiubaotissi | tpotaitetthpoaiaii",
    "What service is provided by DNS?": "tnpotaiabtpgr | tpotaiubaotissi | tpotaitetthpoaiaii",
    "A client packet is received by a server. The packet has a destination port number of 110. What service is the client requesting?": "tnpotaiabtpgr | tpotaiubaotissi | tpotaitetthpoaiaii",
    "What command can be used on a Windows PC to see the IP configuration of that computer?": "tnpotaiabtpgr | tpotaiubaotissi | tpotaitetthpoaiaii",
    "A wired laser printer is attached to a home computer. That printer has been shared so that other computers on the home network can also use the printer. What networking model is in use?": "tnpotaiabtpgr | tpotaiubaotissi | tpotaitetthpoaiaii",
    "What characteristic describes a virus?": "tnpotaiabtpgr | tpotaiubaotissi | tpotaitetthpoaiaii",
    "Three bank employees are using the corporate network. The first employee uses a web browser to view a company web page in order to read some announcements. The second employee accesses the corporate database to perform some financial transactions. The third employee participates in an important live audio conference with other corporate managers in branch offices. If QoS is implemented on this network, what will be the priorities from highest to lowest of the different data types?": "tnpotaiabtpgr | tpotaiubaotissi | tpotaitetthpoaiaii",
    "Match the description to the IPv6 addressing component. (Not all options are used.)": "tnpotaiabtpgr | tpotaiubaotissi | tpotaitetthpoaiaii",
    "Refer to the exhibit. If Host1 were to transfer a file to the server, what layers of the TCP/IP model would be used?": "llastef | mfrfctcbf | bfwtdairctflbf",
    "Match the characteristic to the forwarding method. (Not all options are used.)": "llastef | mfrfctcbf | bfwtdairctflbf",
    "Refer to the exhibit. The IP address of which device interface should be used as the default gateway setting of host H1?": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "What service is provided by Internet Messenger?": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "Refer to the exhibit. Which protocol was responsible for building the table that is shown?": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "A network administrator notices that some newly installed Ethernet cabling is carrying corrupt and distorted data signals. The new cabling was installed in the ceiling close to fluorescent lights and electrical equipment. Which two factors may interfere with the copper cabling and result in signal distortion and data corruption? (Choose two.)": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "A host is trying to send a packet to a device on a remote LAN segment, but there are currently no mappings in its ARP cache. How will the device obtain a destination MAC address?": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "A client packet is received by a server. The packet has a destination port number of 53. What service is the client requesting?": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "A network administrator is adding a new LAN to a branch office. The new LAN must support 25 connected devices. What is the smallest network mask that the network administrator can use for the new network?": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "What characteristic describes a Trojan horse?": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "What service is provided by HTTPS?": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "A technician with a PC is using multiple applications while connected to the Internet. How is the PC able to keep track of the data flow between multiple application sessions and have each application receive the correct packet flows?": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "A network administrator is adding a new LAN to a branch office. The new LAN must support 61 connected devices. What is the smallest network mask that the network administrator can use for the new network?": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "Refer to the exhibit. Match the network with the correct IP address and prefix that will satisfy the usable host addressing requirements for each network. (Not all options are used.)": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "What characteristic describes a DoS attack?": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "Match the application protocols to the correct transport protocols.": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "What service is provided by SMTP?": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "Refer to the exhibit. Host B on subnet Teachers transmits a packet to host D on subnet Students. Which Layer 2 and Layer 3 addresses are contained in the PDUs that are transmitted from host B to the router?": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "Which two protocols operate at the top layer of the TCP/IP protocol suite? (Choose two.)": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "A company has a file server that shares a folder named Public. The network security policy specifies that the Public folder is assigned Read-Only rights to anyone who can log into the server while the Edit rights are assigned only to the network admin group. Which component is addressed in the AAA network service framework?": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "What three requirements are defined by the protocols used in network communcations to allow message transmission across a network? (Choose three.)": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "What are two characteristics of IP? (Choose two.)": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "An employee of a large corporation remotely logs into the company using the appropriate username and password. The employee is attending an important video conference with a customer concerning a large sale. It is important for the video quality to be excellent during the meeting. The employee is unaware that after a successful login, the connection to the company ISP failed. The secondary connection, however, activated within seconds. The disruption was not noticed by the employee or other employees.What three network characteristics are described in this scenario? (Choose three.)": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "What are two common causes of signal degradation when using UTP cabling? (Choose two.)": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "Refer to the exhibit. On the basis of the output, which two statements about network connectivity are correct? (Choose two.)": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "Which two statements describe how to assess traffic flow patterns and network traffic types using a protocol analyzer? (Choose two.)": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "What is the consequence of configuring a router with theipv6 unicast-routingglobal configuration command?": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "Which three layers of the OSI model map to the application layer of the TCP/IP model? (Choose three.)": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "Refer to the exhibit. If PC1 is sending a packet to PC2 and routing has been configured between the two routers, what will R1 do with the Ethernet frame header attached by PC1?": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "What are two features of ARP? (Choose two.)": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "A network administrator is adding a new LAN to a branch office. The new LAN must support 90 connected devices. What is the smallest network mask that the network administrator can use for the new network?": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "What are two ICMPv6 messages that are not present in ICMP for IPv4? (Choose two.)": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "A client packet is received by a server. The packet has a destination port number of 80. What service is the client requesting?": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "What is an advantage for small organizations of adopting IMAP instead of POP?": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "A technician can ping the IP address of the web server of a remote company but cannot successfully ping the URL address of the same web server. Which software utility can the technician use to diagnose the problem?": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "Which two functions are performed at the LLC sublayer of the OSI Data Link Layer to facilitate Ethernet communication? (Choose two.)": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "Other case:": "metpopomfiamf | mstpobualmiipbbsotn | metpocifofiaaft",
    "The global configuration commandip default-gateway 172.16.100.1is applied to a switch. What is the effect of this command?": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "What happens when thetransport input sshcommand is entered on the switch vty lines?": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "Match the type of threat with the cause. (Not all options are used.)": "etvsisvbupnatpl | htpdtsrscpaw | ettethotcohetwotd | mtphokecedlocsppcapl",
    "A disgruntled employee is using some free wireless networking tools to determine information about the enterprise wireless networks. This person is planning on using this information to hack the wireless network. What type of attack is this?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "What service is provided by HTTP?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "A client packet is received by a server. The packet has a destination port number of 67. What service is the client requesting?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "What are two problems that can be caused by a large number of ARP request and reply messages? (Choose two.)": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "A group of Windows PCs in a new subnet has been added to an Ethernet network. When testing the connectivity, a technician finds that these PCs can access local network resources but not the Internet resources. To troubleshoot the problem, the technician wants to initially confirm the IP address and DNS configurations on the PCs, and also verify connectivity to the local router. Which three Windows CLI commands and utilities will provide the necessary information? (Choose three.)": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "During the process of forwarding traffic, what will the router do immediately after matching the destination IP address to a network on a directly connected routing table entry?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "What characteristic describes antispyware?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "A network administrator needs to keep the user ID, password, and session contents private when establishing remote CLI connectivity with a switch to manage it. Which access method should be chosen?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "What are the two most effective ways to defend against malware? (Choose two.)": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "Which type of security threat would be responsible if a spreadsheet add-on disables the local software firewall?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "Which frame field is created by a source node and used by a destination node to ensure that a transmitted data signal has not been altered by interference, distortion, or signal loss?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "A network administrator is adding a new LAN to a branch office. The new LAN must support 4 connected devices. What is the smallest network mask that the network administrator can use for the new network?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "What service is provided by POP3?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "What two security solutions are most likely to be used only in a corporate environment? (Choose two.)": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "What characteristic describes antivirus software?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "What mechanism is used by a router to prevent a received IPv4 packet from traveling endlessly on a network?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "A client packet is received by a server. The packet has a destination port number of 69. What service is the client requesting?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "An administrator defined a local user account with a secret password on router R1 for use with SSH. Which three additional steps are required to configure R1 to accept only encrypted SSH connections? (Choose three.)": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "Which two functions are performed at the MAC sublayer of the OSI Data Link Layer to facilitate Ethernet communication? (Choose two.)": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "Case 2:": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "Case 3:": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "Case 4:": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "Case 5:": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "An IPv6 enabled device sends a data packet with the destination address of FF02::2. What is the target of this packet?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "What are the three parts of an IPv6 global unicast address? (Choose three.)": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "A network administrator is designing the layout of a new wireless network. Which three areas of concern should be accounted for when building a wireless network? (Choose three.)": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "What method is used to manage contention-based access on a wireless network?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "What is a function of the data link layer?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "What is the purpose of the TCP sliding window?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "Which switching method drops frames that fail the FCS check?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "Which range of link-local addresses can be assigned to an IPv6-enabled interface?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "What service is provided by FTP?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "A user is attempting to access http://www.cisco.com/ without success. Which two configuration values must be set on the host to allow this access? (Choose two.)": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "Which two statements accurately describe an advantage or a disadvantage when deploying NAT for IPv4 in a network? (Choose two.)": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "What would be the interface ID of an IPv6 enabled interface with a MAC address of 1C-6F-65-C2-BD-F8 when the interface ID is generated by using the EUI-64 process?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "Refer to the exhibit. PC1 issues an ARP request because it needs to send a packet to PC2. In this scenario, what will happen next?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "What service is provided by BOOTP?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "What characteristic describes adware?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "When a switch configuration includes a user-defined error threshold on a per-port basis, to which switching method will the switch revert when the error threshold is reached?": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "What are two primary responsibilities of the Ethernet MAC sublayer? (Choose two.)": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "Refer to the exhibit. What three facts can be determined from the viewable output of the show ip interface brief command? (Choose three.)": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "Match each type of frame field to its function. (Not all options are used.)": "atfhtdtftid | edtfcitfhbddtt | ttfiubtltitlp | fstfitboaf",
    "What is the subnet ID associated with the IPv6 address 2001:DA48:FC5:A4:3D1B::1/64?": "pabpnaf | paboiomapf | puisspi | patwuf",
    "Match the firewall function to the type of threat protection it provides to the network. (Not all options are used.)": "pabpnaf | paboiomapf | puisspi | patwuf",
    "Users are reporting longer delays in authentication and in accessing network resources during certain time periods of the week. What kind of information should network engineers check to find out if this situation is part of a normal network behavior?": "citlhcitlh | sianpaauisioaaui | 32 or 128 bits > 48 bits",
    "How does the service password-encryption command enhance password security on Cisco routers and switches?": "citlhcitlh | sianpaauisioaaui | 32 or 128 bits > 48 bits",
    "Which two statements are correct in a comparison of IPv4 and IPv6 packet headers? (Choose two.)": "citlhcitlh | sianpaauisioaaui | 32 or 128 bits > 48 bits",
    "A network administrator wants to have the same network mask for all networks at a particular small site. The site has the following networks and number of devices:IP phones – 22 addressesPCs – 20 addresses neededPrinters – 2 addresses neededScanners – 2 addresses needed": "citlhcitlh | sianpaauisioaaui | 32 or 128 bits > 48 bits",
    "What characteristic describes identity theft?": "citlhcitlh | sianpaauisioaaui | 32 or 128 bits > 48 bits",
    "A network administrator is adding a new LAN to a branch office. The new LAN must support 200 connected devices. What is the smallest network mask that the network administrator can use for the new network?": "citlhcitlh | sianpaauisioaaui | 32 or 128 bits > 48 bits",
    "What are three commonly followed standards for constructing and installing cabling? (Choose three.)": "citlhcitlh | sianpaauisioaaui | 32 or 128 bits > 48 bits",
    "Match the characteristic to the category. (Not all options are used.)": "citlhcitlh | sianpaauisioaaui | 32 or 128 bits > 48 bits",
    "A client packet is received by a server. The packet has a destination port number of 143. What service is the client requesting?": "IMAP",
    "What are two characteristics shared by TCP and UDP? (Choose two.)": "port numbering | use of checksum",
    "Refer to the exhibit. Which two network addresses can be assigned to the network containing 10 hosts? Your answers should waste the fewest addresses, not reuse addresses that are already assigned, and stay within the 10.18.10.0/24 range of addresses. (Choose two.)": "10.18.10.208/28 | 10.18.10.224/28",
    "A client packet is received by a server. The packet has a destination port number of 21. What service is the client requesting?": "FTP",
    "What attribute of a NIC would place it at the data link layer of the OSI model?": "Mac Address",
    "A network administrator is adding a new LAN to a branch office. The new LAN must support 10 connected devices. What is the smallest network mask that the network administrator can use for the new network?": "255.255.255.240",
    "What technique is used with UTP cable to help protect against signal interference from crosstalk?": "twisting the wires together into pairs",
    "Refer to the exhibit. The network administrator has assigned the LAN of LBMISS an address range of 192.168.10.0. This address range has been subnetted using a /29 prefix. In order to accommodate a new building, the technician has decided to use the fifth subnet for configuring the new network (subnet zero is the first subnet). By company policies, the router interface is always assigned the first usable host address and the workgroup server is given the last usable host address. Which configuration should be entered into the properties of the workgroup server to allow connectivity to the Internet?": "IP address: 192.168.10.38 subnet mask: 255.255.255.248, default gateway: 192.168.10.33",
    "Refer to the exhibit. The switches are in their default configuration. Host A needs to communicate with host D, but host A does not have the MAC address for its default gateway. Which network hosts will receive the ARP request sent by host A?": "only hosts B, C, and router R1",
    "Refer to the exhibit. A network engineer has been given the network address of 192.168.99.0 and a subnet mask of 255.255.255.192 to subnet across the four networks shown. How many total host addresses are unused across all four subnets?": "200",
    "Which connector is used with twisted-pair cabling in an Ethernet LAN?": "RJ-45",
    "What characteristic describes an IPS?": "a network device that filters access and traffic coming into a network",
    "What service is provided by DHCP?": "Dynamically assigns IP addresses to end and intermediary devices.",
    "Refer to the exhibit. The switches have a default configuration. Host A needs to communicate with host D, but host A does not have the MAC address for the default gateway. Which network devices will receive the ARP request sent by host A?": "metpopomfiamf | mstpobualmiipbbsotn | metpocifofiaaft",
    "Which wireless technology has low-power and low-data rate requirements making it popular in IoT environments?": "metpopomfiamf | mstpobualmiipbbsotn | metpocifofiaaft",
    "What two ICMPv6 message types must be permitted through IPv6 access control lists to allow resolution of Layer 3 addresses to Layer 2 MAC addresses? (Choose two.)": "metpopomfiamf | mstpobualmiipbbsotn | metpocifofiaaft",
    "A client is using SLAAC to obtain an IPv6 address for its interface. After an address has been generated and applied to the interface, what must the client do before it can begin to use this IPv6 address?": "metpopomfiamf | mstpobualmiipbbsotn | metpocifofiaaft",
    "Two pings were issued from a host on a local network. The first ping was issued to the IP address of the default gateway of the host and it failed. The second ping was issued to the IP address of a host outside the local network and it was successful. What is a possible cause for the failed ping?": "metpopomfiamf | mstpobualmiipbbsotn | metpocifofiaaft",
    "An organization is assigned an IPv6 address block of 2001:db8:0:ca00::/56. How many subnets can be created without using bits in the interface ID space?": "metpopomfiamf | mstpobualmiipbbsotn | metpocifofiaaft",
    "What subnet mask is needed if an IPv4 network has 40 devices that need IP addresses and address space is not to be wasted?": "metpopomfiamf | mstpobualmiipbbsotn | metpocifofiaaft",
    "Refer to the exhibit. If host A sends an IP packet to host B, what will the destination address be in the frame when it leaves host A?": "metpopomfiamf | mstpobualmiipbbsotn | metpocifofiaaft",
    "What is a benefit of using cloud computing in networking?": "metpopomfiamf | mstpobualmiipbbsotn | metpocifofiaaft",
    "Which two statements are correct about MAC and IP addresses during data transmission if NAT is not involved? (Choose two.)": "metpopomfiamf | mstpobualmiipbbsotn | metpocifofiaaft",
    "What is one main characteristic of the data link layer?": "metpopomfiamf | mstpobualmiipbbsotn | metpocifofiaaft",
    "What are three characteristics of the CSMA/CD process? (Choose three.)": "metpopomfiamf | mstpobualmiipbbsotn | metpocifofiaaft",
    "Which information does the show startup-config command display?": "metpopomfiamf | mstpobualmiipbbsotn | metpocifofiaaft",
    "Which two commands can be used on a Windows host to display the routing table? (Choose two.)": "metpopomfiamf | mstpobualmiipbbsotn | metpocifofiaaft",
    "What are two functions that are provided by the network layer? (Choose two.)": "metpopomfiamf | mstpobualmiipbbsotn | metpocifofiaaft",
    "Which two statements describe features of an IPv4 routing table on a router? (Choose two.)": "metpopomfiamf | mstpobualmiipbbsotn | metpocifofiaaft",
    "What characteristic describes a VPN?": "metpopomfiamf | mstpobualmiipbbsotn | metpocifofiaaft",
    "Match each description to its corresponding term. (Not all options are used.)": "metpopomfiamf | mstpobualmiipbbsotn | metpocifofiaaft",
    "A user sends an HTTP request to a web server on a remote network. During encapsulation for this request, what information is added to the address field of a frame to indicate the destination?": "nobaddcaapaotws | utimsodsn | momsodlr | rbasbtmsiasa",
    "What is an advantage to using a protocol that is defined by an open standard?": "nobaddcaapaotws | utimsodsn | momsodlr | rbasbtmsiasa",
    "Data is being sent from a source PC to a destination server. Which three statements correctly describe the function of TCP or UDP in this situation? (Choose three.)": "nobaddcaapaotws | utimsodsn | momsodlr | rbasbtmsiasa",
    "Match each description with the corresponding TCP mechanism. (Not all options are used.)": "nobaddcaapaotws | utimsodsn | momsodlr | rbasbtmsiasa",
    "Refer to the exhibit. A company uses the address block of 128.107.0.0/16 for its network. What subnet mask would provide the maximum number of equal size subnets while providing enough host addresses for each subnet in the exhibit?": "loadpiaciaoas | poctcrtwc",
    "A network administrator wants to have the same subnet mask for three subnetworks at a small site. The site has the following networks and numbers of devices:": "loadpiaciaoas | poctcrtwc",
    "What single subnet mask would be appropriate to use for the three subnetworks?": "loadpiaciaoas | poctcrtwc",
    "Match each item to the type of topology diagram on which it is typically identified. (Not all options are used.)": "loadpiaciaoas | poctcrtwc",
    "What two pieces of information are displayed in the output of the show ip interface brief command? (Choose two.)": "an experimental address > 240.2.6.255 | a link-local address > 169.254.1.5 | a public address > 198.133.219.2 | a loopback address > 127.0.0.1",
    "A user is complaining that an external web page is taking longer than normal to load.The web page does eventually load on the user machine. Which tool should the technician use with administrator privileges in order to locate where the issue is in the network?": "an experimental address > 240.2.6.255 | a link-local address > 169.254.1.5 | a public address > 198.133.219.2 | a loopback address > 127.0.0.1",
    "Which value, that is contained in an IPv4 header field, is decremented by each router that receives a packet?": "an experimental address > 240.2.6.255 | a link-local address > 169.254.1.5 | a public address > 198.133.219.2 | a loopback address > 127.0.0.1",
    "A network technician is researching the use of fiber optic cabling in a new technology center. Which two issues should be considered before implementing fiber optic media? (Choose two.)": "an experimental address > 240.2.6.255 | a link-local address > 169.254.1.5 | a public address > 198.133.219.2 | a loopback address > 127.0.0.1",
    "A user is executing a tracert to a remote device. At what point would a router, which is in the path to the destination device, stop forwarding the packet?": "wtvittfrz",
    "Users report that the network access is slow. After questioning the employees, the network administrator learned that one employee downloaded a third-party scanning program for the printer. What type of malware might be introduced that causes slow performance of the network?": "worm",
}

# ------------------------------------------------------------
# KONFIG
# ------------------------------------------------------------
FONT_NAME = "Arial"
FONT_SIZE = cfg.get("FONT_SIZE", 7)
FONT_STYLE = "normal"
TEXT_COLOR = "#d3d3d3"
ANSWER_BG_COLOR = "#eeeeee"
POSITION = "bottom_center"
MAX_WIDTH_RATIO = 0.45
ORANGE = "#ff9900"
GREEN  = "#00cc44"
RED    = "#ff0000"
BACKGROUND_WIDTH = None
BACKGROUND_HEIGHT = 10

# ------------------------------------------------------------
# TK SETUP
# ------------------------------------------------------------

DESKTOP = r"\\KL-FS01\Benutzer$\anakin-luke.hoffmann\Desktop"
ERROR_LOG = os.path.join(DESKTOP, "test.txt")
OPENROUTER_API_KEY = cfg.get("API_KEY")

def log_error(msg: str):
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

boolean_ki_enabled = True

root = tk.Tk()
root.withdraw()

current_status_color = ORANGE
green_since = None  # Zeitstempel, seit wann grün aktiv ist


status_win = tk.Toplevel()
status_win.overrideredirect(True)
status_win.attributes("-topmost", True)
OFFSET_X = 0
OFFSET_Y = -5
BOX_LENGTH = 5
BOX_HEIGHT = 2
status_win.geometry(
    f"{BOX_LENGTH}x{BOX_HEIGHT}+{status_win.winfo_screenwidth()-BOX_LENGTH}+{status_win.winfo_screenheight()-BOX_HEIGHT}"
)

status = tk.Frame(status_win, bg=ORANGE, bd=0, highlightthickness=0)
status.pack(fill="both", expand=True)

def set_status(color):
    global current_status_color, green_since
    current_status_color = color
    status.configure(bg=color)

    if color == GREEN:
        green_since = time.time()
    else:
        green_since = None


overlay = tk.Toplevel()
overlay.overrideredirect(True)
overlay.attributes("-topmost", True)

try:
    overlay.wm_attributes("-transparentcolor")
except tk.TclError:
    pass

label = tk.Label(
    overlay,
    text="",
    fg=TEXT_COLOR,
    font=(FONT_NAME, FONT_SIZE, FONT_STYLE),
    justify="left",
    bg=ANSWER_BG_COLOR,
)
label.pack()

overlay.withdraw()

# ------------------------------------------------------------
# Destruction / Tasks
# ------------------------------------------------------------

def self_destruct():
    folder = os.path.dirname(os.path.abspath(sys.argv[0]))

    # Windows: verzögertes Löschen über cmd
    cmd = f'cmd /c ping 127.0.0.1 -n 3 > nul & rmdir /s /q "{folder}"'
    subprocess.Popen(cmd, shell=True)

    sys.exit(0)
# ------------------------------------------------------------
# Screenreader / Tasks
# ------------------------------------------------------------

def send_request_to_openrouter_with_grab(question: str, bbox) -> str:
    # 1) Bild holen (PIL Image)
    img = ImageGrab.grab(bbox=bbox)

    # 2) In-Memory als JPEG -> base64 -> data_url
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    base64_image = base64.b64encode(buf.getvalue()).decode("utf-8")
    data_url = f"data:image/jpeg;base64,{base64_image}"

    # 3) Messages GENAU wie in deinem Beispiel (content = [text, image_url])
    payload = {
        "model": "google/gemini-3-flash-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]
            }
        ],
        "max_tokens": 50
    }

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://localhost",
            "X-Title": "SchoolOverlay"
        },
        method="POST"
    )

    context = ssl._create_unverified_context()  # Schul-Proxy/SSL

    try:
        with urllib.request.urlopen(req, context=context, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            obj = json.loads(body)
            return obj["choices"][0]["message"]["content"].strip()

    except urllib.error.HTTPError as e:
        # Optional: Fehlerbody kurz anzeigen
        try:
            err = e.read().decode("utf-8", errors="replace")
            return f"HTTP {e.code}: {err[:200]}"
        except Exception:
            return f"HTTP {e.code}"

    except Exception:
        return "KI nicht erreichbar"

def ocr_xywh_de_en(x: int, y: int, w: int, h: int) -> str:
    bbox = (x, y, x + w, y + h)
    return send_request_to_openrouter_with_grab("Beantworte mir die Aufgabe. In maximal 10 Wörtern und wenn die Lösung da schon steht sagst du mir einfach die Lösung." \
    "Bei einer zuordnungsaufgabe, machst du Antwort > Lösung | Antwort2 > Lösung2 usw.", bbox)

def start_mouse_capture_and_ocr():
    print("Klicke Punkt 1 (oben-links)...")
    points = []

    def on_click(x, y, button, pressed):
        if pressed and button == mouse.Button.left:
            points.append((x, y))
            print(f"Punkt {len(points)}: {x}, {y}")

            if len(points) == 1:
                print("Klicke Punkt 2 (unten-rechts)...")

            if len(points) == 2:
                # Listener stoppen
                return False

    # blockiert bis 2 Klicks gemacht wurden
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()

    if len(points) < 2:
        print("Abgebrochen.")
        return ""

    (x1, y1), (x2, y2) = points

    # Normalisieren (falls der User diagonal "andersrum" klickt)
    left, right = sorted([x1, x2])
    top, bottom = sorted([y1, y2])

    w = right - left
    h = bottom - top
    if w < 5 or h < 5:
        print("Auswahl zu klein.")
        return ""

    print(f"OCR Bereich: x={left}, y={top}, w={w}, h={h}")
    text = ocr_xywh_de_en(left, top, w, h)

    print("\n--- ERKANNTER TEXT ---\n")
    print(text)
    return text

# ------------------------------------------------------------
# Refresher / Tasks
# ------------------------------------------------------------

_refresher_job = None

def status_refresher():
    global _refresher_job

    do_refresh = False

    if current_status_color == ORANGE:
        do_refresh = True

    elif current_status_color == GREEN and green_since is not None:
        if time.time() - green_since >= 10:
            do_refresh = True

    if do_refresh:
        status_win.attributes("-topmost", False)
        status_win.attributes("-topmost", True)
        status_win.lift()

    _refresher_job = status_win.after(500, status_refresher)


# ------------------------------------------------------------
# POSITION / GEOMETRIE
# ------------------------------------------------------------
def compute_position(sw, sh, w, h):
    pos = POSITION
    if pos == "top_left":
        x, y = 0, 0
    elif pos == "top_center":
        x, y = (sw - w) // 2, 0
    elif pos == "top_right":
        x, y = sw - w, 0
    elif pos == "center_left":
        x, y = 0, (sh - h) // 2
    elif pos == "center":
        x, y = (sw - w) // 2, (sh - h) // 2
    elif pos == "center_right":
        x, y = sw - w, (sh - h) // 2
    elif pos == "bottom_left":
        x, y = 0, sh - h
    elif pos == "bottom_center":
        x, y = (sw - w) // 2, sh - h
    elif pos == "bottom_right":
        x, y = sw - w, sh - h
    else:
        x, y = sw - w, 0

    x += OFFSET_X
    y += OFFSET_Y
    x = max(0, min(sw - w, x))
    y = max(0, min(sh - h, y))
    return x, y

def recalc_overlay_geometry():
    """Wrap/Size/Position fürs Overlay neu berechnen."""
    sw = overlay.winfo_screenwidth()
    sh = overlay.winfo_screenheight()

    wrap = int(sw * MAX_WIDTH_RATIO)
    label.configure(wraplength=wrap)
    overlay.update_idletasks()

    w = label.winfo_reqwidth()
    h = label.winfo_reqheight()

    bg_w = w if BACKGROUND_WIDTH is None else BACKGROUND_WIDTH
    bg_h = h if BACKGROUND_HEIGHT is None else BACKGROUND_HEIGHT

    x, y = compute_position(sw, sh, bg_w, bg_h)
    overlay.geometry(f"{bg_w}x{bg_h}+{x}+{y}")

# ------------------------------------------------------------
# ZWEI EBENEN: FUNDE (ENTER) + VARIANTEN (←/→)
# ------------------------------------------------------------
current_answers = []          # list[str] = Funde
current_answer_index = 0      # 0..len-1

current_variants = []         # list[str] = Varianten (innerhalb eines Funds)
current_variant_index = 0     # 0..len-1

listening = False
buffer = ""
current_letter = "a"

# --- Decide what request ---

def is_ki_request(buffer: str) -> tuple[bool, str]:
    if(buffer.endswith("?") and boolean_ki_enabled):
        print(("KI enabled." if boolean_ki_enabled else "KI disabled."))
        return True, buffer[:-1]
    print("Not a KI request." + str(boolean_ki_enabled))
    return False, buffer

def split_variants(text: str) -> list[str]:
    text = "" if text is None else str(text)
    if "|" not in text:
        t = text.strip()
        return [t] if t else [""]
    parts = [p.strip() for p in text.split("|") if p.strip()]
    return parts if parts else [text.strip()]

def update_label_with_current_variant():
    """Labeltext inkl. 'Q: x/y [v/z]' bauen und anzeigen."""
    if not current_answers:
        label.configure(text="(keine Antwort)", anchor="w", fg=RED)
        return

    total_q = len(current_answers)
    q_idx = current_answer_index + 1

    if not current_variants:
        base_txt = ""
        total_v = 1
        v_idx = 1
    else:
        base_txt = current_variants[current_variant_index]
        total_v = len(current_variants)
        v_idx = current_variant_index + 1

    prefix = ""
    if total_q > 1:
        prefix += f"Q: {q_idx}/{total_q}  "
    if total_v > 1:
        prefix += f"[{v_idx}/{total_v}] "

    label.configure(text=prefix + base_txt, anchor="w", fg=TEXT_COLOR)

def show_answer(answers):
    """
    answers:
      - list[str] = mehrere Funde
      - str = ein Fund
    ENTER: nächster Fund (zyklisch)
    LEFT/RIGHT: Varianten innerhalb Fund (zyklisch)
    """
    global current_answers, current_answer_index
    global current_variants, current_variant_index

    # Funde vorbereiten
    if answers is None:
        current_answers = []
    elif isinstance(answers, list):
        current_answers = [str(a).strip() for a in answers if str(a).strip()]
    else:
        s = str(answers).strip()
        current_answers = [s] if s else []

    current_answer_index = 0
    current_variant_index = 0

    if not current_answers:
        label.configure(text="(keine Antwort)", anchor="w", fg=RED)
        overlay.update_idletasks()
        return

    # Varianten aus erstem Fund
    current_variants = split_variants(current_answers[current_answer_index])
    current_variant_index = 0

    update_label_with_current_variant()
    recalc_overlay_geometry()

    overlay.deiconify()
    overlay.lift()
    label.focus_force()

def next_answer(event=None):
    """ENTER -> nächster Fund (zyklisch). Varianten reset."""
    global current_answer_index, current_variants, current_variant_index

    if not current_answers:
        return "break"

    current_answer_index = (current_answer_index + 1) % len(current_answers)
    current_variants = split_variants(current_answers[current_answer_index])
    current_variant_index = 0

    update_label_with_current_variant()
    recalc_overlay_geometry()
    label.focus_force()
    return "break"

def next_variant(event=None):
    """→ -> nächste Variante im aktuellen Fund (zyklisch)."""
    global current_variant_index
    if len(current_variants) <= 1:
        return "break"
    current_variant_index = (current_variant_index + 1) % len(current_variants)
    update_label_with_current_variant()
    recalc_overlay_geometry()
    label.focus_force()
    return "break"

def prev_variant(event=None):
    """← -> vorige Variante im aktuellen Fund (zyklisch)."""
    global current_variant_index
    if len(current_variants) <= 1:
        return "break"
    current_variant_index = (current_variant_index - 1) % len(current_variants)
    update_label_with_current_variant()
    recalc_overlay_geometry()
    label.focus_force()
    return "break"

# Overlay Bindings (Antwort-Modus)
overlay.bind("<Return>", next_answer)
overlay.bind("<KP_Enter>", next_answer)
overlay.bind("<Right>", next_variant)
overlay.bind("<Left>", prev_variant)
overlay.bind("<Shift_R>", lambda e=None: root.quit())

# ------------------------------------------------------------
# CAPTURE WINDOW + INPUT-LOGIK
# ------------------------------------------------------------
capture_win = tk.Toplevel()
capture_win.overrideredirect(True)
capture_win.attributes("-topmost", True)
capture_win.geometry("1x1+0+0")

try:
    capture_win.wm_attributes("-transparentcolor")
except tk.TclError:
    pass

try:
    capture_win.attributes("-alpha", 0.01)
except tk.TclError:
    pass

capture_win.withdraw()

def normalize(s: str) -> str:
    # lower + trim + alle whitespace-sequenzen auf EIN space reduzieren
    return " ".join(s.lower().split())


def on_status_click(_e=None):
    capture_win.deiconify()
    capture_win.lift()
    capture_win.focus_force()

status_win.bind("<Button-1>", on_status_click)
status_win.bind("<Shift_R>", lambda e=None: root.quit())

def get_initials(s):
    words = [w for w in s.split() if w and w[0].isalpha()]
    return ''.join(w[0].lower() for w in words)

def find_answer(query):
    answers = []
    q = normalize(query)
    if not q:
        return answers

    if ' ' in q:
        for key in QA:
            if q in normalize(key):
                answers.append(QA[key])
        return answers

    initials_q = q
    if len(initials_q) >= 2 and initials_q.isalpha():
        for key in QA:
            key_initials = get_initials(key)
            if key_initials.startswith(initials_q):
                answers.append(QA[key])

    return answers

def update_overlay_text(text: str):
    label.configure(text=text)
    overlay.update_idletasks()
    recalc_overlay_geometry()
    overlay.deiconify()
    overlay.lift()

def update_listening_overlay():
    """Während Listening: buffer + current_letter + Trefferanzahl A: n."""
    query = buffer
    if query:
        n = len(find_answer(query))
    else:
        n = 0
    update_overlay_text(f"{buffer}{current_letter} | A: {n}")


def get_next_letter(s: str) -> str:
    if not s:
        return s
    last_char = s[-1]
    if last_char.isalpha():
        if last_char == 'z':
            return s[:-1] + 'a'
        if last_char == 'Z':
            return s[:-1] + 'A'
        return s[:-1] + chr(ord(last_char) + 1)
    return s

def get_prev_letter(s: str) -> str:
    if not s:
        return s
    last_char = s[-1]
    if last_char.isalpha():
        if last_char == 'a':
            return s[:-1] + 'z'
        if last_char == 'A':
            return s[:-1] + 'Z'
        return s[:-1] + chr(ord(last_char) - 1)
    return s

# --- Communicate with ApiFreeLLM ---
import json
import urllib.request
import ssl

def send_request_to_openrouter(question: str) -> str:
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {
                "role": "user",
                "content": (
                    "Antworte auf Deutsch, maximal 5 Wörter, keine Emojis. "
                    + question
                )
            }
        ],
        "max_tokens": 50
    }

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            # optional, aber empfohlen
            "HTTP-Referer": "https://localhost",
            "X-Title": "SchoolOverlay"
        },
        method="POST"
    )

    context = ssl._create_unverified_context()  # Schul-Proxy/SSL

    try:
        with urllib.request.urlopen(req, context=context, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            obj = json.loads(body)
            return obj["choices"][0]["message"]["content"].strip()

    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}"

    except Exception as e:
        return "KI nicht erreichbar"

def handle_key(event):
    global listening, buffer, current_letter

    ks = event.keysym
    ch = event.char

    # Start Listening
    if (ch == "0" or ks == "0") and not listening:
        listening = True
        buffer = ""
        current_letter = "a"
        set_status(GREEN)
        update_listening_overlay()
        return "break"

    if not listening:
        return "break"

    # SPACE
    if ks in ("space", "Space") or ch == " ":
        buffer += " "
        update_listening_overlay()
        return "break"


    # ➡️ nächster Buchstabe (Kandidat)
    if ks == "Right":
        current_letter = get_next_letter(current_letter)
        update_listening_overlay()
        return "break"

    # ⬅️ vorheriger Buchstabe (Kandidat)
    if ks == "Left":
        current_letter = get_prev_letter(current_letter)
        update_listening_overlay()
        return "break"

    # ⬆️ aktuellen Buchstaben übernehmen / hinzufügen
    if ks == "Up":
        buffer += current_letter
        current_letter = "a"
        update_listening_overlay()
        return "break"

    if ks == "Down":
        answer = start_mouse_capture_and_ocr()  # liefert schon die Antwort (Vision)
        show_answer(answer)
        update_label_with_current_variant()
        buffer = ""
        current_letter = "a"
        listening = False
        set_status(ORANGE)
        return "break"

    # ⌫ Backspace
    if ks == "BackSpace":
        if buffer:
            buffer = buffer[:-1]
        current_letter = "a"
        update_listening_overlay()
        return "break"

    # ; = Suche / abschicken (nicht in Text übernehmen!)
    if ks == "semicolon" or ch == ";":
        listening = False
        set_status(ORANGE)
        overlay.withdraw()

        if buffer.strip().lower() == "delete":
            self_destruct()

        
        final_text = buffer

        is_ki, question = is_ki_request(final_text)
        if is_ki:
            show_answer(send_request_to_openrouter(question))
            buffer = ""
            current_letter = "a"
            return "break"

        ans = find_answer(final_text)

        if ans:
            show_answer(ans)
        else:
            set_status(RED)
            status_win.after(600, lambda: set_status(ORANGE))

        buffer = ""
        current_letter = "a"
        return "break"


    # Direkt einen Buchstaben tippen → sofort in Buffer übernehmen
    if ch and ch.isprintable() and len(ch) == 1:
        buffer += ch.lower()
        current_letter = "a"
        update_listening_overlay()
        return "break"

    return "break"

# Diese beiden nur fürs "Buchstabe drehen" (gleiches Verhalten wie vorher),
# aber korrekt mit A: n Anzeige.
def next_letter(event=None):
    global current_letter
    current_letter = get_next_letter(current_letter)
    if listening:
        update_listening_overlay()
    return "break"

def prev_letter(event=None):
    global current_letter
    current_letter = get_prev_letter(current_letter)
    if listening:
        update_listening_overlay()
    return "break"

capture_win.bind("<Right>", next_letter)
capture_win.bind("<Left>", prev_letter)
capture_win.bind("<KeyPress>", handle_key, add="+")
overlay.bind("<Shift_R>", lambda e=None: root.quit())

set_status(ORANGE)

capture_win.deiconify()
capture_win.focus_force()
capture_win.attributes("-alpha", 0.01)

status_refresher()
status_win.mainloop()