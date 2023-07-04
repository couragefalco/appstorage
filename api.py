from fastapi import FastAPI, File, UploadFile, HTTPException
import pandas as pd
from starlette.responses import JSONResponse
from app import preprocess_file, compare_files, render_2d_projection, save_uploadedfile_api, upload_file_to_blob
from azure.storage.blob import BlobServiceClient

app = FastAPI()
CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=blobconfigurator;AccountKey=j9kYa3w9z11ukkynzpJuhgPheGbgEJGPve9sNAfHG9ErsKUpZCtnqC+hnNRURqudc3UhACwOSZ3g+AStdKhYpg==;EndpointSuffix=core.windows.net"

@app.post("/files/")
async def create_file(file: UploadFile = File(...)):
    try:
        save_uploadedfile_api(file)
        volume, cog, num_faces, num_vertices, num_edges = preprocess_file(f'tempDir/{file.filename}')
        blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
        upload_file_to_blob(blob_service_client, f'tempDir/{file.filename}', file.filename, 'blobcontainer')
        data = {'filename': file.filename, 'volume:': volume, 'cog_x': cog[0], 'cog_y': cog[1], 'cog_z': cog[2], 'num_faces': num_faces, 'num_vertices': num_vertices, 'num_edges': num_edges}
        df = pd.DataFrame(data, index=[0])
        df.to_csv('database.csv', mode='a', header=False, index=False)
        response = {"filename": file.filename, "volume": volume, "num_faces": num_faces, "num_vertices": num_vertices, "num_edges": num_edges, "cog": cog.tolist()}
        return JSONResponse(status_code=200, content=response)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/match/")
async def match_file(file: UploadFile = File(...)):
    try:
        save_uploadedfile_api(file)
        volume, cog, num_faces, num_vertices, num_edges = preprocess_file(f'tempDir/{file.filename}')
        top_matches = compare_files(volume, cog, num_faces, num_vertices, num_edges)
        matches = [{"filename": match[1]["filename"], "similarity_score": match[2]} for match in top_matches]
        response = {"filename": file.filename, "top_matches": matches}
        return JSONResponse(status_code=200, content=response)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))