# ScrapeBooru

ScrapeBooru is a GUI program that gets images from Gelbooru (with possible others added) using supplied tags.

## Checklist:
- [ ] Fix 'post' JSON bug, or suppress it.
- [ ] Adjust layout or add stuff in general.

## Args:

Tags: Enter (or paste) the tags you want in here, seperated by a space per tag, a "-" to exclude one, and an "_" per word.

An example would be `kanna_kamui  kobayashi-san_chi_no_maidragon 1girl -skateboard -1boy -half-life_(series) -2boys -tohru_(maidragon) -greyscale -thick_outlines -english_text -painting_(medium) -multiple_views -rating:sensitive -official_art  -from_above -animated_gif `

max_resolution: The maximum resolution to download images at. The default is 3072, and must be a power of 2.

total_limit: The total amount of images to download. Default is 100, but can be changed at users discretion.

include_posts_with_parent: Weither to download variations of another image. Default is True.
