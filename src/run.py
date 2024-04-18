if __name__ == "__main__":
    import os
    import dotenv
    import uvicorn

    dotenv.load_dotenv()
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", default="localhost"),
        port=int(os.getenv("PORT", default=8000)),
        reload=True,
        reload_dirs=["."],
    )
