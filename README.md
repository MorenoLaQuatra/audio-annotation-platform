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
python init_database.py --data_path <path to data directory> \
--users_table_name <name of users table> \
--dataset_table_name <name of dataset table> \
--verification_table_name <name of verification table> \
--database_name <name of database>

# Add a user (only needs to be done each time a new user is added)
python add_user.py --username <username> --password <password>

# Parse json data (superb) and add it to the database
python init_dataset.py --data_path <path_to_json_data> --database_name <name_of_database> --verification_table_name <name_of_verification_table> --users_table_name <name_of_users_table> --dataset_table_name <name_of_dataset_table>

# Run the server
python app.py --port <port> --run_over_https --debug --database_name <name_of_database> --verification_table_name <name_of_verification_table> --users_table_name <name_of_users_table> --dataset_table_name <name_of_dataset_table>
```

## Audio verification

The project also implements a random verification page. Users can access a verification page where are asked to listen to a random audio file and verify if it is correct or not. The verification page is accessible at `https://<server_address>/verification`.

There is no specific role for the verification page. Any user can access it. The verification page **can** be implemented to specific users in the future but it is not implemented yet!

**How verification works**
- Each annotation is initialized with a `verification_score` of 0.
- When a user verifies an annotation, the `verification_score` she/he can choose between `correct` and `incorrect`.
    - If the user chooses `correct`, the `verification_score` is increased by 1 ( +=1 ).
    - If the user chooses `incorrect`, the `verification_score` is decreased by 1 ( -= 1).
- The `verification_score` is used to determine if an annotation is correct or not at the end of the annotation process.
    - If the `verification_score` is greater than 0, the annotation is considered **correct**.
    - If the `verification_score` is less than 0, the annotation is considered **incorrect**.
    - If the `verification_score` is equal to 0, the annotation is considered **unverified**.

NB. There is no tracking of the user who verified an annotation. This is a feature that **can** be implemented in the future.

### Parameters

#### init_database.py
- `--data_path`: path to the json data
- `--database_name`: name of the database (default: `database`)
- `--verification_table_name`: name of the table containing the verification logs (default: `verifications`)
- `--users_table_name`: name of the table containing the users (default: `users`)
- `--dataset_table_name`: name of the table containing the dataset and annotations (default: `superb`)

#### add_user.py
- `--username`: username of the user
- `--password`: password of the user
- WIP: we are currently working on updating the fields of the user table to include more information about the user

#### app.py
- `--port`: port on which the server runs
- `--run_over_https`: if set, the server runs over https
- `--debug`: if set, the server runs in debug mode
- `--audio_folder`: path to the folder that will contain the audio files after annotation
- `--database_name`: name of the database (default: `database`)
- `--verification_table_name`: name of the table containing the verification logs (default: `verifications`)
- `--users_table_name`: name of the table containing the users (default: `users`)
- `--dataset_table_name`: name of the table containing the dataset and annotations (default: `superb`)

## Annotations

Each time a user annotates an audio file using her/his voice:
- The entry in the database is updated with the information about the id of the user
- The audio file is converted from webm to wav and both formats are stored in the folder specified by the `--audio_folder` parameter

The final table in the database will look like this:
| id | partition | utt | path | speaker | verification_score | timestamp |
|----|-----------|-----|------|---------| -------------------| ----------|
| 1  | train     | Text of the utterance   | 1.wav | 1       | 0 | 2022-09-01 12:00:00 |
| 2  | train     | Text of the utterance   | 2.wav | 2       | 0 | 2022-09-01 12:00:00 |

## Verification

Herafter a description of the fields:
- `id`: id of the entry for the verification table
- `utt_id`: id of the utterance in the dataset table
- `verifier_id`: id of the user who verified the utterance (from the users table)
- `score`: score of the verification (1, -1)
- `verification_timestamp`: timestamp of the verification


The information about the user is stored in the `verifications` table. The final table in the database will look like this:

| id | utt_id | verifier_id | score | verification_timestamp |
|----|--------|-------------|-------|------------------------|
| 1  | 1      | 1           | 1     | 2022-09-01 12:00:00    |
| 2  | 2      | 2           | -1    | 2022-09-01 12:00:00    |

## Users

Herafter a description of the fields:
- `id`: id of the entry for the users table
- `username`: username of the user
- `password`: password of the user

The information about the user is stored in the `users` table:

| id | username | password |
|----|----------|----------|
| 1  | user1    | BCrypted |
| 2  | user2    | BCrypted |

NB: The username and password (crypted) are currently the only information stored in the table.

## Why this platform?

This platform has been originally created for the ITALIC data collection phase. Bibtex of the published paper for the Italian Intent Classification dataset below:

```bibtex
@inproceedings{koudounas23_interspeech,
  title     = {ITALIC: An Italian Intent Classification Dataset},
  author    = {Alkis Koudounas and Moreno {La Quatra} and Lorenzo Vaiani and Luca Colomba and Giuseppe Attanasio and Eliana Pastor and Luca Cagliero and Elena Baralis},
  year      = {2023},
  booktitle = {INTERSPEECH 2023},
  pages     = {2153--2157},
  doi       = {10.21437/Interspeech.2023-1980},
  issn      = {2958-1796},
}
```
