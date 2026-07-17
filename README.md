# Fitness Music Recommender - Backend

Play music for your workout and achieve your target exercise intensity.
The Fitness Music Recommender monitors your heart rate and selects a suitable song accordingly.
The app was developed as part of my bachelor's thesis at the 
[University of Applied Sciences Düsseldorf](https://www.hs-duesseldorf.de/).

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
authentication and authorization system. Using this backend in any production environment without prior modification is 
highly discouraged.

---

While the backend is running, the documentation for the different API endpoints is available at `/docs`.
