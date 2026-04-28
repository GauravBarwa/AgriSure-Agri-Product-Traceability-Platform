from fastapi import FastAPI
from routes import farmer, lot, inspection, contract, payment, admin, transaction_demo
from contextlib import asynccontextmanager
from db import pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Logic ---
    # Open the connection pool
    pool.open()
    print("DB Connection Pool opened.")
    
    yield  # The app runs while it's "yielding"
    
    # --- Shutdown Logic ---
    # Close the connection pool
    pool.close()
    print("DB Connection Pool closed.")

app = FastAPI(
    title="AgriSure Backend",
    version="1.0",
    lifespan=lifespan # Register the lifespan
)

app.include_router(farmer.router)
app.include_router(lot.router)
app.include_router(inspection.router)
app.include_router(contract.router)
app.include_router(payment.router)
app.include_router(admin.router)
app.include_router(transaction_demo.router)


@app.get("/")
def root():
    return {"message": "AgriSure API is running 🚀"}
