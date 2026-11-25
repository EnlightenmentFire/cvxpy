#!/usr/bin/env bash
# Noto CJK subset fonts (SIL Open Font License) used by the renderer.
set -e; D=${EP_FONT_DIR:-$HOME/fonts}; mkdir -p "$D"; B=https://raw.githubusercontent.com/notofonts/noto-cjk/main
for f in Serif/SubsetOTF/SC/NotoSerifSC-Regular.otf Serif/SubsetOTF/SC/NotoSerifSC-Bold.otf Serif/SubsetOTF/SC/NotoSerifSC-Black.otf \
         Serif/SubsetOTF/TC/NotoSerifTC-Bold.otf Sans/SubsetOTF/SC/NotoSansSC-Medium.otf Sans/SubsetOTF/SC/NotoSansSC-Bold.otf; do
  [ -s "$D/$(basename $f)" ] || curl -sSL -o "$D/$(basename $f)" "$B/$f"; done; ls -la "$D"
