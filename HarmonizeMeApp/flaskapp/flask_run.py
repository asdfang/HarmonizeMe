'''
flask will always return an string that represents an array (with brackets!) back to the javascript.
upload_file makes sure to strip away the brackets first, so harmonizeUpload will cast to a np.array correctly.
'''

from flask import Flask, render_template, request, send_from_directory, make_response, redirect, url_for, session, Markup, flash, g
import sqlite3
import os
from werkzeug.utils import secure_filename
from Harmonizer import *
import librosa
import numpy as np
np.set_printoptions(threshold='nan')

app = Flask(__name__, static_url_path='')

UPLOAD_FOLDER = '/home/asdfang/gitfldr/HarmonizeMe/HarmonizeMeApp/flaskapp/uploads'
DATABASE = '/home/asdfang/gitfldr/HarmonizeMe/HarmonizeMeApp/flaskapp/database.db'

ALLOWED_EXTENSIONS = set(['wav', 'mp3'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DATABASE'] = DATABASE

app.secret_key = 'as@FJ$ZFJO(DI%$F'
app.config['SESSION_TYPE'] = 'filesystem'




# database table columns:
# ip_addr, key_data, shift_data, original_audio_str, harmonized_audio_str
# pitchesmelody_verb_str, melody_midi_str, onset_times_str

# sqlite database stuff
def get_db():
	db = getattr(g, '_database', None)
	if db is None:
		db = g._database = sqlite3.connect(app.config['DATABASE'])
		db.row_factory = sqlite3.Row
	return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


# first page
@app.route('/')
def index():
	db = get_db()
	cur = get_db().cursor()
	ip_addr = request.environ['REMOTE_ADDR'] # ip_addr is a string

	# seeing if there is already a row with the same IP Address
	cur.execute('SELECT count(*) FROM data WHERE ip_addr=?', (ip_addr,))
	count = cur.fetchone()[0] # tuple with just one entry, count is type int
	if count != 0:
		cur.execute('DELETE FROM data WHERE ip_addr=?', (ip_addr,))


	# adding a new row for this IP Address, with the other columns as empty strings
	cur.execute('INSERT INTO data (ip_addr, key_data, shift_data, original_audio_str, harmonized_audio_str, \
		pitchesmelody_verb_str, melody_midi_str, onset_times_str) VALUES \
		(?, ?, ?, ?, ?, ?, ?, ?)', [ip_addr, "", "", "", "", "", "", ""])

	# printing count and row information -- DEBUG for now
	# cur.execute('SELECT count(*) FROM data')
	# total_count = cur.fetchone()[0]
	# print "Total rows: " + str(total_count)
	# for user in query_db('SELECT * FROM data'):
	# 	print "ip_addr: " + user['ip_addr'] + \
	# 	"; key_data: " + user['key_data'] + "; shift_data: " + user['shift_data']

	db.commit()
	# close_connection("Normal")

	session['file_uploaded'] = False
	session['display_warning'] = False
	return render_template('index.html')

# second page
@app.route('/recordkeypick')
def recordkeypick():
	return render_template('recordkeypick.html')

# third page
@app.route('/rangepick')
def rangepick():
	return render_template('rangepick.html')

# fourth page
@app.route('/record')
def record():
	return render_template('record.html')

# second page
@app.route('/uploadkeypick')
def uploadkeypick():
	return render_template('uploadkeypick.html')

# third page
@app.route('/uploadrangepick')
def uploadrangepick():
	return render_template('uploadrangepick.html')

# fourth page
@app.route('/upload')
def upload():
	return render_template('upload.html')

# fifth page for both
@app.route('/harmonizedResults', methods=['GET', 'POST'])
def harmonizedResults():
	return render_template('harmonizedresults.html')

#harmonizing
@app.route('/harmonizeData', methods=['GET', 'POST'])
def harmonizeData():
	if request.method == 'POST':
		# intro
		db = get_db()
		cur = get_db().cursor()
		ip_addr = request.environ['REMOTE_ADDR']

		# making sure that this IP Address already has a row
		cur.execute('SELECT count(*) FROM data WHERE ip_addr=?', (ip_addr,))
		count = cur.fetchone()[0]
		if count == 0:
			error_msg = "IP Address not found"
			close_connection(error_msg)
			return error_msg

		#key data
		cur.execute('SELECT key_data FROM data WHERE ip_addr=?', (ip_addr,))
		string_data = cur.fetchone()[0]
		string_array = string_data.split(',')
		tonic = int(string_array[0])
		mode = int(string_array[1])

		#shift data
		cur.execute('SELECT shift_data FROM data WHERE ip_addr=?', (ip_addr,))
		shift_data = cur.fetchone()[0]
		
		# get original audio posted from user, and get np.array version
		audiodata = request.get_data() # audiodata is str
		audiodata = np.fromstring(audiodata, sep=',')
		original_np = audiodata
		
		#normalize
		if np.max(np.abs(original_np)) > 1:
			original_np = original_np / np.max(np.abs(original_np))

		# converting data to string
		pythlist_original = original_np.tolist() # pythlist_original is list, original_np is np.array
		pythliststring = str(pythlist_original)

		# update this IP Address's original_audio_str; has brackets
		cur.execute('UPDATE data SET original_audio_str=? WHERE ip_addr=?', (pythliststring, ip_addr))

		# GET ACTUAL HARMONIZATION!
		newdata = processAudioWithHarmonies(audiodata, tonic, mode, shift_data) #newdata is np.array

		#normalize
		if np.max(np.abs(newdata)) > 1:
			newdata = newdata / np.max(np.abs(newdata))

		#convert to string
		pythlist = newdata.tolist()
		pythliststring = str(pythlist)

		# update this IP Address's harmonized_audio_str; has brackets
		cur.execute('UPDATE data SET harmonized_audio_str=? WHERE ip_addr=?', (pythliststring, ip_addr))

		# outro
		db.commit()
		# close_connection("Normal")
		return pythliststring
	elif request.method =='GET':
		# intro
		db = get_db()
		cur = get_db().cursor()
		ip_addr = request.environ['REMOTE_ADDR']

		# making sure that this IP Address already has a row
		cur.execute('SELECT count(*) FROM data WHERE ip_addr=?', (ip_addr,))
		count = cur.fetchone()[0]
		if count == 0:
			error_msg = "IP Address not found"
			close_connection(error_msg)
			return error_msg

		# get this IP Address's harmonized_audio_str
		cur.execute('SELECT harmonized_audio_str FROM data WHERE ip_addr=?', (ip_addr,))
		return_data = cur.fetchone()[0] # has brackets

		# outro -- no commit, only got?
		db.commit()
		# close_connection("Normal")
		return return_data
	else:
		return "Normal"

@app.route('/harmonizeUploaded', methods=['GET', 'POST'])
def harmonizedUploaded():
	if request.method == 'POST':
		# intro
		db = get_db()
		cur = get_db().cursor()
		ip_addr = request.environ['REMOTE_ADDR']

		# making sure that this IP Address already has a row
		cur.execute('SELECT count(*) FROM data WHERE ip_addr=?', (ip_addr,))
		count = cur.fetchone()[0]
		if count == 0:
			error_msg = "IP Address not found"
			close_connection(error_msg)
			return error_msg

		dummy = request.get_data()

		#key data
		cur.execute('SELECT key_data FROM data WHERE ip_addr=?', (ip_addr,))
		string_data = cur.fetchone()[0]
		string_array = string_data.split(',')
		tonic = int(string_array[0])
		mode = int(string_array[1])

		#shift data
		cur.execute('SELECT shift_data FROM data WHERE ip_addr=?', (ip_addr,))
		shift_data = cur.fetchone()[0]

		# get this IP Address's original_audio_str
		cur.execute('SELECT original_audio_str FROM data WHERE ip_addr=?', (ip_addr,))
		audiodata = cur.fetchone()[0] # no brackets
		audio_np = np.fromstring(audiodata, sep=',')
		original = audio_np

		#normalize
		if np.max(np.abs(original)) > 1:
			original = original / np.max(np.abs(original))
		pythlist_original = original.tolist()
		pythliststring = str(pythlist_original)

		# update IP Address's original_audio_str to have brackets
		cur.execute('UPDATE data SET original_audio_str=? WHERE ip_addr=?', (pythliststring, ip_addr))

		# GET ACTUAL HARMONIZATION!
		newdata = processAudioWithHarmonies(audio_np, tonic, mode, shift_data)

		#normalize
		if np.max(np.abs(newdata)) > 1:
			newdata = newdata / np.max(np.abs(newdata))

		# convert to string
		pythlist = newdata.tolist()
		pythliststring = str(pythlist)

		# update this IP Address's harmonized_audio_str; has brackets
		cur.execute('UPDATE data SET harmonized_audio_str=? WHERE ip_addr=?', (pythliststring, ip_addr))

		# outro
		db.commit()
		# close_connection("Normal")
		return pythliststring
	else:
		return "Normal"

@app.route('/originalAudio', methods=['GET'])
def originalAudio():
	if request.method == 'GET':
		# intro
		db = get_db()
		cur = get_db().cursor()
		ip_addr = request.environ['REMOTE_ADDR']

		# making sure that this IP Address already has a row
		cur.execute('SELECT count(*) FROM data WHERE ip_addr=?', (ip_addr,))
		count = cur.fetchone()[0]
		if count == 0:
			error_msg = "IP Address not found"
			close_connection(error_msg)
			return error_msg

		cur.execute('SELECT original_audio_str FROM data WHERE ip_addr=?', (ip_addr,))
		return_data = cur.fetchone()[0]

		print "trying to add brackets: " + return_data

		# JSON wants brackets
		if return_data[0] != '[' and return_data[-1] != ']':
			return_data = '[' + return_data + ']'

		# outro
		# db.commit() no need to commit, only getting information?
		db.commit()
		# close_connection("Normal")
		return return_data
	else:
		return "Normal"

@app.route('/keyData', methods=['GET', 'POST'])
def keyData():
	if request.method == 'POST':
		# intro
		db = get_db()
		cur = get_db().cursor()
		ip_addr = request.environ['REMOTE_ADDR']

		# making sure that this IP Address already has a row
		cur.execute('SELECT count(*) FROM data WHERE ip_addr=?', (ip_addr,))
		count = cur.fetchone()[0]
		if count == 0:
			error_msg = "IP Address not found"
			close_connection(error_msg)
			return error_msg

		key_data = request.get_data() # key_data is str

		# update this IP Address's key_data
		cur.execute('UPDATE data SET key_data=? WHERE ip_addr=?', (key_data, ip_addr))

		# outro
		db.commit()
		# close_connection("Normal")
		return key_data
	elif request.method == 'GET': # GET used by record and upload, for user to re-hear key
		# intro
		db = get_db()
		cur = get_db().cursor()
		ip_addr = request.environ['REMOTE_ADDR']

		# making sure that this IP Address already has a row
		cur.execute('SELECT count(*) FROM data WHERE ip_addr=?', (ip_addr,))
		count = cur.fetchone()[0]
		if count == 0:
			error_msg = "IP Address not found"
			close_connection(error_msg)
			return error_msg

		cur.execute('SELECT key_data FROM data WHERE ip_addr=?', (ip_addr,))
		return_data = cur.fetchone()[0]

		# outro
		# db.commit() no need to commit, only getting information?
		db.commit()
		# close_connection("Normal")
		return return_data
	else:
		return "Normal"

@app.route('/shiftData', methods=['POST'])
def shiftData():
	if request.method == 'POST':
		# intro
		db = get_db()
		cur = get_db().cursor()
		ip_addr = request.environ['REMOTE_ADDR']

		# making sure that this IP Address already has a row
		cur.execute('SELECT count(*) FROM data WHERE ip_addr=?', (ip_addr,))
		count = cur.fetchone()[0]
		if count == 0:
			error_msg = "IP Address not found"
			close_connection(error_msg)
			return error_msg

		shift_data = request.get_data() # shift_data is str

		# update this IP Address's shift_data
		cur.execute('UPDATE data SET shift_data=? WHERE ip_addr=?', (shift_data, ip_addr))

		# outro
		db.commit()
		# close_connection("Normal")
		return shift_data
	# FUTURE:
	# there would be a request.method == 'GET' here if we needed to get the information again...for flipping the shift data?
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

	# intro
	db = get_db()
	cur = get_db().cursor()
	ip_addr = request.environ['REMOTE_ADDR']

	# making sure that this IP Address already has a row
	cur.execute('SELECT count(*) FROM data WHERE ip_addr=?', (ip_addr,))
	count = cur.fetchone()[0]
	if count == 0:
		error_msg = "IP Address not found"
		close_connection(error_msg)
		return error_msg

	# update this IP Address's information
	cur.execute('UPDATE data SET pitchesmelody_verb_str=? WHERE ip_addr=?', (pitchesmelody_verb_str, ip_addr))
	cur.execute('UPDATE data SET melody_midi_str=? WHERE ip_addr=?', (melody_midi_str, ip_addr))
	cur.execute('UPDATE data SET onset_times_str=? WHERE ip_addr=?', (onset_times_str, ip_addr))

	# outro
	db.commit()
	# close_connection("Normal")
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
			# so we strip it for when the first time upload_file sets it in the database

			# intro
			db = get_db()
			cur = get_db().cursor()
			ip_addr = request.environ['REMOTE_ADDR']

			# making sure that this IP Address already has a row
			cur.execute('SELECT count(*) FROM data WHERE ip_addr=?', (ip_addr,))
			count = cur.fetchone()[0]
			if count == 0:
				error_msg = "IP Address not found"
				close_connection(error_msg)
				return error_msg

			# update this IP Address's original_audio_str; no brackets
			cur.execute('UPDATE data SET original_audio_str=? WHERE ip_addr=?', (pythliststring, ip_addr))

			# outro
			db.commit()
			# close_connection("Normal")

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

	# intro
	db = get_db()
	cur = get_db().cursor()
	ip_addr = request.environ['REMOTE_ADDR']

	# making sure that this IP Address already has a row
	cur.execute('SELECT count(*) FROM data WHERE ip_addr=?', (ip_addr,))
	count = cur.fetchone()[0]
	if count == 0:
		error_msg = "IP Address not found"
		close_connection(error_msg)
		return error_msg

	### get info needed to plot
	cur.execute('SELECT original_audio_str FROM data WHERE ip_addr=?', (ip_addr,))
	original_audio_str = cur.fetchone()[0] # has brackets
	cur.execute('SELECT pitchesmelody_verb_str FROM data WHERE ip_addr=?', (ip_addr,))
	pitchesmelody_verb_str = cur.fetchone()[0]
	cur.execute('SELECT melody_midi_str FROM data WHERE ip_addr=?', (ip_addr,))
	melody_midi_str = cur.fetchone()[0]
	cur.execute('SELECT onset_times_str FROM data WHERE ip_addr=?', (ip_addr,))
	onset_times_str = cur.fetchone()[0]

	# outro
	db.commit()
	# close_connection("Normal")

	# strip brackets to convert to np.array
	original_audio_str = original_audio_str.strip('[')
	original_audio_str = original_audio_str.strip(']')
	original_np = np.fromstring(original_audio_str, sep=',')

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