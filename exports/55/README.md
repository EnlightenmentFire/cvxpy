# 55 · 托克维尔配音用逐句旁白稿

云端会话没有 GPU，也拿不到参考音频，所以托克维尔声音没法在云端生成。请在 box 上用 `sentences.txt` 逐句生成 `line_0001.wav` 到 `line_0088.wav`，一行一句，不改字。
`sentences.json` 里每句都附了场景名，以及云扬版的时长，供参考。

生成后在 `exports/55_meditator-brain/` 下运行 `bash src/fetch_fonts.sh && bash src/build.sh /path/to/wavs`，即可按新声音重排时间轴、字幕和画面，重新混音并出两版成片。
