import os
import subprocess
import base64
import shutil
import tempfile


def get_ffmpeg_path():
    ffmpeg_path = os.environ.get('FFMPEG_PATH')

    if ffmpeg_path and os.access(ffmpeg_path, os.X_OK):
        return ffmpeg_path

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
            return ffmpeg_candidate

    raise FileNotFoundError('Error: FFMPEG not found.')


i = 0


def convertToMP4GIF(input_base64):
    global i
    tmp_dir = tempfile.TemporaryDirectory()
    input_path = os.path.join(tmp_dir.name, str(i))
    i += 1
    output_path = os.path.join(tmp_dir.name, str(i) + ".mp4")

    if ',' in input_base64:
        input_base64 = input_base64.split(',')[1]

    with open(input_path, 'wb') as f:
        f.write(base64.b64decode(input_base64))

    ffmpeg_path = get_ffmpeg_path()

    try:
        command = [
            ffmpeg_path,
            '-i', input_path,
            '-movflags', 'faststart',
            '-pix_fmt', 'yuv420p',
            '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
            '-f', 'mp4',
            output_path
        ]

        subprocess.run(command, check=True)

        with open(output_path, 'rb') as f:
            output_base64 = base64.b64encode(f.read()).decode('utf-8')

        return 'data:video/mp4;base64,' + output_base64
    finally:
        cleanup_tmp_dir(tmp_dir)


def cleanup_tmp_dir(tmp_dir):
    if tmp_dir:
        try:
            shutil.rmtree(tmp_dir.name)
        except Exception as e:
            pass
