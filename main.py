import os
from fastapi import FastAPI, HTTPException, Header, Depends
from starlette.responses import RedirectResponse
import requests
from dotenv import load_dotenv

load_dotenv()

AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN", "")
AUTH0_API_AUDIENCE = os.environ.get("AUTH0_API_AUDIENCE", "")
CLIENT_ID = os.environ.get("AUTH0_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get(
    "AUTH0_CLIENT_SECRET",
    "",
)

if not AUTH0_DOMAIN or not AUTH0_API_AUDIENCE:
    raise ValueError(
        "AUTH0_DOMAIN and AUTH0_API_AUDIENCE must be set as environment variables."
    )

app = FastAPI(
    title="Profile Management API",
    description="API for user profile management with Auth0 authentication.",
    version="1.0.0",
)


# ---
# Dependencies
# ---


def get_current_user_info(authorization: str = Header(...)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Invalid or missing Authorization header"
        )

    access_token = authorization.split(" ")[1]

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.get(
            f"https://{AUTH0_DOMAIN}/userinfo",
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # Log the error for debugging
        print(f"Auth0 UserInfo request failed: {e}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")


# ---
# API Routes
# ---


@app.get("/login")
def login():
    """
    Redirects the user to Auth0 for authentication.
    """
    return RedirectResponse(
        url=f"https://{AUTH0_DOMAIN}/authorize?audience={AUTH0_API_AUDIENCE}&response_type=code&client_id={CLIENT_ID}&scope=offline_access openid profile email&redirect_uri=http://localhost:8000/token"
    )


@app.get("/token")
def get_access_token(code: str):
    payload = (
        "grant_type=authorization_code",
        f"&code={code}",
        f"&client_id={CLIENT_ID}",
        f"&client_secret={CLIENT_SECRET}",
        f"&redirect_uri=http://localhost:8000/token",
    )

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(
        f"https://{AUTH0_DOMAIN}/oauth/token",
        headers=headers,
        data="".join(payload),
        timeout=10,
    )

    return response.json()


# New endpoint to get user details
@app.get("/user_info")
def get_user_info(user: dict = Depends(get_current_user_info)):
    """
    Returns the user's profile information.
    """
    return {"message": "Welcome to your profile!", "user_details": user}
