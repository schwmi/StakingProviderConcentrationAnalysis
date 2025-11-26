docker build -t jupyter-image-ml0 .
docker run -p 8888:8888 -v .:/home/jovyan/work jupyter-image-ml0
