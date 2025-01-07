"Run the flask App"
from app import App
from app.Utils import RedisFlusher

app_instance = App()
app = app_instance.create_app()

if __name__ == "__main__":
    RedisFlusher().flush()
    app.run(host="0.0.0.0", port=5000, debug=True)
