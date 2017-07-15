# HarmonizeMe
Web app to make chordal harmony to accompany a user sung input<br />
Coming soon: https://asdfang.pythonanywhere.com/<br />
(Old files at HarmonizeMeOldFiles: https://github.com/asdfang/HarmonizeMeOldFiles/)<br />
<br />
Using a virtual environment is recommended! Be it virtualenv or conda!<br />
<br />
Dependencies:<br />
python 2.7.13<br />
flask 0.12.1 -- pip install flask==0.12.1<br />
librosa 0.4.2 -- pip install librosa==0.4.2<br />
aubio 0.4.5 -- pip install aubio==0.4.5<br />
<br />
numpy, scipy, matplotlib get installed with librosa: <br />
numpy 1.12.1<br />
scipy 0.17.0<br />
matplotlib 2.0.0<br />
Issues with numpy and scipy occured with hosting, so those versions might be necessary.<br />
Leaving matplotlib as is should be fine.<br />
<br /><br />
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
