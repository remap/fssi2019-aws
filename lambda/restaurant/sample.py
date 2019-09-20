import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import backend as K
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

from sklearn.model_selection import train_test_split
from itertools import combinations
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)

import json
# from tqdm import tqdm

import os
print(os.listdir("../input"))

import pickle
# from sklearn.externals import joblib


# model = joblib.load('ingred_model.pkl')

# model, tokenizer = pickle.load(open("ingred_model.pkl"),'rb'))
max_len = 141
"""
checkpoint_path = "training_1/cp.ckpt"                                                                                  
checkpoint_dir = os.path.dirname(checkpoint_path) 
"""

def sample(preds, temperature=1.0):
    preds = np.asarray(preds).astype('float64')
    preds = np.log(preds) / temperature
    exp_preds = np.exp(preds)
    preds = exp_preds / np.sum(exp_preds)
    probas = np.random.multinomial(1, preds, 1)
    return np.argmax(probas)

def create_model(max_len, rnn_units, total_words, embedding_matrix):
    inputs = keras.layers.Input(shape=(max_len,))
    x = keras.layers.Embedding(*embedding_matrix.shape, weights=[embedding_matrix], trainable=False)(inputs)
    # x = keras.layers.Embedding(*embedding_matrix.shape, weights=[embedding_matrix], trainable=True)(inputs)
    x = keras.layers.CuDNNGRU(rnn_units, name='gru_1')(x)
    outputs = tf.keras.layers.Dense(total_words, activation='softmax', name='output')(x)

    model = keras.Model(inputs=inputs, outputs=outputs)
    model.compile(
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy'],
        optimizer='adam')

    return model

def generate_text(seed_text, next_words, max_len, model, tokenizer):
    idx2word = {idx: word for word, idx in tokenizer.word_index.items()}
    # Converting our start string to numbers (vectorizing)
    x_pred = tokenizer.texts_to_sequences([seed_text])[0]
    x_pred = np.array(pad_sequences([x_pred], maxlen=max_len - 1, padding='pre'))

    # Empty string to store our results
    text_generated = []

    # Low temperatures results in more predictable text.
    # Higher temperatures results in more surprising text.
    # Experiment to find the best setting.
    temperature = 2.0

    # Here batch size == 1
    model.reset_states()
    for i in range(next_words):
        predictions = model.predict(x_pred, verbose=0)[0]
        predicted_id = sample(predictions, temperature)
        text_generated.append(idx2word[predicted_id])

    return seed_text + ' ' + ' '.join(text_generated)

def load():
    with open('fasttext_matrix.txt', 'rb') as filehandle:
        fasttext_matrix = pickle.load(filehandle)
    # fasttext_matrix = build_matrix(tokenizer.word_index, FASTTEXT_PATH)

    # loading
    with open('tokenizer.pickle', 'rb') as handle:
        loaded_tokenizer = pickle.load(handle)

    total_words = len(loaded_tokenizer.word_index) + 1
    test_model = create_model(max_len - 1, 100, total_words, fasttext_matrix)
    test_model.load_weights(tf.train.latest_checkpoint(checkpoint_dir))
    return test_model, loaded_tokenizer

#test_model, loaded_tokenizer = load()
#test_model.save('saved_model.h5')
def gen_menu(li):
    result = []
    test_model = keras.models.load_model('saved_model.h5')
    with open('tokenizer.pickle', 'rb') as handle:
        loaded_tokenizer = pickle.load(handle)
    for item in li:
        result.append(str(generate_text(item, 4, max_len, test_model, loaded_tokenizer)))
    return result



def generate():

    total=  ['sesame oil', 'oyster sauce', 'hoisin sauce', 'eggs', 'butter', 'shallots', 'cucumber', 'fresh lemon juice', 'feta cheese', 'cumin', 'ground turmeric', 'garam masala', 'extra virgin olive oil', 'fresh basil', 'parmesan', 'rice vinegar', 'mirin', 'sake', 'toasted sesame seeds', 'kimchi', 'gochujang', 'black beans', 'salsa', 'corn tortillas', 'baking soda', 'vanilla extract', 'buttermilk', 'coconut milk', 'fish sauce', 'lemongrass']

    result = list(combinations(total,3))
    result.extend(list(combinations(total,2)))
    return result

def all():
    test_model = keras.models.load_model('saved_model.h5')
    with open('tokenizer.pickle', 'rb') as handle:
        loaded_tokenizer = pickle.load(handle)
    dict = {}
    count = 1
    for combo in generate():
        temp = []
        for i in range (1,11):
            c = ' '.join(map(str,combo))
            temp.append(generate_text(c, 3, max_len, test_model, loaded_tokenizer))
        dict[c] = temp
        print(count)
        count +=1 
    with open('data.txt','w') as outfile:
        json.dump(dict, outfile)
    return "done"

li = generate()
if 'cumin shallots' in list:
    print ('cumin shallots')
# print(all())
print(gen_menu(["butter cheddar-cheese", "rice beans corn-tortillas"]))
