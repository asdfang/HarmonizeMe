#Alexander Fang; 4/10/2017
'''
Main file to interact with user in command line.
Splices audio with detected onsets, determines MIDIs of closest semitone given those onsets.
Gets random progression based off of melody notes and mode, and harmonizes the original sung input.

How to use as of 4/10/2017: run python script python_tests/Harmonizer.py:

python python_tests/Harmonizer.py tonicfilename sungmelodyfilename mode

Inputs:
	tonicfilename: a sound file containing only one sung note representing the tonic
	sungmelodyfilename: a sound file containing the full melody
	mode: 0 for Major, 1 for minor
Outputs:
	written sound file containing harmonized sung input
'''

import sys
from aubio import source, pitch, onset
# from __future__ import print_function

import argparse
import librosa
import aubio
import numpy

from ProgressionCreater import *
from PitchConverter import *

methods = ['yinfft']
hopSize = 128
frameSize = 2048
sampleRate = 44100

def run_pitch(p, input_vec):
    cands = []
    for vec_slice in input_vec.reshape((-1, p.hop_size)):
        a = p(vec_slice)[0]
        cands.append(a)
    return cands

def run_onset(o, input_vec):
	onsets = []
	for vec_slice in input_vec.reshape((-1, o.hop_size)):
		a = o(vec_slice)[0]
		onsets.append(a)
	return onsets


def aubio_pitches(audio):
	a = audio
	#pad with zeros:
	audio_length = a.size
	num_padded_zeros = 128 - (audio_length % 128)
	a = np.concatenate([a, np.zeros(num_padded_zeros, dtype=np.float32)])
	cands = {}

	for method in methods:
	    p = aubio.pitch(method, frameSize, hopSize, sampleRate)
	    cands[method] = run_pitch(p, a)
	    #print method
	    #print "Number of windows: " + str(len(cands[method]))
	    #print(cands[method])

	midis = []
	for freq in cands['yinfft']:
		if freq == 0.0:
			midis.append(0.0)
		else:
			midis.append(PitchConverter.exact_midi_from_freq(freq))
	return midis

def aubio_onsets(audio):
	a = audio
	#pad with zeros:
	audio_length = a.size
	num_padded_zeros = 128 - (audio_length % 128)
	a = np.concatenate([a, np.zeros(num_padded_zeros, dtype=np.float32)])
	onsets = []

	#methods: 'phase' and 'default'
	o = onset("default", frameSize, hopSize, sampleRate)
	onsets = run_onset(o, a)

	#convert into samples
	onset_samps = []
	length = len(onsets)
	for ii in range(0, length):
		if onsets[ii] != 0.0:
			onset_samps.append(ii*128)
	return onset_samps


'''
Get a note in MIDI (rounded to nearest semitone) given a note represented by array of MIDIs or sound file.
	Takes in: float array_of_doubles
	Output: (float midi_num)
'''
def determine_pitch(array):
	notes = delete_zeros_ones(array)
	midi_num = numpy.around(numpy.median(notes))
	return float(midi_num)

def delete_zeros_ones(alist):
	newlist = []
	for element in alist:
		if element != 0.0 and element != -1.0:
			newlist.append(element)
	return np.array(newlist)

'''
Call harmonizeme to harmonize the audio, given in an nd.array
'''

'''
if len(sys.argv) < 3:
    print "Usage: %s <inputfilename1>  <inputfilename2> [mode] [samplerate]" % sys.argv[0]
    sys.exit(1)

filename = sys.argv[1]
melodyfilename = sys.argv[2]
mode = int(sys.argv[3])
downsample = 1
samplerate = 44100 / downsample
if len( sys.argv ) > 4: samplerate = int(sys.argv[4])
'''

