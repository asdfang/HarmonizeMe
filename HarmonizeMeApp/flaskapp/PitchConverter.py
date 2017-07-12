import math
import numpy as np

'''
A static class intended to deal with conversion between MIDI, frequencies, and scale degrees and distance in semitones.
'''
class PitchConverter:
	NOTE_NAMES = ["C", "C\u266F/D\u266D", "D", "D\u266F/E\u266D", "E", "F", "F\u266F/G\u266D", "G", "G\u266F/A\u266D", "A", "A\u266F/B\u266D", "B"]

	'''
	Gets the exact MIDI number given a frequency.
		Takes in: (double frequency) -- in Hertz -- Ex: 442 (Hz)
		Output: (double exact_MIDI) -- Ex: 69.054421862
	'''
	@staticmethod
	def exact_midi_from_freq(frequency):
		midi = 69.00 + (12.00 * math.log(float(frequency)/440.00))
		return midi

	'''
	Gets the rounded MIDI number (to nearest semitone) given a frequency.
		Takes in: (double frequency) -- in Hertz -- Ex: 442 (Hz)
		Output: (int rounded_MIDI) -- Ex: 69
	'''
	@staticmethod
	def rounded_midi_from_freq(frequency):
		return int(round(PitchConverter.exact_midi_from_freq(frequency)))

	'''
	Gets note name (displayable to user) given a note in MIDI.
		Takes in: (int midi_note) -- Ex: 69
		output: (string note_name) -- Ex: "A"
	'''
	@staticmethod
	def note_name_from_midi(midi_num):
		return PitchConverter.NOTE_NAMES[midi_num % 12].decode('unicode-escape')

	'''
	Get a note in scale degrees when given a note in semitones above a tonic.
		Takes in: (int midi_note, int tonic_midi) -- Ex: 7
		Output: (int half_steps_above) -- Ex: 5
	'''
	@staticmethod
	def pitch_in_sd(pitch, tonic):
		p = pitch
		t = tonic
		diff = p - t
		if np.isnan(pitch):
			return 0
		positive = False
		while diff < 0:
			diff = diff + 12
		half_steps_above = diff % 12

		if half_steps_above == 0:
			return 1
		elif half_steps_above == 1:
			return 1
		elif half_steps_above == 2:
			return 2
		elif half_steps_above == 3:
			return 3
		elif half_steps_above == 4:
			return 3
		elif half_steps_above == 5:
			return 4
		elif half_steps_above == 6:
			return 5
		elif half_steps_above == 7:
			return 5
		elif half_steps_above == 8:
			return 6
		elif half_steps_above == 9:
			return 6
		elif half_steps_above == 10:
			return 7
		elif half_steps_above == 11:
			return 7