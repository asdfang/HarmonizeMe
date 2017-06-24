from flask import Flask, render_template, request, send_from_directory
from werkzeug.contrib.cache import SimpleCache
from Harmonizer import *
import numpy as np
app = Flask(__name__, static_url_path='')

cache = SimpleCache()

@app.route('/')
def index():
	return render_template('key_picker.html')

@app.route('/harmonizer', methods=['GET', 'POST'])
def harmonizer():
	return render_template('example_simple_exportwav.html')

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
		#print "This is data", audiodata

		newdata = processAudioWithHarmonies(audiodata, tonic, mode)
		#print newdata

		#normalize
		newdata = newdata / np.max(np.abs(newdata))

		#convert to string
		pythlist = newdata.tolist()
		pythliststring = str(pythlist)
		return pythliststring
		#return request.get_data() + ":response"
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
		return "yes"

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

#not useful
def processAudioWithHarmonies(audio, tonic, mode):
	array = np.fromstring(audio, sep=',')
	print type(array)
	newaudio = harmonizeme(array, tonic, mode)
	return newaudio

def build_sinwave(num_samples, freq, samplerate):
	t = np.arange(0, num_samples)/samplerate
	x = np.sin(2*np.pi*freq*t)
	return x