def harmonizeme(audio, tonic_input, mode_input, shift_input):
	'''
	GETTING TONIC AND EXPITCH
	'''
	tonic = tonic_input*1.0
	mode = int(mode_input) #what type is mode_input?

	#print 'Tonic midi number:'
	#print tonic

	audiolist = audio.tolist() #is this useful? apparently
	audio = audio.astype(np.float32)

	#aubio results
	pitchesmelody_verb = aubio_pitches(audio)
	onset_samps = aubio_onsets(audio)

	#if no onsets, return original audio. -- alert the user?
	if len(onset_samps) == 0:
		return audio

	pitch_indices = []

	#get rid of zero onset
	onset_samps = delete_zeros_ones(onset_samps)

	for ii in range(len(onset_samps)):
		pitch_indices.append(numpy.around(onset_samps[ii] / hopSize))

	'''
	splicing the pitch array
	'''
	pitchspliced = []
	#getting the starting silence
	pitchspliced.append(pitchesmelody_verb[0:pitch_indices[0]])
	#getting the rest of the sound (except for the last)
	for ii in range(len(pitch_indices) - 1):
		x = pitch_indices[ii]
		y = pitch_indices[ii + 1]
		pitchspliced.append(pitchesmelody_verb[x:y])
	#getting the last note
	pitchspliced.append(pitchesmelody_verb[pitch_indices[-1]:len(pitchesmelody_verb)])


	melodysd = []
	melody_midi = [] #for plotting
	for ii in range(len(pitchspliced)):
		determined_pitch = determine_pitch(pitchspliced[ii])
		melody_midi.append(determined_pitch)
		melodysd.append(PitchConverter.pitch_in_sd(determined_pitch, tonic))

	'''
	splicing the audio; audiomelody is np.array representing wav file
	'''
	#audiomelody, sr = librosa.core.load(melodyfilename, sr=44100)
	audiomelody = audio
	audiospliced = []
	audiospliced.append(audiomelody[0:onset_samps[0]])
	for ii in range(len(onset_samps) - 1):
		x = onset_samps[ii]
		y = onset_samps[ii + 1]
		audiospliced.append(audiomelody[x:y])
	#getting the last note
	audiospliced.append(audiomelody[onset_samps[-1]:len(audiomelody)])

	completedaudio, realized = harmonize(melodysd, tonic, audiospliced, mode, shift_input)

	#convert samps to time; for plotting
	onset_times = []
	for ii in range(len(onset_samps)):
		onset_times.append(float(onset_samps[ii]) / float(sampleRate))

	#delete first of melody_midi (to delete the starting silence)
	del melody_midi[0]


	print "Melody in midi: " + str(melody_midi)
	rounded_onsets = []
	for onset in onset_times:
		rounded_onsets.append(round(onset, 2))
	print "Onset times (seconds): " + str(rounded_onsets)
	return completedaudio, pitchesmelody_verb, melody_midi, onset_times


'''
Main function. Starts harmonization.
Takes in a melody and chosen progression by user and returns the realized form of the progression.
	Takes in: ([int] melody_in_scale_degrees) -- Ex: [1, 2, 3, 2, 1, 7, 1]
	Takes in: ([int] tonic_in_midi) -- Ex: 60 (C)
	Takes in: ([[double]] spliced_audio) -- spliced with onsets
	Takes in: ([int] mode) -- 0: major; 1: minor -- Ex: 0
	Output: writes harmonized sound file

Example usage:
harmonize([1, 2, 3, 2, 1, 7, 1, 5, 6, 7, 1, 2, 1], 60, audiospliced, 0)

This is your melody in scale degrees (ignore 0s)
[0, 7, 1, 1, 4, 1, 1, 1, 7, 2, 6, 1, 4]
Here is your random progression in halfsteps away from melodic note: 
[[0, -5, -8], [0, -3, -7], [0, -9, -16], [0, -3, -7], [0, -8, -12], [0, -4, -16], [0, -3, -7], [0, -8, -12], [0, -9, -12], [0, -4, -16], [0, -8, -3], [0, -7, -3], [0, -3, -7]]
Please enter a file name for your output file (include .wav): 
'''
def harmonize(melody, tonic, splicedaudio, mode, shift):
	prog_creater = ProgressionCreater(melody, mode, shift)
	realized, realized_RN = prog_creater.get_progression_semitones()
	'''
	for pitch, chord_choice in zip(melody, progression):
		realized.append(fill_chord(pitch, chord_choice))
	'''
	print 'Here is your random progression: '
	print realized_RN
	print 'Here is your random progression in halfsteps away from melodic note: '
	prog_hs = realized
	print prog_hs

	'''
	making the new pitches in a long melody; taking in melodysd, ex1_prog, tonic, splicedaudio
	'''
	complete = []
	complete = numpy.array(complete)
	for ii in range(len(melody)):
		npchord = [] #has 3 np arrays representing notes
		melodynote = numpy.array(splicedaudio[ii])
		npchord.append(melodynote)
		npchord.append(librosa.effects.pitch_shift(melodynote, 44100, n_steps = prog_hs[ii][1]))
		npchord.append(librosa.effects.pitch_shift(melodynote, 44100, n_steps = prog_hs[ii][2]))
		npchord = numpy.array(npchord)
		soundingchord = npchord[0] + npchord[1] + npchord[2]
		#complete.append(soundingchord)
		complete = numpy.concatenate((complete, soundingchord))

	return complete, realized
