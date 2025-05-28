import subprocess
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, metadata, SessionLocal
from pydantic import BaseModel

app =  FastAPI()

scraped_data = metadata.tables['vorysdata']  # Assuming 'vorysdata' is the name of your table in the SQLite DB

class ScrapedData(BaseModel):
    name: str
    position: str
    location: str
    email: str



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# GET REQUESTS :
@app.get("/sourav")
def get_scraped_data(db: Session = Depends(get_db)):
    results = db.execute(scraped_data.select()).fetchall()
    return [dict(row._mapping) for row in results]


@app.get("/sourav-updated")
def get_updated_data(db: Session = Depends(get_db)):
    try:
        # Replace with the correct path to your scrapy project folder
        project_path = r"D:\Learning\1scraped_data\vorys"  # raw string path (Windows)
        
        result = subprocess.run(
            ["scrapy", "crawl", "vorysdata"],
            cwd=project_path,
            check=True,
            capture_output=True,
            text=True
        )

        # After spider finishes, get updated data
        results = db.execute(scraped_data.select()).fetchall()
        return [dict(row._mapping) for row in results]

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sourav/search")
def search_scraped_data(name: str = "", location: str = "", db: Session = Depends(get_db)):
    query = scraped_data.select()
    if name:
        query = query.where(scraped_data.c.name.ilike(f"%{name.lower()}%"))
    if location:
        query = query.where(scraped_data.c.location.ilike(f"%{location.lower()}%"))
    
    results = db.execute(query).fetchall()
    return [dict(row._mapping) for row in results]


@app.get("/sourav/paginated")
def paginated_scraped_data(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    query = scraped_data.select().offset(skip).limit(limit)
    results = db.execute(query).fetchall()
    return [dict(row._mapping) for row in results]


# for run task in background: 
from fastapi import BackgroundTasks

scraping_status = {"running": False}
def run_spider():
    try:
        scraping_status["running"] = True
        project_path = r"D:\Learning\1scraped_data\vorys"
        result = subprocess.run(
            ["scrapy", "crawl", "vorysdata"],
            cwd=project_path,
            capture_output=True,
            text=True
        )
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
    finally:
        scraping_status["running"] = False
@app.get("/")
def run_scraper_async(bg_tasks: BackgroundTasks):
    bg_tasks.add_task(run_spider)
    return {"message": "Spider started in background"}

@app.get("/status")
def get_scrape_status():
    return {"scraping": scraping_status["running"]}



from fastapi.responses import StreamingResponse
import io
import csv

@app.get("/sourav/export")
def export_scraped_data(db: Session = Depends(get_db)):
    results = db.execute(scraped_data.select()).fetchall()

    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(scraped_data.columns.keys())  # headers
    for row in results:
        writer.writerow(list(row))

    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=data.csv"})


# POST REQUESTS :
@app.post("/sourav/add")
def add_scraped_data(data: ScrapedData, db: Session = Depends(get_db)):
    try:
        new_data = scraped_data.insert().values(
            name=data.name,
            position=data.position,
            location=data.location,
            email=data.email
        )
        db.execute(new_data)
        db.commit()
        return {"message": "Data added successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to add data: {str(e)}")
    

# UPDATE BY ID :
@app.put("/sourav/update/{data_id}")
def update_scraped_data(data_id: int, data: ScrapedData, db: Session = Depends(get_db)):
    try:
        update_query = (
            scraped_data.update()
            .where(scraped_data.c.id == data_id)
            .values(name=data.name, position=data.position, location=data.location, email=data.email)
        )
        db.execute(update_query)
        db.commit()
        return {"message": "Data updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update data: {str(e)}")
    

# DELETE OPERATION :
@app.delete("/sourav/delete/{name}")
def delete_scraped_data(name: str, db: Session = Depends(get_db)):
    try:
        delete_query = scraped_data.delete().where(scraped_data.c.name == name)
        db.execute(delete_query)
        db.commit()
        return {"message": "Data deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to delete data: {str(e)}")

