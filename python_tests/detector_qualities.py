'''
Gets quality of pitch and onset detection; has each pitch/onset detector function
'''

from detector_tests import *
from PitchConverter import *
from essentia import *
from essentia.standard import *
from aubio import source, pitch, onset
from YIN import *
from segmenter import *
import numpy
import argparse
import librosa
import os
import aubio

numpy.set_printoptions(threshold='nan')


hopSize = 128
frameSize = 2048
sampleRate = 44100
guessUnvoiced = True # read the algorithm's reference for more details
run_predominant_melody = PitchMelodia(guessUnvoiced=guessUnvoiced,
                                      frameSize=frameSize,
                                      hopSize=hopSize);

# Load audio file, apply equal loudness filter, and compute predominant melody
#audio = MonoLoader(filename = pathtosoundfile, sampleRate=sampleRate)()
#audio = EqualLoudness()(audio)
#essentia_pitch, confidence = run_predominant_melody(audio)


indir = '/Users/asdfang/Desktop/YEAR3/17SPRING/399EECSindependentstudy/HarmonizeMe/PitchOnsetTrackerTests'


''' IMPORTANT GLOBALS: '''
array_groundlabels = []
array_soundfiles = []
#methods = ['default', 'schmitt', 'fcomb', 'mcomb', 'yin', 'yinfft']
methods = ['yinfft']


''' getting file names'''
for root, dirs, filenames in os.walk(indir):
	for d in dirs:
		for rt, dr, flnames in os.walk(os.path.join(root, d)):
			files = [f for f in flnames if not f[0] == '.'] #ignore hidden
			if files[1].startswith("Female", 0, len(files[1])) and files[1].endswith(".txt", 0, len(files[1])):
				array_groundlabels.append("../PitchOnsetTrackerTests/" + d + "/" + files[1])
			if files[0].startswith("Female", 0, len(files[0])) and files[0].endswith(".wav", 0, len(files[0])):
				array_soundfiles.append("../PitchOnsetTrackerTests/" + d + "/" + files[0])
			else:
				break

'''
Aubio helper
'''
def run_pitch(p, input_vec):
    cands = []
    for vec_slice in input_vec.reshape((-1, p.hop_size)):
        a = p(vec_slice)[0]
        cands.append(a)
    return cands

'''
Aubio helper
'''
def run_onset(o, input_vec):
	onsets = []
	for vec_slice in input_vec.reshape((-1, o.hop_size)):
		a = o(vec_slice)[0]
		onsets.append(a)
	return onsets

'''
Aubio's pitch detector
	Takes in: (float[] audio) -- raw audio data
	Output: (float[] pitches) -- detected midi of pitch every hopsize samples
'''
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

'''
Aubio's onset detector
	Takes in: (float[] audio) -- raw audio data
	Output: (int[] onset_samps) -- onsets in samples
'''
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
Essentia pitch and onset detector
'''
def essentia_pitches_onsets(soundfile):
	pitches = run_predominant_melody(soundfile)

	od2 = OnsetDetection(method = 'complex')

	w = Windowing(type = 'hann')
	fft = FFT() # this gives us a complex FFT
	c2p = CartesianToPolar() # and this turns it into a pair (magnitude, phase)

	pool = Pool()

	# let's get down to business
	for frame in FrameGenerator(soundfile, frameSize = 2048, hopSize = 128):
	    mag, phase, = c2p(fft(w(frame)))
	    pool.add('features.complex', od2(mag, phase))


	# Phase 2: compute the actual onsets locations
	onsets = Onsets()

	onsets_complex = onsets(array([ pool['features.complex'] ]), [ 1 ])

	midis = []
	for val in pitches[0]:
		if val == 0:
			midis.append(0)
		else:
			midis.append(PitchConverter.exact_midi_from_freq(val))

	return midis, onsets_complex

'''
YIN pitches and onset detector
'''
def YIN_pitches_onsets(float_data, samplerate):
	#ytracker = Yin(samplerate, hopsize, windowsize)
	#freqs = ytracker.trackPitch(float_data)

	frqs, onsets = segmenter(float_data, samplerate)

	midis = []

	for val in frqs:
		if val == -1:
			midis.append(-1)
		else:
			midis.append(PitchConverter.exact_midi_from_freq(val))

	return midis, onsets

##########################################################################################

'''
Gets the quality of the pitch and onset get_detection_quality
	Takes in: (string path_to_sound_file) -- path to audio file
	Takes in: (string path_to_groundtruth_labels) -- path to ground truth labels
	Output: lots of information (see functions in detector_tests.py)
