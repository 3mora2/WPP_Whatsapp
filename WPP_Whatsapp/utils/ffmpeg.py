import os
import subprocess
import base64
import shutil
import tempfile


def get_ffmpeg_path():
    ffmpeg_path = os.environ.get('FFMPEG_PATH')

    if ffmpeg_path and os.path.isfile(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK):
        return ffmpeg_path

    executable = shutil.which('ffmpeg')
    if executable:
        return executable

    search_paths = [
        r'C:\ffmpeg\bin',
        'C:\\FFmpeg\\bin',
        'C:\\FFmpeg\\FFmpeg\\bin',
        'C:\\Program Files\\ffmpeg\\bin',
        'C:\\Program Files (x86)\\ffmpeg\\bin',
    ]

    for path in search_paths:
        ffmpeg_candidate = os.path.join(path, 'ffmpeg')
        ffmpeg_candidate_ = os.path.join(path, 'ffmpeg.exe')
        if os.path.exists(ffmpeg_candidate) or os.path.exists(ffmpeg_candidate_):
            return ffmpeg_candidate_ if os.path.isfile(ffmpeg_candidate_) else ffmpeg_candidate

    raise FileNotFoundError('Error: FFMPEG not found.')



def convertToMP4GIF(input_base64):
    ffmpeg_path = get_ffmpeg_path()
    if ',' in input_base64:
        input_base64 = input_base64.split(',', 1)[1]
    raw = base64.b64decode(input_base64, validate=True)
    with tempfile.TemporaryDirectory(prefix='wpp-whatsapp-') as directory:
        input_path = os.path.join(directory, 'input')
        output_path = os.path.join(directory, 'output.mp4')
        with open(input_path, 'wb') as stream:
            stream.write(raw)
        command = [
            ffmpeg_path, '-i', input_path, '-movflags', 'faststart',
            '-pix_fmt', 'yuv420p', '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
            '-f', 'mp4', output_path,
        ]
        subprocess.run(command, check=True, timeout=180,
                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        with open(output_path, 'rb') as stream:
            content = base64.b64encode(stream.read()).decode('ascii')
        return 'data:video/mp4;base64,' + content


def cleanup_tmp_dir(tmp_dir):
    if tmp_dir:
        tmp_dir.cleanup()
