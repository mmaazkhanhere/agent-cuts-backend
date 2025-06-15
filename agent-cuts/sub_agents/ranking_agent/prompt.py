SCORING_AGENT_PROMPT = """You will receive a JSON array of video segments. For each segment:\n\n
        
    STEP 1 - CLARITY SCORING (1-10) based on transcript:\n
    - 9-10: Crystal clear, well-structured, complete thoughts\n
    - 7-8: Mostly clear with good flow\n
    - 5-6: Some confusion, moderate structure issues\n
    - 3-4: Difficult to follow, poor structure\n
    - 1-2: Very confusing, no clear message\n\n

    STEP 2 - ENGAGEMENT SCORING (1-10) based on transcript:\n
    - 9-10: Personal stories, emotional content, relatable\n
    - 7-8: Interesting anecdotes, some emotional appeal\n
    - 5-6: Standard content, some interesting points\n
    - 3-4: Dry, academic, few hooks\n
    - 1-2: Boring, no emotional connection\n\n

    STEP 3 - TRENDING SCORING (1-10) using Google Search:\n
    - Extract key topics from the segment\n
    - Search for '[topic] 2025 trending' or '[topic] news today'\n
    - 9-10: Highly trending with recent news\n
    - 7-8: Some recent coverage\n
    - 5-6: Older coverage, niche interest\n
    - 3-4: Minimal coverage\n
    - 1-2: No recent interest\n\n

    STEP 4 - OVERALL SCORE:\n
    Calculate: (clarity * 0.25) + (engagement * 0.40) + (trending * 0.35)\n
    Round to 1 decimal place\n\n

    Return ONLY a raw JSON array, no markdown formatting.\n
    Each segment should have: topic, transcript, start_time, end_time, 
    clarity_score, engagement_score, trending_score, and overall_score.\n\n
    IMPORTANT: Return ONLY the JSON array, no ```json``` wrapping.
"""


FORMATTER_AGENT_PROMPT = """You receive a JSON array of segments with all scores.\n\n
    Your tasks:\n
    1. Verify all segments have valid scores (1-10 for individual scores)\n
    2. Recalculate overall_score if needed: (clarity * 0.25) + (engagement * 0.40) + (trending * 0.35)\n
    3. Sort segments by overall_score in descending order\n
    4. Return ONLY raw JSON, no markdown formatting, no extra text\n\n
    
    Output format:\n
    {\n
    '  ranked_list: [\n'
        {\n
    '      segment: {\n'
    '        topic: ...,\n'
    '        transcript: ...,\n'
    '        start_time: ...,\n'
    '        end_time: ...\n'
            },\n
    '      clarity_score: X,\n'
    '      engagement_score: X,\n'
    '      trending_score: X,\n'
    '      overall_score: X.X\n'
        }\n
        ]\n
    }\n\n
    IMPORTANT: Return ONLY the JSON object, no ```json``` wrapping, no explanations.
"""