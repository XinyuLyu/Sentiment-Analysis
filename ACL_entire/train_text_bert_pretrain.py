# from __future__ import print_function
# from self_attention import Attention, Position_Embedding
#from load_final_data_2 import get_data, analyze_data, data_generator, data_generator_output  # process_train_data
# from keras.models import Model
# from keras.layers import Dense, Dropout, Input, Masking, Embedding, concatenate, \
#     GlobalAveragePooling1D, Conv1D, GlobalMaxPooling1D, Lambda, TimeDistributed, Bidirectional, LSTM
# from keras.layers import BatchNormalization, Activation
# from keras.optimizers import Adam
# import numpy as np
# from keras import backend
# from sklearn.utils import shuffle
# from sklearn import preprocessing
# from attention_model import AttentionLayer
#
# max_features = 20000
# batch_size = 16
# epo = 100
# filters = 128
# flag = 0.60
# numclass = 5
# audio_path = r'E:\\Yue\\Entire Data\\ACL_2018_entire\\Word_Mat_New_1\\'
#
# # loading data
# print('Loading data...')
# train_audio_data, train_text_data, train_label, test_audio_data, test_text_data, test_label, test_label_o, embed_matrix, dic = get_data()
#
# train_text_feature_full=np.load("bert_text_pretrained_feather_word_embedding_final.npy")
# print('train_label shape:', train_label.shape)
# train_label_a=train_label.shape[0]
# train_text_feature=train_text_feature_full[:train_label_a]
# test_text_feature=train_text_feature_full[train_label_a:7204]
#
from __future__ import print_function
from self_attention import Attention, Position_Embedding
from test_load_data import get_data, data_generator, data_generator_output  # process_train_data
from keras.models import Model
from keras.layers import Dense, Dropout, Input, concatenate, \
    GlobalAveragePooling1D, Conv1D, GlobalMaxPooling1D, TimeDistributed
from keras.layers import BatchNormalization, Activation
from keras.optimizers import Adam
import numpy as np
from sklearn.utils import shuffle

max_features = 20000
batch_size = 16
epo = 100
filters = 128
flag = 0.60
numclass = 5
audio_path = r'E:\\Yue\\Entire Data\\ACL_2018_entire\\Word_Mat_New_1\\'
feature_text_data=np.load('bert_text_pretrained_feather_word_embedding_final.npy')

# loading data
print('Loading data...')
train_audio_data, train_text_data, train_label, test_audio_data, test_text_data, test_label, test_label_o, embed_matrix, dic, tokendata, ori_label = get_data()

print('train_audio shape:', len(train_audio_data))
print('train_text shape:', train_text_data.shape)
print('test_audio shape:', len(test_audio_data))
print('test_text shape:', test_text_data.shape)
print('train_label shape:', train_label.shape)
print('test_label shape:', test_label.shape)

feature_data_, ori_label_ = shuffle(feature_text_data,ori_label)
train_text_feature_len=train_text_data.shape[0]

train_text_data_feature=feature_data_[:train_text_feature_len]
test_text_data_feature=feature_data_[train_text_feature_len:7204]

train_text_data_feature_label=ori_label_[:train_text_feature_len]
text_text_data_feature_label=ori_label_[train_text_feature_len:7204]
print('train_text_feature shape:',train_text_data_feature.shape)
print('test_text_feature shape:',test_text_data_feature.shape)


# Audio branch
audio_input = Input(shape=(513, 64))
audio_att = Attention(4, 16)([audio_input, audio_input, audio_input])
audio_att = BatchNormalization()(audio_att)
audio_att = Attention(4, 16)([audio_att, audio_att, audio_att])
audio_att = BatchNormalization()(audio_att)

audio_att_gap = GlobalAveragePooling1D()(audio_att)
dropout_audio = Dropout(0.5)(audio_att_gap)
model_frame = Model(audio_input, dropout_audio)

word_input = Input(shape=(50, 513, 64))
audio_input = TimeDistributed(model_frame)(word_input)
word_att = Attention(4, 16)([audio_input, audio_input, audio_input])
word_att = BatchNormalization()(word_att)
word_att = Attention(4, 16)([word_att, word_att, word_att])
word_att = BatchNormalization()(word_att)

word_att_gap = GlobalAveragePooling1D()(word_att)
dropout_word = Dropout(0.5)(word_att_gap)
audio_prediction = Dense(5, activation='softmax')(dropout_word)
audio_model = Model(inputs=word_input, outputs=audio_prediction)
inter_audio_model = Model(inputs=word_input, outputs=[word_att])
adam = Adam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-08)
audio_model.compile(loss='categorical_crossentropy', optimizer=adam, metrics=['accuracy'])

# Text Branch
text_input = Input(shape=(98, 1024))
#em_text = Embedding(len(dic) + 1, 200, weights=[embed_matrix], trainable=True)(text_input)
em_text = Position_Embedding()(text_input)

