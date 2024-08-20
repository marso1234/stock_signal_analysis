from tensorflow.keras.models import load_model
import tensorflow.keras.backend as K
from tensorflow.keras.saving import register_keras_serializable
from tensorflow.keras.layers import Concatenate,Embedding ,Dense ,Input,LSTM,Permute,Softmax,Lambda,Flatten,GRU,Dropout,BatchNormalization, Normalization, Attention, Bidirectional, Masking, TimeDistributed
from keras_self_attention import SeqSelfAttention
from tensorflow.keras import Model
from tensorflow.keras.optimizers import Adam

@register_keras_serializable()
def r2_score(y_true, y_pred):
    y_true = K.cast(y_true, 'float32')
    SS_res =  K.sum(K.square(y_true - y_pred))
    SS_tot = K.sum(K.square(y_true - K.mean(y_true)))
    return (1 - SS_res/(SS_tot + K.epsilon()))

@register_keras_serializable()
def mda(y_true, y_pred):
    # Convert to float32
    y_true = K.cast(y_true, 'float32')
    y_pred = K.cast(y_pred, 'float32')

    # Calculate the direction of the true and predicted values
    direction_true = K.sign(y_true[1:] - y_true[:-1])
    direction_pred = K.sign(y_pred[1:] - y_pred[:-1])

    # Calculate the Mean Directional Accuracy
    correct_directions = K.equal(direction_true, direction_pred)
    mda_value = K.mean(K.cast(correct_directions, 'float32'))

    return mda_value

@register_keras_serializable()
def custom_mae_loss(y_true, y_pred):
    # Convert to float32
    y_true = K.cast(y_true, 'float32')
    y_pred = K.cast(y_pred, 'float32')

    # Calculate the absolute difference
    abs_diff = K.abs(y_true - y_pred)

    # Calculate the mean of the absolute differences
    mae_value = K.mean(abs_diff)

    return mae_value

def load_model_regression():

    custom_objects = {
    'SeqSelfAttention': SeqSelfAttention,
    'r2_score': r2_score,
    'mda': mda,
    'custom_mae_loss': custom_mae_loss
    }
    #model = build_model(20, 19)
    model = load_model('model/PCT_24features_HL.h5', custom_objects=custom_objects)
    return model
