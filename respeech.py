#!/usr/bin/env python3
# TODO tqdm
from vosk import Model, KaldiRecognizer, SetLogLevel
import sys
import os
import subprocess
import json
import argparse
import pyttsx3
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


def gen_subparts(input_file, model_dir, verbose=False, partlen=4, progress=False):

    SetLogLevel(0 if verbose else -1)

    model = Model(model_dir)
    rec = KaldiRecognizer(model, 16000)
    rec.SetWords(True);

    process = subprocess.Popen(['ffmpeg', '-loglevel', 'quiet', '-i',
                                input_file,
                                '-ar', str(16000) , '-ac', '1', '-f', 's16le', '-'],
                                stdout=subprocess.PIPE)

    r = subprocess.run("ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1".split() + [input_file], stdout=subprocess.PIPE)
    duration = float(r.stdout.decode('utf-8').strip())

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
    parser.add_argument("-o", "--output", type=argparse.FileType('w+'), default=sys.stdout)
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
    if tqdm_installed:
        parser.add_argument("-p", "--progress", action="store_true")
    parser.add_argument("input")
    return parser


def main():
    args = create_parser().parse_args()

    respeech_engine = pyttsx3.init()
    respeech_engine.setProperty('rate', args.respeech_rate)
    respeech_engine.setProperty('voice', args.respeech_voice)
    respeech_engine.setProperty('volume', args.respeech_voice)
    respeech_engine.setProperty('pitch', args.respeech_pitch) # Default: 50

    if tqdm_installed:
        it = enumerate(gen_subparts(args.input, args.model, args.verbose, args.interval, args.progress))
    else:
        it = enumerate(gen_subparts(args.input, args.model, args.verbose, args.interval, False))
    for i,subpart in it:
        n = i+1
        args.output.write(f"""{n}
{subpart}

"""
)
        respeech_engine.say(subpart.getText())
        respeech_engine.runAndWait()



if __name__ == "__main__":
    main()
