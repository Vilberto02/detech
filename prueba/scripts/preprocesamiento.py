"""
Script para el pre-procesamiento de datos (Texto, Audio, Imágenes).
Este script implementa las técnicas de digitalización, limpieza y transformación
necesarias para preparar datos en crudo (ubicados en 'data/raw') para modelos de Minería de Datos.

Explicación detallada de cada paso en los comentarios de las funciones correspondientes.
"""

import os
import re
import cv2
import numpy as np
import librosa
import librosa.display
import scipy.signal
import pandas as pd
from pathlib import Path

# NLTK para texto
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Descargar recursos de NLTK necesarios de manera segura
def download_nltk_resources():
    recursos = ['punkt_tab', 'stopwords', 'wordnet']
    for recurso in recursos:
        try:
            nltk.data.find(f'corpora/{recurso}')
        except LookupError:
            try:
                nltk.data.find(f'tokenizers/{recurso}')
            except LookupError:
                nltk.download(recurso, quiet=True)

download_nltk_resources()

# ==========================================
# VARIABLES GLOBALES (ESTADO)
# ==========================================
LANGUAGE = 'spanish'
STOP_WORDS = set(stopwords.words(LANGUAGE))
LEMMATIZER = WordNetLemmatizer()

# ==========================================
# FUNCIONES DE PREPROCESAMIENTO INDIVIDUAL
# ==========================================

def procesar_texto(text: str) -> str:
    """
    Ejecuta el pipeline completo de pre-procesamiento de texto.
    
    Parámetros:
    - text (str): Texto crudo a procesar.
    """
    # 1. Conversión a minúsculas
    text = text.lower()
    
    # 2. Limpieza básica
    text = re.sub(r'[^\w\s]', '', text)  # Elimina puntuación
    text = re.sub(r'\d+', '', text)      # Elimina números
    
    # 3. Tokenización
    tokens = word_tokenize(text, language=LANGUAGE)
    
    # 4. Eliminación de stopwords
    tokens_filtered = [word for word in tokens if word not in STOP_WORDS]
    
    # 5. Lematización
    tokens_lemmatized = [LEMMATIZER.lemmatize(word) for word in tokens_filtered]
    
    return " ".join(tokens_lemmatized)


def procesar_imagen(image_path: str, target_size=(224, 224)) -> np.ndarray:
    """
    Ejecuta el pipeline de pre-procesamiento de imágenes utilizando OpenCV.
    
    Parámetros:
    - image_path (str): Ruta al archivo de la imagen en 'data/raw/'.
    - target_size (tuple): Tamaño (ancho, alto) al cual se redimensionará.
    """
    # 1. Digitalización / Carga de la imagen
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"No se encontró la imagen: {image_path}")
        
    # 2. Conversión de modelos de color
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # 3. Redimensionamiento
    img_resized = cv2.resize(img_rgb, target_size)
    
    # 4. Filtrado (Suavizado y Limpieza)
    img_smoothed = cv2.GaussianBlur(img_resized, (5, 5), 0)
    
    # 5. Ecualización de histogramas
    img_yuv = cv2.cvtColor(img_smoothed, cv2.COLOR_RGB2YUV)
    img_yuv[:, :, 0] = cv2.equalizeHist(img_yuv[:, :, 0])
    img_equalized = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2RGB)
    
    # 6. Aumento de datos (Data Augmentation)
    if np.random.rand() > 0.5:
        img_augmented = cv2.flip(img_equalized, 1) # Flip horizontal
    else:
        img_augmented = img_equalized
        
    # 7. Normalización de píxeles
    img_normalized = img_augmented / 255.0
    
    return img_normalized


