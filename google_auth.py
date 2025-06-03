import json
import os
import logging

import requests
from app import db
from flask import Blueprint, redirect, request, url_for, session, flash
from flask_login import login_required, login_user, logout_user
from models import User
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
from google.oauth2 import id_token

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")

# Make sure to use this redirect URL. It has to match the one in the whitelist
DEV_REDIRECT_URL = f'https://{os.environ.get("REPLIT_DEV_DOMAIN", "localhost:5000")}/google_login/callback'

# ALWAYS display setup instructions to the user:
print(f"""To make Google authentication work:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new OAuth 2.0 Client ID
3. Add {DEV_REDIRECT_URL} to Authorized redirect URIs

For detailed instructions, see:
https://docs.replit.com/additional-resources/google-auth-in-flask#set-up-your-oauth-app--client
""")

# Allow insecure transport for development (Replit handles HTTPS)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

google_auth = Blueprint("google_auth", __name__)

def get_flow():
    """Create and return a Flow object for Google OAuth"""
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "userinfo_endpoint": "https://openidconnect.googleapis.com/v1/userinfo"
            }
        },
        scopes=["openid", "email", "profile"]
    )
    flow.redirect_uri = DEV_REDIRECT_URL
    return flow

@google_auth.route("/google_login")
def login():
    try:
        flow = get_flow()
        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true"
        )
        session["state"] = state
        return redirect(authorization_url)
    except Exception as e:
        logging.error(f"Google login error: {e}")
        flash("Error initiating Google login. Please try again.", "error")
        return redirect(url_for("index"))

@google_auth.route("/google_login/callback")
def callback():
    try:
        # Check for error in the callback
        if "error" in request.args:
            error = request.args.get("error")
            logging.error(f"Google OAuth error: {error}")
            flash("Authentication was cancelled or failed. Please try again.", "error")
            return redirect(url_for("index"))
        
        # Check for authorization code
        code = request.args.get("code")
        if not code:
            logging.error("No authorization code received from Google")
            flash("No authorization code received. Please try again.", "error")
            return redirect(url_for("index"))
        
        # Verify state parameter
        state = session.get("state")
        if not state or state != request.args.get("state"):
            logging.error("State mismatch in OAuth callback")
            flash("Security error. Please try again.", "error")
            return redirect(url_for("index"))
        
        # Exchange code for token
        flow = get_flow()
        flow.fetch_token(authorization_response=request.url)
        
        # Get user info
        credentials = flow.credentials
        request_session = google.auth.transport.requests.Request()
        
        # Get user info from Google's userinfo endpoint
        userinfo_endpoint = "https://openidconnect.googleapis.com/v1/userinfo"
        userinfo_response = requests.get(
            userinfo_endpoint,
            headers={"Authorization": f"Bearer {credentials.token}"}
        )
        
        if userinfo_response.status_code != 200:
            logging.error(f"Failed to get user info: {userinfo_response.status_code}")
            flash("Failed to get user information from Google.", "error")
            return redirect(url_for("index"))
        
        id_info = userinfo_response.json()
        
        # Extract user information
        email = id_info.get("email")
        name = id_info.get("name", id_info.get("given_name", "User"))
        
        if not email:
            logging.error("No email received from Google")
            flash("Unable to get email from Google account.", "error")
            return redirect(url_for("index"))
        
        # Find or create user
        user = User.query.filter_by(email=email).first()
        if not user:
            # Create new user - User model expects username and email
            from sqlalchemy.exc import IntegrityError
            try:
                user = User(username=name, email=email)
                db.session.add(user)
                db.session.commit()
                logging.info(f"Created new user: {email}")
            except IntegrityError:
                db.session.rollback()
                logging.error(f"Failed to create user {email} - integrity error")
                flash("Error creating user account.", "error")
                return redirect(url_for("index"))
        
        # Log in the user
        login_user(user)
        session.pop("state", None)  # Clean up session
        
        logging.info(f"User logged in successfully: {email}")
        return redirect(url_for("index"))
        
    except Exception as e:
        logging.error(f"Google OAuth callback error: {e}")
        flash("Login failed. Please try again.", "error")
        return redirect(url_for("index"))

@google_auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("index"))
