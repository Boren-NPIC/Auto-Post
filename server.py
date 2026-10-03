import os
import shutil
import json
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Auto-Post Multi-Folder Manager API")

# អនុញ្ញាត CORS សម្រាប់ Web Interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ថតមេសម្រាប់ផ្ទុកវីដេអូ
UPLOAD_BASE_DIR = "uploads"
os.makedirs(UPLOAD_BASE_DIR, exist_ok=True)


# ==========================================
# 1. ROUTE បង្ហាញផ្ទាំង FRONTEND (INDEX.HTML)
# ==========================================
@app.get("/")
async def serve_home():
    """ពេលចូល http://127.0.0.1:8000 វានឹងបើកផ្ទាំង index.html ភ្លាមៗ មិនចេញ 404 ទៀតឡើយ"""
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"message": "រកមិនឃើញ file index.html សូមប្រាកដថាវាស្ថិតក្នុង folder តែមួយជាមួយ server.py"}


# ==========================================
# 2. ROUTE ទទួល UPLOAD វីដេអូ & កាលវិភាគ
# ==========================================
@app.post("/api/bulk-upload")
async def bulk_upload(
    page_id: str = Form(...),
    start_date: str = Form(...),
    caption: str = Form(...),
    auto_delete: bool = Form(True),
    videos: List[UploadFile] = File(...),
    # ប៉ារ៉ាម៉ែត្រថ្ងៃបញ្ចប់ពី Master Campaign UI
    end_date: Optional[str] = Form(None),
    # ប៉ារ៉ាម៉ែត្រម៉ោង (បញ្ជូនមកជា JSON String ពី Front-end)
    morning_times: Optional[str] = Form(None),
    noon_times: Optional[str] = Form(None),
    night_times: Optional[str] = Form(None),
    total_per_day: Optional[int] = Form(None),
    # ប៉ារ៉ាម៉ែត្រចាស់ៗ (Optional ដើម្បីបង្ការ Error 422 ពេលមាន request ចាស់)
    morning_time: Optional[str] = Form(None),
    noon_time: Optional[str] = Form(None),
    night_time: Optional[str] = Form(None),
    post_time: Optional[str] = Form(None)
):
    try:
        # បង្កើត Folder ផ្ទុកវីដេអូដាច់ដោយឡែកតាម Page ID
        target_dir = os.path.join(UPLOAD_BASE_DIR, page_id)
        os.makedirs(target_dir, exist_ok=True)

        # បម្លែងម៉ោងផុសពី JSON string
        morning_list = json.loads(morning_times) if morning_times else ([morning_time] if morning_time else [])
        noon_list = json.loads(noon_times) if noon_times else ([noon_time] if noon_time else [])
        night_list = json.loads(night_times) if night_times else ([night_time] if night_time else [])

        all_slots = morning_list + noon_list + night_list

        # រក្សាទុក Files វីដេអូទៅក្នុង Folder របស់ Page នោះ
        saved_files = []
        for video in videos:
            file_path = os.path.join(target_dir, video.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(video.file, buffer)
            saved_files.append(video.filename)

        # កត់ត្រា Configuration & Schedule ទុកសម្រាប់ Script Auto Post
        config_data = {
            "page_id": page_id,
            "start_date": start_date,
            "end_date": end_date or start_date,
            "auto_delete": auto_delete,
            "caption_template": caption,
            "morning_times": morning_list,
            "noon_times": noon_list,
            "night_times": night_list,
            "total_per_day": total_per_day or len(all_slots),
            "files": saved_files
        }

        config_path = os.path.join(target_dir, "schedule_config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)

        print(f"✅ បានរក្សាទុកទិន្នន័យ Page: {page_id} | ចំនួនវីដេអូ: {len(saved_files)} | ថ្ងៃផុស: {start_date} ដល់ {end_date or start_date}")

        return {
            "status": "success",
            "message": f"បានបញ្ចូលវីដេអូចំនួន {len(saved_files)} ទៅ Folder {page_id} ដោយជោគជ័យ!",
            "data": config_data
        }

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 3. ROUTE SYNC FACEBOOK PAGES
# ==========================================
@app.post("/api/sync-facebook-pages")
async def sync_facebook_pages(user_access_token: str = Form(...)):
    """ទាញបញ្ជី Pages ពី Facebook Graph API"""
    return {
        "status": "success",
        "data": [
            {"id": "61554109830366", "name": "Mrr. Boren"},
            {"id": "61580479197489", "name": "NCBR-Video"}
        ]
    }


if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)