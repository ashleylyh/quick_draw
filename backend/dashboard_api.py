import os
import json
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(module_path)

from utils.redis_utils import get_redis
from dashboard.utils.data_fetcher import DataFetcher


router = APIRouter()

@router.get("/api/leaderboard") #TODO
async def get_leaderboard(difficulty: str = None):
    """Get leaderboard data"""
    try:
        r = get_redis()
        
        # Get all session keys
        session_keys = r.keys("session:*")
        
        # Collect all sessions with scores
        sessions = []
        for key in session_keys:
            session_data = r.hgetall(key)
            if session_data:
                # Decode byte strings
                session = {k.decode(): v.decode() for k, v in session_data.items()}
                
                # Filter by difficulty if specified
                if difficulty and session.get('difficulty') != difficulty:
                    continue
                
                # Calculate a simple score (this could be more sophisticated)
                # For now, just use timestamp as a placeholder
                session['score'] = session.get('timestamp', '0')

                sessions.append(session)
        
        # Sort by timestamp (most recent first) - replace with actual scoring logic
        sessions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Limit results
        # sessions = sessions[:limit]
        
        return {
            "leaderboard": sessions,
            "total_players": len(sessions),
            "difficulty_filter": difficulty
        }
        
    except Exception as e:
        print(f"Error getting leaderboard: {e}")
        raise HTTPException(status_code=500, detail=f"Leaderboard retrieval failed: {str(e)}")


@router.get("/api/dashboard/stats")
async def get_dashboard_stats(
    difficulty: Optional[str] = Query(None, description="Filter by difficulty level"),
    hours: Optional[int] = Query(None, description="Filter by last N hours"),
    # limit: Optional[int] = Query(100, description="Limit number of results")
):
    """
    Get overall dashboard statistics
    """
    try:
        r = get_redis()
        # Get all session keys
        session_keys = r.keys("session:*")
        sessions = []
        
        # Filter sessions based on criteria
        cutoff_time = None
        if hours:
            cutoff_time = datetime.now() - timedelta(hours=hours)
        
        for key in session_keys:
            if ":drawings" not in key and ":qr_code" not in key:
                session_data = r.hgetall(key)
                if session_data:
                    # Filter by difficulty
                    if difficulty and session_data.get('difficulty') != difficulty:
                        continue
                    
                    # Filter by time
                    if cutoff_time:
                        timestamp_str = session_data.get('timestamp', '')
                        if timestamp_str:
                            try:
                                session_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                if session_time.replace(tzinfo=None) < cutoff_time:
                                    continue
                            except:
                                continue
                    
                    sessions.append(session_data)
        
        # Calculate statistics
        total_players = len(sessions)
        difficulty_counts = {}
        total_games = 0
        
        for session in sessions:
            diff = session.get('difficulty', 'unknown')
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
            
            # Count games for this session
            session_id = session.get('session_id')
            if session_id:
                drawing_count = r.llen(f"session:{session_id}:drawings")
                total_games += drawing_count
        
        return {
            "total_players": total_players,
            "total_games": total_games,
            "difficulty_distribution": difficulty_counts,
            "period_description": f"Last {hours} hours" if hours else "All time"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Statistics retrieval failed: {str(e)}")

@router.get("/api/dashboard/rankings")
async def get_rankings(
    difficulty: str = Query(..., description="Difficulty level (easy/hard)"),
    # limit: Optional[int] = Query(50, description="Number of top players to return")
):
    """
    Get player rankings for a specific difficulty
    """
    try:
        r = get_redis()
        data_fetcher = DataFetcher()
        
        # Get all sessions for this difficulty
        sessions = data_fetcher.get_all_sessions()
        filtered_sessions = [s for s in sessions if s.get('difficulty') == difficulty]
        
        # Calculate rankings
        rankings = []
        for session in filtered_sessions:
            drawings = session.get('drawings', [])
            total_score = data_fetcher.calculate_session_score(drawings)
            
            rankings.append({
                'player_name': session.get('player_name', 'Unknown'),
                'total_score': total_score,
                'games_played': len(drawings),
                'timestamp': session.get('timestamp', ''),
                'session_id': session.get('session_id', ''),
                'age': session.get('age', 0),
                'gender': session.get('gender', 'Unknown')
            })
        
        # Sort by score and limit
        rankings.sort(key=lambda x: x['total_score'], reverse=True)
        # top_rankings = rankings[:limit] if limit else rankings
        
        return {
            "difficulty": difficulty,
            "total_players": len(rankings),
            "rankings": rankings
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rankings retrieval failed: {str(e)}")

@router.get("/api/dashboard/score-distribution")
async def get_score_distribution(
    difficulty: Optional[str] = Query(None, description="Filter by difficulty level"),
    bins: Optional[int] = Query(20, description="Number of histogram bins")
):
    """
    Get score distribution data for histogram visualization
    """
    try:

        data_fetcher = DataFetcher()
        sessions = data_fetcher.get_all_sessions()
        
        if difficulty:
            sessions = [s for s in sessions if s.get('difficulty') == difficulty]
        
        # Calculate scores
        scores_by_difficulty = {'easy': [], 'hard': []}
        
        for session in sessions:
            session_difficulty = session.get('difficulty', 'easy')
            score = session.get('total_score', 0)
            if session_difficulty in scores_by_difficulty:
                scores_by_difficulty[session_difficulty].append(score)
        
        # Create histogram data
        histogram_data = {}
        
        for diff, scores in scores_by_difficulty.items():
            if scores:
                import numpy as np

                hist, bin_edges = np.histogram(scores, bins=bins)
                histogram_data[diff] = {
                    'counts': hist.tolist(),
                    'bin_edges': bin_edges.tolist(),
                    'statistics': {
                        'mean': float(np.mean(scores)),
                        'median': float(np.median(scores)),
                        'std': float(np.std(scores)),
                        'min': float(np.min(scores)),
                        'max': float(np.max(scores)),
                        'total_players': len(scores)
                    }
                }
        
        return {
            "histogram_data": histogram_data,
            "filter_applied": difficulty if difficulty else "all_difficulties"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Score distribution retrieval failed: {str(e)}")

@router.get("/api/dashboard/recent-activity")
async def get_recent_activity(
    limit: Optional[int] = Query(20, description="Number of recent sessions to return")
):
    """
    Get recent game activity
    """
    try:

        data_fetcher = DataFetcher()
        sessions = data_fetcher.get_all_sessions()
        
        # Sort by timestamp (most recent first)
        sessions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        recent_sessions = sessions[:limit] if limit else sessions
        
        # Format for dashboard consumption
        activity_data = []
        for session in recent_sessions:
            activity_data.append({
                'player_name': session.get('player_name', 'Unknown'),
                'difficulty': session.get('difficulty', 'unknown'),
                'total_score': session.get('total_score', 0),
                'games_played': len(session.get('drawings', [])),
                'timestamp': session.get('timestamp', ''),
                'age': session.get('age', 0),
                'gender': session.get('gender', 'Unknown')
            })
        
        return {
            "recent_activity": activity_data,
            "total_sessions": len(sessions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recent activity retrieval failed: {str(e)}")