def procesar_audio(audio_path: str, target_sr=22050):
    """
    Ejecuta el pipeline de pre-procesamiento de señales de audio usando Librosa.
    
    Parámetros:
    - audio_path (str): Ruta al archivo de audio en 'data/raw/'.
    - target_sr (int): Frecuencia de muestreo destino.
    """
    # 1. Digitalización (Carga con Librosa)
    y, sr = librosa.load(audio_path, sr=target_sr, mono=False)
    
    # 2. Conversión a mono
    if y.ndim > 1:
        y_mono = librosa.to_mono(y)
    else:
        y_mono = y
        
    # 3. Recorte de silencios (Trimming)
    y_trimmed, index = librosa.effects.trim(y_mono, top_db=20)
    
    # 4. Eliminación de ruidos
    y_denoised = scipy.signal.wiener(y_trimmed)
    
    # 5. Normalización de amplitud
    y_normalized = librosa.util.normalize(y_denoised)
    
    # 6. Segmentación por ventanas (Framing)
    frame_length = 2048
    hop_length = 512
    frames = librosa.util.frame(y_normalized, frame_length=frame_length, hop_length=hop_length)
    
    # 7. Análisis frecuencial (STFT -> Espectrograma)
    stft_matrix = librosa.stft(y_normalized, n_fft=frame_length, hop_length=hop_length)
    spectrogram_db = librosa.amplitude_to_db(np.abs(stft_matrix), ref=np.max)
    
    return y_normalized, frames, spectrogram_db


# ==========================================
# FUNCIONES ORQUESTADORAS (LOTES)
# ==========================================

def procesar_lote_texto(ruta_entrada_csv: str, ruta_salida_csv: str, col_texto_raw='texto'):
    """
    Lee el CSV crudo, procesa cada fila y lo guarda en procesado.
    Asigna dinámicamente los nombres de columna esperados ('texto_procesado' y 'etiqueta').
    """
    if not os.path.exists(ruta_entrada_csv):
        print(f"Archivo de texto no encontrado: {ruta_entrada_csv}")
        return
        
    df = pd.read_csv(ruta_entrada_csv)
    
    print("Procesando textos...")
    df['texto_procesado'] = df[col_texto_raw].apply(lambda x: procesar_texto(str(x)))
    
    if 'etiqueta' not in df.columns:
        for col in ['label', 'sentiment', 'clase']:
            if col in df.columns:
                df = df.rename(columns={col: 'etiqueta'})
                break
                
    os.makedirs(os.path.dirname(ruta_salida_csv), exist_ok=True)
    df.to_csv(ruta_salida_csv, index=False)
    print(f"Textos guardados exitosamente en: {ruta_salida_csv}")


def procesar_lote_multimedia(directorio_raw: str, ruta_salida_X: str, ruta_salida_y: str, tipo='imagen', target_size=(224, 224)):
    """
    Itera sobre un directorio (donde cada subcarpeta es una clase/etiqueta).
    Procesa las imágenes o audios y las consolida en archivos .npy
    """
    if not os.path.exists(directorio_raw):
        print(f"Directorio no encontrado: {directorio_raw}")
        return
        
    X = []
    y = []
    
    clases = [d for d in os.listdir(directorio_raw) if os.path.isdir(os.path.join(directorio_raw, d))]
    etiquetas_dict = {clase: idx for idx, clase in enumerate(clases)}
    
    print(f"Iniciando procesamiento de {tipo.upper()}s...")
    for clase, etiqueta in etiquetas_dict.items():
        dir_clase = os.path.join(directorio_raw, clase)
        for archivo in os.listdir(dir_clase):
            ruta_archivo = os.path.join(dir_clase, archivo)
            try:
                if tipo == 'imagen':
                    if archivo.lower().endswith(('.png', '.jpg', '.jpeg')):
                        img_proc = procesar_imagen(ruta_archivo, target_size=target_size)
                        X.append(img_proc)
                        y.append(etiqueta)
                elif tipo == 'audio':
                    if archivo.lower().endswith(('.wav', '.mp3')):
                        _, _, spectrogram_db = procesar_audio(ruta_archivo)
                        X.append(spectrogram_db)
                        y.append(etiqueta)
            except Exception as e:
                print(f"Error procesando {archivo}: {e}")
                
    X_arr = np.array(X)
    y_arr = np.array(y)
    
    os.makedirs(os.path.dirname(ruta_salida_X), exist_ok=True)
    np.save(ruta_salida_X, X_arr)
    np.save(ruta_salida_y, y_arr)
    
    print(f"Lote multimedia guardado. Matrices X shape: {X_arr.shape}")


if __name__ == '__main__':
    print("Módulo 'preprocesamiento.py' compilado correctamente.")
    print("Funciones disponibles: procesar_texto, procesar_imagen, procesar_audio, procesar_lote_texto, procesar_lote_multimedia")
