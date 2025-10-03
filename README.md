# SBY OST Tool

The SBY OST Tool is a powerful tool designed to extract and rename soundtracks from the "Seishun Buta Yarou" (Rascal Does Not Dream) series.

* If there is translation issues please feel free to let me know! Translations are all done by me or retrieved from a music database.

## Features

- Extract soundtracks from the SBY series
- Rename soundtrack files in multiple languages (Japanese, Romaji, English)
- Dynamic color theming based on album artwork
- User-friendly GUI with album selection and language options
- In-program track playback

![Example 1](https://github.com/Synthworks0/SBY-OST-Tool/blob/dev/example1.png)

![Example 2](https://github.com/Synthworks0/SBY-OST-Tool/blob/dev/example2.png)

![Example 3](https://github.com/Synthworks0/SBY-OST-Tool/blob/dev/example3.png)

## Installation

### Download

1. Go to the [Releases](https://github.com/Synthworks0/SBY-OST-Tool/releases) page.
2. Download the latest version:
   - SBY_OST_Tool: Self extracting archive
   - SBY_OST_Tool_Portable: A fully contained, portable version. Startup time may be slower for this version!

* Mac OS and Linux support will be added soon!

## Usage

1. Launch the application by running the executable.
2. Select an album from the dropdown menu.
3. Choose the desired language for renaming (Japanese, Romaji, or English).
4. Click the "Browse" button to select an output folder.
5. Click "Extract Soundtrack" to extract the files and set the desired langauge.
6. If needed, click "Rename Files" to rename the soundtrack files after extracting.

## Developer Notes

I've loved this series for a long time and as a audiophile I bought the blurays and extracted the soundtracks in flac lossless from them. When I was going to add them to my media server (I use Jellyfin)
and I wanted to batch rename all of the soundtrack albums with some better metadata and thought, "Why don't I just make a program to do this instead of a terminal program just for me?"

Fast forward 6 months and now we're here in November of 2024.

I spent a lot of time on this as I've never used PySide6 and had to learn the hard way that everything I wanted to do just wasn't possible :)

I'm aware that less than 10 people will probably ever use this and that does make me disappointed. But while making it I felt happy to contribute and make something for a series that has changed my life.
So if you are reading this, thank you. You can find me at `synthworks` on Discord and Reddit.

## Support

If you encounter any issues or have questions, please [open an issue](https://github.com/Synthworks0/SBY-OST-Tool/issues) on the GitHub repository.

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/Synthworks0/SBY-OST-Tool/blob/main/LICENSE) file for details.

The soundtracks are not distributed in the github repo for copyright reasons.
