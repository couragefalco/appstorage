import streamlit as st
import os
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

def save_uploadedfile(uploadedfile):
    with open(os.path.join("tempDir",uploadedfile.name),"wb") as f:
         f.write(uploadedfile.getbuffer())
    return st.success("Saved File:{} to tempDir".format(uploadedfile.name))

def upload_file_to_blob(blob_service_client, file_path, file_name, container_name):
    blob_client = blob_service_client.get_blob_client(container_name, file_name)
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data)
    return st.success("Uploaded File:{} to Blob Storage".format(file_name))

def main():
    st.title('CAD File Upload')
    uploaded_file = st.file_uploader("Choose a file", type=['stp', 'step'])
    if uploaded_file is not None:
        file_details = {"FileName":uploaded_file.name,"FileType":uploaded_file.type,"FileSize":uploaded_file.size}
        st.write(file_details)
        save_uploadedfile(uploaded_file)

        blob_service_client = BlobServiceClient.from_connection_string("DefaultEndpointsProtocol=https;AccountName=blobconfigurator;AccountKey=j9kYa3w9z11ukkynzpJuhgPheGbgEJGPve9sNAfHG9ErsKUpZCtnqC+hnNRURqudc3UhACwOSZ3g+AStdKhYpg==;EndpointSuffix=core.windows.net")
        upload_file_to_blob(blob_service_client, f'tempDir/{uploaded_file.name}', uploaded_file.name, 'blobcontainer')

if __name__ == '__main__':
    main()

