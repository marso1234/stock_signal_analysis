from tensorflow.keras.models import load_model
import tensorflow.keras.backend as K
from tensorflow.keras.saving import register_keras_serializable
from tensorflow.keras.layers import Input, Dense, Dropout, LayerNormalization, MultiHeadAttention, Add, GlobalAveragePooling1D, TimeDistributed, Bidirectional, GRU, Concatenate, Lambda, Reshape, Conv1D, AveragePooling1D, AveragePooling2D
from keras_self_attention import SeqSelfAttention
from tensorflow.keras import Model
from tensorflow.keras.initializers import HeNormal, GlorotUniform
from tensorflow.keras.optimizers import Adam
import tensorflow as tf

@register_keras_serializable()
def r2_score(y_true, y_pred):
    
    y_true = K.cast(y_true, 'float32')
    y_pred = K.cast(y_pred, 'float32')

    y_true = K.cast(y_true, 'float32')
    SS_res =  K.sum(K.square(y_true - y_pred))
    SS_tot = K.sum(K.square(y_true - K.mean(y_true)))
    return (1 - SS_res/(SS_tot + K.epsilon()))

@register_keras_serializable()
def mda(y_true, y_pred):
    # Convert to float32
    y_true = K.cast(y_true[:, 0:4], 'float32')
    y_pred = K.cast(y_pred[:, 0:4], 'float32')

    # Calculate the direction of the true and predicted values
    direction_true = K.sign(y_true[1:] - y_true[:-1])
    direction_pred = K.sign(y_pred[1:] - y_pred[:-1])

    # Calculate the Mean Directional Accuracy
    correct_directions = K.equal(direction_true, direction_pred)
    mda_value = K.mean(K.cast(correct_directions, 'float32'))

    return mda_value

@register_keras_serializable()
def sign_accuracy(y_true, y_pred):
    # Convert to float32
    y_true = K.cast(y_true[:, 0:4], 'float32')
    y_pred = K.cast(y_pred[:, 0:4], 'float32')

    # Calculate the sign of the true and predicted values
    sign_true = K.sign(y_true)
    sign_pred = K.sign(y_pred)

    # Calculate the accuracy of the signs
    correct_signs = K.equal(sign_true, sign_pred)
    sign_accuracy_value = K.mean(K.cast(correct_signs, 'float32'))

    return sign_accuracy_value

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

def transformer_encoder(inputs, head_size, num_heads, ff_dim, dropout=0):
    # Attention and Normalization
    x = LayerNormalization(epsilon=1e-9)(inputs)
    x = MultiHeadAttention(key_dim=head_size, num_heads=num_heads, dropout=dropout, kernel_initializer=GlorotUniform())(x, x)
    x = Add()([x, inputs])

    # Feed Forward Part
    y = LayerNormalization(epsilon=1e-9)(x)
    y = Dense(ff_dim, activation="relu", kernel_initializer=HeNormal())(y)
    y = Dropout(dropout)(y)
    y = Dense(inputs.shape[-1], kernel_initializer=GlorotUniform())(y)
    return Add()([y, x])

def transformer_decoder(inputs, encoder_output, head_size, num_heads, ff_dim, dropout=0):
    # Attention and Normalization
    x = LayerNormalization(epsilon=1e-9)(inputs)
    x = MultiHeadAttention(key_dim=head_size, num_heads=num_heads, dropout=dropout, kernel_initializer=GlorotUniform())(x, encoder_output)
    x = Add()([x, inputs])
    
    # Feed Forward Part
    y = LayerNormalization(epsilon=1e-9)(x)
    y = Dense(ff_dim, activation="relu", kernel_initializer=HeNormal())(y)
    y = Dropout(dropout)(y)
    y = Dense(inputs.shape[-1], kernel_initializer=GlorotUniform())(y)
    return Add()([y, x])

def build_model(input_shape, output_shape, decoder_shape, head_size, num_heads, ff_dim, num_layers, dropout=0):
    # Encoder
    encoder_inputs = Input(shape=input_shape)
    x = encoder_inputs
    for _ in range(num_layers):
        x = transformer_encoder(x, head_size, num_heads, ff_dim, dropout)
    encoder_outputs = LayerNormalization(epsilon=1e-6)(x)
    
    # Decoder
    decoder_inputs = Input(shape=(decoder_shape)) 
    high_low_base = Lambda(lambda x: tf.gather(x[:, -1, :], [1, 2], axis=1))(decoder_inputs)
    
    x = decoder_inputs
    for _ in range(num_layers):
        x = transformer_decoder(x, encoder_outputs, head_size, num_heads, ff_dim, dropout)
    x = LayerNormalization(epsilon=1e-9)(x) 
    
    outputs = TimeDistributed(Dense(output_shape[1], kernel_initializer=GlorotUniform()))(x)
    outputs = Lambda(lambda x: x[:, :output_shape[0], :])(outputs)
    
    average_high_low = Lambda(lambda x: tf.reduce_mean(x, axis=1))(high_low_base)
    outputs = Add()([outputs, average_high_low])

    model = Model(inputs=[encoder_inputs, decoder_inputs], outputs=outputs)
    
    return model

def create_model():
    model = build_model(input_shape, output_shape, decoder_shape, head_size, num_heads, ff_dim, num_layers, dropout)
    #model = build_model(input_shape, init_neuron=512)
    adam_optimizer = Adam(learning_rate=0.00001, clipnorm=1., weight_decay=1e-7)
    #model.compile(loss=weighted_mse_loss,optimizer=adam_optimizer,metrics=[r2_score, mda, sign_accuracy, last_r2_score, last_sign_accuracy])    
    #model.summary()
    return model

input_shape = (60,24)
decoder_shape = (20,24)
output_shape = (20,2)
head_size = 128
num_heads = 60
ff_dim = 1024
num_layers = 8
dropout = 0.3

def load_model_regression():
    # custom_objects = {
    # 'SeqSelfAttention': SeqSelfAttention,
    # 'r2_score': r2_score,
    # 'mda': mda,
    # 'custom_mae_loss': custom_mae_loss,
    # 'sign_accuracy':sign_accuracy
    # }
    model = create_model()
    model.load_weights('model/Transformer_60_20_percentage_HL.keras')
    #model = load_model('model/Transformer_60_20_percentage_HL.keras', custom_objects=custom_objects, safe_mode=False)
    return model
