from django.db import models
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from PIL import Image
import io, base64, random

import pickle

graph = tf.Graph()

# インデックスと文字で辞書を作成
char_indices = {}
indices_char = {}

class Photo(models.Model):
    image = models.ImageField(upload_to='photos')

    IMAGE_SIZE = 150 # 画像サイズ
    MODEL_FILE_PATH = './ai/ml_models/dcm_CNN.h5'

    classes = ["dog", "cat", "monkey"]
    num_classes = len(classes)

    def predict(self):
        model = None
        global graph
        with graph.as_default():
            model = load_model(self.MODEL_FILE_PATH)

            img_data = self.image.read()
            img_bin = io.BytesIO(img_data)
            image = Image.open(img_bin)
            image = image.convert("RGB")
            image = image.resize((self.IMAGE_SIZE, self.IMAGE_SIZE))
            data = np.asarray(image) / 256.0
            X = []
            X.append(data)
            X = np.array(X)

            result = model.predict([X])[0]
            predicted = result.argmax()
            percentage = int(result[predicted] * 100)

            return self.classes[predicted], percentage

    def image_src(self):
        with self.image.open() as img:
            base64_img = base64.b64encode(img.read()).decode()

            return 'data:' + img.file.content_type + ';base64,' + base64_img

class Kakugen():
    maxlen = 4
    max_length = 100
    TEXT_FILE_PATH = './ai/ml_models/data_kakugen.txt'
    MODEL_FILE_PATH = './ai/ml_models/kakugen_model.h5'

    # 次の言葉を選択するヘルパー
    def sample(self, preds, temperature=0.5):
        preds = np.asarray(preds).astype('float64')
        preds = np.log(preds) / temperature
        exp_preds = np.exp(preds)
        preds = exp_preds / np.sum(exp_preds)
        probas = np.random.multinomial(1, preds, 1)
        return np.argmax(probas)

    def make_kakugen(self):
        start_index = random.randint(0, 19000)
        global graph
        model = None
        with graph.as_default():
            model = load_model(self.MODEL_FILE_PATH)
            generated = ''
            with io.open(self.TEXT_FILE_PATH, encoding='utf-8') as f:
                text = f.read().lower()
            # 文章生成のための最初の言葉を取得
            sentence = text[start_index: start_index + self.maxlen]
            generated += sentence
            chars = sorted(list(set(text)))
            char_indices = dict((c, i) for i, c in enumerate(chars))
            indices_char = dict((i, c) for i, c in enumerate(chars))

            #末尾に初めて“。”がつくまで文章を生成
            while True:
                x_pred = np.zeros((1, self.maxlen, len(chars)))
                for t, char in enumerate(sentence):
                    x_pred[0, t, char_indices[char]] = 1.

                preds = model.predict(x_pred, verbose=0)[0]
                next_index = self.sample(preds, 2)
                next_char = indices_char[next_index]

                generated += next_char
                sentence = sentence[1:] + next_char

                if (next_char in ("。", "!")):
                    generated = ""
                    break  # それまで生成したものは削除する

            while True:
                x_pred = np.zeros((1, self.maxlen, len(chars)))
                for t, char in enumerate(sentence):
                    x_pred[0, t, char_indices[char]] = 1.

                preds = model.predict(x_pred, verbose=0)[0]
                next_index = self.sample(preds, 0.2)
                next_char = indices_char[next_index]

                if ((50 <= len(generated) < self.max_length and next_char in ("。", "!")) or len(generated) > self.max_length):
                    generated += "。"
                    break  # 60字以上、設定文字数未満で次の文字が。のとき、もしくは最大文字数を超えたときは終了

                generated += next_char
                sentence = sentence[1:] + next_char
                
            return generated


class Talk:
    with open('./ai/ml_models/kana_chars.pickle', mode='rb') as f:
        chars_list = pickle.load(f)

        for i, char in enumerate(chars_list):
            char_indices[char] = i
        for i, char in enumerate(chars_list):
            indices_char[i] = char

    MODEL_FILE_PATH1 = './ai/ml_models/encoder_model.h5'
    MODEL_FILE_PATH2 = './ai/ml_models/decoder_model.h5'

    n_char = len(chars_list)
    max_length_x = 128

    def is_invalid(self,message):
         with open('./ai/ml_models/kana_chars.pickle', mode='rb') as f:
              chars_list = pickle.load(f)

              is_invalid =False
              for char in message:
                  if char not in chars_list:
                      is_invalid = True
              return is_invalid

    # 文章をone-hot表現に変換する関数
    def sentence_to_vector(self, sentence):
        vector = np.zeros((1, self.max_length_x, self.n_char), dtype=np.bool)
        for j, char in enumerate(sentence):
            vector[0][j][char_indices[char]] = 1
        return vector

    def respond(self, message, beta=2):
        global graph
        encoder_model = None
        decoder_model = None
        with graph.as_default():
            if  self.is_invalid(message):
                respond_sentence = "ひらがなか、カタカナをつかってください。"
                return respond_sentence

            encoder_model = load_model(self.MODEL_FILE_PATH1)
            decoder_model = load_model(self.MODEL_FILE_PATH2)
            vec = self.sentence_to_vector(message)  # 文字列をone-hot表現に変換

            state_value = encoder_model.predict(vec)
            y_decoder = np.zeros((1, 1, self.n_char))  # decoderの出力を格納する配列
            y_decoder[0][0][char_indices['\t']] = 1  # decoderの最初の入力はタブ。one-hot表現にする。

            respond_sentence = ""  # 返答の文字列
            while True:
                y, h = decoder_model.predict([y_decoder, state_value])
                p_power = y[0][0] ** beta  # 確率分布の調整
                next_index = np.random.choice(len(p_power), p=p_power/np.sum(p_power)) 
                next_char = indices_char[next_index]  # 次の文字
                
                if (next_char == "\n" or len(respond_sentence) >= self.max_length_x):
                    break  # 次の文字が改行のとき、もしくは最大文字数を超えたときは終了
                    
                respond_sentence += next_char
                y_decoder = np.zeros((1, 1, self.n_char))  # 次の時刻の入力
                y_decoder[0][0][next_index] = 1

                state_value = h  # 次の時刻の状態

            return respond_sentence