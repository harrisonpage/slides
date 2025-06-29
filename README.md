# Slides

Automation for posting 35mm slide images to various places:

* [Internet Archive](https://archive.org/details/@harrisonpage)
* [Bluesky](https://bsky.app/profile/harrison.page)

## Usage

```bash
./post.sh [Image(s) to upload]
```

One can also run individual scripts, see `post.sh` for usage.

## Features

* Asks OpenAI for a title, description and tags for a set of images, to be used in metadata and alt-text
* TUI to apply edits

## Notes

* All credentials (OpenAI API key, Bluesky account info) stored in environment variables

## About

* Created: 29-Jun-2025
* Author: [Harrison Page](https://harrison.page) <harrison.page@harrison.page>

![1947.jpg](1947.jpg)