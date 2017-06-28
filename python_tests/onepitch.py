''' This is used to plot the results from the pitch detector.
	To change which sound file you're looking at, modify the 'testing' variable.
	To change which note you're looking at, modify the 'ii' variable.
	To change if you're looking at a single note or the entire melody,
		modify the 'sung_note' variable, and 'timestamps', and axarr[0].scatter
'''


#import pitch detectors:
from helpers import *
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
np.set_printoptions(threshold='nan')

hopSize = 128 #units: samples
frameSize = 2048 #units: samples
sr = 44100 #sample rate: 44100 samples per second
guessUnvoiced = True # read the algorithm's reference for more details
run_predominant_melody = PitchMelodia(guessUnvoiced=guessUnvoiced,
                                      frameSize=frameSize,
                                      hopSize=hopSize)
methods = ['yinfft']

indir = '/Users/asdfang/Desktop/YEAR3/17SPRING/399EECSindependentstudy/HarmonizeMe/PitchOnsetTrackerTests'

''' MODIFY testing AND ii BASED ON WHAT TEST AND WHICH LABEL YOU'RE LOOKING AT: '''
testing = 'Female_1a'
ii = 3 #looking at the ii-th label, starting from 0

sound_file = testing + '.wav'
label_file = testing + '_Labels.txt'

sound_path = indir + '/' + testing + '/' + sound_file
label_path = indir + '/' + testing + '/' + label_file

#loading full sound file into a mono array of dtype=numpy.float32
audio_array, dummy_var = librosa.core.load(sound_path, sr=sr)

#parsing text file
full_labels = open(label_path)
lines = full_labels.readlines()
label_info = [] #parsed file
for l in lines:
	label_info.append(l.strip().split('\t')) #split with spaces as separation; strip() takes care of the \t's
#label_info[x] holds the xth label; elements are strings
#label[x][0] holds the start time, label[x][1] holds the end time, label[x][2] holds the info for the xth label

#parsing ground truths
ground_truth_onsets_seconds = []
ground_truth_onsets_samps = []
lines = []
with open(label_path) as input:
    lines = zip(*(line.strip().split('\t') for line in input))

for midi, onset in zip(lines[2], lines[0]):
	ground_truth_onsets_seconds.append(float(onset))
# convert onsets to samples
for onset in ground_truth_onsets_seconds:
	ground_truth_onsets_samps.append(int(numpy.around(onset*sr)))

#start and end in terms of seconds
s_time = float(label_info[ii][0])
e_time = float(label_info[ii][1])
#start and end in terms of samples
start = int(np.rint(s_time * float(sr)))
end = int(np.rint(e_time * float(sr)))
lbl = label_info[ii][2]

#making midi arrays
ground_truth_midis = []
for l in label_info:
	if l[2].strip() == "SIL":
		ground_truth_midis.append(90.0)
	else:
		ground_truth_midis.append(float(l[2]))

''' MODIFY THIS BASED ON ISOLATED NOTE VS. FULL MELODY: '''
# ISOLATED NOTE:
sung_note = audio_array[start:end]

#FULL MELODY:
# sung_note = audio_array
# s_time = 0.0
# e_time = librosa.get_duration(audio_array, sr=sr)


#feeding it into the pitch detector; first pad
#pad with zeros to make it divisible by hopSize
# audio_length = sung_note.size
# num_padded_zeros = 128 - (audio_length % 128)
# sung_note = np.concatenate([sung_note, np.zeros(num_padded_zeros, dtype=np.float32)])
detector_result_midi_verbose = aubio_pitches(audio_array)
detector_result_midis = verbose_to_detected_midi(detector_result_midi_verbose, ground_truth_onsets_samps, hopSize)

'''
matplot time!
'''
''' MODIFY THIS BASED ON ISOLATED NOTE VS. FULL MELODY: '''
dur = librosa.get_duration(sung_note, sr=sr)
# if full melody:
# timestamps = np.linspace(s_time, e_time, len(detector_result_midi_verbose))
#if sliced note:
num_times = len(detector_result_midi_verbose[int(np.around(start/hopSize)):int(np.around(end/hopSize))])
timestamps = np.linspace(s_time, e_time, num_times) #+1 because of padding

#plotting
f, axarr = plt.subplots(2, figsize=(15, 9))
green_patch = mpatches.Patch(color='green', label='Ground Truth Onsets')
black_patch = mpatches.Patch(color='black', label='Ground Truth Pitch')
red_patch = mpatches.Patch(color='red', label='Pitch Detector Result')
axarr[0].legend(handles=[green_patch, black_patch, red_patch])
''' MODIFY THIS BASED ON ISOLATED NOTE VS. FULL MELODY: '''
#full melody:
# axarr[0].scatter(timestamps, detector_result_midi_verbose)
#spliced note:
axarr[0].scatter(timestamps, detector_result_midi_verbose[int(np.around(start/hopSize)):int(np.around(end/hopSize))])
axarr[0].set_title('Pitch Detector')
axarr[0].set_ylabel('MIDI Note Number')
axarr[0].set_xlabel('Time (s)')
xmin = s_time
xmax = e_time
ymin = 50.0
ymax = 80.0
axarr[0].axis([xmin, xmax, ymin, ymax]) #xmin, xmax, ymin, ymax
axarr[0].vlines(ground_truth_onsets_seconds, ymin, ymax, colors='green')


''' MODIFY THIS BASED ON ISOLATED NOTE VS. FULL MELODY: '''
#if visualizing one note
if label_info[ii][2].strip() == 'SIL':
	axarr[0].text((e_time-s_time)/2.5, (ymax-ymin)*0.75, "SIL", color='black')
else:
	axarr[0].hlines(ground_truth_midis[ii], s_time, e_time, color='black')
	axarr[0].text(s_time+(e_time-s_time)/2.0, ground_truth_midis[ii]+5, str(ground_truth_midis[ii]), color='black')
	axarr[0].hlines(detector_result_midis[ii], s_time, e_time, color='red')
	axarr[0].text(s_time+(e_time-s_time)/2.0, detector_result_midis[ii]-5, str(round(float(detector_result_midis[ii]), 1)), color='red')


#if visualizing full melody
'''
for ii in range(0, len(ground_truth_midis)):
	if label_info[ii][2].strip() == 'SIL':
		continue
	s = float(label_info[ii][0])
	e = float(label_info[ii][1])
	axarr[0].hlines(ground_truth_midis[ii], s, e, colors='black')
	axarr[0].text(s+(e-s)/3.5, ground_truth_midis[ii]+5, str(ground_truth_midis[ii]), color='black')
	axarr[0].hlines(detector_result_midis[ii], s, e, colors='red')
	axarr[0].text(s+(e-s)/3.5, detector_result_midis[ii]-5, str(round(float(detector_result_midis[ii]), 1)), color='red')
'''

f.subplots_adjust(hspace=0.5)
plt.show()

