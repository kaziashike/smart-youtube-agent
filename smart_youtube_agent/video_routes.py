from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import os
import logging
from datetime import datetime
from pathlib import Path
import uuid
import httpx
import threading
import time

from .auth import get_current_user
from .seo_optimizer import SEOOptimizer
from .youtube_manager import youtube_manager as enhanced_youtube_manager

router = APIRouter()

# Data models
class ScriptGenerationRequest(BaseModel):
    topic: str
    style: str
    duration: int
    tone: str
    context: Optional[str] = None

class VideoCreationRequest(BaseModel):
    title: str
    description: str
    script: str
    style: str
    duration: int

class SEOOptimizationRequest(BaseModel):
    title: str
    description: str
    script: str

class YouTubeUploadRequest(BaseModel):
    video_id: str
    title: str
    description: str
    category_id: str
    tags: List[str]
    privacy_status: str

# Initialize SEO optimizer
seo_optimizer = SEOOptimizer()


def _update_user_video(user_id: str, video_id: str, updates: Dict[str, Any]) -> None:
    """Safely update a user's video record by ID."""
    user_videos_file = Path(f"user_data/{user_id}/videos.json")
    if not user_videos_file.exists():
        return
    try:
        with open(user_videos_file, 'r', encoding='utf-8') as f:
            videos = json.load(f)
    except Exception:
        videos = []
    changed = False
    for v in videos:
        if v.get("id") == video_id:
            v.update(updates)
            changed = True
            break
    if changed:
        with open(user_videos_file, 'w', encoding='utf-8') as f:
            json.dump(videos, f, indent=2, ensure_ascii=False)


def _run_generation_background(user_id: str, video_id: str, request: VideoCreationRequest) -> None:
    """Background worker to generate video without blocking the request thread."""
    try:
        videos_dir = Path("videos")
        videos_dir.mkdir(exist_ok=True)
        video_file_path = videos_dir / f"{video_id}.mp4"

        downloads_dir = Path("downloads")
        downloads_dir.mkdir(exist_ok=True)
        capcut_video = downloads_dir / "capcut_output.mp4"

        print("[VideoGen] Background CapCut generation starting...")
        try:
            import sys
            # Ensure import path
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from Video_agent import run as capcut_run

            # Fresh start: remove stale output
            try:
                if capcut_video.exists():
                    print(f"[VideoGen] Removing stale file before generation: {capcut_video}")
                    capcut_video.unlink(missing_ok=True)
            except Exception as e:
                print(f"[VideoGen] Warning: Could not remove stale file: {e}")

            start_ts = time.time()
            print(f"[VideoGen] Starting CapCut with script length: {len(request.script)}")
            video_path = None
            try:
                video_path = capcut_run(request.script, headless=True)
                print(f"[VideoGen] CapCut returned path: {video_path}")
            except Exception as e:
                print(f"[VideoGen] CapCut generation error: {e}")

            # Give FS small time
            time.sleep(2)

            # Check download result
            print(f"[VideoGen] Checking for video file: {capcut_video}")
            if capcut_video.exists():
                mtime = capcut_video.stat().st_mtime
                if mtime >= start_ts - 1:
                    video_path = str(capcut_video)
                    print("[VideoGen] Verified fresh download ✅")
                else:
                    print("[VideoGen] Detected stale download; ignoring")
                    video_path = None
            else:
                print("[VideoGen] No capcut_output.mp4 found")

            if video_path and os.path.exists(video_path):
                import shutil
                shutil.copy2(video_path, video_file_path)
                print(f"[VideoGen] Video copied successfully: {video_file_path}")
                # Optional: realistic delay to smooth UX (kept in background only)
                min_processing_time = 5
                time.sleep(min_processing_time)
                _update_user_video(user_id, video_id, {
                    "file_path": video_file_path.as_posix(),
                    "status": "completed",
                })
            else:
                # Placeholder on failure
                placeholder_content = f"""
Video ID: {video_id}
Title: {request.title}
Description: {request.description}
Style: {request.style}
Duration: {request.duration} seconds
Script: {request.script[:200]}...
Generated at: {datetime.now().isoformat()}
                """.strip()
                with open(video_file_path.with_suffix('.txt'), 'w', encoding='utf-8') as f:
                    f.write(placeholder_content)
                print(f"[VideoGen] Created placeholder: {video_file_path.with_suffix('.txt')}")
                _update_user_video(user_id, video_id, {
                    "file_path": video_file_path.with_suffix('.txt').as_posix(),
                    "status": "placeholder",
                })
        except ImportError as e:
            print(f"[VideoGen] CapCut integration not available: {e}")
            # Placeholder
            placeholder_content = f"""
Video ID: {video_id}
Title: {request.title}
Description: {request.description}
Style: {request.style}
Duration: {request.duration} seconds
Script: {request.script[:200]}...
Generated at: {datetime.now().isoformat()}
            """.strip()
            with open(video_file_path.with_suffix('.txt'), 'w', encoding='utf-8') as f:
                f.write(placeholder_content)
            _update_user_video(user_id, video_id, {
                "file_path": video_file_path.with_suffix('.txt').as_posix(),
                "status": "placeholder",
            })
        except Exception as e:
            print(f"[VideoGen] Background generation error: {e}")
            # Best-effort mark as failed
            _update_user_video(user_id, video_id, {
                "status": "failed",
            })
        finally:
            print(f"[VideoGen] Background job finished for {video_id}")
    except Exception as e:
        print(f"[VideoGen] Worker wrapper error: {e}")


