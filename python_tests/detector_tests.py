'''
Helps evaluate pitch and onset detection (never called, used by detector_quality.py)
'''

import numpy as np

actual = [0.0, 1.0, 1.1, 1.5, 1.65]
expected = [0.0, 1.0, 1.5]

new_actual = []
new_expected = []
for val in actual:
	new_actual.append(int(val*44100))
for val in expected:
	new_expected.append(int(val*44100))





def delete_zeros_ones(alist):
	newlist = []
	for element in alist:
		if element != 0.0 or element != -1.0:
			newlist.append(element)
	return newlist

'''
Gets quality of the onset detector
	Takes in: (double or int ground_truth) -- ground truth onsets in seconds or samples
	Takes in: (double or int detected_onsets) -- onsets in sec or samps from onset detector
	Takes in: (int mode) -- 0: in seconds, 1: in samples
	Output: (double or int correct_onsets) -- which detected onsets were within the threshold
			(double or int closest_onsets) -- array of the closest onsets
			(double or int avg_diff) -- average difference between a ground truth onset and its closest onset
			(double or int missed_onsets) -- ground truth onsets that didn't have a detected onset within the threshold
			(double or int false_onsets) -- detected onsets that weren't a ground truth onset

'''
def onset_detector_quality(ground_truth, detected_onsets, mode):

	missed_onsets = [] # this will be returned
	closest_onsets = [] # this will be returned
	correct_onsets = [] # this will be returned
	false_onsets = [] # this will be returned


	if (len(detected_onsets) == 0):
											#avg_diff					#recall, precision
		return correct_onsets, closest_onsets, 0, missed_onsets, false_onsets, 0, 0


	threshold = 0
	if mode == 0:
		threshold = .10 # seconds
	else:
		threshold = 4410 # samples (assuming 44100 sample rate)

	for e_onset in ground_truth:
		# see which onset in detected_onsets is closest:
		min_diff = abs(e_onset - detected_onsets[0])
		min_diff_ii = 0

		for ii in range(1, len(detected_onsets)):
			curr_diff = abs(e_onset - detected_onsets[ii])
			if curr_diff < min_diff:
				min_diff = curr_diff
				min_diff_ii = ii

		closest_onsets.append(detected_onsets[min_diff_ii])

		# if the closest onset was more than .25 seconds away, then we missed it.
		if min_diff > threshold:
			missed_onsets.append(e_onset)
		else:
			# if it was close enough, add it was correct.
			correct_onsets.append(detected_onsets[min_diff_ii])

	# calculating the average difference between ground truth and detected onsets
	total_diff = 0
	for e_onset, c_onset in zip(ground_truth, closest_onsets):
		total_diff = total_diff + abs(e_onset - c_onset)

	avg_diff = total_diff / len(ground_truth) # this will be returned

	# get false onsets
	for d_onset in detected_onsets:
		if d_onset not in closest_onsets:
			false_onsets.append(d_onset)

	'''
	print "***** ONSET DETECTOR QUALITY RESULTS:"
	print "   ground_truth_onsets: " + str(ground_truth)
	print "   correct_onsets: " + str(correct_onsets)
	print "   closest_onsets: " + str(closest_onsets)
	print "   avg_diff: " + str(avg_diff)
	print "   missed_onsets: " + str(missed_onsets)
	print "   false_onsets: " + str(false_onsets)
	'''
	
	num_ground_truth_onsets = len(ground_truth)

	recall = ((len(correct_onsets) * 1.0) / num_ground_truth_onsets) * 100
	precision = (len(correct_onsets) / (1.0 * len(detected_onsets))) * 100
	
	#percent_missed = (len(missed_onsets) * 1.0) / num_ground_truth_onsets))

	return correct_onsets, closest_onsets, avg_diff, missed_onsets, false_onsets, recall, precision

#results = onset_detector_quality(new_expected, new_actual, 1)


'''
Gets quality of the pitch detector
	Takes in: (double true_midi_array) -- ground truth melody in midi
	Takes in: (double detected_midi_verbose) -- has detected pitches in midi, every hop_size samples
	Takes in: (int true_onsets) -- the ground truth onsets in samples
	Takes in: (int hop_size) -- hop hop_size
	Outputs: (double detected_midi) -- detected midi of soundfile partitioned by ground truth onsets
			 (int percent_correct) -- percent of pitches correct (ignores octave errors)

'''
def pitch_detector_quality(true_midi_array, detected_midi_verbose, true_onsets, hop_size):
	# convert ground truth onsets (in samples) to indices of array (affected by hop_size)
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

	differences = []

	correct = 0
	incorrect = 0
	# compare true_midi_array to detected_midi
	for ii in range(len(true_midi_array)):
		# mod to disregard octave displacement
		diff = abs(true_midi_array[ii] - detected_midi[ii]) % 12.0
		differences.append(diff)
		if diff < 1.0 or diff > 11.0:
			correct = correct + 1
		else:
			incorrect = incorrect + 1


	percent_correct = (correct * 1.0) / (incorrect + correct * 1.0) * 100

	'''
	print "***** PITCH DETECTOR QUALITY RESULTS:"
	print "   ground_truth_midi: " + str(true_midi_array)
	print "   detected_midi: " + str(detected_midi)
	print "   percent_correct: " + str(percent_correct)
	print "   differences: " + str(differences)
	'''

	return detected_midi, percent_correct

groundtruthmidi = [60.0, 62.0, 64.0]
detectedmidi = [0.0, 0.0, 0.0, 0.0, 0.0, 72.0, 72.0, 72.0, 72.0, 72.0, 74.0, 74.0, 74.0, 74.0, 74.0, 68.0, 68.0, 68.0, 68.0, 68.0]
onsets = [5, 10, 15]
#results = pitch_detector_quality(groundtruthmidi, detectedmidi, onsets, 1)
#print results