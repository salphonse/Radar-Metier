# Test API
uvicorn main:app --host "0.0.0.0" --port 8000

# Build image
docker build -t radar_metier_api . 

# Run containers
docker run -d -p 127.0.0.1:8000:8000 radar_metier_api