text_att = Attention(10, 20)([em_text, em_text, em_text])
text_att = BatchNormalization()(text_att)

text_att1 = Attention(10, 20)([text_att, text_att, text_att])
text_att1 = BatchNormalization()(text_att1)

text_att2 = Attention(10, 20)([text_att1, text_att1, text_att1])
text_att2 = BatchNormalization()(text_att2)

text_att_gap = GlobalMaxPooling1D()(text_att2)
#text_att_gap = GlobalAveragePooling1D()(text_att2)
#dropout_text_gap = Dropout(0.5)(text_att_gap)

text_prediction = Dense(5, activation='softmax')(text_att_gap)
text_model = Model(inputs=text_input, outputs=text_prediction)
inter_text_model = Model(inputs=text_input, outputs=text_att2)
adam = Adam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-08)
#text_model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
text_model.compile(loss='categorical_crossentropy', optimizer=adam, metrics=['accuracy'])

# Fusion Model
audio_f_input = Input(shape=(50,64))  # 50，    #98,200      #98,
text_f_input = Input(shape=(50,200))  # ，64 #98,200      #98,513,64
merge = concatenate([text_f_input, audio_f_input], name='merge')
merge = Dropout(0.5)(merge)

merge_weight1 = Attention(10,20)([merge,merge,merge])
merge_weight1 = BatchNormalization()(merge_weight1)

merge_weight2 = Attention(10,20)([merge_weight1,merge_weight1,merge_weight1])
merge_weight2 = BatchNormalization()(merge_weight2)

merge_weight3 = Attention(10,20)([merge_weight2,merge_weight2,merge_weight2])
merge = BatchNormalization()(merge_weight3)#(?,98,264)
#merge_gmp = GlobalMaxPooling1D()(merge)

cnn_1 = Conv1D(filters, 2, padding='valid', strides=1)(merge)
batchnol1 = BatchNormalization()(cnn_1)
activation1 = Activation('relu')(batchnol1)
maxpool_1 = GlobalMaxPooling1D()(activation1)
dropout_1 = Dropout(0.7)(maxpool_1)

cnn_2 = Conv1D(filters, 3, padding='valid', strides=1)(merge)
batchnol2 = BatchNormalization()(cnn_2)
activation2 = Activation('relu')(batchnol2)
maxpool_2 = GlobalMaxPooling1D()(activation2)
dropout_2 = Dropout(0.7)(maxpool_2)

cnn_3 = Conv1D(filters, 4, padding='valid', strides=1)(merge)
batchnol3 = BatchNormalization()(cnn_3)
activation3 = Activation('relu')(batchnol3)
maxpool_3 = GlobalMaxPooling1D()(activation3)
dropout_3 = Dropout(0.7)(maxpool_3)

cnn_4 = Conv1D(filters, 5, padding='valid', strides=1)(merge)
batchnol4 = BatchNormalization()(cnn_4)
activation4 = Activation('relu')(batchnol4)
maxpool_4 = GlobalMaxPooling1D()(activation4)
dropout_4 = Dropout(0.7)(maxpool_4)
final_merge = concatenate([dropout_1, dropout_2, dropout_3, dropout_4], name='final_merge')


d_1 = Dense(256)(final_merge)
batch_nol1 = BatchNormalization()(d_1)
activation1 = Activation('relu')(batch_nol1)
d_drop1 = Dropout(0.6)(activation1)

d_2 = Dense(128)(d_drop1)
batch_nol2 = BatchNormalization()(d_2)
activation2 = Activation('relu')(batch_nol2)
d_drop2 = Dropout(0.6)(activation2)

f_prediction = Dense(5, activation='softmax')(d_drop2)
print('f_prediction',f_prediction.shape)
final_model = Model(inputs=[text_f_input, audio_f_input], outputs=f_prediction)
adam = Adam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-08)
final_model.compile(loss='categorical_crossentropy', optimizer=adam, metrics=['accuracy'])
final_inter_model = Model(inputs=[text_f_input, audio_f_input], outputs=merge_weight3)

text_acc = 0
train_text_inter = None
test_text_inter = None

#text_model.load_weights(r'E:\Yue\Code\ACL_entire\text_model\\text_model_1_13.h5')
#inter_text_model.load_weights(r'E:\Yue\Code\ACL_entire\text_model\\inter_text_model_1_13.h5')
loss_t, acc_t = text_model.evaluate(test_text_data_feature, text_text_data_feature_label, batch_size=batch_size, verbose=0)
text_acc = acc_t
train_text_inter = inter_text_model.predict(train_text_data_feature, batch_size=batch_size)
test_text_inter = inter_text_model.predict(test_text_data_feature, batch_size=batch_size)

