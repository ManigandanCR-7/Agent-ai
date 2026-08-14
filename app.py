import os, re, urllib.parse, urllib.request
from flask import Flask, abort, jsonify, render_template, request

app = Flask(__name__)

def youtube_id(query):
    try:
        url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=5).read().decode()
        ids = re.findall(r'"videoId":"([^"]+)"', data)
        return ids[0] if ids else None
    except Exception:
        return None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/agent", methods=["POST"])
def agent():
    data = request.get_json(silent=True)

    if not data or not (data.get("command") or data.get("text_command")):
        abort(400)

    cmd = (data.get("command") or data.get("text_command")).strip().lower()

    # YouTube
    if "youtube" in cmd:
        q = re.sub(
            r"\b(open youtube and search|open youtube and play|open youtube|search for|search|and play|play|on youtube)\b",
            "",
            cmd
        ).strip()

        vid = youtube_id(q)

        if vid:
            url = f"https://www.youtube.com/embed/{vid}?autoplay=1&mute=1"
            msg = f"Playing {q}"
        else:
            url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(q)
            msg = f"Searching YouTube for {q}"

    # Gmail
    elif any(x in cmd for x in ("gmail", "email", "mail", "message")):
        clean = re.sub(
            r"^(please\s+)?(open\s+)?(gmail|email|mail|message)\s*",
            "",
            cmd
        ).strip()

        parts = re.split(r"\b(?:type|write|saying|message|content|with body)\b", clean, maxsplit=1)
        recipient = re.sub(
            r"^(?:update\s+to|to|send\s+to|and\s+update\s+to)\s*",
            "",
            parts[0]
        ).strip()

        body = parts[1].strip() if len(parts) > 1 else "how was your day"

        if recipient:
            recipient = (
                recipient.replace(" at ", "@")
                .replace(" dot ", ".")
                .replace(" ", "")
            )
            recipient = re.sub(r"[^a-zA-Z0-9@._%-]", "", recipient)

            if "@" not in recipient:
                recipient += "@gmail.com"
        else:
            recipient = "sharanbalaji2025@gmail.com"

        params = urllib.parse.urlencode({
            "to": recipient,
            "body": body
        })

        url = f"https://mail.google.com/mail/u/0/?view=cm&fs=1&{params}"
        msg = f"Drafting email to {recipient}"

    # No Google search
    else:
        return jsonify({
            "success": False,
            "message": "Command not supported. Use YouTube or Gmail."
        }), 400

    return jsonify({
        "success": True,
        "message": msg,
        "url": url
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000))
    )
