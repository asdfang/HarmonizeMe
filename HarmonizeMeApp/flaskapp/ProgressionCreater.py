from random import randint

'''
Creates the random progression. Must pass in inputs during initialization.
Inputs:
	Takes in: (int melody_scale_degrees) -- Ex: [1, 2, 3, 2, 1, 7, 1]
	Takes in: (int mode) -- 0: major; 1: minor
Output: ([[int]]) mainly from get_progression_semitones(): a progression with chords represented in semitones away from melody note.
	Useful for the inputs for pitch shifting.
	Ex: [[0, -8, -12], [0, -5, -9], [0, -9, -16], [0, -5, -9], [0, -8, -12], [0, -4, -16], [0, -3, -7]]

'''
class ProgressionCreater:
	'''
	Initializes a ProgressionCreater -- MUST pass in melody and mode with initializer
		Takes in: (int melody_in_scale_degrees) -- Ex: [1, 2, 3, 2, 1, 7, 1]
		Takes in: (int mode) -- 0: major; 1: minor
		Output: N/A

	Typical complete usage of ProgressionCreater:
	mel = [1, 2, 3, 2, 1, 7, 1]
	prog = ProgressionCreater(mel, 0)
	progression = prog.get_progression_semitones()
	'''
	def __init__(self, melody=None, mode=None, shift=None):
		self.melody_SD = melody if melody is not None else []
		self.progression_mode = mode if mode is not None else 0
		self.shift = shift if shift is not None else "down"

	'''
	This function is what the user will usually use:
	After initialization, use get_progression_semitones() to get how many semitones
	to pitch shift away from the melody for each voice.
		Takes in: melody and mode (from initialization)
		Output: ([[int]] progression_semitones) -- a 2D array of ints
			Ex: [[0, -8, -12], [0, -5, -9], [0, -9, -16], [0, -5, -9], [0, -8, -12], [0, -4, -16], [0, -3, -7]]
				progression_semitones[i] will represent a chord in the format of [melody, mid voice, bass voice]

	'''
	def get_progression_semitones(self):
		progression_semitones = []
		progression_RN = self.get_progression_RN()

		for ii in range(0, len(self.melody_SD)):
			chord_SD = self.fill_chord(self.melody_SD[ii], progression_RN[ii])
			chord_semitones = self.chord_sd_to_semitones(chord_SD, self.progression_mode)
			progression_semitones.append(chord_semitones)

		return progression_semitones, progression_RN


	'''
	After initialization, use get_progression_RN() to get a progression in Roman numerals
		Takes in: melody and mode (from initialization)
		Outputs: ([string] progression) -- array of strings, each containing a Roman numerals
			Ex: ['I', 'V', 'I', 'V6', 'vi', 'V', 'vi']
	'''
	def get_progression_RN(self):
		progression = []
		for note in self.melody_SD:
			# possible chords to harmonize the melodic note
			possible_chords = self.get_possible_chords(note, self.progression_mode)

			# randomly choosing one of them
			random_index = randint(0, len(possible_chords) - 1)
			random_chord = possible_chords[random_index]

			progression.append(random_chord)

		return progression

	'''
	Helper function.
	Get array of possible chords in Roman numerals to harmonize the current note in the melody.
		Takes in: (int melodic_note_in_scale_degrees) -- Ex: 5
		Takes in: (int mode) -- 0: major; 1: minor
		Outputs: ([string] possible_chords) -- Ex: self.get_possible_chords(5, 0) --> ["I", "I6", "V", "V6"]
	'''
	def get_possible_chords(self, note_sd, mode):
		if self.shift == "down":
			if mode == 0:
				return {
					0: ["skip"],
					1: ["I", "I6", "IV", "vi"],
					2: ["V", "V6", "ii6"],
					3: ["I"],
					4: ["IV"],
					5: ["I", "I6", "V", "V6"],
					6: ["IV", "ii6", "vi"],
					7: ["V"],
				}.get(note_sd, ["INVALID MELODY NOTE"])
			elif mode == 1:
				return {
					0: ["skip"],
					1: ["i", "i6", "iv", "VI"],
					2: ["v", "v6", "iio6"],
					3: ["i"],
					4: ["iv"],
					5: ["i", "i6", "v", "v6"],
					6: ["iv", "ii6", "VI"],
					7: ["v"],
				}.get(note_sd, ["INVALID MELODY NOTE"])
			else:
				return ["INVALID MODE"]
		else: #shift is up
			if mode == 0:
				return {
					0: ["skip"],
					1: ["I", "IV64", "vi6"],
					2: ["V64"],
					3: ["I6"],
					4: ["ii6", "IV"],
					5: ["I64", "V"],
					6: ["IV6", "vi"],
					7: ["V6"],
				}.get(note_sd, ["INVALID MELODY NOTE"])
			elif mode == 1:
				return {
					0: ["skip"],
					1: ["i", "iv64", "VI6"],
					2: ["V64"],
					3: ["i6"],
					4: ["iio6", "iv"],
					5: ["i64", "V"],
					6: ["iv6", "VI"],
					7: ["v6"],
				}.get(note_sd, ["INVALID MELODY NOTE"])
			else:
				return ["INVALID MODE"]

	'''
	Helper function.
	Get a filled chord in the form of [melody, mid voice, bass voice] in scale degrees.
		Takes in: (int melodic_note_in_scale_degrees) -- Ex: 5
		Takes in: (string chord_Roman_numeral -- Ex: "I"
		Outputs: ([int] chord_scale_degrees) -- Ex: [5, 3, 1]
	'''
	def fill_chord(self, note_sd, chord):
		filled_chord = []
		if self.shift == "down":
			filled_chord.append(self.top_note(note_sd, chord))
			filled_chord.append(self.mid_note(note_sd, chord))
			filled_chord.append(self.bass_note(chord))
			return filled_chord
		else:
			possible_notes = self.chord_sd(chord)
			bottom = self.bass_note(chord)
			top = self.top_note(note_sd, chord)
			possible_notes.remove(bottom)
			possible_notes.remove(top)
			mid = possible_notes[0]
			filled_chord.append(top)
			filled_chord.append(mid)
			filled_chord.append(bottom)
			return filled_chord

	'''
	Helper function.
	Get a chord represented in semitones away from the melody.
	Melodic note will always be 0 semitones away from the melody.
		Takes in: (int chord_scale_degrees) -- Ex: [5, 3, 1]
		Takes in: (int mode) -- 0: major; 1: minor
		Outputs: ([int] chord_semitones_away_from_melody) -- Ex: [0, -3, -19]
	'''
	def chord_sd_to_semitones(self, chord, mode):
		if chord == [0, 0, 0]:
			return [0, 0, 0]

		chord_semitones = []

		top = self.note_sd_to_semitones(chord[0], mode)
		mid = self.note_sd_to_semitones(chord[1], mode)
		bottom = self.note_sd_to_semitones(chord[2], mode)

		if self.shift == "down":
			#top note
			chord_semitones.append(0)

			#mid note
			mid_semitones = mid - top
			if mid > top:
				chord_semitones.append(mid_semitones - 12)
			else:
				chord_semitones.append(mid_semitones)

			#bottom note
			chord_semitones.append(bottom - top - 12)

			return chord_semitones
		else: #shift is up
			mid_semitones = mid - bottom
			if mid_semitones < 0:
				mid_semitones = mid_semitones + 12
			top_semitones = top - bottom
			if top_semitones < mid_semitones:
				top_semitones = top_semitones + 12
			chord_semitones.append(top_semitones)
			chord_semitones.append(mid_semitones)
			chord_semitones.append(0)
			return chord_semitones


	'''
	Helper function.
	Get a note represented in semitones above the tonic (between 0 and 11).
		Takes in: (int melodic_note_in_scale_degrees) -- Ex: 6 (solfege is Le if minor)
		Takes in: (int mode) -- 0: major; 1: minor -- Ex: 1 (minor)
		Outputs: (int semitones_above_tonic) -- Ex: 8
	'''
	def note_sd_to_semitones(self, note, mode):
		if mode == 0:
			return {
				0: 0,
				1: 0,
				2: 2,
				3: 4,
				4: 5,
				5: 7,
				6: 9,
				7: 11,
			}.get(note, -1)
		elif mode == 1:
			return {
				0: 0,
				1: 0,
				2: 2,
				3: 3,
				4: 5,
				5: 7,
				6: 8,
				7: 10,
			}.get(note, -1)
		else:
			return -1

	'''
	Helper function.
	Gets the chord in scale degrees -- order doesn't matter
		Takes in: string
		Output: [int, int, int]
	'''
	def chord_sd(self, chord):
		if chord == "I" or chord == "i" or chord == "I6" or chord == "i6" or chord == "I64" or chord =="i64":
			return [1, 3, 5]
		elif chord == "IV64" or chord == "iv64" or chord == "iv" or chord == "IV" or chord == "IV6" or chord == "iv6":
			return [1, 4, 6]
		elif chord == "vi6" or chord == "VI6" or chord == "vi" or chord == "VI":
			return [6, 1, 3]
		elif chord == "V64" or chord == "V" or chord == "v" or chord == "V6" or chord == "v6":
			return [2, 5, 7]
		elif chord == "ii6" or chord == "iio6":
			return [4, 6, 2]
		elif chord == "skip":
			return [0, 0, 0]

	'''
	Helper function.
	Get the bass note in scale degrees given a chord in Roman numerals.
	Straightforward, as figured bass in the Roman numeral will give away the bass voice.
		Takes in: (string chord_Roman_numeral) -- Ex: "v"
		Output: (int bass_scale_degrees) -- Ex: 5

	'''
	def bass_note(self, chord):
		#clean by: if chord in [array of chords]
		if chord == "I" or chord == "i" or chord == "IV64" or chord == "iv64" or chord == "vi6" or chord == "VI6":
			return 1
		elif chord == "V64":
			return 2
		elif chord == "I6" or chord == "i6":
			return 3
		elif chord == "IV" or chord == "iv" or chord == "ii6" or chord == "iio6":
			return 4
		elif chord == "V" or chord == "v" or chord == "I64" or chord == "i64":
			return 5
		elif chord == "VI" or chord == "vi" or chord == "IV6" or chord == "iv6":
			return 6
		elif chord == "V6" or chord == "v6":
			return 7
		elif chord == "skip":
			return 0
		else:
			return -1

	'''
	Helper function.
	Get the mid voice in scale degrees given what the melodic note in scale degrees is and
	a chord in Roman numerals. It will infer what the mid voice should be to fill out the chord.
		Takes in: (int melodic_note_in_scale_degrees) -- Ex: 5
		Takes in: (string chord_Roman_numeral) -- Ex: "I"
		Output: (int mid_voice_scale_degrees) -- Ex: 3
	'''
	def mid_note(self, note_sd, chord):
		if note_sd == 0:
			return 0
		elif chord == "I" or chord == "i":
			if note_sd == 1 or note_sd == 5:
				return 3
			elif note_sd == 3:
				return 5
			else:
				return -1
		elif chord == "I6" or chord == "i6":
			if note_sd == 1:
				return 5
			elif note_sd == 5:
				return 1
			else:
				return -1
		elif chord == "IV" or chord == "iv":
			if note_sd == 1 or note_sd == 4:
				return 6
			elif note_sd == 6:
				return 1
			else:
				return -1
		elif chord == "ii6" or chord == "iio6":
			if note_sd == 2:
				return 6
			elif note_sd == 6:
				return 2
			else:
				return -1
		elif chord == "V" or chord == "v":
			if note_sd == 2 or note_sd == 5:
				return 7
			elif note_sd == 7:
				return 5
			else:
				return -1
		elif chord == "VI" or chord == "vi":
			if note_sd == 1:
				return 3
			elif note_sd == 3 or note_sd == 6:
				return 1
			else:
				return -1
		elif chord == "V6" or chord == "v6":
			if note_sd == 2:
				return 5
			elif note_sd == 5:
				return 2
			else:
				return -1
		else:
			return -1

	'''
	Helper function.
	Get the top voice in scale degrees given what the melodic note in scale degrees is and
	a chord in Roman numerals.
		Takes in: (int melodic_note_in_scale_degrees)
		Takes in: (string chord_Roman_numeral)
		Output: (int mid_voice_scale_degrees)
	'''
	def top_note(self, note_sd, chord):
		if self.shift == "down":
			return note_sd #top note is just melody note if shifing down
		else: #shift is up:
			# choose randomly from possibilities
			possible_notes = self.chord_sd(chord)
			possible_notes.remove(self.bass_note(chord))
			random_index = randint(0, len(possible_notes) - 1)
			top = possible_notes[random_index]
			return top