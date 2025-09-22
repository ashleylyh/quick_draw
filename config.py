IMAGE_SIZE = 784  # 28*28
PER_ROUND = 4
NUM_ROUNDS = 6
# add 28*28

MODEL_PATH = "./model/doodleNet-model.keras"
CLASSES_PATH = "./classes.json"

API_CLIENT = "localhost:8000"
FRONTEND_CLIENT = "localhost:3000"
DASHBOARD_CLIENT = "localhost:8501"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

FILE_EMB_5 = "./feature/background_embedding_5per_class.csv"
FILE_UMAP = "./feature/background_Umap.csv"
FILE_UMAP_REDUCER = "./feature/background_Umap_top72.joblib"

MAX_BG_SAMPLES_PER_CLASS = 500

NOTOSANSTC_PATH = "../frontend/fonts/NotoSansTC.ttf"