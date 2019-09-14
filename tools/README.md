# here are all the tools ☜(⌒▽⌒)☞

## emitter.py

Jeff's emission vector simulator.

## scrape-murals.py

Scrape murals from https://www.muralconservancy.org.
Takes `scrape_folder` as an argument, will save everything there following this folder structure:

```
scrape_folder/
  +-- <mural_url_hash>/
            +-- images/
                     +-- <image1>.jpg
                     +-- <image2>.jpg
                     +-- ...
            +-- meta.json
  +-- <...>
  warnings.txt
```

You may use check `warnings.txt` after scraping is completed. It will tell you about missing fields.

Meta JSONs have something like this inside:

```
{
    "muralUrl": <original_URL_for_the_mural>,
    "totalImages": <>,
    "artist": <>,
    "location": <>,
    "size": <>,
    "medium": <>,
    "date": <>,
    "types": [<type1>, <type2>]
    "description": <>
}
```

### show me all the types (ง •̀_•́)ง

You may run script as

```
python scrape-murals.py <scrape_folder> --types
```

It'll iterate over the `scrape_folder`, read JSONs and count all occurrences of types.
