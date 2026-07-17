FROM python:3.9.23

# SQL_PATH is automatically set in settings.py to:
# /fmr_backend/db.sqlite3
ENV MEDIA_URL="/media/"
ENV MEDIA_ROOT="/data/srv/media/"
ENV MODEL_PATH="/data/Models/"
ENV SQL_PATH="/data/srv/db.sqlite3"
# Suppress TensorFlow logging
ENV TF_CPP_MIN_LOG_LEVEL=2
ENV PYTHONWARNINGS="ignore"
# The last thing that is required and cannot be set by default
# is the SECRET_KEY

EXPOSE 8000

WORKDIR /fmr-backend

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
# RUN pip install --extra-index-url https://download.pytorch.org/whl/cpu --no-cache-dir librosa django-ninja scikit-learn==1.0.2 python-dotenv welford typing annoy transformers pandas torch essentia essentia-tensorflow matplotlib django-cors-headers tempocnn

COPY . /fmr-backend

RUN sed -i 's/\r$//' runserver.sh && \
    chmod +x runserver.sh

ENTRYPOINT ["./runserver.sh"]
CMD []
