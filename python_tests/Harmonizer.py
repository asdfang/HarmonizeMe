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
import numpy

from ProgressionCreater import *
from PitchConverter import *

HOP_SIZE = 512

'''
Get a note in MIDI (rounded to nearest semitone) given a note represented by array of MIDIs or sound file.
	Takes in: (string filename) or (float array_of_doubles)
	Output: (float midi_num)
'''
def determine_pitch(pitchfile): #it will either be a filename or a numpy array
	if isinstance(pitchfile, str): #if it's a file
		pitches, onsets = getpitches(pitchfile, 44100)
		notes = delete_zeros(pitches)
	else: #if it's a numpy array
		notes = delete_zeros(pitchfile) #sorry this is named badly

	midi_num = numpy.around(numpy.median(notes))
	
	return midi_num #midi_num is the tonic

'''
Deletes zeros from a list
	Takes in: ([double] alist)
	Outputs: ([double] new_list))
'''
def delete_zeros(alist):
	newlist = []
	for element in alist:
		if element != 0.0:
			newlist.append(element)
	return newlist


'''
Gets pitches every HOP_SIZE (512) in MIDI, and onsets in samples from a filename of a sound file
	Takes in: (string filename), (double samplerate)
	Output: ([double] midi_numbers), ([int] onset_in_samples)
--> NEED a version where it can just take in a float array
'''
def getpitches(filename, samplerate):

	#downsample = 1
	#samplerate = 44100 / downsample	
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

'''
Process arguments from command line and give to globals
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
GETTING TONIC AND EXPITCH
'''
tonic = determine_pitch(filename)
#expitch = determine_pitch(melodyfilename) #not doing just a single pitch anymore
print 'Tonic midi number:'
print tonic

pitchesmelody_verb, onset_samps = getpitches(melodyfilename, 44100)

pitch_indices = []

#get rid of zero onset
onset_samps = delete_zeros(onset_samps)

for ii in range(len(onset_samps)):
	pitch_indices.append(numpy.around(onset_samps[ii] / HOP_SIZE))

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


melodysd = []
pitchspliced.append(pitchesmelody_verb[pitch_indices[-1]:len(pitchesmelody_verb)])
for ii in range(len(pitchspliced)):
	determined_pitch = determine_pitch(pitchspliced[ii])
	melodysd.append(PitchConverter.pitch_in_sd(determined_pitch, tonic))

'''
splicing the audio; audiomelody is np.array representing wav file
'''
audiomelody, sr = librosa.core.load(melodyfilename, sr=44100)
audiospliced = []
audiospliced.append(audiomelody[0:onset_samps[0]])
for ii in range(len(onset_samps) - 1):
	x = onset_samps[ii]
	y = onset_samps[ii + 1]
	audiospliced.append(audiomelody[x:y])
#getting the last note
audiospliced.append(audiomelody[onset_samps[-1]:len(audiomelody)])







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
def harmonize(melody, tonic, splicedaudio, mode):
	prog_creater = ProgressionCreater(melody, mode)
	realized = prog_creater.get_progression_semitones()
	'''
	for pitch, chord_choice in zip(melody, progression):
		realized.append(fill_chord(pitch, chord_choice))
	'''
	#print 'Here is your random progression: '
	#print realized
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

	#complete = (numpy.array(complete)).flatten()
	outputname = str(raw_input('Please enter a file name for your output file (include .wav): '))
	librosa.output.write_wav(outputname, complete, 44100)

	return realized

#has this above:
#tonic = determine_pitch(filename)
#expitch = determine_pitch(melodyfilename)
#

#print pitch_in_sd(expitch, tonic)


#running example
#ex1_melody = []
#ex1_melody.append(pitch_in_sd(expitch, tonic))
print 'This is your melody in scale degrees (ignore 0s)'
print melodysd
harmonize(melodysd, tonic, audiospliced, mode)