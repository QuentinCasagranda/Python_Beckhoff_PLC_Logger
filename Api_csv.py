# Use the command : uvicorn Api_csv:app --host 0.0.0.0 --port 80
# To use this api

from fastapi import FastAPI, Response, HTTPException
import os

app = FastAPI()

CsvDir = "csv"
Csvname = "global"

    # --- API configuration ---
def configure_api(name: str, path: str):
    global CsvDir, Csvname
    CsvDir = path
    Csvname = name


@app.get("/getcsv")
def get_csv():
    file_path = os.path.join(CsvDir, f"{Csvname}.csv")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="CSV not found")
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    return Response(
        content=content,
        media_type="text/csv"
    )

# @app.get("/csv")
# def get_csv_query(sensor: str):
#     file_path = os.path.join(CSV_DIR, f"{sensor}.csv")
#     if not os.path.exists(file_path):
#         raise HTTPException(status_code=404, detail="CSV not found")
    
#     with open(file_path, "r", encoding="utf-8") as f:
#         content = f.read()
    
#     return Response(
#         content=content,
#         media_type="text/csv"
#     )
