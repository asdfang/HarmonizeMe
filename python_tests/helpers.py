from PitchConverter import *
from essentia import *
from essentia.standard import *
from aubio import source, pitch, onset
from YIN import *
from segmenter import *
import numpy as np
import librosa
import aubio

'''
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
HELPER FUNCTIONS:
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
'''

hopSize = 128 #units: samples
frameSize = 2048 #units: samples
sr = 44100 #sample rate: 44100 samples per second
guessUnvoiced = True # read the algorithm's reference for more details
run_predominant_melody = PitchMelodia(guessUnvoiced=guessUnvoiced,
                                      frameSize=frameSize,
                                      hopSize=hopSize)
methods = ['yinfft']



'''
turning verbose midi (every hop_size samples) into detector_results based off ground_truth_onsets
'''
def delete_zeros_ones(alist):
	newlist = []
	for element in alist:
		if element != 0.0 or element != -1.0:
			newlist.append(element)
	return newlist

def verbose_to_detected_midi(detected_midi_verbose, true_onsets, hop_size):
	indices = []
	for val in true_onsets:
		indices.append(int(np.around(val / hop_size)))
	#print indices

	partitioned_signal = []
	# don't get beginning of signal to first onset (starting silence):
	# partitioned_signal.append(detected_midi_verbose[0:indices[0]])
	# rest of signal to last onset (so, not including last note):
	for ii in range(len(indices) - 1):
		x = indices[ii]
		y = indices[ii + 1]
		partitioned_signal.append(detected_midi_verbose[x:y])
	# last note:
	partitioned_signal.append(detected_midi_verbose[indices[-1]:len(detected_midi_verbose)])
	#print partitioned_signal

	detected_midi = []
	for note in partitioned_signal:
		detected_midi.append(np.median(delete_zeros_ones(note)))

	return detected_midi


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
	cands = {}

	#pad with zeros:
	audio_length = a.size
	num_padded_zeros = 128 - (audio_length % 128)
	a = np.concatenate([a, np.zeros(num_padded_zeros, dtype=np.float32)])


	for method in methods:
	    p = aubio.pitch(method, frameSize, hopSize, sr)
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
	o = onset("default", frameSize, hopSize, sr)
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
def YIN_pitches_onsets(float_data, sr):
	#ytracker = Yin(sr, hopsize, windowsize)
	#freqs = ytracker.trackPitch(float_data)

	frqs, onsets = segmenter(float_data, sr)

	midis = []

	for val in frqs:
		if val == -1:
			midis.append(-1)
		else:
			midis.append(PitchConverter.exact_midi_from_freq(val))

	return midis, onsets

'''
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
'''