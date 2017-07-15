#!/usr/bin/python

import sqlite3

conn = sqlite3.connect('database.db')

print "Opened"

# database
conn.execute('CREATE TABLE IF NOT EXISTS data (\
	ip_addr TEXT PRIMARY KEY, key_data TEXT DEFAULT "", shift_data TEXT DEFAULT "", \
	original_audio_str TEXT DEFAULT "", harmonized_audio_str TEXT DEFAULT "", \
	pitchesmelody_verb_str TEXT DEFAULT "", melody_midi_str TEXT DEFAULT "", onset_times_str TEXT DEFAULT "")')

print "Table created"

conn.close()