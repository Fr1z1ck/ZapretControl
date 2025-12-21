import subprocess
import psutil
import os
import signal
import time
from utils.logger import logger

class ProcessManager:
    def __init__(self, bin_path):
        self.bin_path = bin_path
        self.exe_path = os.path.join(bin_path, "winws.exe")
        self.process = None

    def is_running(self):
        """Check if any winws.exe process is running."""
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'].lower() == "winws.exe":
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def start(self, service_configs, strategy, lists_path):
        """Start winws.exe with the provided service configurations and strategy."""
        if self.is_running():
            logger.warning("winws.exe is already running. Stopping it first.")
            self.stop()

        if not os.path.exists(self.exe_path):
            logger.error(f"winws.exe not found at {self.exe_path}")
            return False

        # Build command
        cmd = [
            self.exe_path,
            "--wf-tcp=80,443,2053,2083,2087,2096,8443",
            "--wf-udp=443,19294-19344,50000-50100"
        ]

        list_exclude = os.path.join(lists_path, "list-exclude.txt")
        ipset_exclude = os.path.join(lists_path, "ipset-exclude.txt")
        
        # Verify files exist, if not, create empty ones to prevent winws error
        for fpath in [list_exclude, ipset_exclude]:
            if not os.path.exists(fpath):
                try:
                    os.makedirs(os.path.dirname(fpath), exist_ok=True)
                    with open(fpath, 'w') as f: pass
                    logger.info(f"Created missing list file: {fpath}")
                except Exception as e:
                    logger.error(f"Could not create missing file {fpath}: {e}")

        import shlex
        for config in service_configs:
            # 1. Handle UDP part if exists
            if "-" in config.ports or "19294" in config.ports or config.l7:
                udp_ports = ",".join([p for p in config.ports.split(",") if "-" in p or int(p) > 10000])
                if udp_ports or config.l7:
                    filter_args = []
                    filter_args.append(f"--filter-udp={udp_ports or '443'}")
                    if config.l7:
                        filter_args.append(f"--filter-l7={config.l7}")
                    filter_args.extend(shlex.split(strategy.udp_args))
                    cmd.extend(filter_args)
                    cmd.append("--new")
            
            # 2. Handle TCP part if exists
            tcp_ports = ",".join([p for p in config.ports.split(",") if "-" not in p and int(p) < 10000])
            if tcp_ports or config.domains or config.list_file:
                filter_args = []
                filter_args.append(f"--filter-tcp={tcp_ports or '80,443'}")
                if config.domains:
                    filter_args.append(f"--hostlist-domains={config.domains}")
                elif config.list_file:
                    # winws.exe doesn't like quotes if the path is already passed as a separate argument in Popen list
                    # or if it's already properly handled. But here we use a list, so Popen handles spaces.
                    filter_args.append(f"--hostlist={config.list_file}")
                
                filter_args.append(f"--hostlist-exclude={list_exclude}")
                filter_args.append(f"--ipset-exclude={ipset_exclude}")
                filter_args.extend(shlex.split(strategy.tcp_args))
                cmd.extend(filter_args)
                cmd.append("--new")
        
        if cmd[-1] == "--new":
            cmd.pop()

        logger.info(f"Starting winws.exe with strategy: {strategy.name}")
        logger.debug(f"Full command: {' '.join(cmd)}")
        
        try:
            # Start process without console window
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # Use PIPE for stderr to capture potential errors
            self.process = subprocess.Popen(
                cmd,
                cwd=self.bin_path,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE, # Capture stderr
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            # Check if it died immediately
            time.sleep(0.5)
            if self.process.poll() is not None:
                _, stderr = self.process.communicate()
                logger.error(f"winws.exe exited immediately with code {self.process.returncode}")
                if stderr:
                    logger.error(f"winws.exe error: {stderr.strip()}")
                return False
                
            logger.info(f"Process started with PID: {self.process.pid}")
            return True
        except Exception as e:
            logger.error(f"Failed to start process: {e}")
            return False

    def stop(self):
        """Stop all winws.exe processes."""
        stopped = False
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if proc.info['name'].lower() == "winws.exe":
                    logger.info(f"Terminating process {proc.info['name']} (PID: {proc.info['pid']})")
                    proc.terminate()
                    stopped = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if stopped:
            logger.info("All winws.exe processes stopped.")
        else:
            logger.info("No winws.exe processes were running.")
        
        self.process = None
        return True
