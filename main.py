# -*- coding: utf-8 -*-
"""MusicGenerationByAI.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1m0QoNinwNUzjqhsGXXUXlF0fJENvtjpY
"""

from music21 import converter, instrument, note, chord, stream
import numpy as np
import pickle
import glob
from keras.utils import np_utils
from keras.models import Sequential, load_model
from keras.layers import *
from keras.callbacks import EarlyStopping, ModelCheckpoint

"""###PREPROCESSING"""

'''
#Code for formation of notes file which has all the notes and chords of dataset stored
notes = []
for file in glob.glob("./dataset_albeniz/*.mid"):
  midi = converter.parse(file)
  element_to_parse = midi.flat.notes
  print("parsing %s"%file)
  for ele in element_to_parse:
    #If element is note store its pitch
    if isinstance(ele, note.Note):
      notes.append(str(ele.pitch))
    #If element is chord split all notes of chord and join it with '+'
    if isinstance(ele, chord.Chord):
      notes.append("+".join(str(n) for n in ele.normalOrder))
'''

'''with open("notes", "wb") as f:
  pickle.dump(notes, f)'''

with open("notes", "rb") as f:
  notes = pickle.load(f)

n_vocab = len(set(notes))

print("Total notes- ", len(notes))
print("total unique notes- ", n_vocab)

"""###Preparing Sequential Data for LSTM Model"""

#Elements LSTM input layer should consider
sequence_length = 100
pitch_names = sorted(set(notes))
#Mapping between element to integer value
ele_to_int = dict((ele, num) for num, ele in enumerate(pitch_names))

network_input = []
network_output = []
for i in range(len(notes) - sequence_length):
  seq_in = notes[i:i+sequence_length]
  seq_ou = notes[i+sequence_length]
  network_input.append([ele_to_int[ch] for ch in seq_in])
  network_output.append(ele_to_int[seq_ou])

network_input = np.array(network_input).reshape((len(network_input), sequence_length, 1))/float(n_vocab)
network_output = np_utils.to_categorical(network_output)
print(network_input.shape)
print(network_output.shape)

"""###LSTM Model"""

model = Sequential()
model.add(LSTM(units = 512, input_shape = (network_input.shape[1], network_input.shape[2]), return_sequences = True))
model.add(Dropout(0.1))
model.add(LSTM(units = 512, return_sequences= True))
model.add(Dropout(0.1))
model.add(LSTM(units = 512))
model.add(Dense(units=256))
model.add(Dropout(0.1))
model.add(Dense(units=n_vocab, activation="softmax"))
model.compile(loss = "categorical_crossentropy", optimizer = "adam")
model.summary()

'''check = ModelCheckpoint("model.hdf5", monitor = "loss", verbose = 0, save_best_only= True, mode = "min")
hist = model.fit(network_input, network_output, epochs = 100, batch_size = 64, callbacks=[check])'''

model = load_model("model.hdf5")

"""###Prediction"""

predicted_network_input = []

for i in range(len(notes) - sequence_length):
  seq_in = notes[i:i+sequence_length]
  predicted_network_input.append([ele_to_int[ch] for ch in seq_in])

start = np.random.randint(len(predicted_network_input)-1)

#integer to element mapping
int_to_ele = dict((num,ele) for num, ele in emumerate(pitch_names))

pattern = network_input[start]
prediction_output = []
# generation of 200 elements
for ni in range(200):
  prediction_input = np.reshape(pattern, (1, len(pattern), 1))/n_vocab
  prediction = model.fit(prediction_input, verbose=0)
  prediction_output.append(int_to_ele[np.argmax(prediction)])
  pattern.append(prediction_output[-1])
  pattern = pattern[1:]

"""###Creation of midi file"""

offset = 0 #TIme
 output_notes = []
 for pattern in prediction_output:
   #if pattern is chord
   if '+' in pattern or pattern.isdigit():
     notes_in_chord = pattern.split('+')
     temp_notes = []
     for curr_note in notes_in_chord:
       new_note = note.Note(int(curr_note))
       new_note.storedInstrument = instrument.Piano()
       temp_notes.append(new_note)
      new_chord = chord.Chord(temp_notes)
      new_chord.offset = offset
      output_notes.append(new_chord)

   #if pattern is note
   else:
     new_note = note.Note(int(pattern))
     new_note.storedInstrument = instrument.Piano()
     new_note.offset = offset
     output_notes.append(new_note)
  offset += 0.5

#creation of stream object
midi_stream = stream.Stream(output_notes)
midi_stream.show('midi')
