# Data directory

When filenames are send to post.sh as command-line arguments, the first file has run through `md5sum` and this value is used to identify images.

## Files

Example filename: 5b57871d3aa7bfb5abc01d9f1f190b0a

* If the file `5b57871d3aa7bfb5abc01d9f1f190b0a` exists we have already posted this
* File `5b57871d3aa7bfb5abc01d9f1f190b0a.json` contains all the metadata
* File `5b57871d3aa7bfb5abc01d9f1f190b0a.id` contains the Internet Archive identifier
* File `5b57871d3aa7bfb5abc01d9f1f190b0a.bluesky` contains the date the image was posted to Bluesky
