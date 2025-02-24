# Setlist.fm to Spotify Playlist Converter
A command-line tool that converts Setlist.fm setlists into Spotify playlists. Perfect for capturing concert memories or exploring artists' live performances.


## Features

- Create Spotify playlists from Setlist.fm URLs
- Process multiple setlists at once
- Read setlist URLs from a file
- Create public or private playlists

## Prerequisites

Python 3.9+
A Spotify Developer account
Spotify API credentials

## Installation

Clone the repository:

```bash
git clone https://github.com/bmw99x/setlist-spotify-converter.git
cd setlist-spotify-converter
```

Install required packages:

```bash
pip install -r requirements.txt
```

Set up your Spotify API credentials:

Create a Spotify Developer application at https://developer.spotify.com/dashboard and set the following environment variables:

```bash
export SPOTIPY_CLIENT_ID='your_client_id'
export SPOTIPY_CLIENT_SECRET='your_client_secret'
export SPOTIPY_REDIRECT_URI='your_redirect_uri'
```

Or create a .env file in the project root:
```
SPOTIPY_CLIENT_ID=your_client_id
SPOTIPY_CLIENT_SECRET=your_client_secret
SPOTIPY_REDIRECT_URI=your_redirect_uri
```

## Usage
### Convert a single setlist:
```bash
python main.py https://www.setlist.fm/setlist/artist/date/venue.html
```

### Convert multiple setlists:
```bash
python main.py url1 url2 url3
```

### 
Read URLs from a file:
```bash
python main.py -f setlists.txt
```

### Create public playlists:
```bash
python main.py -p url1 url2
```

### Enable verbose logging:

```bash
python main.py -v url1
```

### Combine options:
```bash
python main.py -p -v -f setlists.txt
```

### Command Line Arguments
```bash
usage: main.py [-h] [-f FILE] [-p] [-v] [urls ...]

Convert Setlist.fm setlists to Spotify playlists

positional arguments:
  urls                  Setlist.fm URLs to convert

options:
  -h, --help           show this help message and exit
  -f FILE, --file FILE Read setlist URLs from a file (one per line)
  -p, --public         Create public playlists (default: private)
  -v, --verbose        Enable verbose logging
```

### Input File Format
When using the -f/--file option, create a text file with one setlist URL per line:
```bash
https://www.setlist.fm/setlist/artist1/date/venue1.html
https://www.setlist.fm/setlist/artist2/date/venue2.html
https://www.setlist.fm/setlist/artist3/date/venue3.html
```
### Dependencies

- spotipy: Spotify API client
- beautifulsoup4: HTML parsing
- requests: HTTP client
- python-dotenv (optional): Environment variable management

### Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
License
This project is licensed under the Apache License - see the LICENSE file for details.

### Acknowledgments

Setlist.fm for providing concert setlist data
Spotify for their excellent API
All contributors and users of this tool