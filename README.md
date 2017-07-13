# HarmonizeMe
Web app to make chordal harmony to accompany a user sung input

Dependencies:<br />
python 2.7.13<br />
flask 0.12.1 -- pip install flask==0.12.1<br />
librosa 0.4.2 -- pip install librosa==0.4.2<br />
aubio 0.4.5 -- python -m pip install aubio<br />
<br />
numpy, scipy, matplotlib get installed with librosa: <br />
numpy 1.12.1<br />
scipy 0.17.0<br />
matplotlib 2.0.0<br />
Issues with numpy and scipy occured with hosting, so those versions might be necessary.
<br /><br />
Running the flask app on local after cloning repo:<br />
<br />
cd HarmonzieMeApp/flaskapp/<br />
export FLASK_APP="flask_run.py"<br />
flask run<br />
<br />
Then go to 127.0.0.1:5000/ on Chrome.<br />
