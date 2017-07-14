'''
flask will always return an string that represents an array (with brackets!) back to the javascript.
upload_file makes sure to strip away the brackets first, so harmonizeUpload will cast to a np.array correctly.
'''

from flask import Flask, render_template, request, send_from_directory, make_response, redirect, url_for, session, Markup, flash
import sqlite3
import os
from werkzeug.utils import secure_filename
from werkzeug.contrib.cache import SimpleCache
from Harmonizer import *
import librosa
import numpy as np
np.set_printoptions(threshold='nan')

app = Flask(__name__, static_url_path='')

cache = SimpleCache()
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = set(['wav', 'mp3'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'as@FJ$ZFJO(DI%$F'
app.config['SESSION_TYPE'] = 'filesystem'

# database
db = sqlite3.connect('database.db')
# CREATE TABLE [IF NOT EXISTS] MAINDB (

# 	)


@app.route('/')
def index():
	session['file_uploaded'] = False
	session['display_warning'] = False
	return render_template('index.html')

@app.route('/recordkeypick')
def recordkeypick():
	return render_template('recordkeypick.html')

@app.route('/rangepick')
def rangepick():
	return render_template('rangepick.html')

@app.route('/record')
def record():
	return render_template('record.html')

@app.route('/playrecorded')
def playrecorded():
	return render_template('playrecorded.html')


@app.route('/uploadkeypick')
def uploadkeypick():
	return render_template('uploadkeypick.html')

@app.route('/uploadrangepick')
def uploadrangepick():
	return render_template('uploadrangepick.html')

@app.route('/upload')
def upload():
	return render_template('upload.html')



@app.route('/harmonizer', methods=['GET', 'POST'])
def harmonizer():
	return render_template('example_simple_exportwav.html')

@app.route('/harmonizedResults', methods=['GET', 'POST'])
def harmonizedResults():
	return render_template('harmonizedresults.html')

#harmonizing
@app.route('/harmonizeData', methods=['GET', 'POST'])
def harmonizeData():
	if request.method == 'POST':
		#key data
		string_data = cache.get('key_data') # string_data is str
		string_array = string_data.split(',')
		tonic = int(string_array[0])
		mode = int(string_array[1])

		#shift data
		shift_data = cache.get('shift_data') #shift_data is str
		
		audiodata = request.get_data() # audiodata is str
		audiodata = np.fromstring(audiodata, sep=',')
		original_np = audiodata
		
		#normalize
		if np.max(np.abs(original_np)) > 1:
			original_np = original_np / np.max(np.abs(original_np))

		pythlist_original = original_np.tolist() # pythlist_original is list, original_np is np.array
		cache.set('original_audio_str', str(pythlist_original)) # this string has brackets

		newdata = processAudioWithHarmonies(audiodata, tonic, mode, shift_data) #newdata is np.array

		#normalize
		if np.max(np.abs(newdata)) > 1:
			newdata = newdata / np.max(np.abs(newdata))

		#convert to string
		pythlist = newdata.tolist()
		pythliststring = str(pythlist)
		cache.set('harmonized_data_str', pythliststring) # this string  has brackets
		return pythliststring
	elif request.method =='GET':
		return_data = cache.get('harmonized_data_str') # this string has brackets, JSON needs brackets to parse
		return return_data
	else:
		return "Normal"

@app.route('/harmonizeUploaded', methods=['GET', 'POST'])
def harmonizedUploaded():
	if request.method == 'POST':
		#key data
		dummy = request.get_data()
		string_data = cache.get('key_data') # string_data is str
		string_array = string_data.split(',')
		tonic = int(string_array[0])
		mode = int(string_array[1])

		#shift data
		shift_data = cache.get('shift_data') # shift_data is str

		audiodata = cache.get('original_audio_str') # this string does not have brackets
		audio_np = np.fromstring(audiodata, sep=',')
		original = audio_np

		#normalize
		if np.max(np.abs(original)) > 1:
			original = original / np.max(np.abs(original))
		pythlist_original = original.tolist()
		cache.set('original_audio_str', str(pythlist_original))

		newdata = processAudioWithHarmonies(audio_np, tonic, mode, shift_data)
		#normalize
		if np.max(np.abs(newdata)) > 1:
			newdata = newdata / np.max(np.abs(newdata))

		pythlist = newdata.tolist()
		pythliststring = str(pythlist)
		cache.set('harmonized_data_str', pythliststring) # this string has brackets
		return pythliststring
	else:
		return "Normal"

@app.route('/originalAudio', methods=['GET'])
def originalAudio():
	if request.method == 'GET':
		return_data = cache.get('original_audio_str')
		cache.set('original_audio_str', return_data)

		# JSON wants brackets
		if return_data[0] != '[' and return_data[-1] != ']':
			return_data = '[' + return_data + ']'
		return return_data
	else:
		return "Normal"

@app.route('/keyData', methods=['GET', 'POST'])
def keyData():
	if request.method == 'POST':
		data = request.get_data() # type(data) is str
		cache.set('key_data', data)
		return request.get_data()
	elif request.method == 'GET':
		return_data = cache.get('key_data')
		cache.set('key_data', return_data) #set it again for /bufferData. works!
		return return_data
	else:
		return "Normal"

@app.route('/shiftData', methods=['POST'])
def shiftData():
	if request.method == 'POST':
		data = request.get_data() # type(data) is str
		cache.set('shift_data', data)
		return request.get_data()
	else:
		return "Normal"

@app.route('/static/<path:path>')
def send_js(path):
	return send_from_directory('static', path)

#oh. it is useful.
#takes in audio as np.array
def processAudioWithHarmonies(audio, tonic, mode, shift):
	newaudio, pitchesmelody_verb, melody_midi, onset_times = harmonizeme(audio, tonic, mode, shift)

	# converting python lists to strings
	pitchesmelody_verb_str = str(pitchesmelody_verb)
	melody_midi_str = str(melody_midi)
	onset_times_str = str(onset_times)

	#stripping brackets
	pitchesmelody_verb_str = pitchesmelody_verb_str.strip('[')
	pitchesmelody_verb_str = pitchesmelody_verb_str.strip(']')
	melody_midi_str = melody_midi_str.strip('[')
	melody_midi_str = melody_midi_str.strip(']')
	onset_times_str = onset_times_str.strip('[')
	onset_times_str = onset_times_str.strip(']')

	cache.set('pitchesmelody_verb', pitchesmelody_verb_str)
	cache.set('melody_midi', melody_midi_str)
	cache.set('onset_times', onset_times_str)
	return newaudio

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#uploads file
@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
	if request.method == 'POST':
		# check if the post request has the file part
		if 'file' not in request.files:
			flash('No file part')
			return redirect(request.url)
		f = request.files['file']
		# if user does not select file, browser also
		# submit a empty part without filename
		if f.filename == '':
			# flash('No selected file')
			return render_template('upload.html')
		if f and allowed_file(f.filename):
			filename = secure_filename(f.filename)
			f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			original_np, sr = librosa.core.load(os.path.join(app.config['UPLOAD_FOLDER'], filename), sr=44100)

			#normalize
			if np.max(np.abs(original_np)) > 1:
				original_np = original_np / np.max(np.abs(original_np))

			pythlist_original = original_np.tolist()
			pythliststring = str(pythlist_original)
			pythliststring = pythliststring.strip('[')
			pythliststring = pythliststring.strip(']') # strip brackets away
			# why do we strip brackets away here? that's how JavaScript has been posting to flask, supposedly
			# so we strip it for when the first time upload_file sets it in the cache

			cache.set('original_audio_str', pythliststring)	

			os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			session['file_uploaded'] = True
			name_display = Markup(filename)
			flash(name_display, category='name_display')
			return render_template('upload.html')
		# else, file extension not allowed
		else:
			session['display_warning'] = True
			return render_template('upload.html')


#gets uploaded file
@app.route('/uploads/<filename>')
def uploaded_file(filename):
	return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/reload')
def reload():
	session['file_uploaded'] = False
	return render_template('upload.html')


#real matplot
@app.route('/plot')
def plot():
	import StringIO

	import matplotlib.pyplot as plt
	import matplotlib.patches as mpatches
	from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
	from matplotlib.figure import Figure
	from matplotlib.dates import DateFormatter
	sampleRate = 44100
	hopSize = 128

	#get info needed to plot
	original_audio_str = cache.get('original_audio_str') # this has brackets
	cache.set('original_audio_str', original_audio_str)

	# strip brackets to convert to np.array
	original_audio_str = original_audio_str.strip('[')
	original_audio_str = original_audio_str.strip(']')
	original_np = np.fromstring(original_audio_str, sep=',')

	pitchesmelody_verb_str = cache.get('pitchesmelody_verb')
	melody_midi_str = cache.get('melody_midi')
	onset_times_str = cache.get('onset_times')

	# converting into np.array
	pitchesmelody_verb = np.fromstring(pitchesmelody_verb_str, sep=',')
	melody_midi = np.fromstring(melody_midi_str, sep=',')
	onset_times = np.fromstring(onset_times_str, sep=',')

	#num timestamps = num results from detector
	dur = librosa.get_duration(original_np, sr=sampleRate) #in seconds
	timestamps = np.linspace(0.0, dur, len(pitchesmelody_verb))

	fig = Figure()
	fig.set_figheight(9)
	fig.set_figwidth(15)
	ax0 = fig.add_subplot(211)
	ax1 = fig.add_subplot(212)
	fig.subplots_adjust(hspace=0.4)

	# f, axarr = plt.subplots(2, figsize=(15,9))
	green_patch = mpatches.Patch(color='green', label='Detected onsets')
	black_patch = mpatches.Patch(color='black', label='Detected pitches')


	# ax0 is for pitch detection results
	ax0.legend(handles=[green_patch, black_patch])
	ax0.scatter(timestamps, pitchesmelody_verb)
	ax0.set_title('Pitch Detected Results')
	ax0.set_ylabel('MIDI Note Number')
	ax0.set_xlabel('Time (s)')
	xmin = 0.0
	xmax = dur
	ymin = 50.0
	ymax = 80.0
	ax0.axis([xmin, xmax, ymin, ymax])
	ax0.vlines(onset_times, ymin, ymax, colors='green')

	#for the first silence
	s = 0.0
	e = onset_times[0]
	ax0.text(s+(e-s)/3.5, ymin+(ymax-ymin)/2.0, "sil", color='black')

	for ii in range(0, len(melody_midi)):
		s = 0.0
		e = dur
		#for the last segment
		if ii == len(melody_midi)-1:
			s = onset_times[ii]
		#for the middle
		else:
			s = onset_times[ii]
			e = onset_times[ii+1]

		#if melody note is nan
		if str(melody_midi[ii]) == "nan":
			ax0.text(s+(e-s)/3.5, ymin+(ymax-ymin)/2.0, "nan", color='black')
			continue

		ax0.hlines(melody_midi[ii], s, e, colors='black')
		ax0.text(s+(e-s)/3.5, ymin+(ymax-ymin)/2.0, str(round(melody_midi[ii], 1)), color='black')

	# ax1 is for original audio
	timestamps = np.linspace(0.0, dur, len(original_np))
	ax1.legend(handles=[green_patch])
	ax1.plot(timestamps, original_np)
	ax1.set_title('Original Waveform')
	ax1.set_ylabel('Amplitude')
	ax1.set_xlabel('Time (s)')
	xmin = 0.0
	xmax = dur
	ymin = -1.0
	ymax = 1.0
	ax1.axis([xmin, xmax, ymin, ymax])
	ax1.vlines(onset_times, ymin, ymax, colors='green')

	# displaying it
	canvas = FigureCanvas(fig)
	png_output = StringIO.StringIO()
	canvas.print_png(png_output)
	response = make_response(png_output.getvalue())
	response.headers['Content-Type'] = 'image/png'
	return response


#sinwave stuff
def build_sinwave(num_samples, freq, samplerate):
	t = np.arange(0, num_samples)/samplerate
	x = np.sin(2*np.pi*freq*t)
	return x

def processAudioWithSin(audio):
	array = np.fromstring(audio, sep=',')

	a440 = build_sinwave(array.size, 440.0, 44100.0)

	audiowithsin = array + a440
	#normalize:
	audiowithsin = audiowithsin / np.max(np.abs(audiowithsin))

	#convert to string:
	pythlist = audiowithsin.tolist()
	pythliststring = str(pythlist)
	return pythliststring