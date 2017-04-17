from detector_tests import *
from PitchConverter import *
from aubio import source, pitch, onset
import numpy as np
import argparse
import librosa

samplerate = 44100
hopsize = 512

def getpitches(filename, samplerate, hopsize):
	HOP_SIZE = hopsize
	downsample = 1
	samplerate = 44100 / downsample	
	win_s = 4096 / downsample # fft size
	hop_s = HOP_SIZE  / downsample # hop size

	s = source(filename, samplerate, hop_s)
	samplerate = s.samplerate

	tolerance = 0.8

	pitch_o = pitch("yin", win_s, hop_s, samplerate)
	pitch_o.set_unit("midi")
	pitch_o.set_tolerance(tolerance)

	o = onset("default", win_s, hop_s, samplerate)
	onsets = []

	pitches = []
	confidences = []
	#number = 0
	# total number of frames read
	total_frames = 0
	while True:
	    samples, read = s()
	    pitch1 = pitch_o(samples)[0]
	    #pitch = int(round(pitch))
	    confidence = pitch_o.get_confidence()
	    if o(samples):
        	# print "%f" % o.get_last_s()
        	onsets.append(o.get_last())
	    #if confidence < 0.8: pitch = 0.
	    #print "%f %f %f" % (total_frames / float(samplerate), pitch, confidence)
	    pitches += [pitch1]
	    confidences += [confidence]
	    total_frames += read
	    #number = number + 1
	    if read < hop_s: break

	if 0: sys.exit(0)

	return pitches, onsets

pathtosound = "../PitchOnsetTrackerTests/Male_1a/Male_1a.wav"
pathtolabels = "../PitchOnsetTrackerTests/Male_1a/Male_1a_Labels_midi.txt"
soundfile, sr = librosa.core.load(pathtosound, sr=samplerate)
detector_results = getpitches(pathtosound, samplerate, hopsize)


# parsing ground truths
ground_truth_midi = []
ground_truth_onsets_seconds = []
lines = []


with open(pathtolabels) as input:
    lines = zip(*(line.strip().split('\t') for line in input))

for midi, onset in zip(lines[2], lines[0]):
	if midi.strip() != "SIL":
		ground_truth_midi.append(float(midi))
		ground_truth_onsets_seconds.append(float(onset))

# convert onsets to samples
ground_truth_onsets_samps = []
for onset in ground_truth_onsets_seconds:
	ground_truth_onsets_samps.append(int(np.around(onset*samplerate)))

onset_results = onset_detector_quality(ground_truth_onsets_samps, detector_results[1], 1)
pitch_results = pitch_detector_quality(ground_truth_midi, detector_results[0], ground_truth_onsets_samps, hopsize)