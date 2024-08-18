import os
import secrets
from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import FastAPI, Depends, Request
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import gradio as gr
from dotenv import load_dotenv

# Gradio will be mounted in the FastAPI app
app = FastAPI()

# Configure OAuth with Okta
# https://docs.authlib.org/en/latest/client/starlette.html
load_dotenv(".okta.env")
oauth = OAuth()
okta_issuer = os.getenv("OKTA_OAUTH2_ISSUER")
oauth.register(
    name="okta",
    client_id=os.getenv("OKTA_OAUTH2_CLIENT_ID"),
    client_secret=os.getenv("OKTA_OAUTH2_CLIENT_SECRET"),
    access_token_url=f"{okta_issuer}/v1/token",
    authorize_url=f"{okta_issuer}/v1/authorize",
    redirect_uri="http://127.0.0.1:8080/auth",
    # the metadata url is not working for some reason
    # metadata_url=f'{okta_issuer}/.well-known/openid-configuration',
    # without the following, authlib cant get jwks_uri from the metadata url
    jwks_uri=f"{okta_issuer}/v1/keys",
    client_kwargs={"scope": "openid email profile"},
)

# For AWS Lambda, store SECRET_KEY in secrets manager.
# Recreating it on every restart wont work in serverless environments.
SECRET_KEY = secrets.token_hex(64)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


# Dependency to get the current user
def get_user(request: Request):
    user = request.session.get("user")
    return user["name"] if user else None


@app.get("/")
def public(user: dict = Depends(get_user)):
    return RedirectResponse(url="/gradio") if user else RedirectResponse(url="/login-demo")


@app.route("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/")


@app.route("/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth")
    # If your app is running on https, you should ensure that the
    # `redirect_uri` is https, e.g. uncomment the following lines:
    #
    # from urllib.parse import urlparse, urlunparse
    # redirect_uri = urlunparse(urlparse(str(redirect_uri))._replace(scheme='https'))
    return await oauth.okta.authorize_redirect(request, redirect_uri)


@app.route("/auth")
async def auth(request: Request):
    try:
        access_token = await oauth.okta.authorize_access_token(request)
    except OAuthError:
        return RedirectResponse(url="/")
    request.session["user"] = dict(access_token)["userinfo"]
    return RedirectResponse(url="/")


# This Gradio app will be mounted at /login-demo and doesn't require auth
with gr.Blocks() as login_demo:
    gr.Button("Login", link="/login")
app = gr.mount_gradio_app(app, login_demo, path="/login-demo")


def greet(request: gr.Request):
    return f"Welcome to Gradio, {request.username}"


# This Gradio app will be mounted at /gradio and requires auth
with gr.Blocks() as main_demo:
    m = gr.Markdown("Welcome to Gradio!")
    gr.Button("Logout", link="/logout")
    main_demo.load(greet, None, m)
app = gr.mount_gradio_app(
    app, main_demo, path="/gradio", auth_dependency=get_user)

if __name__ == "__main__":
    uvicorn.run(app, port=8080)
