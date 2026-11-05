# Video

## The file

- one file of **at most 25 MiB** (the per-file limit of common static hosts;
  the build checks it);
- H.264 (High profile, `yuv420p`) and AAC in an `.mp4` container, with
  `+faststart`, so that playback starts before the whole file is loaded;
- SDR: an HDR source must be tone-mapped to SDR **before** encoding, or the
  picture looks washed out on some devices;
- the metadata of the source (camera model, location, date) is removed;
- any orientation: the tile on the page and the frame in the viewer take the
  proportion of the video (a portrait video on a desktop is a narrow tile in
  the middle of the column).

## Preparing it

Re-encoding (put in the frame height you need: `-2` in `scale` picks the other
side so that it stays even):

```bash
ffmpeg -i in.mov -vf "scale=-2:1280" \
  -c:v libx264 -profile:v high -pix_fmt yuv420p -crf 26 -preset slow \
  -c:a aac -b:a 96k -movflags +faststart -map_metadata -1 proposal.mp4
```

For a **portrait** video limit the height (`scale=-2:1280`), for a
**landscape** one the width (`scale=1280:-2`). A higher `-crf` gives a smaller
file and lower quality; 23–28 is a sensible range.

When the source is **HDR** (shot on a recent phone), add the tone mapping to
SDR before scaling:

```bash
ffmpeg -i in.mov \
  -vf "format=gbrpf32le,tonemap=hable:desat=0,format=yuv420p,scale=-2:1280" \
  -c:v libx264 -profile:v high -pix_fmt yuv420p -crf 26 -preset slow \
  -c:a aac -b:a 96k -movflags +faststart -map_metadata -1 proposal.mp4
```

When your `ffmpeg` has the `zscale` filter (`ffmpeg -filters | grep zscale`),
it gives a more accurate result:
`-vf "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,scale=-2:1280"`.
Look at the result of tone mapping with your own eyes: no automatic check can
judge it.

When the file does not fit into 25 MiB: raise `-crf` (a step of +2 makes the
file about a third smaller), reduce the frame size or shorten the video
(`-t 40`). A rule of thumb: the total bit rate that gives 25 MiB is about
190,000 / the duration in seconds, in kbit/s (with a margin of about 10 %),
of which about 96 kbit/s goes to the sound. Check the result:

```bash
ls -l proposal.mp4                       # at most 26,214,400 bytes
ffprobe -v error -select_streams v:0 -show_entries stream=width,height \
        -of csv=p=0 proposal.mp4         # → 720,1280
```

The poster is a frame of the finished file (pick the moment to taste):

```bash
ffmpeg -ss 00:00:01 -i proposal.mp4 -frames:v 1 -update 1 -q:v 3 proposal-poster.jpg
```

`-update 1` tells `ffmpeg` that it writes one picture, not a sequence of
frames: without it `ffmpeg` warns about a missing name pattern such as `%03d`
(the file is right all the same).

The poster must have the proportion of the video, or the frame "jumps" while
the page loads.

## The data

A video is an item of the media registry
([data-format.md](data-format.md#media)):

```json
"media": {
  "proposal": { "type": "video", "file": "proposal.mp4", "poster": "proposal-poster.jpg",
                "width": 720, "height": 1280, "alt": "Video of the proposal" } }
```

It is shown like a photo, with a "Media" widget (`"layout": "single"` is one
large tile, `grid` and `ribbon` show it together with photos) or in the
`photos` of a place, where it pages in the viewer together with the photos of
the place. There may be any number of videos, each of its own size.

`width` and `height` are the very numbers `ffprobe` prints. They go into the
markup of the tile (the proportion of a single tile, the size of the poster,
`data-media-ratio` for the viewer): the space of the frame is reserved before
anything loads, and the browser knows the proportion in advance. Without them
the build takes the size of the poster or of the `.mp4` itself; when that
fails too, the 16:9 proportion of a token applies, which spoils the first
screen of a portrait video noticeably. The duration ("0:20" on the tile and
in its label for screen readers) is read from the file by the build.

The build checks the video file: not an `.mp4`, a broken file or another
format is an error; an index at the end of the file (no `+faststart`), a
codec other than H.264, HDR, an unreadable duration and a poster of another
proportion are warnings.

The requirements of the file and the data do not depend on how the video is
shown on the page.

## The tile and the viewer

**On the page** a video is a tile, like a photo: the poster (a single tile,
`.gallery--single`, in the proportion of the frame), a round ▶ badge in the
middle and the duration in a corner; the whole tile is tappable. The tile is
a plain link to the video file; there is no `<video>` on the page, so the
file is not requested at all before a tap.

**A tap** opens the same viewer as for photos, and the video plays at once
with sound: `play()` is called right in the tap handler, the only way iOS and
the in-app browsers of messengers allow sound. When the browser refuses all
the same, the video stays on its poster and starts with the ▶ button of the
panel.

- **The panel** is the browser's native panel of `<video controls>`: its
  look, buttons, seeking, sound and full screen (the system player on an
  iPhone) come from the browser; nothing removes the `controls` attribute,
  and the panel has no styles of its own.
- **Paging**: in a gallery with photos next to it, the video pages together
  with them (the arrows of the viewer, ←/→, a swipe outside the frame of the
  video). A video reached by paging does not load in advance
  (`preload="none"`, only the poster loads) and does not start by itself, only
  on a tap on the frame or on ▶ of the panel. Leaving a video or closing the
  viewer stops it and aborts the loading. At most one video plays at a time.
- **The keys and gestures on a video are its own**: the space bar pauses,
  the arrows and Home/End seek, a swipe across the frame seeks rather than
  pages.
- **Full screen** comes from the button of the panel. The first Esc leaves it
  (the viewer stays and the video keeps playing), the second closes the
  viewer, and the focus returns to the tile.
- **When the video fails to load**, the frame shows "The video could not be
  loaded." (the `lightbox.videoError` string).
- **Without JavaScript** the tile leads to the file: the browser opens the
  video in its own player, and "Back" returns to the page.

The tile (its badge uses the tokens `--media-play-size` and
`--media-play-icon-size` and the overlay colours; section 5 of `app.css`) and
the frame in the viewer (section 8) have styles of their own.
