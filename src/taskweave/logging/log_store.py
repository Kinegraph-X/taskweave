from typing import Pattern, cast
from dataclasses import dataclass
from pathlib import Path
from os import path
from time import time, time_ns
import json

from .log_reader import LogReader

from taskweave.context import get_app_context
config, constants = get_app_context()

def make_log_id(task_name: str) -> str:
    ts = hex(time_ns() // 1_000_000)[-8:]  # ms, 8 chars, 2038-proof on 34 years more
    return f"{task_name}_{ts}"

@dataclass(kw_only=True)
class LogStore:
    log_dir: Path
    log_index: Path = Path(f"{constants.log_index_filename}{constants.log_index_extension}")
    max_elapsed_time = 49 * 24 * 3600 * 1000
    
    # generates log_id, write in index, returns log_id
    def register(self, session_id: str, task_name: str) -> str:
        log_filename = f"{task_name}_{make_log_id(task_name)}"
        index_path = path.join(self.log_dir, self.log_index)
        if path.exists(index_path):
            try :
                with open(index_path, "r") as f:
                    log_content = json.load(f)
            except Exception as e:
                raise RuntimeError(f'Malformed log index file :{index_path}')
            if not log_content[session_id]:
                log_content[session_id] = {
                    "timestamp" : time(),
                    "list" : []
                }
        else:
            log_content = {
                session_id : {
                    "timestamp" : time(),
                    "list" : []
                }
            }

        file_list = log_content[session_id]["list"]
        if (file_list):
            file_list.append(log_filename)
        else:
            log_content[session_id] = [log_filename]
        with open(index_path, "w") as f:
            json.dump(log_content, f)
        return log_filename
    
    # session_id → session data
    def resolve(self, session_id: str) -> dict[str, float | list[str]] | None:
        index_path = path.join(self.log_dir, self.log_index)
        with open(index_path, "r") as f:
            log_content = json.load(f)
        return log_content[session_id]
    
    def console_reader(self, session_id: str) -> None:
        session_data = self.resolve(session_id)
        if not session_data:
            print(f'no log files found for session : {session_id}')
            return None
        
        file_list = cast(list[str], session_data["list"])

        print("Available files for this session :")
        for k, file in enumerate(file_list):
            print(f"{k}: {file}")
        idx : int = int(input(f"please enter the index of the file you want to read"))
        
        log_path = file_list[idx]
        if path.exists(log_path):
            with open(log_path, "r") as f:
                print(f.read())
        else:
            print(f'log file not found for session : {session_id} at idx {idx}')
        
    def reader(self, session_id: str, target : Pattern) -> LogReader | None:
        session_data = self.resolve(session_id)
        if not session_data:
            raise RuntimeError(f'no log files found for session : {session_id}')
        
        file_list = cast(list[str], session_data["list"])
        log_path = next((name for name in file_list if target.match(name)))
        if log_path is None:
            print(f"No log file matched the given pattern : {str(target)}")
            return None

        if path.exists(log_path):
            return LogReader(log_path = Path(log_path))
        else:
            raise RuntimeError(f'log file not found for session : {session_id} and path : {log_path}')
    
    # deletes files older than the 49 days sliding window, and corresponding indices
    def cleanup(self, max_age_ms: int) -> None:
        index_path = path.join(self.log_dir, self.log_index)
        current_time = time()
        
        with open(index_path, "r") as f:
            sessions = json.load(f).items()
            for session_id, session_data in sessions:
                filelist = cast(list[str], session_data["list"])
                if current_time - session_data.timestamp > self.max_elapsed_time:
                    for file in filelist:
                        Path.unlink(Path(file))
                    del sessions[session_id]

        with open(index_path, "w") as f:
            json.dump(sessions, f)
                    