from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="Supply Chain API",
    version="1.0.0",
    description="Supply Chain Management API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "message": "Supply Chain API is running",
    }

@app.get("/api/procurement/summary")
async def procurement_summary():
    return {"message": "Procurement summary endpoint"}

@app.get("/api/procurement/insights")
async def procurement_insights():
    return {"message": "Procurement insights endpoint"}

@app.get("/api/procurement/suppliers/overview")
async def suppliers_overview():
    return {"message": "Suppliers overview endpoint"}

@app.get("/api/procurement/suppliers/top-performers")
async def top_performers():
    return {"message": "Top performers endpoint"}

@app.get("/api/procurement/spend-optimization")
async def spend_optimization():
    return {"message": "Spend optimization endpoint"}

@app.get("/api/procurement/purchase-orders")
async def purchase_orders(limit: int = 4):
    return {"message": f"Purchase orders endpoint with limit {limit}"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
# anything
