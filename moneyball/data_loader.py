"""
Download StatsBomb Open Data files and cache them on disk.

Every file is read from the StatsBomb GitHub repository the first time it is
needed, then saved under ``data/raw/`` so later calls read it from disk. All
download and parsing problems are reported as ``StatsBombError``.
"""

import json
from pathlib import Path

import requests

from moneyball.config import (
    BASE_URL,
    COMPETITION_ID,
    RAW_DIR,
    SEASON_ID,
    TIMEOUT_SECONDS,
)

HTTP_NOT_FOUND = 404


class StatsBombError(Exception):
    """Raised when a StatsBomb file cannot be obtained or parsed."""


class StatsBombClient:
    """
    Client for the StatsBomb Open Data repository, with a local file cache.

    Parameters
    ----------
    base_url : str, optional
        Root URL of the ``data/`` folder of the repository.
    cache_dir : str or pathlib.Path, optional
        Folder where downloaded files are saved (default ``data/raw/``).
    timeout : float, optional
        Seconds to wait for the server before giving up.
    max_retries : int, optional
        Number of attempts for each download (not used yet).
    """

    def __init__(
        self,
        base_url=BASE_URL,
        cache_dir=RAW_DIR,
        timeout=TIMEOUT_SECONDS
    ):
        self.base_url = base_url
        self.cache_dir = Path(cache_dir)
        self.timeout = timeout

    def _cache_path(self, relative_path):
        """
        Return the local path where a file is cached.

        Parameters
        ----------
        relative_path : str
            Path inside the repository, for example ``"events/3879608.json"``.

        Returns
        -------
        pathlib.Path
            The same path inside ``cache_dir``.
        """
        return self.cache_dir / relative_path

    def _download(self, relative_path):
        """
        Download one file from StatsBomb Open Data.

        Parameters
        ----------
        relative_path : str
            Path inside the repository, for example ``"events/3879608.json"``.

        Returns
        -------
        str
            The raw JSON text of the file.

        Raises
        ------
        StatsBombError
            If the file does not exist (404), the server returns another HTTP
            error, the request times out or the connection fails.
        """
        url = f"{self.base_url}/{relative_path}"

        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            status = error.response.status_code
            if status == HTTP_NOT_FOUND:
                raise StatsBombError(
                    f"File not found on StatsBomb Open Data: {relative_path}"
                ) from error
            raise StatsBombError(
                f"StatsBomb server returned HTTP {status} for {relative_path}"
            ) from error
            
        except requests.exceptions.Timeout as error:
            raise StatsBombError(
                f"StatsBomb did not answer within {self.timeout} s: {relative_path}"
            ) from error
        except requests.exceptions.ConnectionError as error:
            raise StatsBombError(
                f"Connection error, cannot download {relative_path}"
            ) from error

        return response.text

    def get_json(self, relative_path):
        """
        Return the content of a StatsBomb file, using the cache when possible.

        The file is read from ``cache_dir`` if it exists. Otherwise it is
        downloaded, checked to be valid JSON, and only then saved to the cache.

        Parameters
        ----------
        relative_path : str
            Path inside the repository, for example ``"events/3879608.json"``.

        Returns
        -------
        list or dict
            The parsed JSON content.

        Raises
        ------
        StatsBombError
            If the file cannot be downloaded or is not valid JSON.
        """
        cache_path = self._cache_path(relative_path)

        if cache_path.exists():
            return json.loads(cache_path.read_text(encoding="utf-8"))

        text = self._download(relative_path)

        # Parse before writing, so a broken download never ends up in the cache
        try:
            data = json.loads(text)
        except json.JSONDecodeError as error:
            raise StatsBombError(
                f"StatsBomb returned invalid JSON for {relative_path}"
            ) from error

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(text, encoding="utf-8")
        return data

    def get_competitions(self):
        """
        Return every competition and season available.

        Returns
        -------
        list of dict
            One dict per competition-season, with ``competition_id`` and
            ``season_id``.
        """
        return self.get_json("competitions.json")

    def get_matches(self, competition_id=COMPETITION_ID, season_id=SEASON_ID):
        """
        Return the matches of one competition season.

        Parameters
        ----------
        competition_id : int, optional
            StatsBomb competition ID (default: Serie A).
        season_id : int, optional
            StatsBomb season ID (default: 2015/16).

        Returns
        -------
        list of dict
            One dict per match, with ``match_id``, teams and final score.
        """
        return self.get_json(f"matches/{competition_id}/{season_id}.json")

    def get_events(self, match_id):
        """
        Return every event of one match.

        Parameters
        ----------
        match_id : int
            StatsBomb match ID.

        Returns
        -------
        list of dict
            One dict per event, in match order.
        """
        return self.get_json(f"events/{match_id}.json")

    def get_lineups(self, match_id):
        """
        Return the lineups of both teams for one match.

        Parameters
        ----------
        match_id : int
            StatsBomb match ID.

        Returns
        -------
        list of dict
            Two dicts, one per team, each with a ``lineup`` list of players.
        """
        return self.get_json(f"lineups/{match_id}.json")
