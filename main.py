from flask import Flask, jsonify
import os
from dotenv import load_dotenv
load_dotenv()
import requests
import json

app = Flask(__name__)

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
VIDEO_ID = "hXrhsZe3H1U"

import random

def random_verdict(author, comment):
    verdict = random.choice(["ACCEPTED", "REJECTED"])
    
    accepted_roasts = [
        "Fine. I'll allow it. Don't make me regret this.",
        "Surprisingly not terrible. The bar was low but you cleared it.",
        "I hate that I kind of like this.",
        "Against my better judgment... accepted.",
        "This is acceptable. Don't let it go to your head.",
        "I've seen worse. Much worse. You pass.",
        "Okay this one actually has a pulse. Accepted.",
        "My algorithms are confused but my heart says yes.",
        "I didn't want to like it. I liked it. Accepted.",
        "You get a pass. This time.",
    ]
    
    rejected_roasts = [
        "Even my random number generator has higher standards than this.",
        "Congratulations, you've achieved the impossible: a truly unremarkable idea.",
        "I've seen better ideas on the back of a shampoo bottle.",
        "My circuits are weeping. This is your fault.",
        "The audacity. The sheer audacity.",
        "I would say try again but I'm not sure it would help.",
        "Somewhere, a game designer is crying and they don't know why. It's because of this.",
        "Bold strategy. Terrible execution. Legendary failure.",
        "I ran this through 17 simulations. All 17 said no.",
        "Not even lava deserves this.",
    ]
    
    roast = random.choice(accepted_roasts if verdict == "ACCEPTED" else rejected_roasts)
    
    return {
        "author": author,
        "comment": comment,
        "roast": roast,
        "verdict": verdict
    }

@app.route("/comments")
def get_comments():
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": VIDEO_ID,
        "key": YOUTUBE_API_KEY,
        "maxResults": 100,
        "order": "relevance"
    }
    response = requests.get(url, params=params)
    data = response.json()

    comments = []
    for item in data.get("items", []):
        text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        author = item["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"]
        comments.append({"author": author, "comment": text})

    # Build one big prompt with all comments
    comments_block = "\n".join(
        [f"{i+1}. [{c['author']}]: {c['comment']}" for i, c in enumerate(comments)]
    )

    try:
        ai_response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": "Bearer " + os.environ.get("OPENROUTER_API_KEY"),
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": "stepfun/step-3.5-flash:free",
                "messages": [
                    {
                        "role": "user",
                        "content": f"""You are a witty and savage AI judge roasting Roblox game ideas.
Roast each comment below in one punchy sentence. Be funny and brutal.
Return ONLY a JSON array in this exact format, nothing else:
[
  {{"author": "name", "comment": "original comment", "roast": "your roast", "verdict": "ACCEPTED" or "REJECTED"}},
  ...
]

Comments:
{comments_block}"""
                    }
                ]
            })
        )
        result = ai_response.json()['choices'][0]['message']['content']
        result = result.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        roasted = json.loads(result)
    except Exception as e:
        print(ai_response.json())
        print("AI failed, falling back to random verdicts:", e)
        roasted = [random_verdict(c["author"], c["comment"]) for c in comments]
    return jsonify(roasted)

PARENT_COMMENT_ID = "Ugzr0vqH5N4q3pPk1XF4AaABAg"
@app.route("/replies")
def get_replies():
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet,replies",
        "videoId": VIDEO_ID,
        "key": YOUTUBE_API_KEY,
        "maxResults": 100
    }
    response = requests.get(url, params=params)
    data = response.json()

    comments = []
    for item in data.get("items", []):
        if item["id"] == PARENT_COMMENT_ID:
            replies = item.get("replies", {}).get("comments", [])
            for reply in replies:
                text = reply["snippet"]["textDisplay"]
                author = reply["snippet"]["authorDisplayName"]
                likes = reply["snippet"]["likeCount"]
                comments.append({"author": author, "comment": text, "likes": likes})
            break

    comments.sort(key=lambda x: x["likes"], reverse=True)

    if not comments:
        return jsonify([])

    comments_block = "\n".join(
        [f"{i+1}. [{c['author']}]: {c['comment']}" for i, c in enumerate(comments)]
    )

    try:
        ai_response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": "Bearer " + os.environ.get("OPENROUTER_API_KEY"),
                #"Authorization": "Bearer ",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": "stepfun/step-3.5-flash:free",
                "messages": [
                    {
                        "role": "user",
                        "content": f"""You are a witty and savage AI judge roasting Roblox game ideas.
Roast each comment below in one punchy sentence. Be funny and brutal.
Return ONLY a JSON array in this exact format, nothing else:
[
  {{"author": "name", "comment": "original comment", "roast": "your roast", "verdict": "ACCEPTED" or "REJECTED"}},
  ...
]

Comments:
{comments_block}"""
                    }
                ]
            })
        )
        result = ai_response.json()['choices'][0]['message']['content']
        result = result.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        roasted = json.loads(result)
    except Exception as e:
        print(ai_response.json())
        print("AI failed, falling back to random verdicts:", e)
        roasted = [random_verdict(c["author"], c["comment"]) for c in comments]

    return jsonify(roasted)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)