from flask import Flask, render_template, request, send_from_directory
import numpy as np
app = Flask(__name__, static_url_path='')


@app.route('/')
def index():
	return render_template('example_simple_exportwav.html')


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

def build_sinwave(num_samples, freq, samplerate):
	t = np.arange(0, num_samples)/samplerate
	x = np.sin(2*np.pi*freq*t)
	return x