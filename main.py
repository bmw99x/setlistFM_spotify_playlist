import requests
import spotipy
from bs4 import BeautifulSoup
from spotipy.oauth2 import SpotifyOAuth

# Must set the following environment variables
# SPOTIPY_CLIENT_ID
# SPOTIPY_CLIENT_SECRET
# SPOTIPY_REDIRECT_URI
MODIFY_PRIVATE_SCOPE = "playlist-modify-private"


sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=MODIFY_PRIVATE_SCOPE))

def get_song_link(artist: str, song: str) -> str | None:
    try:
        results = sp.search(q=f"artist:{artist} track:{song}", type="track")
        return results["tracks"]["items"][0]["external_urls"]["spotify"]
    except IndexError:
        return None

def slug_to_plain(text: str) -> str:
    return text.replace("-", " ")

def get_song_labels(souped: BeautifulSoup) -> list[str]:
    songs_list = souped.find_all("ol", class_="songsList")
    labels = songs_list[0].find_all("a", class_="songLabel")
    return "\n".join((label.text.replace("\n", "") for label in labels if label.text.replace("\n", "")))

def get_date_of_setlist(souped: BeautifulSoup) -> str:
    """Div dateBlockContainer > div dateBlock: month, day, year"""
    content = souped.find("div", class_="dateBlockContainer").find("div", class_="dateBlock").text
    return content.replace("\n", " ").strip()


def create_playlist(
    playlist_name: str,
    playlist_public: bool = False,
) -> str:
    playlist = sp.user_playlist_create(
        sp.current_user()["id"],
        playlist_name,
        public=playlist_public,
        description="",
    )
    return playlist["id"]

def add_songs_to_playlist(playlist_id: str, song_links: list[str]):
    sp.playlist_add_items(playlist_id, song_links)
    print("Added songs to playlist")

def is_empty_setlist(souped: BeautifulSoup) -> bool:
    """EmptySetlist class will be present if the setlist is empty"""
    return bool(souped.find("div", class_="emptySetlist"))

def get_venue(souped: BeautifulSoup) -> str:
    """<a href="../../../venue/newcastle-nx-newcastle-upon-tyne-england-13d055c5.html" title="More setlists from Newcastle NX, Newcastle upon Tyne, England"><span>Newcastle NX, Newcastle upon Tyne, England</span></a>"""
    return souped.select_one(".setlistHeadline a[href*='/venue/']").text.strip()

def convert(links: list[str]):
    for link in links:
        artist = slug_to_plain(link.split("setlist.fm/setlist/")[1].split("/")[0])
        content = requests.get(link).content
        souped = BeautifulSoup(content, "html.parser")
        setlist_date = get_date_of_setlist(souped)
        print("Setlist date:", setlist_date)
        venue = get_venue(souped)
        if is_empty_setlist(souped):
            print(f"Setlist for {artist} on {setlist_date} is empty, ignoring...")
            continue
        song_labels = get_song_labels(souped).split("\n")
        print("Song labels:", song_labels)
        song_links = list(filter(bool, (get_song_link(artist, label) for label in song_labels if label is not None)))
        print("Song links:", song_links)
        playlist_name = f"{artist} - {setlist_date} - {venue}".title()
        playlist_id = create_playlist(playlist_name)
        add_songs_to_playlist(playlist_id, song_links)

if __name__ == "__main__":
    convert([
        "https://www.setlist.fm/setlist/circa-waves/2025/barrowland-glasgow-scotland-2b50ac12.html",
        "https://www.setlist.fm/setlist/circa-waves/2025/cambridge-junction-cambridge-england-2350ac0b.html",
        "https://www.setlist.fm/setlist/circa-waves/2025/nick-rayns-lcr-uea-norwich-england-3b50ac00.html",
        "https://www.setlist.fm/setlist/circa-waves/2025/newcastle-nx-newcastle-upon-tyne-england-3350acf9.html",
        "https://www.setlist.fm/setlist/circa-waves/2025/o2-victoria-warehouse-manchester-england-3350acf1.html",
    ])