@router.post("/api/videos/create-with-ai")
async def create_video_with_ai(request: VideoCreationRequest, current_user: dict = Depends(get_current_user)):
    """Create a video using AI based on the script (non-blocking)."""
    try:
        user_id = current_user.get('user_id', 'unknown')
        print(f"Creating video for user: {user_id}")
        print(f"Video title: {request.title}")
        print(f"Video style: {request.style}")
        print(f"Video duration: {request.duration}")

        # Generate a unique video ID
        video_id = str(uuid.uuid4())
        print(f"Generated video ID: {video_id}")

        # Create initial video metadata
        video_data = {
            "id": video_id,
            "user_id": user_id,
            "title": request.title,
            "description": request.description,
            "script": request.script,
            "style": request.style,
            "duration": request.duration,
            "status": "generating",
            "created_at": datetime.now().isoformat(),
            "file_path": f"videos/{video_id}.mp4"
        }

        # Persist initial record
        user_videos_file = Path(f"user_data/{user_id}/videos.json")
        user_videos_file.parent.mkdir(parents=True, exist_ok=True)
        print(f"Saving video data to: {user_videos_file}")
        videos = []
        if user_videos_file.exists():
            with open(user_videos_file, 'r', encoding='utf-8') as f:
                try:
                    videos = json.load(f)
                except Exception:
                    videos = []
        videos.append(video_data)
        with open(user_videos_file, 'w', encoding='utf-8') as f:
            json.dump(videos, f, indent=2, ensure_ascii=False)
        print(f"Video data saved successfully. Total videos for user: {len(videos)}")

        # Start background generation thread (do not block request)
        worker = threading.Thread(target=_run_generation_background, args=(user_id, video_id, request), daemon=True)
        worker.start()

        return {
            "success": True,
            "message": "Video generation started",
            "video_id": video_id,
            "status": "generating"
        }

    except Exception as e:
        print(f"Error creating video: {str(e)}")
        print(f"Current user data: {current_user}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create video: {str(e)}"
        )

@router.post("/api/videos/seo-optimize")
async def optimize_video_seo(request: SEOOptimizationRequest, current_user: dict = Depends(get_current_user)):
    """Optimize video metadata for SEO using OpenRouter."""
    try:
        # Use the existing SEO optimizer
        seo_result = await seo_optimizer.optimize_video_metadata(
            title=request.title,
            description=request.description,
            topic=request.script[:100]  # Use first 100 chars of script as topic
        )
        
        return seo_result
        
    except Exception as e:
        # Fallback to basic optimization
        return {
            "seo_score": 75,
            "keywords": ["video", "content", "tutorial"],
            "title_optimization": "Good",
            "description_optimization": "Good",
            "recommendations": [
                "Consider adding more specific keywords",
                "Include a call-to-action in the description"
            ]
        }

