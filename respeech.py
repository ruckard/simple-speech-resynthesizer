#!/usr/bin/env python3
# TODO tqdm
from vosk import Model, KaldiRecognizer, SetLogLevel
import sys
import os
import subprocess
import json
import argparse
import pyttsx3
import importlib
import tempfile
import shutil
import time
from collections import namedtuple
from pprint import pprint
try:
    from tqdm import tqdm
    tqdm_installed = True
except:
    tqdm_installed = False

class SubPart:

    def __init__(self, start, end, text):
        self.start = start
        self.end = end
        self.text = text

    @staticmethod
    def ftot(f):
        h = int(f//3600)
        m = int(f//60 % 60)
        s = int(f//1 % 60)
        ms = int((1000 * f) % 1000)
        s = f"{h:02}:{m:02}:{s:02},{ms:03}"
        return s

    def __repr__(self):
        return f"""
{self.ftot(self.start)} --> {self.ftot(self.end)}
{self.text}
"""[1:-1]
    def getText(self):
        return self.text
    def getStart(self):
        return self.start
    def getEnd(self):
        return self.end


def gen_subparts(input_file, duration, model_dir, verbose=False, partlen=4, progress=False):

    SetLogLevel(0 if verbose else -1)

    model = Model(model_dir)
    rec = KaldiRecognizer(model, 16000)
    rec.SetWords(True);

    process = subprocess.Popen(['ffmpeg', '-loglevel', 'quiet', '-i',
                                input_file,
                                '-ar', str(16000) , '-ac', '1', '-f', 's16le', '-'],
                                stdout=subprocess.PIPE)

    if progress:
        pbar = tqdm(total=duration, unit="s")

    prev_end = 0
    while True:
        data = process.stdout.read(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            r = json.loads(rec.Result())
            if 'result' in r:
                resultpart = [] # TODO: use this across AccesptForm
                for result in r['result']:
                    if len(resultpart) > 0 and float(result['end']) - float(resultpart[0]['start']) >= partlen:
                        yield SubPart(start=resultpart[0]['start'],
                                      end=float(resultpart[-1]['end']),
                                      text=" ".join(r['word'] for r in resultpart))
                        prev_end = float(resultpart[-1]['end'])
                        resultpart = []
                    if float(result['end'] - result['start']) >= partlen:
                        yield SubPart(start=float(result['start']),
                                      end=float(result['end']),
                                      text=result['word'])
                        prev_end = float(result['end'])
                        resultpart = []
                    else:
                        resultpart.append(result)
                    if progress:
                        pbar.update(float(result['end'] - pbar.n))


                if len(resultpart) > 0:
                    yield SubPart(start=float(resultpart[0]['start']),
                                    end=float(resultpart[-1]['end']),
                                    text=" ".join(r['word'] for r in resultpart))
                    prev_end = float(resultpart[-1]['end'])
                    resultpart = []

        else:
            pass
            #print(rec.PartialResult())
    #pprint(rec.PartialResult())
    if progress:
        pbar.close()
    r = json.loads(rec.PartialResult())
    text = r['partial']
    yield SubPart(start=prev_end, end=duration, text=text)


def create_parser():
    parser = argparse.ArgumentParser(prog="SRT file extractor using Speech-To-Text")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-s", "--srt-output", type=argparse.FileType('w+'), default=sys.stdout)
    parser.add_argument("-o", "--output", type=str)
    parser.add_argument("-m", "--model", required=True)
    parser.add_argument("-i", "--interval", type=int, default=4)
    parser.add_argument(
        "--respeech-rate",
        dest="respeech_rate",
        default=80,
        type=int,
        help=("The sample rate to use for playing back.\n" "Defaults to 80."),
        required=False,
    )

    parser.add_argument(
        "--respeech-voice",
        dest="respeech_voice",
        default="us1",
        type=str,
        help=(
            "The name of the voice to use for playing back.\n"
            'See the output of "espeak-ng --voices=en" or "espeak-ng --voices=es" to find voices names (using the identifier following "File:").'
        ),
        required=False,
    )

    parser.add_argument(
        "--respeech-volume",
        dest="respeech_volume",
        default=1,
        type=int,
        help=("The volume to use for playing back.\n" "Defaults to 1 (which means 100%)."),
        required=False,
    )

    parser.add_argument(
        "--respeech-pitch",
        dest="respeech_pitch",
        default=50,
        type=int,
        help=("The pitch to use for playing back.\n" "Defaults to 50."),
        required=False,
    )

    parser.add_argument(
        "--respeech-tmp-dir",
        dest="respeech_tmp_dir",
        default="/tmp",
        type=str,
        help=(
            "Default temporary directory.\n"
        ),
        required=False,
    )
    if tqdm_installed:
        parser.add_argument("-p", "--progress", action="store_true")
    parser.add_argument("input")
    return parser

def respeech_engine_init (respeech_rate, respeech_voice, respeech_volume, respeech_pitch):
    importlib.reload(pyttsx3) # Workaround to be avoid pyttsx3 being stuck
    respeech_engine = pyttsx3.init()
    respeech_engine.setProperty('rate', respeech_rate)
    respeech_engine.setProperty('voice', respeech_voice)
    respeech_engine.setProperty('volume', respeech_volume)
    respeech_engine.setProperty('pitch', respeech_pitch) # Default: 50
    return respeech_engine

def get_duration (input_file):
    r = subprocess.run("ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1".split() + [input_file], stdout=subprocess.PIPE)
    duration = float(r.stdout.decode('utf-8').strip())
    return duration

def create_silence_file (duration, silence_wav):
    process = subprocess.call(['ffmpeg', '-loglevel', 'quiet', '-y', '-f', 'lavfi', '-t', str(duration), '-i',
                                'anullsrc=channel_layout=mono:sample_rate=22050',
                                '-ar', str(22050) , '-ac', '1', silence_wav],
                                stdout=subprocess.PIPE)

def create_concatenated_wav(ffmpeg_concat_configuration_file, ffmpeg_concat_wav_file):
    process = subprocess.call(['ffmpeg', '-loglevel', 'quiet', '-y', '-safe', '0', '-f', 'concat', '-i',
                                ffmpeg_concat_configuration_file,
                                '-codec', 'copy' , ffmpeg_concat_wav_file],
                                stdout=subprocess.PIPE)

def create_final_video(input_video, input_audio, output_video, audio_format):
    process = subprocess.call(['ffmpeg', '-loglevel', 'quiet', '-y', '-i',
                                input_video, '-i', input_audio, '-c:v', 'copy', '-c:a', audio_format, '-map', '0:v:0', '-map', '1:a:0',
                                output_video],
                                stdout=subprocess.PIPE)

def main():
    args = create_parser().parse_args()
    duration = get_duration(args.input)

    wav_directory = args.respeech_tmp_dir + os.path.basename(args.input) + ".waws.d"
    try:
        os.makedirs(wav_directory)
    except FileExistsError:
        pass

    ffmpeg_concat_configuration_file = wav_directory + '/' + "ffmpeg_concat.conf"
    ffmpeg_concat_wav_file = wav_directory + '/' + "ffmpeg_concat.wav"
    silence_wav = wav_directory + '/' + 'silence.wav'
    f_ffmpeg_concat_configuration_file = open(ffmpeg_concat_configuration_file, 'w')

    if tqdm_installed:
        it = enumerate(gen_subparts(args.input, duration, args.model, args.verbose, args.interval, args.progress))
    else:
        it = enumerate(gen_subparts(args.input, duration, args.model, args.verbose, args.interval, False))

    last_subpart_end = 0
    maximum_silence_duration = 0
    tmp_respeech_wav_directory = tempfile.mkdtemp()
    for i,subpart in it:
        n = i+1
        args.srt_output.write(f"""{n}
{subpart}

"""
)
        silence_start = last_subpart_end

        respeech_text = subpart.getText()
        respeech_wav_filename = wav_directory + '/' + str(n)+'.wav'
        tmp_respeech_wav_filename = tmp_respeech_wav_directory + '/' + 'tmpwavefile' +'.wav'
        # Make sure to delete the temporary wav filename
        if os.path.exists(tmp_respeech_wav_filename):
            os.remove(tmp_respeech_wav_filename)
        respeech_engine = respeech_engine_init(args.respeech_rate, args.respeech_voice, args.respeech_volume, args.respeech_pitch)
        respeech_engine.save_to_file(respeech_text, tmp_respeech_wav_filename)
        respeech_engine.runAndWait()
        # So that we can wait for the actual runAndWait()
        while not os.path.exists(tmp_respeech_wav_filename):
            time.sleep(0.1)
        time.sleep(0.1)
        # shutil is a workaround because save_to_file function from pyttsx3 engine does not seem to handle
        # filepaths with spaces on them
        shutil.copyfile(tmp_respeech_wav_filename, respeech_wav_filename)

        current_silence_duration = subpart.getStart() - last_subpart_end
        if (current_silence_duration >= maximum_silence_duration):
            maximum_silence_duration = current_silence_duration

        f_ffmpeg_concat_configuration_file.write(f"""file {silence_wav}
outpoint {current_silence_duration}

file {respeech_wav_filename}

"""
)

        last_subpart_end = subpart.getEnd()

    create_silence_file (maximum_silence_duration, silence_wav)

    f_ffmpeg_concat_configuration_file.flush()
    create_concatenated_wav(ffmpeg_concat_configuration_file, ffmpeg_concat_wav_file)
    create_final_video(args.input, ffmpeg_concat_wav_file, args.output, 'aac')


if __name__ == "__main__":
    main()
