import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # supress warning TF

import json
import random
import numpy as np
import pickle

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import Adam

from sklearn.preprocessing import LabelEncoder
from nltk.stem import WordNetLemmatizer
import nltk

nltk.download('punkt')
nltk.download('wordnet')

lemmatizer = WordNetLemmatizer()

print("📘 Membaca data intents...")

with open("intents.json", encoding="utf-8") as file:
    intents = json.load(file)

words = []
classes = []
documents = []
ignore_letters = ['?', '!', '.', ',']

# =====================
# PREPROCESSING
# =====================
for intent in intents["intents"]:
    for pattern in intent["patterns"]:
        word_list = nltk.word_tokenize(pattern)
        words.extend(word_list)
        documents.append((word_list, intent["tag"]))
        if intent["tag"] not in classes:
            classes.append(intent["tag"])

words = [
    lemmatizer.lemmatize(word.lower())
    for word in words
    if word not in ignore_letters
]

words = sorted(set(words))
classes = sorted(set(classes))

print(f"🧩 Jumlah kata unik: {len(words)} | Jumlah kelas intent: {len(classes)}")

# =====================
# TRAINING DATA
# =====================
training = []
output_empty = [0] * len(classes)

for document in documents:
    bag = []
    word_patterns = [
        lemmatizer.lemmatize(word.lower())
        for word in document[0]
    ]

    for word in words:
        bag.append(1 if word in word_patterns else 0)

    output_row = output_empty[:]
    output_row[classes.index(document[1])] = 1
    training.append([bag, output_row])

random.shuffle(training)
training = np.array(training, dtype=object)

X_train = np.array(list(training[:, 0]))
y_train = np.array(list(training[:, 1]))

print(f"📊 Data training siap: {len(X_train)} sampel")

# =====================
# MODEL (ANTI OVERFITTING)
# =====================
model = Sequential([
    Dense(64, activation='relu', input_shape=(X_train.shape[1],)),
    Dropout(0.4),

    Dense(32, activation='relu'),
    Dropout(0.4),

    Dense(len(classes), activation='softmax')
])

model.compile(
    optimizer=Adam(learning_rate=0.001),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

# =====================
# EARLY STOPPING
# =====================
early_stop = EarlyStopping(
    monitor='val_loss',
    patience=5,
    restore_best_weights=True
)

print("🚀 Mulai training model (anti-overfitting)...")

history = model.fit(
    X_train,
    y_train,
    epochs=100,              # BUKAN 200
    batch_size=5,
    validation_split=0.2,    # PENTING
    callbacks=[early_stop],
    verbose=1
)

# =====================
# SAVE MODEL & DATA
# =====================
model.save("chatbot_model.keras")

with open("words.pkl", "wb") as f:
    pickle.dump(words, f)

with open("classes.pkl", "wb") as f:
    pickle.dump(classes, f)

print("✅ Model berhasil disimpan sebagai chatbot_model.keras")
print("📦 Training selesai! Model siap digunakan di chatbot.py")
