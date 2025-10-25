from PIL import Image
import numpy as np
import requests
from io import BytesIO
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

def extractColours(url, num_colors=1) -> list[list[int, int, int]]:
    # Download image
    response = requests.get(url)
    img = Image.open(BytesIO(response.content)).convert("RGB")
    img = img.resize((150, 150))  # Resize for faster clustering

    # Convert image to numpy array
    img_data = np.array(img)
    img_data = img_data.reshape((-1, 3))  # Flatten to list of RGB pixels

    # Run KMeans clustering
    kmeans = KMeans(n_clusters=num_colors, random_state=42)
    kmeans.fit(img_data)

    colours = kmeans.cluster_centers_.astype(int)

    return colours