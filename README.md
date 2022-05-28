# Simple Speech Resynthesizer

Resynthesises natural voice from videos onto computer-generated voice thanks to vosk and pyttsx3

## Prerequisites
### Summary
- python3
- pip3
- You have vosk installed and some of its vosk models installed
- python3 pyttsx3 module
- mbrola voices (Optional but recommended)
- ffmpeg
- openshot-qt
- unzip
- 4 GB RAM
- ( Originally installed in Ubuntu 22.04. )

### Package installation
```bash
sudo apt install python3 python3-pip ffmpeg openshot unzip mbrola
sudo pip3 install vosk pyttsx3
```
### Mbrola voices (optional)
#### Mbrola English voices
```bash
sudo apt install mbrola-en1 mbrola-us1 mbrola-us2 mbrola-us3
```

#### Mbrola Spanish voices
```bash
sudo apt install mbrola-es1 mbrola-es2 mbrola-es3 mbrola-es4
sudo apt install mbrola-mx1 mbrola-mx2 mbrola-vz1
```

### Vosk models suggested installation

Run as a normal user in your home.

#### English Vosk model
```bash
cd
mkdir vosk-models
cd vosk-models
wget 'https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip'
unzip vosk-model-small-en-us-0.15.zip
```
#### Spanish Vosk model
```bash
cd
mkdir vosk-models
cd vosk-models
wget 'https://alphacephei.com/vosk/models/vosk-model-small-es-0.22.zip'
unzip vosk-model-small-es-0.22.zip
```

## Installation

TODO

## Usage

TODO

# Bibliography

* [Boi4 subextractor](https://github.com/boi4/subextractor)
* [configuration pour transcrire des fichiers audio wav avec Vosk](https://forge.chapril.org/tykayn/transcription)
* [Vosk models](https://alphacephei.com/vosk/models)
