import os
import pandas as pd
from azure.storage.blob import BlobServiceClient
import streamlit as st
import trimesh
import math

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

def compare_files(volume, cog, num_faces, num_vertices, num_edges):
    database = pd.read_csv('database.csv')
    database.columns = database.columns.str.strip()
    min_distance = float("inf")
    best_match = None
    for index, row in database.iterrows():
        distance = math.sqrt((row['volume'] - volume)**2 + (row['num_faces'] - num_faces)**2 + (row['num_vertices'] - num_vertices)**2 + (row['num_edges'] - num_edges)**2)
        if distance < min_distance:
            min_distance = distance
            best_match = row
    return best_match

def main():
    st.title('CAD Matching API')
    st.header('Upload CAD File to Database')
    database_file = st.file_uploader("Choose a file to add to database", type=['stl'])
    if database_file is not None:
        file_details = {"FileName":database_file.name,"FileType":database_file.type,"FileSize":database_file.size}
        st.write(file_details)
        save_uploadedfile(database_file)
        volume, cog, num_faces, num_vertices, num_edges = preprocess_file(f'tempDir/{database_file.name}')
        data = {'filename': database_file.name, 'volume': volume, 'cog_x': cog[0], 'cog_y': cog[1], 'cog_z': cog[2], 'num_faces': num_faces, 'num_vertices': num_vertices, 'num_edges': num_edges}
        df = pd.DataFrame(data, index=[0])
        df.to_csv('database.csv', mode='a', header=False)
    st.header('Upload CAD File for Comparison')
    uploaded_file = st.file_uploader("Choose a file for comparison", type=['stl'])
    if uploaded_file is not None:
        file_details = {"FileName":uploaded_file.name,"FileType":uploaded_file.type,"FileSize":uploaded_file.size}
        st.write(file_details)
        save_uploadedfile(uploaded_file)
        volume, cog, num_faces, num_vertices, num_edges = preprocess_file(f'tempDir/{uploaded_file.name}')
        st.write(f'Volume: {volume}, Center of Gravity: {cog}, Number of Faces: {num_faces}, Number of Vertices: {num_vertices}, Number of Edges: {num_edges}') 
        best_match = compare_files(volume, cog, num_faces, num_vertices, num_edges)
        st.write(f'Best Match: {best_match["filename"]}') 
        blob_service_client = BlobServiceClient.from_connection_string("DefaultEndpointsProtocol=https;AccountName=blobconfigurator;AccountKey=j9kYa3w9z11ukkynzpJuhgPheGbgEJGPve9sNAfHG9ErsKUpZCtnqC+hnNRURqudc3UhACwOSZ3g+AStdKhYpg==;EndpointSuffix=core.windows.net")
        upload_file_to_blob(blob_service_client, f'tempDir/{uploaded_file.name}', uploaded_file.name, 'blobcontainer')

if __name__ == '__main__':
    main()