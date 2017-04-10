# HarmonizeMe
Web app to make chordal harmony to accompany a user sung input

Libraries needed: librosa, numpy, aubio

How to use as of 4/10/2017:
run python script python_tests/Harmonizer.py:

python python_tests/Harmonizer.py tonicfilename sungmelodyfilename mode

tonicfilename: a sound file containing only one sung note representing the tonic
sungmelodyfilename: a sound file containing the full melody
mode: 0 for Major, 1 for minor
