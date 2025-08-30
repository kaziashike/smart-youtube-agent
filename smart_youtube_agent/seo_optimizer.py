#!/usr/bin/env python3
"""
SEO Optimizer - Uses OpenRouter to optimize video metadata for YouTube
"""

import os
import json
import logging
import httpx
from typing import Dict, Any, List, Optional
from fastapi import HTTPException

# Configure logging
logger = logging.getLogger(__name__)

class SEOOptimizer:
    def __init__(self):
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_base_url = "https://openrouter.ai/api/v1"
        
    async def optimize_video_metadata(self, title: str, description: str, topic: str) -> Dict[str, Any]:
        """Optimize video metadata for YouTube SEO."""
        try:
            if not self.openrouter_api_key:
                logger.warning("OpenRouter API key not configured, using basic optimization")
                return self._basic_optimization(title, description, topic)
            
            # Create optimization prompt
            prompt = self._create_optimization_prompt(title, description, topic)
            
            # Call OpenRouter API
            response = await self._call_openrouter(prompt)
            
            if response:
                return self._parse_optimization_response(response)
            else:
                return self._basic_optimization(title, description, topic)
                
        except Exception as e:
            logger.error(f"Error optimizing video metadata: {e}")
            return self._basic_optimization(title, description, topic)
    
    def _create_optimization_prompt(self, title: str, description: str, topic: str) -> str:
        """Create a prompt for SEO optimization."""
        return f"""
You are a YouTube SEO expert with 10+ years of experience optimizing videos for maximum visibility, engagement, and search ranking. Your goal is to create highly optimized metadata that will rank well in YouTube search and drive high click-through rates.

VIDEO INFORMATION:
Original Title: {title}
Original Description: {description}
Topic: {topic}

OPTIMIZATION REQUIREMENTS:

1. TITLE OPTIMIZATION (Max 60 characters):
- Include primary keyword in first 30 characters
- Use power words: "Best", "Ultimate", "Complete", "How to", "Top", "Amazing", "Incredible"
- Add trending keywords and current year if relevant
- Make it clickable and curiosity-driven
- Include numbers when relevant (e.g., "5 Tips", "10 Ways")

2. DESCRIPTION OPTIMIZATION (Max 5000 characters):
- Start with a compelling hook (first 2-3 lines)
- Include primary keyword in first 100 characters
- Add timestamps if applicable
- Include relevant links and resources
- Add strong call-to-actions (Subscribe, Like, Share)
- Use emojis strategically for visual appeal
- Include relevant hashtags
- Add social proof or credentials
- End with engagement prompts

3. KEYWORDS/TAGS (15-20 highly relevant tags):
- Primary keyword variations
- Long-tail keywords
- Trending related terms
- Competitor keywords
- Seasonal/current event keywords
- Brand keywords if applicable

4. SEO SCORING (0-100):
- Title optimization (25 points)
- Description optimization (30 points)
- Keyword relevance (25 points)
- Click-through rate potential (20 points)

RESPONSE FORMAT (JSON only):
{{
    "optimized_title": "Exact optimized title (max 60 chars)",
    "optimized_description": "Complete optimized description with proper formatting, timestamps, and CTAs",
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8", "keyword9", "keyword10", "keyword11", "keyword12", "keyword13", "keyword14", "keyword15"],
    "seo_score": 85,
    "title_optimization": "Excellent/Good/Fair",
    "description_optimization": "Excellent/Good/Fair",
    "keyword_optimization": "Excellent/Good/Fair",
    "optimization_notes": "Detailed explanation of optimizations made and why they will improve performance"
}}

CRITICAL REQUIREMENTS:
- Focus on high-search-volume keywords
- Include trending terms and current events
- Use proven YouTube SEO patterns
- Optimize for both search and suggested videos
- Ensure mobile-friendly formatting
- Include engagement triggers
- Make it shareable and viral-worthy
"""
    
    async def _call_openrouter(self, prompt: str) -> Optional[str]:
        """Call OpenRouter API for optimization."""
        try:
            headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://smart-youtube-agent.com",
                "X-Title": "Smart YouTube Agent"
            }
            
            data = {
                "model": "moonshotai/kimi-k2:free",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.openrouter_base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {e}")
            return None
    
    def _parse_optimization_response(self, response: str) -> Dict[str, Any]:
        """Parse the OpenRouter response."""
        try:
            # Try to extract JSON from the response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                
                parsed = json.loads(json_str)
                
                return {
                    "optimized_title": parsed.get("optimized_title", ""),
                    "optimized_description": parsed.get("optimized_description", ""),
                    "keywords": parsed.get("keywords", []),
                    "seo_score": parsed.get("seo_score", 70),
                    "title_optimization": parsed.get("title_optimization", "Good"),
                    "description_optimization": parsed.get("description_optimization", "Good"),
                    "keyword_optimization": parsed.get("keyword_optimization", "Good"),
                    "optimization_notes": parsed.get("optimization_notes", "")
                }
            else:
                # Fallback to basic optimization
                return self._basic_optimization("", "", "")
                
        except Exception as e:
            logger.error(f"Error parsing optimization response: {e}")
            return self._basic_optimization("", "", "")
    
    def _basic_optimization(self, title: str, description: str, topic: str) -> Dict[str, Any]:
        """Enhanced basic optimization when OpenRouter is not available."""
        # Generate comprehensive keywords based on topic
        keywords = self._generate_enhanced_keywords(topic)
        
        # Optimize title with power words
        optimized_title = self._optimize_title_basic(title, topic)
        
        # Create comprehensive description
        optimized_description = self._create_enhanced_description(description, topic, keywords)
        
        return {
            "optimized_title": optimized_title,
            "optimized_description": optimized_description,
            "keywords": keywords,
            "seo_score": 80,
            "title_optimization": "Good",
            "description_optimization": "Good", 
            "keyword_optimization": "Good",
            "optimization_notes": "Enhanced basic optimization applied with power words and comprehensive keywords"
        }
    
    def _generate_enhanced_keywords(self, topic: str) -> List[str]:
        """Generate comprehensive keywords based on topic."""
        topic_lower = topic.lower()
        
        # Power keywords for YouTube
        power_keywords = ["best", "ultimate", "complete", "amazing", "incredible", "viral", "trending", "top", "how to", "tips", "tricks", "secrets", "guide", "tutorial"]
        
        # Common YouTube keywords
        base_keywords = ["youtube", "video", "content", "creator", "trending", "viral", "shorts", "2024", "latest"]
        
        # Topic-specific comprehensive keywords
        topic_keywords = []
        if "tech" in topic_lower or "technology" in topic_lower or "ai" in topic_lower:
            topic_keywords = ["tech", "technology", "innovation", "digital", "future", "ai", "artificial intelligence", "machine learning", "automation", "digital transformation", "tech trends", "innovation", "startup", "digital marketing"]
        elif "business" in topic_lower or "entrepreneur" in topic_lower:
            topic_keywords = ["business", "entrepreneur", "success", "money", "startup", "marketing", "strategy", "growth", "leadership", "management", "business tips", "entrepreneurship", "side hustle", "passive income"]
        elif "education" in topic_lower or "learn" in topic_lower or "tutorial" in topic_lower:
            topic_keywords = ["education", "learning", "tutorial", "how to", "tips", "skills", "knowledge", "training", "course", "online learning", "self improvement", "personal development", "study tips", "academic"]
        elif "entertainment" in topic_lower or "fun" in topic_lower:
            topic_keywords = ["entertainment", "fun", "viral", "trending", "amazing", "comedy", "lifestyle", "vlog", "daily life", "funny", "entertaining", "reaction", "challenge"]
        elif "fitness" in topic_lower or "health" in topic_lower or "workout" in topic_lower:
            topic_keywords = ["fitness", "health", "workout", "exercise", "wellness", "nutrition", "diet", "gym", "training", "weight loss", "muscle building", "healthy lifestyle", "fitness tips", "motivation"]
        elif "cooking" in topic_lower or "food" in topic_lower or "recipe" in topic_lower:
            topic_keywords = ["cooking", "food", "recipe", "delicious", "kitchen", "chef", "cooking tips", "easy recipes", "quick meals", "healthy food", "cooking tutorial", "kitchen hacks", "meal prep"]
        elif "gaming" in topic_lower or "game" in topic_lower:
            topic_keywords = ["gaming", "game", "streamer", "esports", "gaming tips", "gameplay", "walkthrough", "review", "gaming setup", "pc gaming", "console gaming", "mobile gaming"]
        elif "travel" in topic_lower or "trip" in topic_lower:
            topic_keywords = ["travel", "trip", "vacation", "adventure", "exploring", "travel tips", "budget travel", "travel vlog", "destination", "travel guide", "backpacking", "solo travel"]
        else:
            # Generic comprehensive keywords
            topic_keywords = ["trending", "viral", "amazing", "best", "top", "popular", "must watch", "recommended", "favorite", "essential", "ultimate guide", "complete tutorial"]
        
        # Extract and enhance words from topic
        topic_words = [word for word in topic.split() if len(word) > 2]
        enhanced_topic_words = []
        for word in topic_words:
            enhanced_topic_words.extend([word, f"{word} tips", f"{word} tutorial", f"best {word}", f"how to {word}"])
        
        # Combine all keywords and ensure uniqueness
        all_keywords = power_keywords + base_keywords + topic_keywords + enhanced_topic_words
        unique_keywords = list(dict.fromkeys(all_keywords))  # Remove duplicates while preserving order
        
        return unique_keywords[:20]  # Return top 20 keywords
    
    def _optimize_title_basic(self, title: str, topic: str) -> str:
        """Optimize title with power words and trending elements."""
        power_words = ["Ultimate", "Complete", "Best", "Top", "Amazing", "Incredible", "Essential", "Must-Watch", "Comprehensive", "Definitive"]
        
        # If title is too short, enhance it
        if len(title) < 30:
            # Add power word and year
            for power_word in power_words:
                enhanced_title = f"{power_word} {title} 2024"
                if len(enhanced_title) <= 60:
                    return enhanced_title
        
        # If title is already good length, just add year if not present
        if "2024" not in title and len(title) < 55:
            return f"{title} 2024"
        
        return title[:60]  # Ensure it doesn't exceed 60 characters
    
    def _create_enhanced_description(self, description: str, topic: str, keywords: List[str]) -> str:
        """Create comprehensive description with engagement elements."""
        enhanced_description = f"{description}\n\n"
        
        # Add timestamps if applicable
        enhanced_description += "⏰ Timestamps:\n"
        enhanced_description += "00:00 - Introduction\n"
        enhanced_description += "02:30 - Main Content\n"
        enhanced_description += "08:45 - Key Takeaways\n"
        enhanced_description += "12:00 - Conclusion\n\n"
        
        # Add relevant keywords
        enhanced_description += f"🔍 Related topics: {', '.join(keywords[:8])}\n\n"
        
        # Add engagement elements
        enhanced_description += "📺 Subscribe for more amazing content!\n"
        enhanced_description += "👍 Like this video if you found it helpful!\n"
        enhanced_description += "💬 Comment below with your thoughts!\n"
        enhanced_description += "🔄 Share with friends who might benefit!\n\n"
        
        # Add hashtags
        enhanced_description += f"#{topic.replace(' ', '')} #YouTube #ContentCreator #Video #Trending #Viral"
        
        return enhanced_description
    
    def calculate_seo_score(self, title: str, description: str, keywords: List[str]) -> int:
        """Calculate an SEO score for the video metadata."""
        score = 0
        
        # Title optimization (30 points)
        if len(title) >= 30 and len(title) <= 60:
            score += 20
        if any(word in title.lower() for word in ["how to", "best", "top", "amazing", "viral"]):
            score += 10
        
        # Description optimization (40 points)
        if len(description) >= 200:
            score += 20
        if "subscribe" in description.lower():
            score += 10
        if "like" in description.lower() and "share" in description.lower():
            score += 10
        
        # Keywords optimization (30 points)
        if len(keywords) >= 10:
            score += 15
        if len(keywords) <= 15:
            score += 15
        
        return min(score, 100)

# Global instance
seo_optimizer = SEOOptimizer() 