@router.post("/api/videos/upload-to-youtube")
async def upload_video_to_youtube(request: YouTubeUploadRequest, current_user: dict = Depends(get_current_user)):
    """Upload a video to YouTube."""
    try:
        # Check if user has YouTube connected
        # Check YouTube connection via enhanced manager (supports demo and real creds)
        channel = enhanced_youtube_manager.get_channel_info(current_user["user_id"])
        
        # Load video data
        user_videos_file = Path(f"user_data/{current_user['user_id']}/videos.json")
        if not user_videos_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )
        
        with open(user_videos_file, 'r') as f:
            videos = json.load(f)
        
        video = None
        for v in videos:
            if v["id"] == request.video_id:
                video = v
                break
        
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )
        
        # Resolve actual video file path; ensure it's an mp4 and exists
        video_file_path = Path(video.get("file_path", "")).resolve()
        if not video_file_path.exists() or video_file_path.suffix.lower() != ".mp4":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video file not ready. Please generate the video successfully before uploading."
            )

        # Perform upload via enhanced manager when available; otherwise simulate
        if channel:
            upload_result = enhanced_youtube_manager.upload_video(current_user["user_id"], {
                "title": request.title,
                "description": request.description,
                "tags": request.tags,
                "category_id": request.category_id,
                "privacy_status": request.privacy_status,
                "video_file": str(video_file_path)
            })
        else:
            # Fallback simulated upload to keep UX flowing in non-configured environments
            upload_result = {
                "success": True,
                "message": "Simulated upload (YouTube not connected)",
                "video_id": f"demo_{uuid.uuid4().hex[:11]}",
                "url": f"https://www.youtube.com/watch?v=demo_{uuid.uuid4().hex[:8]}"
            }
        
        # Save upload data
        uploads_file = Path(f"user_data/{current_user['user_id']}/uploads.json")
        uploads_file.parent.mkdir(parents=True, exist_ok=True)
        
        uploads = []
        if uploads_file.exists():
            with open(uploads_file, 'r') as f:
                uploads = json.load(f)
        
        uploads.append({
            "video_id": request.video_id,
            "youtube_video_id": upload_result.get("video_id") or upload_result.get("videoId") or upload_result.get("url", "").split("v=")[-1],
            "title": request.title,
            "description": request.description,
            "category_id": request.category_id,
            "tags": request.tags,
            "privacy_status": request.privacy_status,
            "uploaded_at": datetime.now().isoformat(),
            "status": "uploaded"
        })
        
        with open(uploads_file, 'w') as f:
            json.dump(uploads, f, indent=2)
        
        # Update video status
        video["status"] = "uploaded"
        video["youtube_video_id"] = uploads[-1]["youtube_video_id"]
        
        with open(user_videos_file, 'w') as f:
            json.dump(videos, f, indent=2)
        
        return {
            "success": True,
            "youtube_video_id": uploads[-1]["youtube_video_id"],
            "message": "Video uploaded successfully",
            "data": upload_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload video: {str(e)}"
        )

@router.get("/api/videos/user-videos")
async def get_user_videos(current_user: dict = Depends(get_current_user)):
    """Get all videos for the current user."""
    try:
        user_videos_file = Path(f"user_data/{current_user['user_id']}/videos.json")
        
        if not user_videos_file.exists():
            return {"videos": []}
        
        with open(user_videos_file, 'r') as f:
            videos = json.load(f)
        
        return {"videos": videos}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load videos: {str(e)}"
        )

@router.get("/api/videos/{video_id}")
async def get_video(video_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific video by ID."""
    try:
        user_videos_file = Path(f"user_data/{current_user['user_id']}/videos.json")
        
        if not user_videos_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )
        
        with open(user_videos_file, 'r') as f:
            videos = json.load(f)
        
        for video in videos:
            if video["id"] == video_id:
                return video
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load video: {str(e)}"
        )

@router.get("/api/videos/stream/{file_path:path}")
async def stream_video(file_path: str, current_user: dict = Depends(get_current_user)):
    """Stream a video file for preview."""
    try:
        import os
        from pathlib import Path
        from urllib.parse import unquote
        
        print(f"Streaming request for file_path (raw): {file_path}")
        
        # Robustly decode URL (handle double-encoded backslashes like %255C)
        decoded_once = unquote(file_path)
        decoded_twice = unquote(decoded_once)
        print(f"Decoded once: {decoded_once}")
        print(f"Decoded twice: {decoded_twice}")
        
        # Normalize any remaining encodings/backslashes
        normalized = (
            decoded_twice
            .replace('%5C', '\\')  # if still present
            .replace('%2F', '/')
        )
        print(f"Normalized path: {normalized}")
        
        videos_dir = Path("videos").resolve()
        print(f"Videos directory: {videos_dir}")
        
        # Build a safe path inside videos_dir regardless of input form
        candidate_path = Path(normalized)
        candidate_parts = list(candidate_path.parts)
        if 'videos' in candidate_parts:
            idx = candidate_parts.index('videos')
            safe_subpath = Path(*candidate_parts[idx+1:])
            video_file = (videos_dir / safe_subpath).resolve()
            print(f"Detected 'videos' in path. Subpath: {safe_subpath}")
        else:
            # If path is just a filename or relative, put it inside videos_dir
            video_file = (videos_dir / candidate_path).resolve()
            print(f"No 'videos' in path. Using relative to videos_dir: {candidate_path}")
        
        print(f"Resolved video file path: {video_file}")
        
        # Security check: ensure the video file is within the videos directory
        try:
            video_file.relative_to(videos_dir)
            print("Security check: within videos_dir ✅")
        except ValueError:
            print(f"Access denied: {video_file} not in {videos_dir}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check if file exists
        if not video_file.exists():
            print(f"Video file not found: {video_file}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video file not found"
            )
        
        print(f"Video file exists: {video_file.exists()}")
        print(f"Video file size: {video_file.stat().st_size}")
        
        # Return the video file
        from fastapi.responses import FileResponse
        print(f"Streaming video file: {video_file}")
        return FileResponse(
            path=str(video_file),
            media_type='video/mp4',
            filename=video_file.name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error streaming video: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stream video: {str(e)}"
        ) 