#!/bin/bash
set -x
set -v

./respeech.py -m /home/playg/vosk-models/vosk-model-small-es-0.22 -o test.srt /home/playg/personal/bitcoin/2022/respeech_input/respeech_input_30s.mp4
