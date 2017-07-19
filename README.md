# HarmonizeMe
Web app to make chordal harmony to accompany a user sung input!<br /><br />

Slightly stable (ON CHROME ONLY -- make sure https:// is in the URL): https://asdfang.pythonanywhere.com/<br />
Might take a long time when you click to harmonize on a first try; if that happens, graciously try a second time please!<br />
<br />
<br />
If you want to install and run it locally, follow these instructions:<br />
Using a virtual environment is recommended! Be it virtualenv or conda!<br />

Install dependencies:<br />
python 2.7.13<br />
flask 0.12.1 -- pip install flask==0.12.1<br />
librosa 0.4.2 -- pip install librosa==0.4.2<br />
aubio 0.4.5 -- pip install aubio==0.4.5<br />
<br />
numpy, scipy, matplotlib get installed with librosa: <br />
numpy 1.12.1 -- pip install numpy==1.12.1<br />
scipy 0.17.0 -- pip install scipy==0.17.0<br />
matplotlib 2.0.0<br />
Issues with numpy and scipy occured with hosting, so those versions might be necessary.<br />
Leaving matplotlib as is should be fine.<br />
<br />
IF RUNNING ON LOCAL, MODIFY flask_run.py: <br />
1) Comment out the 2 lines below "# for server", and 2) uncomment the two lines below "# for local" to change paths for UPLOAD_FOLDER and DATABASE.<br />
Running the flask app on local after cloning repo:<br />
<br />
-- Setting up flask:<br />
cd HarmonzieMeApp/flaskapp/<br />
export FLASK_APP="flask_run.py"<br />
-- Seting up database (do this only once, database.db will pop up):<br />
chmod +x sqlite.py<br />
./sqlite.py<br />
flask run<br />
<br />
Then go to 127.0.0.1:5000/ on Chrome.<br />

(Old files at HarmonizeMeOldFiles: https://github.com/asdfang/HarmonizeMeOldFiles/)<br />
