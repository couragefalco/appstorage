import os
import pandas as pd
from azure.storage.blob import BlobServiceClient
import streamlit as st
import trimesh
import math
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from PIL import Image

def save_uploadedfile(uploadedfile):
    with open(os.path.join("tempDir", uploadedfile.name), "wb") as f:
        f.write(uploadedfile.getbuffer())
    return st.success(f"Saved File:{uploadedfile.name} to tempDir")

def upload_file_to_blob(blob_service_client, file_path, file_name, container_name):
    blob_client = blob_service_client.get_blob_client(container_name, file_name)
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    return st.success(f"Uploaded File:{file_name} to Blob Storage")

def preprocess_file(file_path):
    mesh = trimesh.load(file_path)
    volume = mesh.volume
    num_faces = mesh.faces.shape[0]
    num_vertices = mesh.vertices.shape[0]
    num_edges = mesh.edges.shape[0]
    cog = mesh.center_mass
    return volume, cog, num_faces, num_vertices, num_edges

def sync_database(blob_service_client, container_name):
    container = blob_service_client.get_container_client(container_name)
    generator = container.list_blobs()

    data_frames = []
    for blob in generator:
        blob_client = container.get_blob_client(blob.name)
        blob_file_path = f'tempDir/{blob.name}'

        # Download file locally
        with open(blob_file_path, 'wb') as download_file:
            download_file.write(blob_client.download_blob().readall())
        
        volume, cog, num_faces, num_vertices, num_edges = preprocess_file(blob_file_path)
        data = {'filename': blob.name, 'volume': volume, 'cog_x': cog[0], 'cog_y': cog[1], 'cog_z': cog[2], 'num_faces': num_faces, 'num_vertices': num_vertices, 'num_edges': num_edges}
        data_frames.append(pd.DataFrame(data, index=[0]))
    
    # Write all data to CSV
    pd.concat(data_frames).to_csv('database.csv', index=False)

def main():
    st.title('CAD Matching API')
    st.header('Upload CAD File to Database')
    database_file = st.file_uploader("Choose a file to add to database", type=['stl'])

    if database_file is not None:
        save_uploadedfile(database_file)
        volume, cog, num_faces, num_vertices, num_edges = preprocess_file(f'tempDir/{database_file.name}')
        blob_service_client = BlobServiceClient.from_connection_string("DefaultEndpointsProtocol=https;AccountName=blobconfigurator;AccountKey=j9kYa3w9z11ukkynzpJuhgPheGbgEJGPve9sNAfHG9ErsKUpZCtnqC+hnNRURqudc3UhACwOSZ3g+AStdKhYpg==;EndpointSuffix=core.windows.net")
        upload_file_to_blob(blob_service_client, f'tempDir/{database_file.name}', database_file.name, 'blobcontainer')

    st.header('Sync')
    sync_button = st.button('Sync Database')
    if sync_button:
        blob_service_client = BlobServiceClient.from_connection_string("DefaultEndpointsProtocol=https;AccountName=blobconfigurator;AccountKey=j9kYa3w9z11ukkynzpJuhgPheGbgEJGPve9sNAfHG9ErsKUpZCtnqC+hnNRURqudc3UhACwOSZ3g+AStdKhYpg==;EndpointSuffix=core.windows.net")
        sync_database(blob_service_client, 'blobcontainer')

    st.header('Upload CAD File for Comparison')
    uploaded_file = st.file_uploader("Choose a file for comparison", type=['stl'])
    if uploaded_file is not None:
        save_uploadedfile(uploaded_file)
        volume, cog, num_faces, num_vertices, num_edges = preprocess_file(f'tempDir/{uploaded_file.name}') 

        # Rest of your logic here...
        
if __name__ == '__main__':
    main()
