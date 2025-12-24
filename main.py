from flask import Flask, request, jsonify
import os
import tempfile
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.cloud import storage

app = Flask(__name__)

SHEET_ID = os.environ["SHEET_ID"]
BUCKET_NAME = os.environ["BUCKET_NAME"]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/devstorage.read_write"
]

creds = service_account.Credentials.from_service_account_file(
    "service-account.json",
    scopes=SCOPES
)

sheets_service = build("sheets", "v4", credentials=creds)
storage_client = storage.Client(credentials=creds)


@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name")
    description = request.form.get("description")
    keywords = request.form.get("keywords")
    link = request.form.get("link")

    if not name or not description:
        return jsonify({"error": "Missing required fields"}), 400

    # Handle file upload
    if "file" in request.files:
        f = request.files["file"]

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            f.save(tmp.name)

        blob = storage_client.bucket(BUCKET_NAME).blob(f.filename)
        blob.upload_from_filename(tmp.name)
        blob.make_public()

        link = blob.public_url

    row = [[name, description, keywords, link]]

    sheets_service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range="Sheet1!A:D",
        valueInputOption="USER_ENTERED",
        body={"values": row}
    ).execute()

    return jsonify({"status": "ok"})
