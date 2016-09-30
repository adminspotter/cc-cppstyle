#!python3

import json
import os
import hashlib
import re

def find_sources(root_path, search_paths):
    paths = [];
    for path in search_paths:
        for root, dirs, files in os.walk(os.path.join(root_path, path)):
            for fname in files:
                if fname.endswith(".h") or fname.endswith(".cc") \
                   or fname.endswith(".H") or fname.endswith(".C") \
                   or fname.endswith(".hpp") or fname.endswith(".cpp"):
                    paths.append(os.path.join(root, fname))
    return paths

def find_headers(root_path, search_paths):
    paths = [];
    for path in search_paths:
        for root, dirs, files in os.walk(os.path.join(root_path, path)):
            for fname in files:
                if fname.endswith(".h") or fname.endswith(".H") \
                   or fname.endswith(".hpp"):
                    paths.append(os.path.join(root, fname))
    return paths

def long_lines(paths, max_len, root_path):
    for fname in paths:
        base_fname = str.replace(fname, root_path + "/", "")
        with open(fname) as f:
            i = 1
            fp = str.replace(base_fname, "/", "_")
            desc = "Line longer than {0} characters.".format(max_len)
            for line in f:
                if len(line) > max_len:
                    line_hash = hashlib.md5(line.encode('utf-8')).hexdigest()
                    print(json.dumps({
                        "type": "issue",
                        "check_name": "Line Too Long",
                        "description": desc,
                        "categories": ["Style"],
                        "location": {
                            "path": base_fname,
                            "lines": {
                                "begin": i,
                                "end": i
                            }
                        },
                        "severity": "normal",
                        "fingerprint": "{0}___{1}".format(fp, line_hash)
                    }))
                    print("\x00")
                i += 1

def trailing_space(paths, root_path):
    desc = "Line contains trailing whitespace."
    for fname in paths:
        base_fname = str.replace(fname, root_path + "/", "")
        with open(fname) as f:
            i = 0
            fp = str.replace(base_fname, "/", "_")
            for line in f:
                if re.search("[ \t]+$", line) is not None:
                    line_hash = hashlib.md5(line.encode('utf-8')).hexdigest()
                    print(json.dumps({
                        "type": "issue",
                        "check_name": "Trailing whitespace",
                        "description": desc,
                        "categories": ["Style"],
                        "location": {
                            "path": base_fname,
                            "lines": {
                                "begin": i,
                                "end": i
                            }
                        },
                        "severity": "normal",
                        "fingerprint": "{0}___{1}".format(fp, line_hash)
                    }))
                    print("\x00")
                i += 1

def multi_include_protection(paths, root_path):
    for fname in paths:
        base_fname = str.replace(fname, root_path + "/", "")
        with open(fname) as f:
            file_multi_include(f, base_fname)

def multi_include_parse_file(f):
    state = 0
    ndef = re.compile("^#ifndef (__.*__)$")
    define = ""
    endif = ""
    for line in f:
        if state == 0:
            if re.search("^\s*/\*", line) is not None:
                for comment in f:
                    if re.search("\*/\s*$", comment) is not None:
                        break
                state = 1
            elif re.search(ndef, line) is not None:
                break
        elif state == 1:
            match = re.search(ndef, line)
            if match:
                state = 2
                define = re.compile("^#define " + match.group(1))
                endif = re.compile("^#endif.*" + match.group(1))
        elif state == 2 and re.search(define, line) is not None:
            state = 3
        elif state == 3 and re.search(endif, line) is not None:
            state = 4
        elif state == 4:
            if re.search("^\s*/\*", line) is not None:
                for comment in f:
                    if re.search("\*/\s*$", comment) is not None:
                        break
            else:
                state = 5
        else:
            pass
    return state

def file_multi_include(f, fname):
    state = multi_include_parse_file(f)
    if state == 4:
        return
    desc = ""
    if state == 0:
        desc = "No leading comment block"
    elif state == 1 or state == 2:
        desc = "No multi-include protection found"
    elif state == 3:
        desc = "No matching close #endif found"
    elif state == 5:
        desc = "Non-comment stuff after closing #endif"
    print(json.dumps({
        "type": "issue",
        "check_name": "Multi-include protection",
        "description": desc,
        "categories": ["Style"],
        "location": {
            "path": fname,
            "lines": {
                "begin": 1,
                "end": 1
            },
        },
        "severity": "normal",
        "fingerprint": str.replace(fname, "/", "_")
    }))
    print("\x00")


code_root = "/code"
max_length = 80

with open('/config.json') as data_file:
    config = json.load(data_file)

sources = find_sources(code_root, config["include_paths"])
long_lines(sources, max_length, code_root)
trailing_space(sources, code_root)

headers = find_headers(code_root, config["include_paths"])
multi_include_protection(headers, code_root)

