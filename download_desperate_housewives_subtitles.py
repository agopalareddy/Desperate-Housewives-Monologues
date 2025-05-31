import logging
import os
from babelfish import Language
from subliminal import download_best_subtitles
from subliminal.core import ProviderPool  # For advanced provider configuration
from subliminal.video import Video
from subliminal.cache import (
    region,
)  # If you need to configure region/language specifics

# Configure logging for subliminal and our script
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional: Configure subliminal's cache region if needed for language detection
# Example: region.configure('dogpile.cache.memory')
region.configure("dogpile.cache.memory")


def download_show_subtitles(
    series_name, seasons_episodes, language_code="eng", output_dir="subtitles"
):
    """
    Downloads subtitles for a given TV show.

    Args:
        series_name (str): The name of the TV series.
        seasons_episodes (dict): A dictionary where keys are season numbers (int)
                                 and values are the number of episodes in that season (int).
        language_code (str): The ISO 639-3 code for the desired language (e.g., 'eng', 'fra').
        output_dir (str): Directory to save the downloaded subtitles.
    """
    lang = Language(language_code)
    os.makedirs(output_dir, exist_ok=True)

    # Note: Subliminal uses a set of default providers.
    # For better results or specific needs (e.g., using API keys for OpenSubtitles),
    # you might need to configure providers explicitly.
    # See subliminal documentation for `ProviderPool` and provider configuration.
    # Example (requires provider-specific setup):
    # from subliminal.providers.opensubtitles import OpenSubtitlesProvider
    # from subliminal.providers.podnapisi import PodnapisiProvider
    # with ProviderPool() as pp:
    # pp.register_provider(OpenSubtitlesProvider(username='your_user', password='your_password')) # If API requires auth
    # pp.register_provider(PodnapisiProvider())
    # subtitles_list = download_best_subtitles([video], {lang}, providers=pp.providers)

    for season, num_episodes in seasons_episodes.items():
        season_dir = os.path.join(output_dir, f"Season {season:02d}")
        os.makedirs(season_dir, exist_ok=True)

        for episode in range(1, num_episodes + 1):
            video_identifier = f"{series_name} S{season:02d}E{episode:02d}"
            logger.info(f"Attempting to download subtitles for {video_identifier}")

            # Create a Video object with metadata. Subliminal uses this to search.
            # video = Video(
            #     name=video_identifier, # Used for matching and potentially naming
            #     series=series_name,
            #     season=season,
            #     episode=episode,
            #     # title=f"Episode {episode}", # Optional: specific episode title if known
            #     # year=2004 # Optional: Series start year or specific episode air year
            # )
            video = Video.fromname(video_identifier)
            # Ensure the series name is correctly set if fromname doesn't pick it up as expected,
            # or if you want to be explicit.
            # video.series = series_name # This might be redundant if fromname works well
            # video.season = season # Redundant if fromname parses it
            # video.episode = episode # Redundant if fromname parses it

            try:
                # Download the best subtitles for this "video"
                # Uses default providers unless `providers` list is passed.
                subtitles_found = download_best_subtitles([video], {lang})

                if video in subtitles_found and subtitles_found[video]:
                    best_subtitle = subtitles_found[video][
                        0
                    ]  # Take the first one (usually best match)

                    # Determine file extension (e.g., .srt, .sub)
                    # subtitle_ext = best_subtitle.format if best_subtitle.format else 'srt'
                    subtitle_ext = "srt"  # Default to .srt
                    if hasattr(best_subtitle, "format") and best_subtitle.format:
                        subtitle_ext = best_subtitle.format

                    subtitle_filename = os.path.join(
                        season_dir, f"{video_identifier}.{language_code}.{subtitle_ext}"
                    )

                    with open(subtitle_filename, "wb") as f:
                        f.write(best_subtitle.content)  # content is usually bytes
                    logger.info(f"Saved subtitle: {subtitle_filename}")
                else:
                    logger.warning(f"No subtitles found for {video_identifier}")
            except Exception as e:
                logger.error(f"Error downloading subtitles for {video_identifier}: {e}")
            # Consider adding a small delay here if making many requests, e.g., time.sleep(1)


if __name__ == "__main__":
    # Episode counts for Desperate Housewives (verify these from a reliable source)
    desperate_housewives_episodes_per_season = {
        1: 23,  # Season 1
        2: 24,  # Season 2
        3: 23,  # Season 3
        4: 17,  # Season 4 (affected by Writers' Guild strike)
        5: 24,  # Season 5
        6: 23,  # Season 6
        7: 23,  # Season 7
        8: 23,  # Season 8
    }

    SERIES_NAME = "Desperate Housewives"
    OUTPUT_SUBTITLE_DIR = os.path.join(
        "data", "subtitles", SERIES_NAME.lower().replace(" ", "_")
    )
    TARGET_LANGUAGE = "eng"  # For English subtitles

    logger.info(f"Starting subtitle download for '{SERIES_NAME}'...")
    logger.info(f"Subtitles will be saved in: {os.path.abspath(OUTPUT_SUBTITLE_DIR)}")
    logger.info(f"Target language: {TARGET_LANGUAGE}")

    download_show_subtitles(
        series_name=SERIES_NAME,
        seasons_episodes=desperate_housewives_episodes_per_season,
        language_code=TARGET_LANGUAGE,
        output_dir=OUTPUT_SUBTITLE_DIR,
    )

    logger.info("Subtitle download process finished.")
    logger.info(f"Please check the '{OUTPUT_SUBTITLE_DIR}' directory.")
    logger.info(
        "Note: Success depends on subtitle availability on the configured providers."
    )
    logger.info(
        "You might need to configure providers in subliminal (e.g., OpenSubtitles, Podnapisi) for better results."
    )
    logger.info(
        "Refer to the subliminal documentation for advanced provider configuration."
    )
