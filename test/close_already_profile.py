import os
import psutil

__close_already_profile = True
path = "path/"
path_old = dict()
for proc in psutil.process_iter():
    if "chrome.exe" in proc.name():
        cmd = proc.cmdline()
        user = list(filter(lambda x: "--user-data-dir" in x, cmd))
        if user:
            _path = os.path.normpath(user[0].split("=")[-1])
            if _path not in path_old:
                path_old[_path] = []
            path_old[_path].append(proc)

    elif "firefox.exe" in proc.name():
        cmd = proc.cmdline()
        user = list(filter(lambda x: "-profile" in x, cmd))
        if user:
            _path = os.path.normpath(cmd[cmd.index(user[0]) + 1])
            if _path not in path_old:
                path_old[_path] = []
            path_old[_path].append(proc)

if os.path.normpath(path) in path_old:
    if __close_already_profile:
        for proc in path_old[os.path.normpath(path)]:
            proc.kill()
    else:
        raise Exception("Profile Already Open")
