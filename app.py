import os
from azure.storage.blob import BlobServiceClient
import streamlit as st
import trimesh

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
    # Load mesh
    mesh = trimesh.load(file_path)

    # Compute Volume
    volume = mesh.volume

    # Compute the number of faces, vertices, and edges
    num_faces = mesh.faces.shape[0]
    num_vertices = mesh.vertices.shape[0]
    num_edges = mesh.edges.shape[0]

    # Center of gravity
    cog = mesh.center_mass

    return volume, cog, num_faces, num_vertices, num_edges

def main():
    st.title('CAD File Upload')
    uploaded_file = st.file_uploader("Choose a file", type=['stl'])

    if uploaded_file is not None:
        file_details = {"FileName":uploaded_file.name,"FileType":uploaded_file.type,"FileSize":uploaded_file.size}
        st.write(file_details)
        save_uploadedfile(uploaded_file)

        # Preprocessing file
        volume, cog, num_faces, num_vertices, num_edges = preprocess_file(f'tempDir/{uploaded_file.name}')
        st.write(f'Volume: {volume}, Center of Gravity: {cog}, Number of Faces: {num_faces}, Number of Vertices: {num_vertices}, Number of Edges: {num_edges}') 

        blob_service_client = BlobServiceClient.from_connection_string("DefaultEndpointsProtocol=https;AccountName=blobconfigurator;AccountKey=j9kYa3w9z11ukkynzpJuhgPheGbgEJGPve9sNAfHG9ErsKUpZCtnqC+hnNRURqudc3UhACwOSZ3g+AStdKhYpg==;EndpointSuffix=core.windows.net")
        upload_file_to_blob(blob_service_client, f'tempDir/{uploaded_file.name}', uploaded_file.name, 'blobcontainer')

if __name__ == '__main__':
    main()