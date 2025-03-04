import glob
import os
import itertools
from loguru import logger

from tqdm import tqdm
from sweepai.utils.utils import chunk_code


def filter_file(file, sweep_config):
    for ext in sweep_config.exclude_exts:
        if file.endswith(ext):
            return False
    for dir_name in sweep_config.exclude_dirs:
        if file[len("repo/") :].startswith(dir_name):
            return False
    if not os.path.isfile(file):
        return False
    with open(file, "rb") as f:
        is_binary = False
        for block in iter(lambda: f.read(1024), b""):
            if b"\0" in block:
                is_binary = True
                break
        if is_binary:
            return False

    with open(file, "rb") as f:
        if len(f.read()) > 60000:
            return False
    return True


def read_file(file_name):
    try:
        with open(file_name, "r") as f:
            return f.read()
    except:
        return ""

FILE_THRESHOLD = 100

def repo_to_chunks(directory, sweep_config):
    dir_file_count = {}
    
    def is_dir_too_big(file_name):
        dir_name = os.path.dirname(file_name) 
        if file_name == "node_modules" or file_name == "venv":
            return True
        if dir_name not in dir_file_count:
            dir_file_count[dir_name] = len(os.listdir(dir_name))
        return dir_file_count[dir_name] > FILE_THRESHOLD
    logger.info(f"Reading files from {directory}")

    file_list = glob.iglob(f"{directory}/**", recursive=True)
    file_list = [
        file_name for file_name in file_list 
        if filter_file(file_name, sweep_config) and not is_dir_too_big(file_name)
    ]
    logger.info(f"Found {len(file_list)} files")
    all_chunks = []
    for file_path in tqdm(file_list):
        file_contents = read_file(file_path)
        logger.info(f"Reading {file_path}")
        chunks = chunk_code(file_contents, path=file_path)
        all_chunks.extend(chunks)
    return all_chunks, file_list
