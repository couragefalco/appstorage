import os
import pandas as pd
import trimesh
import matplotlib.pyplot as plt
from PIL import Image
import streamlit as st
import shutil
from azure.storage.blob import BlobServiceClient
from apscheduler.schedulers.background import BackgroundScheduler
import os
from dotenv import load_dotenv

load_dotenv()

CONNECTION_STRING = os.getenv("CONNECTION_STRING")

def save_uploadedfile(uploadedfile):
    with open(os.path.join("tempDir", uploadedfile.name), "wb") as f:
        f.write(uploadedfile.getbuffer())
    return st.success(f"Saved File:{uploadedfile.name} to tempDir")

def upload_file_to_blob(blob_service_client, file_path, file_name, container_name):
    blob_client = blob_service_client.get_blob_client(container_name, file_name)
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    return st.success(f"Uploaded File:{file_name} to Blob Storage")

def save_uploadedfile_api(uploadedfile):
    with open(os.path.join("tempDir", uploadedfile.filename), "wb") as f:
        f.write(uploadedfile.file.read())
    return st.success(f"Saved File:{uploadedfile.filename} to tempDir")

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
    top_matches = [[float("inf"), None, 0]] * 10  # Added third element for similarity score
    max_distance = 0 # keep track of the maximum Euclidean distance
    for index, row in database.iterrows():
        distance = ((row['volume'] - volume)**2 + 
                   (row['num_faces'] - num_faces)**2 + 
                   (row['num_vertices'] - num_vertices)**2 + 
                   (row['num_edges'] - num_edges)**2)**0.5
        max_distance = max(distance, max_distance) # update the maximum distance if needed
        for i in range(10):
            if distance < top_matches[i][0]:
                # Insert distance, matched row, and placeholder for similarity score
                top_matches.insert(i, [distance, row, 0])
                top_matches.pop()
                break
    for match in top_matches:
        match[2] = 1 - match[0] / max_distance  # calculate normalized similarity score 
    return top_matches

def render_2d_projection(file_path, file_name):
    mesh = trimesh.load_mesh(file_path)
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_trisurf(mesh.vertices[:,0], mesh.vertices[:,1], mesh.vertices[:,2], triangles=mesh.faces, cmap=plt.cm.Spectral)
    plt.savefig('temp.png')
    image = Image.open('temp.png')
    st.image(image, caption=f'2D Projection of {file_name}', use_column_width=True)

def download_blobs(blob_service_client, container_name, dest_folder):
    blob_container_client = blob_service_client.get_container_client(container_name)
    blobs_list = blob_container_client.list_blobs()
    for blob in blobs_list:
        blob_client = blob_service_client.get_blob_client(container_name, blob.name)
        with open(os.path.join(dest_folder, blob.name), "wb") as my_blob:
            download_stream = blob_client.download_blob()
            my_blob.write(download_stream.readall())

def update_db():
    blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    download_blobs(blob_service_client, "blobcontainer", "tempDir")
    if os.path.exists("database.csv"):
        os.remove("database.csv")
    for filename in os.listdir("tempDir"):
        volume, cog, num_faces, num_vertices, num_edges = preprocess_file(os.path.join("tempDir", filename))
        data = {'filename': filename, 'volume': volume, 'cog_x': cog[0], 'cog_y': cog[1], 'cog_z': cog[2], 'num_faces': num_faces, 'num_vertices': num_vertices, 'num_edges': num_edges}
        df = pd.DataFrame(data, index=[0])
        # check if the file exists, if not write header
        if not os.path.isfile('database.csv'):
            df.to_csv('database.csv', mode='a', header=True, index=False)
        else: # else it exists so append without writing the header
            df.to_csv('database.csv', mode='a', header=False, index=False)
    for filename in os.listdir("tempDir"):
        os.remove(os.path.join("tempDir", filename))

def download_blob(blob_service_client, container_name, blob_name, dest_folder):
    blob_client = blob_service_client.get_blob_client(container_name, blob_name)

    # List all blobs in the container to ensure that blob_name exists
    blob_container_client = blob_service_client.get_container_client(container_name)
    blobs_list = blob_container_client.list_blobs()
    for blob in blobs_list:
        print(blob.name)
    
    with open(os.path.join(dest_folder, blob_name), "wb") as my_blob:
        download_stream = blob_client.download_blob()
        my_blob.write(download_stream.readall())

def clear_directory(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

sched = BackgroundScheduler()
sched.add_job(update_db, 'interval', hours=3)
sched.start()

def main():
    st.title('CAD Matching API')
    database_file = st.file_uploader("Choose a file to add to database", type=['stl', 'step'], key='database_uploader')

    if st.button('Sync Database'):
        update_db()
        st.success('Database Synced')
        
    if database_file is not None:
        save_uploadedfile(database_file)
        volume, cog, num_faces, num_vertices, num_edges = preprocess_file(f'tempDir/{database_file.name}')        
        # load or initialize data
        if not os.path.isfile('database.csv'):
            data = pd.DataFrame()
        else:
            data = pd.read_csv('database.csv')
        # check if file name exists and only write new record
        if database_file.name not in data['filename'].values:
            blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
            upload_file_to_blob(blob_service_client, f'tempDir/{database_file.name}', database_file.name, 'blobcontainer')
            new_data = {'filename': database_file.name, 'volume:': volume, 'cog_x': cog[0], 'cog_y': cog[1], 'cog_z': cog[2], 'num_faces': num_faces, 'num_vertices': num_vertices, 'num_edges': num_edges}
            df = pd.DataFrame(new_data, index=[0])
            df.to_csv('database.csv', mode='a', header=False, index=False)
        
    uploaded_file = st.file_uploader("Choose a file for comparison", type=['stl', 'step'], key='comparison_uploader')
    
    if uploaded_file is not None:
        save_uploadedfile(uploaded_file)
        volume, cog, num_faces, num_vertices, num_edges = preprocess_file(f'tempDir/{uploaded_file.name}')
        top_matches = compare_files(volume, cog, num_faces, num_vertices, num_edges)
        st.write(f'Best Matches: {top_matches[0][1]["filename"]}, {top_matches[1][1]["filename"]}, {top_matches[2][1]["filename"]}') 
        st.write(f'Similarity Scores: {top_matches[0][2]}, {top_matches[1][2]}, {top_matches[2][2]}')
        # Preprocess and comparison code
        blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
        for match in top_matches[:3]:
            # print out the blob names
            container_client = blob_service_client.get_container_client('blobcontainer')
            blobs_list = container_client.list_blobs()
            for blob in blobs_list:
                print(blob.name)
            # Download the matched file from blob storage
            download_blob(blob_service_client, 'blobcontainer', match[1]["filename"], 'tempdownload')
            render_2d_projection(f'tempdownload/{match[1]["filename"]}', match[1]["filename"])
        render_2d_projection(f'tempDir/{uploaded_file.name}', uploaded_file.name)
        # clear the tempdownload directory
        clear_directory('tempdownload')

if __name__ == '__main__':
    main()