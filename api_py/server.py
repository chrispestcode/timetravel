import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from api.api import API
from service.sqlite_record_service import SQLiteRecordService
from util.log import log_error

app = FastAPI()

service = SQLiteRecordService("timetravel.db")
api = API(records=service)

app.include_router(api.router, prefix="/api/v1")
app.include_router(api.router, prefix="/api/v2")

@app.get("/api/v1/health")
async def health() -> JSONResponse:
    return JSONResponse(content={"ok": True})


if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)
