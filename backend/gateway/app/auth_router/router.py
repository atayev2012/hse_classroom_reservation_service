from fastapi import APIRouter

# Creating auth router
router = APIRouter(prefix="/auth", tags=["Authorization/Authentication API"])

@router.get("/health")
async def health():
    return {"status": "ok"}

# Get current user endpoint
@router.get("/me")
async def me():
    # TODO: Write full get user functionality
    return {"status": "ok"}

# Login endpoint
@router.post("/login")
async def login():
    # TODO: Write full login functionality with HSE university email
    return {"status": "ok"}

# Logout endpoint
@router.post("/logout")
async def logout():
    # TODO: Write logout functionality
    return {"status": "ok"}

# Verify email code or link received through email after login
@router.post("/verify")
async def verify():
    # TODO: Write code verification functionality
    return {"status": "ok"}

# Endpoint to refresh JWT Token
@router.post("/refresh")
async def refresh():
    # TODO: Write functionality to refresh JWT token
    return {"status": "ok"}
