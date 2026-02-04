import tkinter as tk

QA = {
    "test est st t": "Windows Updates",
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
    "Refer to the exhibit. A network administrator is connecting a new host to the Medical LAN. The host needs to communicate with remote networks. What IP address would be configured as the default gateway on the new host?": "192.168.201.200"
}

FONT_NAME = "Arial"
FONT_SIZE = 7
FONT_STYLE = "normal"
TEXT_COLOR = "gray"
ANSWER_BG_COLOR = "white"
POSITION = "bottom_left"
OFFSET_X = 50
OFFSET_Y = 10
MAX_WIDTH_RATIO = 0.45
ORANGE = "#ff9900"
GREEN  = "#00cc44"
RED    = "#ff0000"
BACKGROUND_WIDTH = None
BACKGROUND_HEIGHT = 10

root = tk.Tk()
root.withdraw()

status_win = tk.Toplevel()
status_win.overrideredirect(True)
status_win.attributes("-topmost", True)
status_win.geometry("2x1+0+0")

status = tk.Frame(status_win, bg=ORANGE, bd=0, highlightthickness=0)
status.pack(fill="both", expand=True)

def set_status(color):
    status.configure(bg=color)

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

# ────────────────────────────────────────────────
# Neue globale Variablen (am besten ganz oben nach den anderen Konstanten)
# ────────────────────────────────────────────────

current_variants = []
current_variant_index = 0

# ────────────────────────────────────────────────
# Hilfsfunktion: Antwort splitten und bereinigen
# ────────────────────────────────────────────────

def split_variants(text: str) -> list[str]:
    if '|' not in text:
        return [text.strip()]
    
    parts = [p.strip() for p in text.split('|') if p.strip()]
    return parts if parts else [text.strip()]

# ────────────────────────────────────────────────
# Angepasste show_answer Funktion
# ────────────────────────────────────────────────

def show_answer(text: str):
    global current_variants, current_variant_index
    
    current_variants = split_variants(text)
    current_variant_index = 0
    
    if not current_variants:
        label.configure(text="(keine Antwort)", anchor="w", fg=RED)
        overlay.update_idletasks()
        return
    
    # Erste Variante anzeigen
    update_label_with_current_variant()
    
    # Position neu berechnen & sichtbar machen
    sw = overlay.winfo_screenwidth()
    sh = overlay.winfo_screenheight()
    wrap = int(sw * MAX_WIDTH_RATIO)
    label.configure(wraplength=wrap)
    overlay.update_idletasks()
    
    w = label.winfo_reqwidth()
    h = label.winfo_reqheight()
    background_width = w if BACKGROUND_WIDTH is None else BACKGROUND_WIDTH
    background_height = h if BACKGROUND_HEIGHT is None else BACKGROUND_HEIGHT
    
    x, y = compute_position(sw, sh, background_width, background_height)
    overlay.geometry(f"{background_width}x{background_height}+{x}+{y}")
    overlay.deiconify()
    overlay.lift()
    label.focus_force()

# ────────────────────────────────────────────────
# Label mit aktueller Variante aktualisieren
# ────────────────────────────────────────────────

def update_label_with_current_variant():
    if not current_variants:
        label.configure(text="")
        return

    txt = current_variants[current_variant_index]

    # Optional: Index + Gesamtanzahl anzeigen, wenn > 1 Variante
    if len(current_variants) > 1:
        txt = f"[{current_variant_index+1}/{len(current_variants)}]  {txt}"

    # <-- FEHLT: wirklich ins Label schreiben
    label.configure(text=txt, anchor="w")


# ────────────────────────────────────────────────
# Wechsel zur nächsten Variante (Zyklisch)
# ────────────────────────────────────────────────

def next_variant(event=None):
    global current_variant_index
    if len(current_variants) <= 1:
        return

    current_variant_index = (current_variant_index + 1) % len(current_variants)
    update_label_with_current_variant()

    sw = overlay.winfo_screenwidth()
    sh = overlay.winfo_screenheight()
    wrap = int(sw * MAX_WIDTH_RATIO)
    label.configure(wraplength=wrap)
    overlay.update_idletasks()

    w = label.winfo_reqwidth()
    h = label.winfo_reqheight()
    background_width  = w if BACKGROUND_WIDTH  is None else BACKGROUND_WIDTH
    background_height = h if BACKGROUND_HEIGHT is None else BACKGROUND_HEIGHT

    x, y = compute_position(sw, sh, background_width, background_height)
    overlay.geometry(f"{background_width}x{background_height}+{x}+{y}")

# ────────────────────────────────────────────────
# Event-Bindings hinzufügen (am besten nach overlay = tk.Toplevel() )
# ────────────────────────────────────────────────

overlay.bind("<Button-1>", next_variant)           # Linksklick → nächste Variante
overlay.bind("<space>", next_variant)            # Leertaste
overlay.bind("<Right>", next_variant)            # Pfeil rechts
overlay.bind("<Up>", label.focus_force())               # Hoch-Pfeil → Fokus auf Label
# overlay.bind("<Return>", next_variant)           # Enter

# Optional: Rechtsklick → zurück (oder schließen)
def prev_variant(event=None):
    global current_variant_index
    if len(current_variants) <= 1:
        return
    current_variant_index = (current_variant_index - 1) % len(current_variants)
    update_label_with_current_variant()

overlay.bind("<Button-3>", prev_variant)           # Rechtsklick → vorherige

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

listening = False
buffer = ""

def normalize(s: str) -> str:
    return s.strip().lower()

def on_status_click(_e=None):
    capture_win.deiconify()
    capture_win.lift()
    capture_win.focus_force()

status_win.bind("<Button-1>", on_status_click)

def get_initials(s):
    words = [w for w in s.split() if w and w[0].isalpha()]
    return ''.join(w[0].lower() for w in words)

def find_answer(query):
    q = normalize(query).strip()
    if not q:
        return None

    q_lower = q.lower()

    if ' ' in q:
        # mit Leerzeichen → Teilstring-Suche
        for key in QA:
            if q_lower in normalize(key):
                return QA[key]
        return None

    # ohne Leerzeichen → Anfangsbuchstaben-Präfix
    initials_q = q_lower

    if len(initials_q) >= 2 and initials_q.isalpha():
        for key in QA:
            key_initials = get_initials(key)
            if key_initials.startswith(initials_q):
                return QA[key]          # ← erste passende Frage

    return None

def handle_key(event):
    global listening, buffer

    ch = event.char
    ks = event.keysym

    if (ch == "0" or ks == "0") and not listening:
        listening = True
        buffer = ""
        set_status(GREEN)
        overlay.withdraw()
        return "break"

    if not listening:
        return "break"

    if ch == ";" or ks == "semicolon":
        listening = False
        set_status(ORANGE)

        ans = find_answer(buffer)
        if ans:
            show_answer(ans)
        else:
            set_status(RED)
            status_win.after(600, lambda: set_status(ORANGE))
            label.focus_force()

        buffer = ""
        return "break"

    if ks == "BackSpace":
        if buffer:
            buffer = buffer[:-1]
        return "break"

    if ch and ch.isprintable() and len(ch) == 1:
        buffer += ch
        return "break"

    return "break"

capture_win.bind("<KeyPress>", handle_key)

set_status(ORANGE)

capture_win.deiconify()
capture_win.focus_force()
capture_win.withdraw()

status_win.mainloop()
