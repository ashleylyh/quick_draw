

todo:

[ok] question randomness
[ok] frontend

[ok] database
[ok] translation (zh)

[ok] clustering plot automate (almost) (faster)
[ok] how do the prob for easy and normal calculate
[] pdf download -> layout, chinese word
[ok] transcript design
[] qrcode generate
[ok] real time prob? (check prob correctness)
[] frontend wording
[ok] 雷達圖


umap workflow:
in score.js page, call the umap api -> 
umap api fetch embedding and prompt using drawing api
call the asynv function to process umap 
return by function and upload to db and return from umap api to go back to score page
visualize on page

[ok] upload background embedding to db -> see if i can only use the umap bg + joblib file

redis -> fucntion
---
### Frontend Command
```
python -m http.server 3000
```
### Backend Command
```
python app.py
```
### Start Redis DB
```
redis-server
```
### Flush Redis
open a new terminal session
```
redis-cli flushall
```
Ctrl+F5 -> hard refresh webpage
Ctrl+C  -> kill the process

---
## API Endpoint
```@router.post("/api/sessions")```\
Creates a new game session for a player.

How it works:
- Receives player info (player_name, gender, age, difficulty) as JSON.
- Generates a unique session_id.
- Builds game rounds and prompts based on difficulty.
- Stores session data in Redis.
- Returns session_id, rounds, and prompts to the frontend.


```@router.post("/api/predict-realtime")```\
Provides real-time predictions for a drawing (used for live preview).

How it works:

- Receives base64-encoded image data and a list of choices.
- Decodes and preprocesses the image.
- Runs the image through the ML model.
- Returns prediction probabilities for the specified choices (or all classes if choices are empty).

```@router.post("/api/predict")```\
Submits a finished drawing for a round and gets predictions.

How it works:

- Receives session info, round number, prompt, time spent, timeout flag, and the drawing image (as file upload).
- Reads and preprocesses the image.
- Runs the image through the ML model for predictions and embedding.
- Stores all data (including image as base64) in Redis.
- Returns predictions and embedding to the frontend.

```@router.get("/api/health")```\
Checks the health/status of the backend and models.

How it works:

- Returns a JSON object with status, model loaded flags, and number of classes.


## Database


1. Session Data

    Key: ```session:{session_id}```

    Stored Data (Hash):
    - player_name
    - gender
    - age
    - difficulty
    - rounds (JSON string: list of choices for each round) [6][?]
    - prompts (JSON string: list of prompts for each round) [6] each round pick 1 from ?
    - timestamp


2. Drawing Data (per round)

    Key: ```drawing:{session_id}:{round}```

    Stored Data (Hash):
    - session_id
    - round
    - prompt
    - time_spent_sec
    - timed_out
    - image_base64 (base64-encoded image data)
    - predictions (JSON string: probability map for choices)
    - round_choices (JSON string: choices for this round)
    - embedding (JSON string: model embedding vector)
    - timestamp

3. Drawings List (per session)

    Key: ```session:{session_id}:drawings```

    Stored Data (List):
    - List of drawing IDs (drawing:{session_id}:{round}) for all rounds in this session
    