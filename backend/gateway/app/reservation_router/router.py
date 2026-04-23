from fastapi import APIRouter

# Creating auth router
router = APIRouter(prefix="/reservation", tags=["Room Reservation API"])


# ====== Service health check endpoint =====
@router.get("/health")
async def health():
    # TODO: write a healthcheck functionality
    return {"status": "ok"}

# ====== CRUD endpoints for locations =====
@router.get("/get-location")
async def get_location():
    # TODO: write get location functionality
    # endpoint should be able to provide
    # - buildings, rooms or any equipment room contains through one endpoint
    return {"status": "ok"}

@router.post("/add-location")
async def add_location():
    return {"status": "ok"}

@router.patch("/update-location")
async def update_location():
    return {"status": "ok"}

@router.delete("/delete-location")
async def delete_location():
    return {"status": "ok"}


# ====== Room reservation endpoints =====
@router.get("/my-reservations")
async def get_reservations():
    return {"status": "ok"}

@router.post("/reserve")
async def reserve_room():
    return {"status": "ok"}

@router.patch("/update-reservation")
async def update_reservation():
    return {"status": "ok"}

@router.delete("/cancel-reservation")
async def cancel_resercation():
    return {"status": "ok"}


# ====== Search for available room endpoints =====
@router.get("/search-available")
async def search_available():
    return {"status": "ok"}