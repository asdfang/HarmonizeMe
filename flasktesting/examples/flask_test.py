from flask import Flask, render_template, request, send_from_directory, make_response
from werkzeug.contrib.cache import SimpleCache
from Harmonizer import *
import numpy as np
np.set_printoptions(threshold='nan')

app = Flask(__name__, static_url_path='')

cache = SimpleCache()

@app.route('/')
def index():
	return render_template('key_picker.html')

@app.route('/harmonizer', methods=['GET', 'POST'])
def harmonizer():
	return render_template('example_simple_exportwav.html')

@app.route('/harmonizedResults', methods=['GET', 'POST'])
def harmonizedResults():
	return render_template('harmonized_results.html')

#testing with sin
@app.route('/bufferData', methods=['GET', 'POST'])
def bufferData():
	if request.method == 'POST':
		audiodata = request.get_data()
		#print "This is data", audiodata

		newdata = processAudioWithSin(audiodata)
		#print newdata
		return newdata
		#return request.get_data() + ":response"
	else:
		return "Normal"

#harmonizing
@app.route('/harmonizeData', methods=['GET', 'POST'])
def harmonizeData():
	if request.method == 'POST':
		string_data = cache.get('key_data')
		string_array = string_data.split(',')
		tonic = int(string_array[0])
		mode = int(string_array[1])
		
		audiodata = request.get_data()
		original = np.fromstring(audiodata, sep=',')
		
		#normalize
		if np.max(np.abs(original)) > 1:
			original = original / np.max(np.abs(original))
		pythlist_original = original.tolist()
		cache.set('original_audio', str(pythlist_original))

		newdata = processAudioWithHarmonies(audiodata, tonic, mode)
		#print newdata

		#normalize
		if np.max(np.abs(newdata)) > 1:
			newdata = newdata / np.max(np.abs(newdata))

		#do I need to do all of these conversions if the flask cache can do it?
		#convert to string
		pythlist = newdata.tolist()
		pythliststring = str(pythlist)
		cache.set('harmonized_data', pythliststring)
		return pythliststring
	elif request.method =='GET':
		return_data = cache.get('harmonized_data')
		return return_data
	else:
		return "Normal"

@app.route('/originalAudio', methods=['GET'])
def originalAudio():
	if request.method == 'GET':
		return_data = cache.get('original_audio')
		cache.set('original_audio', return_data)
		return return_data
	else:
		return "Normal"

@app.route('/keyData', methods=['GET', 'POST'])
def keyData():
	if request.method == 'POST':
		data = request.get_data()
		cache.set('key_data', data)
		return request.get_data()
	elif request.method == 'GET':
		return_data = cache.get('key_data')
		cache.set('key_data', return_data) #set it again for /bufferData. works!
		return return_data
	else:
		return "Normal"

@app.route('/static/<path:path>')
def send_js(path):
	return send_from_directory('static', path)	

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

#oh. it is useful.
def processAudioWithHarmonies(audio, tonic, mode):
	array = np.fromstring(audio, sep=',')
	cache.set('original_np', array)
	#print type(array)
	newaudio, pitchesmelody_verb, melody_midi, onset_times = harmonizeme(array, tonic, mode)
	cache.set('pitchesmelody_verb', pitchesmelody_verb)
	cache.set('melody_midi', melody_midi)
	cache.set('onset_times', onset_times)
	return newaudio

def build_sinwave(num_samples, freq, samplerate):
	t = np.arange(0, num_samples)/samplerate
	x = np.sin(2*np.pi*freq*t)
	return x

#real matplot
@app.route("/plot")
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
	original_np = cache.get('original_np')
	pitchesmelody_verb = cache.get('pitchesmelody_verb')
	melody_midi = cache.get('melody_midi')
	onset_times = cache.get('onset_times')
	print "asdf"
	print melody_midi
	print onset_times

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
	

#matplot test
@app.route("/plottest")
def plottest():
	import datetime
	import StringIO
	import random

	from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
	from matplotlib.figure import Figure
	from matplotlib.dates import DateFormatter

	fig=Figure()
	ax=fig.add_subplot(111)
	x=[]
	y=[]
	now=datetime.datetime.now()
	delta=datetime.timedelta(days=1)
	for i in range(10):
		x.append(now)
		now+=delta
		y.append(random.randint(0, 1000))
	ax.plot_date(x, y, '-')
	ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
	fig.autofmt_xdate()
	canvas=FigureCanvas(fig)
	png_output = StringIO.StringIO()
	canvas.print_png(png_output)
	response=make_response(png_output.getvalue())
	response.headers['Content-Type'] = 'image/png'
	return response