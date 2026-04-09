from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, time
import uuid

app = FastAPI(
    title="Timesheet API",
    description="A simple API to manage timesheet entries",
    version="1.0.0"
)

# --- In-memory store ---
timesheets: dict = {}


# --- Models ---
class TimesheetEntry(BaseModel):
    employee_name: str = Field(..., example="Alice Johnson")
    project: str = Field(..., example="Project Phoenix")
    work_date: date = Field(..., example="2026-04-09")
    start_time: time = Field(..., example="09:00:00")
    end_time: time = Field(..., example="17:30:00")
    description: Optional[str] = Field(None, example="Implemented login module")


class TimesheetResponse(TimesheetEntry):
    id: str
    hours_worked: float


# --- Helpers ---
def calc_hours(start: time, end: time) -> float:
    start_mins = start.hour * 60 + start.minute
    end_mins = end.hour * 60 + end.minute
    return round((end_mins - start_mins) / 60, 2)


# --- Routes ---

@app.get("/", tags=["Health"])
def root():
    return {"message": "Timesheet API is running. Visit /docs for the Swagger UI."}


@app.post("/timesheets", response_model=TimesheetResponse, status_code=201, tags=["Timesheets"])
def add_entry(entry: TimesheetEntry):
    """Add a new timesheet entry."""
    if entry.end_time <= entry.start_time:
        raise HTTPException(status_code=400, detail="end_time must be after start_time.")

    entry_id = str(uuid.uuid4())
    hours = calc_hours(entry.start_time, entry.end_time)

    record = TimesheetResponse(id=entry_id, hours_worked=hours, **entry.model_dump())
    timesheets[entry_id] = record
    return record


@app.get("/timesheets", response_model=list[TimesheetResponse], tags=["Timesheets"])
def view_all_entries(employee_name: Optional[str] = None, project: Optional[str] = None):
    """View all timesheet entries. Optionally filter by employee_name or project."""
    results = list(timesheets.values())

    if employee_name:
        results = [r for r in results if r.employee_name.lower() == employee_name.lower()]
    if project:
        results = [r for r in results if r.project.lower() == project.lower()]

    return results


@app.get("/timesheets/{entry_id}", response_model=TimesheetResponse, tags=["Timesheets"])
def view_entry(entry_id: str):
    """Retrieve a single timesheet entry by its ID."""
    entry = timesheets.get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Entry '{entry_id}' not found.")
    return entry

# added for code review demo
# demo change for PR
@app.delete("/timesheets/{entry_id}", status_code=200, tags=["Timesheets"])
def delete_entry(entry_id: str):
    """Delete a timesheet entry by its ID."""
    if entry_id not in timesheets:
        raise HTTPException(status_code=404, detail=f"Entry '{entry_id}' not found.")
    del timesheets[entry_id]
    return {"message": f"Entry '{entry_id}' deleted successfully."}


# --- Run directly ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("timesheet_api:app", host="0.0.0.0", port=8000, reload=True)