'''
def get_detection_quality(path_to_sound_file, path_to_groundtruth_labels):

	pathtosound = path_to_sound_file
	pathtolabels = path_to_groundtruth_labels
	soundfile, sr = librosa.core.load(pathtosound, sr=sampleRate)

	#padding with zeros:
	audio_length = soundfile.size
	num_padded_zeros = 128 - (audio_length % 128)
	soundfile = np.concatenate([soundfile, np.zeros(num_padded_zeros, dtype=np.float32)])
	
	#parsing ground truths
	ground_truth_midi = []
	ground_truth_onsets_seconds = []
	ground_truth_onsets_samps = []

	lines = []

	with open(pathtolabels) as input:
	    lines = zip(*(line.strip().split('\t') for line in input))

	for midi, onset in zip(lines[2], lines[0]):
		if midi.strip() != "SIL":
			ground_truth_midi.append(float(midi))
			ground_truth_onsets_seconds.append(float(onset))

	# convert onsets to samples
	for onset in ground_truth_onsets_seconds:
		ground_truth_onsets_samps.append(int(numpy.around(onset*sampleRate)))


	''' ********************** FOR AUBIO '''
	#onset detector quality 
	#aubio_onset_results = onset_detector_quality(ground_truth_onsets_samps, aubio_results[1], 1)

	#pitch detector quality
	#aubio_pitch_results = pitch_detector_quality(ground_truth_midi, aubio_results[0], ground_truth_onsets_samps, hopSize)
	#aubio_pitch = aubio_pitches(soundfile) # this has midis
	#aubio_onset = aubio_onsets(soundfile)
	
	aubio_pitch_results = aubio_pitches(soundfile)
	aubio_onset_results = aubio_onsets(soundfile)

	aubio_pitch_quality = pitch_detector_quality(ground_truth_midi, aubio_pitch_results, ground_truth_onsets_samps, hopSize)
	aubio_onset_quality = onset_detector_quality(ground_truth_onsets_samps, aubio_onset_results, 1)

	#print aubio_pitch_results
	#print aubio_onset_results
									#recall: #percent of positive cases caught			#precision: percent of positive predictions correct
									#correctly detected positives / expected positives	# correctly detected positives / total detected positives
									#len(correct)/len(groundtruths)						#len(correct)/len(detected)
	return aubio_pitch_quality[1], aubio_onset_quality[5], aubio_onset_quality[6]



 	''' ******************** FOR YIN:
	#onsets in time
	# FOR YIN: hop: 1024, framesize: 2048
	YIN_pitch_results, YIN_onset_results = YIN_pitches_onsets(soundfile, sampleRate)
	YIN_pitch_quality = pitch_detector_quality(ground_truth_midi, YIN_pitch_results, ground_truth_onsets_samps, 1024.0)
	YIN_onset_quality = onset_detector_quality(ground_truth_onsets_samps, YIN_onset_results, 1)

	# percent correct pitches,       percent correct onsets, 				percent false onsets
	return YIN_pitch_quality[1], YIN_onset_quality[5], YIN_onset_quality[6]
	'''



	''' ************************ FOR ESSENTIA:
	
	essentia_pitch_results, essentia_onset_results = essentia_pitches_onsets(soundfile)

	essentia_pitch_quality = pitch_detector_quality(ground_truth_midi, essentia_pitch_results, ground_truth_onsets_samps, hopSize)
	essentia_onset_quality = onset_detector_quality(ground_truth_onsets_samps, essentia_onset_results, 1)

	return essentia_pitch_quality[1], essentia_onset_quality[5], essentia_onset_quality[6]
	'''


YIN_all_pitches_percent_correct = []
YIN_all_onsets_recall = []
YIN_all_onsets_precision = []

aubio_all_pitches_percent_correct = []
aubio_all_onsets_recall = []
aubio_all_onsets_precision = []

essentia_all_pitches_percent_correct = []
essentia_all_onsets_recall = []
essentia_all_onsets_precision = []


''' *** UNCOMMENT WHEN DONE WITH onepitch.py
print "len(array_soundfiles): " + str(len(array_soundfiles))
for ii in range(0, len(array_soundfiles)):
#for ii in range(5, 6):

	soundfilepath = array_soundfiles[ii]
	groundtruthpath = array_groundlabels[ii]

	print "*****************************"
	print "Viewing: " + array_soundfiles[ii]
	results = get_detection_quality(soundfilepath, groundtruthpath)
	print "Pitches percent correct: " + str(results[0])
	print "Onsets precision: " + str(results[1])
	print "Onsets recall: " + str(results[2])

	aubio_all_pitches_percent_correct.append(results[0])
	aubio_all_onsets_recall.append(results[1])
	aubio_all_onsets_precision.append(results[2])


print aubio_all_pitches_percent_correct
print aubio_all_onsets_recall
print aubio_all_onsets_precision
'''




#audio = MonoLoader(filename = soundfile, sampleRate=sampleRate)()
#audio = EqualLoudness()(audio)










#get_detection_quality(pathtosoundfile, pathtogroundlabels)