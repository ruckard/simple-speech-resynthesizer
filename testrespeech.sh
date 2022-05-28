#!/bin/bash
set -x
set -v

./respeech.py --respeech-rate 85 --respeech-voice 'spanish-mbrola-1' --respeech-volume=1 --respeech-pitch=70 -m /home/playg/vosk-models/vosk-model-small-es-0.22 -o test.srt /home/playg/personal/bitcoin/2022/respeech_input/respeech_input_30s.mp4
