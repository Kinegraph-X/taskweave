from datetime import datetime
import multiprocessing
import threading
from multiprocessing import Process
from multiprocessing.synchronize import Event as MpEvent
import subprocess

from .worker_logger import WorkerLogger
from taskweave.messages import LogEventProducer

from taskweave.messages import LogEvent
from taskweave.states import WorkerContext

def get_time():
	current_datetime = datetime.now()
	return current_datetime.strftime("%Y-%m-%d %H:%M:%S") + " :"

class BasicWorker(Process):

    def __init__(self, name, args_list, print_queue, debug=False, dist=False, **kwargs):
        super(BasicWorker, self).__init__()
        self.name = name
        self.args_list = args_list
        self.dest_con, self.origin_con = multiprocessing.Pipe()
        self.ctx = WorkerContext(name)
        self.log_producer = LogEventProducer()
        self.print_queue = print_queue
        log_folder = f"{args_list[0]}_logs/" if args_list[0] != "python" else f"{args_list[1][:-3]}_logs/"
        self.logger = WorkerLogger(name, log_folder)

    def run(self):
        try:
            sp = subprocess.Popen(
                # command,
                self.args_list,
                # cwd = "../Wav2Lip_resident/",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            # Start a thread to read the output (problem with sys.stdout, shared accross threads in the subprocess, colliding with reading it from another process)
            threading.Thread(target = self.read_subprocess_output, args = (sp,), daemon=True).start()

            # dDetect terminated subprocess(in success) with sp.poll()
            # Listen to logical SIGKILL ("EXIT") from outside (the Manager calls worker.terminate)
            while sp.poll() is None:
                if self.dest_con.poll(timeout=0.1):
                    message = self.dest_con.recv()
                    if message == "EXIT":
                        break

            # Proceed to termination on "EXIT" received
            self.print_queue.put(f"{get_time()} INFO : about to kill the {self.name} worker")
            self.logger.close()
            sp.terminate()

            exit_code = sp.wait()
            if exit_code == 0:
                self.ctx.success_event.set()
            else:
                self.ctx.failure_event.set()

            self.print_queue.put(
                f"{get_time()} INFO : {self.name} subprocess terminated.")
            self.ctx.set_stopped('subprocess terminated')

        except Exception as e:
            self.print_queue.put(
                f'Raised exception in {self.name} Worker {str(e)}')

    def terminate(self):
        self.origin_con.send('EXIT')
        self.origin_con.close()

        self.join(timeout=5)
        self.ctx.set_stopped('subprocess terminated')

        if self.is_alive():
            super().terminate()
            self.print_queue.put(
                f"{get_time()} INFO : {self.name} process forcefully terminated.")
            self.ctx.set_stopped('process forcefully terminated')

    def read_subprocess_output(self, sp):
        # for line in iter(sp.stdout.readline, ''):  # ← string, not bytes
        #    self.print_queue.put(line.strip())

        # We use read(n) rather than readline() to catch potential \r
        buffer = ""
        while True:
            # blocking-read by small blocks
            chunk = sp.stdout.read(256)
            if not chunk:
                break
            buffer += chunk
            # Split on \n AND \r, cause some programs write removable lines with \r 
            lines = buffer.replace('\r', '\n').split('\n')
            # in case the last line is empty, process it later
            buffer = ""
            for line in lines:
                if line.strip():
                    event = self.log_producer.on_line(self.name, line.strip())
                    self.print_queue.put(event)

