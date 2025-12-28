import os
import re
import glob
from utils.logger import logger

class Strategy:
    def __init__(self, name, description, tcp_args, udp_args, discord_tcp_args=None):
        self.name = name
        self.description = description
        self.tcp_args = tcp_args
        self.udp_args = udp_args
        self.discord_tcp_args = discord_tcp_args or tcp_args

def parse_bat_strategy(file_path, bin_path):
    """
    Parses a .bat file to extract winws.exe arguments.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Remove line continuations (^) and normalize spaces
        content = content.replace('^\n', ' ').replace('^\r\n', ' ')
        
        tcp_args = ""
        udp_args = ""
        
        # Use regex to find TCP filters that include ports 80 or 443
        tcp_matches = re.findall(r'--filter-tcp=[0-9,]+.*?(?=(?:--new|$))', content, re.DOTALL)
        
        best_tcp_match = None
        for match in tcp_matches:
            # Match ports 80 or 443 using word boundaries to avoid 8443
            if re.search(r'\b(80|443)\b', match):
                # Prefer matches that use list-google.txt for better YouTube compatibility
                if 'list-google.txt' in match:
                    best_tcp_match = match
                    break
                if best_tcp_match is None:
                    best_tcp_match = match
        
        if best_tcp_match:
            match = best_tcp_match
            # Better extraction of arguments using regex to handle quoted values
            # Extract everything that looks like an argument we care about
            arg_patterns = [
                r'--dpi-desync[^ ]*(?:="[^"]*"|=[^ ]*)?',
                r'--ip-id[^ ]*(?:="[^"]*"|=[^ ]*)?',
                r'--wssize[^ ]*(?:="[^"]*"|=[^ ]*)?',
                r'--desync-[^ ]*(?:="[^"]*"|=[^ ]*)?',
                r'--hostfakesplit-mod[^ ]*(?:="[^"]*"|=[^ ]*)?',
                r'--fake-tls-mod[^ ]*(?:="[^"]*"|=[^ ]*)?',
                r'--fake-quic-mod[^ ]*(?:="[^"]*"|=[^ ]*)?'
            ]
            
            extracted = []
            for pattern in arg_patterns:
                found = re.findall(pattern, match)
                for f_arg in found:
                    # Replace %BIN% and clean up
                    f_arg = f_arg.replace('%BIN%', bin_path + '\\').replace('^', '').strip()
                    if f_arg:
                        extracted.append(f_arg)
            tcp_args = " ".join(extracted)

        # Same for UDP
        udp_matches = re.findall(r'--filter-udp=[0-9,]+.*?(?=(?:--new|$))', content, re.DOTALL)
        for match in udp_matches:
            if re.search(r'\b(443)\b', match):
                extracted = []
                arg_patterns = [
                    r'--dpi-desync[^ ]*(?:="[^"]*"|=[^ ]*)?',
                    r'--ip-id[^ ]*(?:="[^"]*"|=[^ ]*)?',
                    r'--desync-[^ ]*(?:="[^"]*"|=[^ ]*)?',
                    r'--fake-quic[^ ]*(?:="[^"]*"|=[^ ]*)?',
                    r'--fake-quic-mod[^ ]*(?:="[^"]*"|=[^ ]*)?'
                ]
                for pattern in arg_patterns:
                    found = re.findall(pattern, match)
                    for f_arg in found:
                        f_arg = f_arg.replace('%BIN%', bin_path + '\\').replace('^', '').strip()
                        if f_arg:
                            extracted.append(f_arg)
                udp_args = " ".join(extracted)
                break
        
        if tcp_args or udp_args:
            name = os.path.basename(file_path).replace('.bat', '')
            # Clean up name: "general (ALT)" -> "ALT"
            name = re.sub(r'^general\s*', '', name).strip('() ')
            if not name: name = "Default"
            
            return Strategy(
                name,
                f"Загружено из {os.path.basename(file_path)}",
                tcp_args,
                udp_args
            )
    except Exception as e:
        logger.error(f"Error parsing {file_path}: {e}")
    return None

def get_strategies(zapret_path):
    bin_path = os.path.join(zapret_path, "bin")
    quic_fake = os.path.join(bin_path, "quic_initial_www_google_com.bin")
    tls_4pda = os.path.join(bin_path, "tls_clienthello_4pda_to.bin")
    tls_google = os.path.join(bin_path, "tls_clienthello_www_google_com.bin")

    # Start with built-in defaults
    strategies = [
        Strategy(
            "Standard (Multisplit)",
            "Стандартный метод обхода (Multisplit)",
            f"--dpi-desync=multisplit --dpi-desync-split-seqovl=568 --dpi-desync-split-pos=1 --dpi-desync-split-seqovl-pattern=\"{tls_4pda}\"",
            f"--dpi-desync=fake --dpi-desync-repeats=6 --dpi-desync-fake-quic=\"{quic_fake}\""
        ),
        Strategy(
            "ALT (Fakedsplit)",
            "Альтернативный метод обхода (Fakedsplit)",
            f"--dpi-desync=fake,fakedsplit --dpi-desync-repeats=6 --dpi-desync-fooling=ts --dpi-desync-fakedsplit-pattern=0x00 --dpi-desync-fake-tls=\"{tls_google}\"",
            f"--dpi-desync=fake --dpi-desync-repeats=6 --dpi-desync-fake-quic=\"{quic_fake}\""
        ),
        Strategy(
            "Fake TLS Auto",
            "Обход с использованием Fake TLS (Автоматический)",
            f"--dpi-desync=fake,multidisorder --dpi-desync-split-pos=1,midsld --dpi-desync-repeats=11 --dpi-desync-fooling=badseq --dpi-desync-fake-tls=0x00000000 --dpi-desync-fake-tls=^! --dpi-desync-fake-tls-mod=rnd,dupsid,sni=www.google.com",
            f"--dpi-desync=fake --dpi-desync-repeats=11 --dpi-desync-fake-quic=\"{quic_fake}\""
        )
    ]

    # Parse other .bat files in Zapret folder
    bat_files = glob.glob(os.path.join(zapret_path, "general*.bat"))
    seen_names = {s.name.lower() for s in strategies}
    
    for bat_file in bat_files:
        strategy = parse_bat_strategy(bat_file, bin_path)
        if strategy and strategy.name.lower() not in seen_names:
            strategies.append(strategy)
            seen_names.add(strategy.name.lower())
            
    return strategies

class ServiceConfig:
    def __init__(self, name, displayName, description, ports, list_file=None, domains=None, l7=None):
        self.name = name
        self.displayName = displayName
        self.description = description
        self.ports = ports
        self.list_file = list_file
        self.domains = domains
        self.l7 = l7

def get_services(lists_path):
    list_general = os.path.join(lists_path, "list-general.txt")
    list_exclude = os.path.join(lists_path, "list-exclude.txt")
    list_google = os.path.join(lists_path, "list-google.txt")
    ipset_exclude = os.path.join(lists_path, "ipset-exclude.txt")

    return [
        ServiceConfig(
            "discord",
            "Discord (All)",
            "Обход блокировок Discord (Голос + Медиа)",
            "19294-19344,50000-50100,2053,2083,2087,2096,8443",
            l7="discord,stun",
            domains="discord.media"
        ),
        ServiceConfig(
            "youtube",
            "YouTube",
            "Сервисы YouTube и Google",
            "443",
            list_file=list_google
        ),
        ServiceConfig(
            "general",
            "Общий список",
            "Сайты из общего списка",
            "80,443",
            list_file=list_general
        )
    ]
