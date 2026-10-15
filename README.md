# Fitness Music Recommender - Backend

Play music for your workout and achieve your target exercise intensity.
The Fitness Music Recommender monitors your heart rate and selects a suitable song accordingly.
The app was developed as part of my bachelor's thesis at the 
[University of Applied Sciences Düsseldorf](https://www.hs-duesseldorf.de/).

<img src="https://github.com/simonldwg/fmr-phone/blob/471e476a87e5edbb8c34f1d8985af7a291b9bca4/Screenshot_20261006-175859.png" alt="app screenshot" width="250">

---

This repository contains the source code for the backend REST API. The API uses Django and Django Ninja as the base
framework. Music feature extraction uses Essentia / Essentia-TensorFlow and custom ML models which are not included in 
this repository for licensing reasons. The models, as well as the recommendation and feature extraction code itself are 
based on the music recommender developed in seminars and projects led by Professor 
[Jochen Steffens](https://medien.hs-duesseldorf.de/personen/steffens). The API is based largely on the 
[Remommender](https://github.com/Nasenboi/remommender), a previous project that I co-developed with my teammate 
[Christian](https://github.com/Nasenboi). Large parts of this source code are therefore written by him.

While the Remommender focuses on music recommendation based on Speech Emotion Recognition (SER) (i.e. recommending music 
based on the emotion observed while you talk), this API has been adapted for recommending music in general. This means 
it solely provides an endpoint for generating playlists based on music features (such as bpm) and filters (such 
as genre or maximum song length). For generating the playlist, a simple k-Nearest-Neighbor algorithm is used. The 
fitness-specific code lives entirely in the [FMR phone](https://github.com/simonldwg/fmr-phone) app, where the actual 
feature values used for the recommendation (such as bpm and arousal) are computed based on the user's heart rate. This 
backend is solely used for managing the music library (e.g. adding/deleting songs) and generating playlists based on 
generic music features. Therefore, this backend could also be used in other contexts, not just in the fitness domain.

This backend is intended as a prototype / proof-of-concept and has **zero security measures,** not even a basic 
authentication and authorization system. By default, any host can access this backend, unless the port is blocked by a 
third-party firewall. Also, anyone can access the stored media files. Using this backend in any production environment 
without prior modification is therefore highly discouraged.

---

## Getting Started
The easiest way to start the backend is using Docker.

To build the docker container from the source code, you have to:
1. Clone the repository
   ```shell
   git clone https://github.com/simonldwg/fmr-backend.git
   ```
2. Configure the app using the Docker compose file.
   You **need to specify the data directory** you want to mount. The rest is set by default.
   The data directory can be specified within the Docker Compose file as follows:
   ```yaml
   # ...
   volumes:
     - "C:/Users/<username>/fmr-backend-data:/data"
   # ...
   ```
   Replace `C:/Users/<username>/fmr-backend-data` with the path on your local filesystem. `:/data` means that the 
   specified folder on your own filesystem will be mounted at `/data` within the container filesystem.
   > The path structure within your local directory should look like this:  
   > /fmr-backend-data  
   > |- /srv  
   > |----|- db.sqlite3  
   > |----|- /Media  
   > |- /Models  
   > |----|- /gmbi_old_nn  
   > |----|----|- \<...\>  
   > |----|- /gmbi_rf  
   > |----|----|- \<...\>  
   > |----|- genre.pb  
   > |----|- \<...\>
   
   If you want to import pre-calculated data, you also have to customize the corresponding environment variables in the 
   `docker-compose.yml` file (see below).
3. Run the Docker Compose command to build
   ```shell
   docker compose build backend
   ```
4. Run the container
   ```shell
   docker compose up
   # If you don't want terminal output, you can run the command detached by adding the option -d
   ```
   Note: You may need to add sudo if permissions are failing.

### Backend Server without Docker
Please note: There are major issues when trying to install / run Essentia for Python on Windows. Therefore, it is 
strongly recommended to use a Docker container if you are on Windows. The instructions below are only for Unix-based 
systems (i.e. macOS / Linux).

To run the backend server without a Docker container, you need a Python virtual environment. **It is important to use Python Version 3.9.**

1. Create a virtual environment in the `.venv/` folder
   ```shell
   python -m venv .venv
   ```
2. Activate the virtual environment
   ```shell
   source .venv/bin/activate
   ```
   If the virtual environment is active, the string `(.venv)` should appear before the prompt.
3. Install the necessary packages in your Python environment
   ```shell
   pip install -r requirements.txt
   ```
4. Make sure to set the necessary environment variables (see below). Alternatively, you can create a `.env` file 
   containing all required environment variables. See the `.env.sample` file for an example.
5. Create the necessary database tables
   ```shell
   python manage.py migrate
   ```
6. Run the server
   ```shell
   python manage.py runserver
   ```

Make sure to always activate the virtual environment before running the server.

### Pre-calculated songs
The app allows you to import songs which have pre-calculated features. This was built to quickly import an existing test 
database of songs. For each song, three files have to be provided: an audio file, a JSON file (metadata and music 
features) and an album artwork file. If you want to use pre-calculated data, you have to specify the corresponding 
environment variables (see below). Once the environment variables are specified, you can add the pre-calculated data 
using the following management command:

```shell
python manage.py add_pre_calculated_songs
```

> Note: When using Docker, executing this command is not necessary. The pre-calculated data is added automatically if
> the environment variables `PRE_CALC_JSON_PATH`, `PRE_CALC_AUDIO_PATH` and `PRE_CALC_ALBUM_ART_PATH` are set within the 
> `docker-compose.yml` file. 
> 
> Simply move the `Audio_jsons/`, `Audio/` and `Album_Art/` directories to the `srv/Media/` directory.
> Then, provide the environment variables in the `docker-compose.yml` file.


## Configuration (environment variables)
| Name                        | Description                                                                                                                                                                                                                                                                                           |
|-----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| SECRET\_KEY                 | The secret key for the Django backend server. Used for cryptographic signing. Always has to be set. An insecure default value is provided in the `docker-compose.yml` file.                                                                                                                           |
| FRONTEND_URL                | A comma separated list of URL strings. Used to configure CORS. Optional and only necessary when working with a web frontend.                                                                                                                                                                          |
| MEDIA\_URL                  | The URL prefix added to the URL of a media file. These media files include the songs and album artworks that were uploaded by users, ex. `http://SERVER_URL/MEDIA_URL/songs/<id>` => link to a specific song.                                                                                         |
| MEDIA\_ROOT                 | The root folder where media files (songs and album artworks) are stored. Additional sub-directories are created automatically if they do not exist.                                                                                                                                                   |
| SQL\_PATH                   | The path to the SQL server file used by the Django DB.                                                                                                                                                                                                                                                |
| MODEL\_PATH                 | The path to pre trained models used for the song feature extraction.                                                                                                                                                                                                                                  |
| PRE\_CALC\_JSON\_PATH       | The path to pre calculated JSON data, see above.                                                                                                                                                                                                                                                      |
| PRE\_CALC\_AUDIO\_PATH      | The path to the songs from pre calculated song data, see above.                                                                                                                                                                                                                                       |
| PRE\_CALC\_ALBUM\_ART\_PATH | The path to the album artworks from pre calculated song data, see above.                                                                                                                                                                                                                              |
| MIN\_PLAYLIST\_LENGTH       | Clients can provide a desired playlist length when requesting the API to recommend a playlist. This variable sets the minimum playlist length, i.e. the minimum length before the API throws an error because the requested playlist length is too short. Defaults to 3 if nothing else is specified. |
| MAX\_PLAYLIST\_LENGTH       | Clients can provide a desired playlist length when requesting the API to recommend a playlist. This variable sets the maximum playlist length, i.e. the maximum length before the API throws an error because the requested playlist length is too long. Defaults to 20 if nothing else is specified. |
| DEFAULT\_PLAYLIST\_LENGTH   | Clients can provide a desired playlist length when requesting the API to recommend a playlist. This variable sets the default playlist length, i.e. the playlist length used when clients don't provide a desired length themselves. Defaults to 10 if nothing else is specified.                     |

---

## API Documentation
While the backend is running, the documentation for the different API endpoints is available at `/docs`.

## Statistics
To export statistics about your current song library to an Excel file, you can use the following command:

```shell
python manage.py export_library_stats_to_excel
```

Use the `--help` flag to show the different arguments of the command. The default filename of the generated workbook is
`song_stats.xlsx`.

---

### Other repos of this project
* [Smartphone app](https://github.com/simonldwg/fmr-phone)
* [Wear OS app](https://github.com/simonldwg/fmr-wearos)
* [FMRAndroidCore library](https://github.com/simonldwg/fmr-android-core)
