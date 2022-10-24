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
python dataset_parsing.py --data_path <path_to_json_data> --table_name <name_of_table>

# Run the server
python app.py --port <port> --run_over_https --debug --table_name <name_of_table>
```

### Parameters

#### init_db.py
- No parameters

#### add_user.py
- `--username`: username of the user
- `--password`: password of the user
- WIP: we are currently working on updating the fields of the user table to include more information about the user

#### dataset_parsing.py
- `--data_path`: path to the json data
- `--table_name`: name of the table in the database

#### app.py
- `--port`: port on which the server runs
- `--run_over_https`: if set, the server runs over https
- `--debug`: if set, the server runs in debug mode
- `--audio_folder`: path to the folder that will contain the audio files after annotation
- `--table_name`: name of the table in the database

## Annotations

Each time a user annotates an audio file using her/his voice:
- The entry in the database is updated with the information about the id of the user
- The audio file is converted from webm to wav and both formats are stored in the folder specified by the `--audio_folder` parameter

The final table in the database will look like this:
| id | partition | utt | path | speaker |
|----|-----------|-----|------|---------|
| 1  | train     | Text of the utterance   | 1.wav | 1       |
| 2  | train     | Text of the utterance   | 2.wav | 2       |

Herafter a description of the fields:
- `id`: id of the entry in the original json file
- `partition`: partition of the entry in the original json file (train, dev, test)
- `utt`: utterance of the entry (e.g., "Accendi la luce")
- `path`: path to the audio file
- `speaker`: id of the user who annotated the audio file

The information about the user is stored in the `users` table:

| id | username | password |
|----|----------|----------|
| 1  | user1    | BCrypted |
| 2  | user2    | BCrypted |

The username and password are currently the only information stored in the table.