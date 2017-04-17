import numpy as np

actual = [0.0, 1.0, 1.1, 1.5, 1.65]
expected = [0.0, 1.0, 1.5]

new_actual = []
new_expected = []
for val in actual:
	new_actual.append(int(val*44100))
for val in expected:
	new_expected.append(int(val*44100))

'''
Takes in: (double or int ground_truth) -- ground truth onsets in seconds or samples
Takes in: (double or int detected_onsets) -- onsets in sec or samps from onset detector
Takes in: (int mode) -- 0: in seconds, 1: in samples
'''
def onset_detector_quality(ground_truth, detected_onsets, mode):

	missed_onsets = [] # this will be returned
	closest_onsets = [] # this will be returned
	correct_onsets = [] # this will be returned

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
	false_onsets = []
	for d_onset in detected_onsets:
		if d_onset not in closest_onsets:
			false_onsets.append(d_onset)

	print "ONSET DETECTOR QUALITY RESULTS:"
	print "ground_truth_onsets: " + str(ground_truth)
	print "correct_onsets: " + str(correct_onsets)
	print "closest_onsets: " + str(closest_onsets)
	print "avg_diff: " + str(avg_diff)
	print "missed_onsets: " + str(missed_onsets)
	print "false_onsets: " + str(false_onsets)
	
	return correct_onsets, closest_onsets, avg_diff, missed_onsets, false_onsets

#results = onset_detector_quality(new_expected, new_actual, 1)


'''

Takes in: (double true_midi_array) -- has detected pitches in midi, every hop_size samples

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
		detected_midi.append(np.median(note))

	correct = 0
	incorrect = 0
	# compare true_midi_array to detected_midi
	for ii in range(len(true_midi_array)):
		# mod to disregard octave displacement
		diff = abs(true_midi_array[ii] - detected_midi[ii]) % 12.0
		if diff < 0.5 or diff > 11.5:
			correct = correct + 1
		else:
			incorrect = incorrect + 1

	percent_correct = (correct * 1.0) / (incorrect + correct * 1.0)

	print "PITCH DETECTOR QUALITY RESULTS:"
	print "ground_truth_midi: " + str(true_midi_array)
	print "detected_midi: " + str(detected_midi)
	print "percent_correct: " + str(percent_correct)
	return detected_midi, percent_correct

groundtruthmidi = [60.0, 62.0, 64.0]
detectedmidi = [0.0, 0.0, 0.0, 0.0, 0.0, 72.0, 72.0, 72.0, 72.0, 72.0, 74.0, 74.0, 74.0, 74.0, 74.0, 68.0, 68.0, 68.0, 68.0, 68.0]
onsets = [5, 10, 15]
#results = pitch_detector_quality(groundtruthmidi, detectedmidi, onsets, 1)
#print results