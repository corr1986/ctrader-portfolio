"""Pubblicazione su X via API v2. Dry-run di default: senza --post non esce nulla."""
import os

ENV_VARS = ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET")


def _load_env_file(env_path: str) -> None:
    """Carica un .env minimale (KEY=value) senza dipendenze esterne."""
    if not env_path or not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


def post(text: str, image_path: str = None, dry_run: bool = True,
         preview_path: str = "copyfunnel_preview.txt",
         env_path: str = None) -> dict:
    """Pubblica il post (o salva l'anteprima in dry-run)."""
    if dry_run:
        with open(preview_path, "w", encoding="utf-8") as f:
            f.write(text)
            if image_path:
                f.write(f"\n\n[immagine: {image_path}]")
        return {"posted": False, "dry_run": True, "preview": preview_path}

    _load_env_file(env_path)
    missing = [v for v in ENV_VARS if not os.environ.get(v)]
    if missing:
        return {
            "posted": False, "dry_run": False,
            "error": f"Credenziali X mancanti: {', '.join(missing)}. "
                     "Compila copyfunnel/.env (vedi docs/x-setup.md).",
        }

    import tweepy

    client = tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_SECRET"],
    )
    media_ids = None
    if image_path:
        auth = tweepy.OAuth1UserHandler(
            os.environ["X_API_KEY"], os.environ["X_API_SECRET"],
            os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_SECRET"],
        )
        media = tweepy.API(auth).media_upload(image_path)
        media_ids = [media.media_id]

    response = client.create_tweet(text=text, media_ids=media_ids)
    return {"posted": True, "dry_run": False,
            "tweet_id": response.data["id"]}
