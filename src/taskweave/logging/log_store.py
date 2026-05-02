from typing import Pattern, cast, TypedDict, Callable, List
from dataclasses import dataclass, field, asdict, is_dataclass
from pathlib import Path
from os import path
from time import time, time_ns
import json

from .log_reader import LogReader
from .session_data import SessionData
from .make_log_id import make_log_id

from taskweave.context import get_app_context
from taskweave.utils import StrSerializable
config, constants, args = get_app_context()

class Encoder(json.JSONEncoder):
    def default(self, obj):
        if is_dataclass(obj):
            return asdict(obj)
        if isinstance(obj, StrSerializable):
            return str(obj)  # ou int(obj)
        return super().default(obj)


@dataclass(kw_only=True)
class LogStore:
    log_dir: Path
    log_index: Path = Path(f"{constants.log_index_filename}{constants.log_index_extension}")
    max_age : float = float(49 * 24 * 3600 * 1000)

    # generates log_id, write in index, returns log_id
    def register(self, session_id: str, task_name: str | StrSerializable) -> str | StrSerializable:
        log_filename = make_log_id(task_name)
        index_path = path.join(self.log_dir, self.log_index)
        if path.exists(index_path):
            try :
                with open(index_path, "r") as f:
                    log_content = json.load(f)
                    # reconstruct original structure, for consistancy in code
                    log_content = data = {k: SessionData(**v) for k, v in log_content.items()}
            except Exception as e:
                raise RuntimeError(f"error loading log index file, possibly malformed : {index_path} :{e}")
            if not session_id in log_content.keys():
                log_content[session_id] = SessionData()
        else:
            log_content = {
                session_id : SessionData()
            }

        file_list = log_content[session_id].list
        if (file_list):
            file_list.append(log_filename)
        else:
            log_content[session_id] = SessionData(list = [log_filename])
        with open(index_path, "w") as f:
            json.dump(log_content, f, cls = Encoder)

        return log_filename
    
    # session_id → session_data
    def resolve(self, session_id: str) -> SessionData | None:
        index_path = path.join(self.log_dir, self.log_index)
        with open(index_path, "r") as f:
            log_content = json.load(f)
        return log_content[session_id]
    
    def console_reader(self, session_id: str) -> None:
        session_data = self.resolve(session_id)
        if not session_data:
            print(f'no log files found for session : {session_id}')
            return None
        
        file_list = cast(list[str], session_data.list)

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
        
        file_list = cast(list[str], session_data.list)
        log_path = next((name for name in file_list if target.match(name)))
        if log_path is None:
            print(f"No log file matched the given pattern : {str(target)}")
            return None

        if path.exists(log_path):
            return LogReader(log_path = Path(log_path))
        else:
            raise RuntimeError(f'log file not found for session : {session_id} and path : {log_path}')
    
    # deletes files older than the 49 days sliding window, and corresponding indices
    def cleanup(self) -> None:
        index_path = path.join(self.log_dir, self.log_index)
        if not path.exists(index_path):
            return

        current_time = time()
        
        with open(index_path, "r") as f:
            to_delete = []
            try:
                # reconstruct original, for consistancy in code
                sessions = {k: SessionData(**v) for k, v in json.load(f).items()}
            except Exception as e:
                raise RuntimeError(f"error loading log index file, possibly malformed : {index_path} :{e}")
            
            for session_id, session_data in sessions.items():
                filelist = session_data.list
                if current_time - session_data.timestamp > self.max_age:
                    for file in filelist:
                        Path(str(file)).unlink()
                    to_delete.append(session_id)

            for session_id in to_delete:
                del sessions[session_id]

        with open(index_path, "w") as f:
            json.dump(sessions, f, cls = Encoder)
                    