import json
from typing import Union
from pathlib import Path

def read_json(path: Union[Path, str]):
    """open and load json files

    Args:
        path (Union[Path, str]): [json data directory]

    Returns:
        [dict]: [json data converted to python dict]
    """
    with open(path) as f:
        return json.load(f)

def read_file(path: Union[Path, str]):
    """[open file directory]

    Args:
        path (Union[Path, str]): [file directory]

    Returns:
        [str]: [returns file contents]
    """
    with open(path) as f:
        return f.readlines()