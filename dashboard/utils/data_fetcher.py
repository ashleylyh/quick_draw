import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import redis
import os

class DataFetcher:
    """Handles data fetching from Redis and backend API for the dashboard"""
    
    def __init__(self, backend_url: str = "http://140.109.74.39:8088/"):
        self.backend_url = backend_url.rstrip('/')
        self.redis_client = None
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            # Use environment variables if available (for Docker), otherwise use localhost
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', '6379'))
            redis_db = int(os.getenv('REDIS_DB', '0'))
            
            self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
            # Test connection
            self.redis_client.ping()
        except Exception as e:
            print(f"Redis connection failed: {e}")
            self.redis_client = None
    
    def check_connection(self) -> bool:
        """Check if backend API is accessible"""
        try:
            response = requests.get(f"{self.backend_url}/api/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_all_sessions(self, filter_complete: bool = True, required_games: int = 6) -> List[Dict[str, Any]]:
        """Fetch all game sessions from Redis
        
        Args:
            filter_complete: If True, only return sessions with exactly required_games
            required_games: Number of games required for a complete session
        """
        if not self.redis_client:
            return []
        
        sessions = []
        try:
            # Get all session keys
            session_keys = self.redis_client.keys("session:*")
            
            for key in session_keys:
                if ":drawings" not in key and ":qr_code" not in key:
                    session_data = self.redis_client.hgetall(key)
                    if session_data:
                        # Parse JSON fields
                        if 'rounds' in session_data:
                            session_data['rounds'] = json.loads(session_data['rounds'])
                        if 'prompts' in session_data:
                            session_data['prompts'] = json.loads(session_data['prompts'])
                        
                        # Get session drawings and calculate score
                        session_id = session_data.get('session_id')
                        if session_id:
                            drawings = self.get_session_drawings(session_id)
                            session_data['drawings'] = drawings
                            session_data['total_score'] = self.calculate_session_score(drawings)
                            
                            # Apply filter if requested
                            if filter_complete:
                                games_played = len(drawings)
                                if games_played != required_games:
                                    continue  # Skip this session if it doesn't have the required number of games
                        
                        sessions.append(session_data)
            # print(f"[DEBUG] Fetched {len(sessions)} sessions from Redis")
        except Exception as e:
            print(f"Error fetching sessions: {e}")
        
        return sessions
    
    def get_session_drawings(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all drawings for a session"""
        if not self.redis_client:
            return []
        
        drawings = []
        try:
            # Get drawing IDs for this session
            drawing_ids = self.redis_client.lrange(f"session:{session_id}:drawings", 0, -1)
            
            for drawing_id in drawing_ids:
                drawing_data = self.redis_client.hgetall(drawing_id)
                if drawing_data:
                    # Parse JSON fields
                    if 'predictions' in drawing_data:
                        drawing_data['predictions'] = json.loads(drawing_data['predictions'])
                    if 'embedding' in drawing_data:
                        drawing_data['embedding'] = json.loads(drawing_data['embedding'])
                    
                    # Convert numeric fields
                    if 'round' in drawing_data:
                        drawing_data['round'] = int(drawing_data.get('round', 0))
                    if 'time_spent_sec' in drawing_data:
                        drawing_data['time_spent_sec'] = float(drawing_data.get('time_spent_sec', 0))
                    if 'timed_out' in drawing_data:
                        drawing_data['timed_out'] = int(drawing_data.get('timed_out', 0))
                    
                    drawings.append(drawing_data)
            
            # Sort by round number
            drawings.sort(key=lambda x: x.get('round', 0))
            # print(f"[DEBUG] Fetched {len(drawings)} drawings for session {session_id}")
        
        except Exception as e:
            print(f"Error fetching drawings for session {session_id}: {e}")
        
        return drawings
    
    def calculate_session_score(self, drawings: List[Dict[str, Any]]) -> float:
        """Calculate total score for a session"""
        total_score = 0.0
        
        for drawing in drawings:
            predictions = drawing.get('predictions', {})
            target_class = drawing.get('prompt', '')
            # print(f"Calculating score for drawing with target class '{target_class}' and predictions {predictions}")
            
            if target_class in predictions:
                score = predictions[target_class]*100
                # Score based on confidence and time
                # time_bonus = max(0, 1 - (drawing.get('time_spent_sec', 30) / 30))  # Assume 30s max
                # score = confidence * (1 + time_bonus * 0.5)  # 50% time bonus
                total_score += score
        # print(f"Calculated session score: {total_score}"    )
        
        return round(total_score, 2)
    
    def filter_sessions(self, sessions: List[Dict[str, Any]], time_range: str, 
                       difficulty_filter: List[str]) -> List[Dict[str, Any]]:
        """Filter sessions based on time range and difficulty"""
        filtered = []
        
        # Calculate time threshold
        now = datetime.now()
        if time_range == "Last 1 hour":
            threshold = now - timedelta(hours=1)
        elif time_range == "Last 24 hours":
            threshold = now - timedelta(hours=24)
        elif time_range == "Last 7 days":
            threshold = now - timedelta(days=7)
        elif time_range == "Last 30 days":
            threshold = now - timedelta(days=30)
        else:  # All time
            threshold = None
        
        for session in sessions:
            # Filter by difficulty
            if session.get('difficulty') not in difficulty_filter:
                continue
            
            # Filter by time
            if threshold:
                timestamp_str = session.get('timestamp', '')
                if timestamp_str:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        if timestamp.replace(tzinfo=None) < threshold:
                            continue
                    except:
                        continue
            
            filtered.append(session)
        
        return filtered
    
    def filter_complete_sessions(self, sessions: List[Dict[str, Any]], required_games: int = 6) -> List[Dict[str, Any]]:
        """Filter sessions to only include those with exactly the required number of games played"""
        complete_sessions = []
        
        for session in sessions:
            drawings = session.get('drawings', [])
            games_played = len(drawings)
            
            # Only include sessions with exactly the required number of games played
            if games_played == required_games:
                complete_sessions.append(session)
        
        return complete_sessions
    
    def get_ranking_data(self, sessions: List[Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get ranking data organized by difficulty, only including complete sessions (6 games)"""
        # If no sessions provided, get all complete sessions
        if sessions is None:
            sessions = self.get_all_sessions(filter_complete=True)
        else:
            # Filter provided sessions for complete ones
            sessions = self.filter_complete_sessions(sessions)
        
        rankings = {'easy': [], 'hard': []}
        
        for session in sessions:
            difficulty = session.get('difficulty', 'easy')
            if difficulty in rankings:
                player_data = {
                    'player_name': session.get('player_name', 'Unknown'),
                    'total_score': session.get('total_score', 0),
                    'games_played': len(session.get('drawings', [])),
                    'timestamp': session.get('timestamp', ''),
                    'session_id': session.get('session_id', ''),
                    'age': session.get('age', 0),
                    'gender': session.get('gender', 'Unknown')
                }
                rankings[difficulty].append(player_data)
        
        # Sort each difficulty by score (descending)
        for difficulty in rankings:
            rankings[difficulty].sort(key=lambda x: x['total_score'], reverse=True)
        
        return rankings
    
    def get_score_distribution(self, sessions: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get score distribution data for histogram, only including complete sessions (6 games)"""
        # If no sessions provided, get all complete sessions
        if sessions is None:
            sessions = self.get_all_sessions(filter_complete=True)
        else:
            # Filter provided sessions for complete ones
            sessions = self.filter_complete_sessions(sessions)
        
        scores_by_difficulty = {'easy': [], 'hard': []}
        
        for session in sessions:
            difficulty = session.get('difficulty', 'easy')
            score = session.get('total_score', 0)
            if difficulty in scores_by_difficulty:
                scores_by_difficulty[difficulty].append(score)
        
        return scores_by_difficulty