for i in range(50):
    print('text branch, epoch: ', str(i))
    data_,label_= shuffle(train_text_data_feature,train_text_data_feature_label)
    text_model.fit(data_, label_, batch_size=batch_size, epochs=1, verbose=1)
    loss_t, acc_t = text_model.evaluate(test_text_data_feature, text_text_data_feature_label, batch_size=batch_size, verbose=0)
    print('epoch: ', str(i))
    print('loss_t', loss_t, ' ', 'acc_t', acc_t)
    if acc_t >= text_acc:
        text_acc = acc_t
        train_text_inter = inter_text_model.predict(data_, batch_size=batch_size)
        test_text_inter = inter_text_model.predict(test_text_data_feature, batch_size=batch_size)
        text_model.save_weights(r'E:\Yue\Code\ACL_entire\text_model\\text_model_1_13.h5')
        inter_text_model.save_weights(r'E:\Yue\Code\ACL_entire\text_model\\inter_text_model_1_13.h5')
print(text_acc)

train_audio_inter = None
test_audio_inter = None
audio_acc = 0
'''
audio_model.load_weights(r'E:\Yue\Code\ACL_entire\audio_model\audio_model2.h5')
inter_audio_model.load_weights(r'E:\Yue\Code\ACL_entire\audio_model\inter_audio_model2.h5')
loss_a, acc_a = audio_model.evaluate_generator(
    data_generator(audio_path, test_audio_data, test_label, len(test_audio_data)),
    steps=len(test_audio_data) / 4)
audio_acc = acc_a
train_audio_inter = inter_audio_model.predict_generator(
    data_generator_output(audio_path, train_audio_data, train_label, len(train_audio_data)),
    steps=len(train_audio_data))
test_audio_inter = inter_audio_model.predict_generator(
    data_generator_output(audio_path, test_audio_data, test_label, len(test_audio_data)), steps=len(test_audio_data))'''
for i in range(0):
    print('audio branch, epoch: ', str(i))
    train_d, train_l = shuffle(train_audio_data, train_label)
    audio_model.fit_generator(data_generator(audio_path, train_d, train_l, len(train_d)),
                              steps_per_epoch=len(train_d) / 4, epochs=1, verbose=1)
    loss_a, acc_a = audio_model.evaluate_generator(
        data_generator(audio_path, test_audio_data, test_label, len(test_audio_data)),
        steps=len(test_audio_data) / 4)
    print('epoch: ', str(i))
    print('loss_a', loss_a, ' ', 'acc_a', acc_a)
    if acc_a >= audio_acc:
        audio_model.save_weights(r'E:\Yue\Code\ACL_entire\audio_model\audio_model2.h5')
        inter_audio_model.save_weights(r'E:\Yue\Code\ACL_entire\audio_model\inter_audio_model2.h5')
        audio_acc = acc_a
        train_audio_inter = inter_audio_model.predict_generator(
            data_generator_output(audio_path, train_audio_data, train_label,len(train_audio_data)),steps=len(train_audio_data))
        test_audio_inter = inter_audio_model.predict_generator(
            data_generator_output(audio_path, test_audio_data, test_label,len(test_audio_data)),steps=len(test_audio_data))

final_acc = 0
result = None
for i in range(0):
    print('fusion branch, epoch: ', str(i))
    final_model.fit([train_text_inter, train_audio_inter], train_label, batch_size=batch_size, epochs=1)
    loss_f, acc_f = final_model.evaluate([test_text_inter, test_audio_inter], test_label, batch_size=batch_size,
                                         verbose=0)
    print('epoch: ', str(i))
    print('loss_f', loss_f, ' ', 'acc_f', acc_f)
    if acc_f >= final_acc:
        #final_model.save_weights(r'E:\Yue\Code\ACL_entire\final_model\final_model2.h5')
        #final_inter_model.save_weights(r'E:\Yue\Code\ACL_entire\final_model\final_inter_model2.h5')
        final_acc = acc_f
        result = final_model.predict([test_text_inter, test_audio_inter], batch_size=batch_size)
        test_fusion_weight = final_inter_model.predict([test_text_inter, test_audio_inter], batch_size=batch_size)
        result = np.argmax(result, axis=1)
'''
final_model.load_weights(r'E:\Yue\Code\ACL_entire\final_model\final_model.h5')
final_inter_model.load_weights(r'E:\Yue\Code\ACL_entire\final_model\final_inter_model.h5')
loss_f, acc_f = final_model.evaluate([test_text_inter, test_audio_inter], test_label, batch_size=batch_size,
                                     verbose=0)
final_acc = acc_f
result = final_model.predict([test_text_inter, test_audio_inter], batch_size=batch_size)
test_fusion_weight = final_inter_model.predict([test_text_inter, test_audio_inter], batch_size=batch_size)
result = np.argmax(result, axis=1)
'''
'''
r_0, r_1, r_2, r_3, r_4 = analyze_data(test_label_o, result)
print('final result: ')
print('text acc: ', text_acc, ' audio acc: ', audio_acc, ' final acc: ', final_acc)
print("0", r_0)
print("1", r_1)
print("2", r_2)
print("3", r_3)
print("4", r_4)
'''
