"""
Script para agrupamiento (Clustering) de datos de texto.
Contiene implementaciones de algoritmos no supervisados soportados nativamente por Scikit-Learn.
Incluye carga, vectorización (TF-IDF) y evaluación de los clústeres resultantes.
"""

import os
import pandas as pd

# Extracción de características de texto
from sklearn.feature_extraction.text import TfidfVectorizer

# Algoritmos de clustering
from sklearn.cluster import KMeans, MiniBatchKMeans, AgglomerativeClustering, DBSCAN

# Métricas de evaluación para aprendizaje no supervisado
from sklearn.metrics import silhouette_score, davies_bouldin_score

# ==========================================
# 1. CARGA Y VECTORIZACIÓN DE DATOS (TEXTO)
# ==========================================

def cargar_y_vectorizar_texto(ruta_csv: str, col_texto='texto_procesado', max_features=5000):
    """
    Carga los datos de texto procesado desde un archivo CSV y aplica TF-IDF 
    para convertirlos en una matriz numérica procesable por los modelos.
    
    Parámetros:
    - ruta_csv: Ruta relativa o absoluta al CSV de los datos.
    - col_texto: Nombre de la columna donde se halla el texto preprocesado.
    - max_features: Límite del vocabulario a usar para acelerar el proceso.
    
    Retorna:
    - X_tfidf: Matriz esparcida o densa generada.
    - vectorizer: El objeto TfidfVectorizer ajustado (para futuras predicciones o análisis).
    """
    if not os.path.exists(ruta_csv):
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_csv}")
        
    df = pd.read_csv(ruta_csv)
    
    # Manejar posibles valores nulos que puedan dañar el vectorizador
    textos = df[col_texto].fillna("").values
    
    # Inicializar y ajustar el vectorizador TF-IDF
    # TF-IDF penaliza las palabras que aparecen en casi todos los documentos
    vectorizer = TfidfVectorizer(max_features=max_features)
    X_tfidf = vectorizer.fit_transform(textos)
    
    print(f"Texto vectorizado con éxito. Dimensiones de la matriz: {X_tfidf.shape}")
    return X_tfidf, vectorizer


# ==========================================
# 2. EVALUACIÓN Y ENTRENAMIENTO
# ==========================================

def evaluar_agrupamiento(modelo, X):
    """
    Realiza el agrupamiento y calcula métricas de validación interna 
    para juzgar la calidad de los grupos formados sin tener etiquetas previas.
    
    Retorna:
    - etiquetas: Array con la asignación del clúster de cada muestra.
    - silueta: Silhouette Score del modelo.
    - davies: Davies-Bouldin Index.
    """
    print(f"\n--- Evaluando modelo de Agrupamiento: {modelo.__class__.__name__} ---")
    
    # Excepción: Algunos algoritmos requieren de una matriz densa.
    # El TF-IDF devuelve una matriz esparcida para optimizar memoria, así que la expandimos si es necesario.
    if hasattr(X, "toarray") and modelo.__class__.__name__ in ["AgglomerativeClustering", "DBSCAN"]:
        print("Convirtiendo la matriz esparcida a formato denso (requerimiento del algoritmo)...")
        X = X.toarray()
        
    # Predecir/Asignar los clústeres. Usamos fit_predict que funciona universalmente
    # tanto para algoritmos iterativos como basados en densidad.
    etiquetas = modelo.fit_predict(X)
    
    # Comprobar que no generó un solo clúster (o que DBSCAN no marcó todo como ruido "-1")
    num_clusters = len(set(etiquetas)) - (1 if -1 in etiquetas else 0)
    
    if num_clusters < 2:
        print("El modelo encontró menos de 2 clústeres válidos. No es posible calcular las métricas.")
        return etiquetas, None, None
        
    # Calcular métricas (Davies Bouldin exige matriz densa siempre)
    X_densa = X.toarray() if hasattr(X, "toarray") else X
    
    silueta = silhouette_score(X, etiquetas)
    davies = davies_bouldin_score(X_densa, etiquetas)
    
    print(f"Número de clústeres hallados: {num_clusters}")
    print(f"Puntuación de Silueta (Silhouette Score): {silueta:.4f} (De -1 a 1, más cerca a 1 es mejor)")
    print(f"Índice de Davies-Bouldin: {davies:.4f} (Más bajo es mejor)")
    
    return etiquetas, silueta, davies


# ==========================================
# 3. ALGORITMOS PARTICIONALES
# ==========================================

def obtener_kmeans(n_clusters=3):
    """
    K-Means Estándar (Algoritmo Particional iterativo).
    Busca minimizar la varianza intra-clúster.
    """
    return KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')

def obtener_minibatch_kmeans(n_clusters=3):
    """
    Mini-Batch K-Means.
    Procesa un subconjunto de los datos en cada iteración.
    Es más rápido que K-Means para bases de texto masivas, sacrificando levemente la precisión.
    """
    return MiniBatchKMeans(n_clusters=n_clusters, random_state=42, n_init='auto', batch_size=256)


# ==========================================
# 4. ALGORITMOS JERÁRQUICOS Y POR DENSIDAD
# ==========================================

def obtener_aglomerativo(n_clusters=3):
    """
    Clustering Jerárquico Aglomerativo (Bottom-up).
    Inicia con cada documento como su propio clúster y los va fusionando
    basado en métricas de distancia (euclidiana) y linkage (Ward).
    """
    return AgglomerativeClustering(n_clusters=n_clusters, metric='euclidean', linkage='ward')

def obtener_dbscan(eps=0.5, min_samples=5):
    """
    DBSCAN (Clustering basado en Densidad Espacial con Ruido).
    Agrupa puntos contiguos densamente poblados y marca como ruido (etiqueta '-1')
    a aquellos que quedan solos. No se le pasa "n_clusters".
    """
    return DBSCAN(eps=eps, min_samples=min_samples, metric='euclidean')


if __name__ == "__main__":
    print("Módulo 'agrupamiento.py' compilado correctamente.")
    print("Contiene vectorizador de texto (TF-IDF), modelos clásicos (K-Means, Agglomerative, DBSCAN) y evaluación (Silhouette, Davies-Bouldin).")
