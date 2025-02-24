from typing import List, Optional
import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
import logging
from urllib.parse import urlparse

import requests
import spotipy
from bs4 import BeautifulSoup
from spotipy.oauth2 import SpotifyOAuth

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MODIFY_PRIVATE_SCOPE = "playlist-modify-private"
MODIFY_PUBLIC_SCOPE = "playlist-modify-public"

@dataclass
class SetlistConfig:
    public: bool
    verbose: bool
    input_file: Optional[Path]

class SetlistError(Exception):
    """Base exception for setlist processing errors"""

class SetlistConverter:
    def __init__(self, config: SetlistConfig):
        self.config = config
        scope = MODIFY_PUBLIC_SCOPE if config.public else MODIFY_PRIVATE_SCOPE
        
        try:
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
        except Exception as e:
            raise SetlistError(f"Failed to initialize Spotify client: {e}")
        
        if config.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

    def validate_setlist_url(self, url: str) -> bool:
        """Validate that the URL is a setlist.fm setlist URL"""
        try:
            parsed = urlparse(url)
            return (
                parsed.netloc == "www.setlist.fm" 
                and "/setlist/" in parsed.path
            )
        except Exception:
            return False

    def get_song_link(self, artist: str, song: str) -> Optional[str]:
        """Get Spotify URL for a song"""
        try:
            results = self.sp.search(q=f"artist:{artist} track:{song}", type="track")
            return results["tracks"]["items"][0]["external_urls"]["spotify"]
        except IndexError:
            logger.warning(f"Could not find song: {artist} - {song}")
            return None
        except Exception as e:
            logger.error(f"Error searching for song: {e}")
            return None

    @staticmethod
    def slug_to_plain(text: str) -> str:
        """Convert URL slug to plain text"""
        return text.replace("-", " ")

    @staticmethod
    def get_song_labels(souped: BeautifulSoup) -> List[str]:
        """Extract song names from setlist page"""
        try:
            songs_list = souped.find_all("ol", class_="songsList")
            labels = songs_list[0].find_all("a", class_="songLabel")
            return [label.text.strip() for label in labels if label.text.strip()]
        except Exception as e:
            raise SetlistError(f"Failed to extract song labels: {e}")

    @staticmethod
    def get_date_of_setlist(souped: BeautifulSoup) -> str:
        """Extract date from setlist page"""
        try:
            content = souped.find("div", class_="dateBlockContainer").find("div", class_="dateBlock").text
            return content.replace("\n", " ").strip()
        except Exception as e:
            raise SetlistError(f"Failed to extract setlist date: {e}")

    def create_playlist(self, playlist_name: str) -> str:
        """Create a new Spotify playlist"""
        try:
            playlist = self.sp.user_playlist_create(
                self.sp.current_user()["id"],
                playlist_name,
                public=self.config.public,
                description="Created by Setlist.fm converter",
            )
            return playlist["id"]
        except Exception as e:
            raise SetlistError(f"Failed to create playlist: {e}")

    def add_songs_to_playlist(self, playlist_id: str, song_links: List[str]) -> None:
        """Add songs to a Spotify playlist"""
        try:
            self.sp.playlist_add_items(playlist_id, song_links)
            logger.info(f"Added {len(song_links)} songs to playlist")
        except Exception as e:
            raise SetlistError(f"Failed to add songs to playlist: {e}")

    @staticmethod
    def is_empty_setlist(souped: BeautifulSoup) -> bool:
        """Check if setlist is empty"""
        return bool(souped.find("div", class_="emptySetlist"))

    @staticmethod
    def get_venue(souped: BeautifulSoup) -> str:
        """Extract venue from setlist page"""
        try:
            return souped.select_one(".setlistHeadline a[href*='/venue/']").text.strip()
        except Exception as e:
            raise SetlistError(f"Failed to extract venue: {e}")

    def process_setlist(self, url: str) -> None:
        """Process a single setlist URL"""
        if not self.validate_setlist_url(url):
            logger.error(f"Invalid setlist URL: {url}")
            return

        try:
            artist = self.slug_to_plain(url.split("setlist.fm/setlist/")[1].split("/")[0])
            response = requests.get(url)
            response.raise_for_status()
            
            souped = BeautifulSoup(response.content, "html.parser")
            setlist_date = self.get_date_of_setlist(souped)
            venue = self.get_venue(souped)
            
            logger.info(f"Processing setlist for {artist} at {venue} on {setlist_date}")
            
            if self.is_empty_setlist(souped):
                logger.warning("Setlist is empty, skipping...")
                return
                
            song_labels = self.get_song_labels(souped)
            song_links = [
                link for link in (
                    self.get_song_link(artist, label) 
                    for label in song_labels
                ) 
                if link is not None
            ]
            
            if not song_links:
                logger.warning("No songs found on Spotify, skipping playlist creation")
                return
                
            playlist_name = f"{artist} - {setlist_date} - {venue}".title()
            playlist_id = self.create_playlist(playlist_name)
            self.add_songs_to_playlist(playlist_id, song_links)
            logger.info(f"Created playlist: {playlist_name}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch setlist: {e}")
        except SetlistError as e:
            logger.error(f"Error processing setlist: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Convert Setlist.fm setlists to Spotify playlists"
    )
    parser.add_argument(
        "urls",
        nargs="*",
        help="Setlist.fm URLs to convert"
    )
    parser.add_argument(
        "-f", "--file",
        type=Path,
        help="File containing setlist URLs (one per line)"
    )
    parser.add_argument(
        "-p", "--public",
        action="store_true",
        help="Create public playlists (default: private)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if not args.urls and not args.file:
        parser.error("Please provide either URLs or an input file")

    config = SetlistConfig(
        public=args.public,
        verbose=args.verbose,
        input_file=args.file
    )

    converter = SetlistConverter(config)
    
    urls = args.urls
    if args.file:
        try:
            with open(args.file) as f:
                urls.extend(line.strip() for line in f if line.strip())
        except Exception as e:
            logger.error(f"Failed to read input file: {e}")
            sys.exit(1)

    for url in urls:
        converter.process_setlist(url)

if __name__ == "__main__":
    main()