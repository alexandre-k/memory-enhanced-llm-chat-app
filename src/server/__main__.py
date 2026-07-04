def main():
    # For convenience when installed via uv, but usually you run uvicorn directly.
    import uvicorn
    uvicorn.run("server.api:app",
                host="0.0.0.0",
                port=8000,
                log_config=None,
                reload=True)