# Audio annotation platform

This is a platform for recording and annotating audio files. It is built on top of [Flask](https://flask.palletsprojects.com/en/2.2.x/).
The platform is currently in development and is not yet ready for production use.

## Installation
```bash
git clone https://github.com/MorenoLaQuatra/audio-annotation-platform
cd audio-annotation-platform
pip install -r requirements.txt
# install ffmpeg for converting webm to wav
sudo apt install ffmpeg
```

## Usage
```bash
# Initialize the database (only needs to be done once)
python init_db.py

# Add a user (only needs to be done each time a new user is added)
python add_user.py --username <username> --password <password>

# Parse json data (superb) and add it to the database
python dataset_parsing.py --data_path <path_to_json_data>

# Run the server
python run.py --port <port>
```