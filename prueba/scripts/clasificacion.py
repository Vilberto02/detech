"""
Script para la clasificación de datos (Texto, Audio, Imágenes).
Contiene implementaciones de algoritmos de Machine Learning tradicional y Deep Learning (Keras/TensorFlow).
Incluye funciones para cargar datos procesados y evaluar métricas de rendimiento.
"""

import os
import numpy as np
import pandas as pd

# Métricas y partición
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report

# Algoritmos de Machine Learning Clásico
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import MultinomialNB

# Algoritmos de Gradient Boosting
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostClassifier

# Algoritmos de Deep Learning (TensorFlow/Keras)
# Solo se importa TensorFlow si se utiliza, para evitar sobrecarga si no es necesario.
try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, Conv2D, Flatten, MaxPooling2D, Dropout
    HAS_KERAS = True
except ImportError:
    HAS_KERAS = False


# ==========================================
# 1. CARGA DE DATOS PROCESADOS
# ==========================================

def cargar_datos_texto(ruta_csv: str, col_texto='texto_procesado', col_etiqueta='etiqueta'):
    """
    Carga datos procesados de texto desde un archivo CSV.
    El texto ya debe venir limpio desde preprocesamiento.py
    """
    if not os.path.exists(ruta_csv):
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_csv}")
    df = pd.read_csv(ruta_csv)
    X = df[col_texto].values
    y = df[col_etiqueta].values
    return X, y

def cargar_datos_multimedia(ruta_X_npy: str, ruta_y_npy: str):
    """
    Carga datos procesados de imágenes o audio (espectrogramas) desde archivos .npy.
    """
    if not os.path.exists(ruta_X_npy) or not os.path.exists(ruta_y_npy):
        raise FileNotFoundError("No se encontraron los archivos .npy especificados.")
    X = np.load(ruta_X_npy)
    y = np.load(ruta_y_npy)
    return X, y


# ==========================================
# 2. EVALUACIÓN Y ENTRENAMIENTO
# ==========================================

def evaluar_modelo(modelo, X, y, test_size=0.2, random_state=42, is_dl=False, epochs=10, batch_size=32):
    """
    Divide los datos, entrena el modelo y calcula las métricas de rendimiento.
    Retorna el accuracy, f1-score, la matriz de confusión y el modelo entrenado.
    """
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
    
    nombre_modelo = modelo.__class__.__name__ if not is_dl else "Red Neuronal (Keras)"
    print(f"\n--- Evaluando modelo: {nombre_modelo} ---")
    
    # Aplanamiento automático para modelos de ML Clásico si reciben matrices 3D o 4D (imágenes/audio)
    if not is_dl and len(X_train.shape) > 2:
        print("Aplanando datos tensores a formato 2D para que sean compatibles con ML tradicional...")
        X_train = X_train.reshape(X_train.shape[0], -1)
        X_test = X_test.reshape(X_test.shape[0], -1)
    
    # Entrenamiento
    if is_dl:
        modelo.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, validation_split=0.1, verbose=1)
        y_pred_prob = modelo.predict(X_test)
        # Asume clasificación multiclase (con softmax) o binaria (con sigmoid)
        if y_pred_prob.shape[1] > 1:
            y_pred = np.argmax(y_pred_prob, axis=1)
        else:
            y_pred = (y_pred_prob > 0.5).astype(int)
    else:
        modelo.fit(X_train, y_train)
        y_pred = modelo.predict(X_test)
        
    # Métricas
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted') # weighted para datasets desbalanceados
    cm = confusion_matrix(y_test, y_pred)
    
    print(f"Exactitud (Accuracy): {acc:.4f}")
    print(f"Puntuación F1 (F1-Score): {f1:.4f}")
    print("Matriz de Confusión:\n", cm)
    
    return acc, f1, cm, modelo


# ==========================================
# 3. ALGORITMOS DE MACHINE LEARNING TRADICIONAL
# ==========================================

def obtener_regresion_logistica():
    return LogisticRegression(max_iter=1000, random_state=42)

def obtener_knn(n_neighbors=5):
    return KNeighborsClassifier(n_neighbors=n_neighbors)

def obtener_svm(kernel='rbf'):
    return SVC(kernel=kernel, random_state=42)

def obtener_arbol_decision():
    return DecisionTreeClassifier(random_state=42)

def obtener_random_forest(n_estimators=100):
    return RandomForestClassifier(n_estimators=n_estimators, random_state=42)

def obtener_naive_bayes():
    """
    Modelo estadístico ideal para datos discretos, como la clasificación de texto
    procesado a través de frecuencias (Bag of Words o TF-IDF).
    """
    return MultinomialNB()


# ==========================================
# 4. ALGORITMOS DE GRADIENT BOOSTING
# ==========================================

def obtener_xgboost():
    return xgb.XGBClassifier(use_label_encoder=False, eval_metric='mlogloss', random_state=42)

def obtener_lightgbm():
    return lgb.LGBMClassifier(random_state=42)

def obtener_catboost():
    return CatBoostClassifier(verbose=0, random_state=42)


# ==========================================
# 5. ALGORITMOS DE DEEP LEARNING (TENSORFLOW/KERAS)
# ==========================================

def construir_ann(input_dim, num_classes):
    """
    Construye una Red Neuronal Artificial Multicapa (MLP).
    """
    if not HAS_KERAS:
        raise ImportError("TensorFlow/Keras no está instalado.")
        
    model = Sequential([
        Dense(128, activation='relu', input_dim=input_dim),
        Dropout(0.3),
        Dense(64, activation='relu'),
        Dropout(0.3),
        Dense(num_classes, activation='softmax' if num_classes > 2 else 'sigmoid')
    ])
    loss = 'sparse_categorical_crossentropy' if num_classes > 2 else 'binary_crossentropy'
    model.compile(optimizer='adam', loss=loss, metrics=['accuracy'])
    return model

def construir_cnn(input_shape, num_classes):
    """
    Construye una Red Neuronal Convolucional (CNN).
    Ideal para Imágenes (2D/3D) y Audio procesado como espectrogramas.
    El input_shape debe ser del tipo (alto, ancho, canales).
    """
    if not HAS_KERAS:
        raise ImportError("TensorFlow/Keras no está instalado.")
        
    model = Sequential([
        Conv2D(32, (3, 3), activation='relu', input_shape=input_shape),
        MaxPooling2D((2, 2)),
        Conv2D(64, (3, 3), activation='relu'),
        MaxPooling2D((2, 2)),
        Conv2D(128, (3, 3), activation='relu'),
        Flatten(),
        Dense(128, activation='relu'),
        Dropout(0.5),
        Dense(num_classes, activation='softmax' if num_classes > 2 else 'sigmoid')
    ])
    loss = 'sparse_categorical_crossentropy' if num_classes > 2 else 'binary_crossentropy'
    model.compile(optimizer='adam', loss=loss, metrics=['accuracy'])
    return model


if __name__ == "__main__":
    print("Módulo 'clasificacion.py' compilado correctamente.")
    print("Contiene algoritmos tradicionales, Gradient Boosting (XGB, LGBM, CatBoost) y Deep Learning (CNN, ANN).")
    print("Las redes CNN están orientadas al análisis de Imágenes y Audio, mientras que Naive Bayes al Texto.")
