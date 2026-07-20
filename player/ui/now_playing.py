"""Now Playing screen — cover art, progress, controls."""

import logging
from pathlib import Path

logger = logging.getLogger("ui.nowplaying")


class NowPlayingScreen:
    def __init__(self, engine, library):
        self.engine = engine
        self.library = library
        self._screen = None
        self._cover_img = None
        self._title_label = None
        self._artist_label = None
        self._time_label = None
        self._progress_slider = None
        self._play_btn = None
        self._volume_slider = None
        self._volume_label = None
        self._shuffle_btn = None
        self._repeat_btn = None

    def build(self):
        if not self._lv_available():
            return None

        import lvgl as lv

        scr = lv.obj()
        scr.set_style_bg_color(lv.color_hex(0x000015), 0)

        # --- Artist label (top) ---
        artist = lv.label(scr)
        artist.set_text("")
        artist.set_style_text_color(lv.color_hex(0x888888), 0)
        artist.set_style_text_font(lv.font_montserrat_14, 0)
        artist.align(lv.ALIGN.TOP_LEFT, 10, 10)
        self._artist_label = artist

        # --- Cover art (center) ---
        cover = lv.img(scr)
        cover.set_size(200, 200)
        cover.align(lv.ALIGN.TOP_MID, 0, 35)
        cover.set_style_radius(12, 0)
        cover.set_style_clip_corner(True, 0)
        # Default placeholder
        cover.set_src(lv.SYMBOL_IMAGE)
        self._cover_img = cover

        # --- Title label ---
        title = lv.label(scr)
        title.set_text("")
        title.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
        title.set_style_text_font(lv.font_montserrat_16, 0)
        title.set_long_mode(lv.label.LONG.SCROLL_CIRCULAR)
        title.set_width(280)
        title.align(lv.ALIGN.TOP_MID, 0, 240)
        self._title_label = title

        # --- Progress bar (slider) ---
        slider = lv.slider(scr)
        slider.set_size(300, 6)
        slider.align(lv.ALIGN.TOP_MID, 0, 265)
        slider.set_style_bg_color(lv.color_hex(0x333355), lv.PART.KNOB)
        slider.set_style_bg_color(lv.color_hex(0x555577), lv.PART.INDICATOR)
        slider.add_event_cb(self._on_seek, lv.EVENT.VALUE_CHANGED, None)
        slider.set_range(0, 1000)
        self._progress_slider = slider

        # --- Time labels ---
        time_label = lv.label(scr)
        time_label.set_text("0:00 / 0:00")
        time_label.set_style_text_color(lv.color_hex(0x888888), 0)
        time_label.set_style_text_font(lv.font_montserrat_12, 0)
        time_label.align_to(slider, lv.ALIGN.OUT_BOTTOM_MID, 0, 2)
        self._time_label = time_label

        # --- Controls row ---
        controls = lv.obj(scr)
        controls.set_size(320, 55)
        controls.align(lv.ALIGN.BOTTOM_MID, 0, -5)
        controls.set_style_bg_opa(lv.OPA.TRANSP, 0)
        controls.set_flex_flow(lv.FLEX_FLOW.ROW)
        controls.set_flex_align(lv.FLEX_ALIGN.SPACE_EVENLY, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)

        # Shuffle button
        shuffle_btn = lv.btn(controls)
        shuffle_btn.set_size(40, 40)
        shuffle_btn.set_style_radius(20, 0)
        shuffle_btn.add_event_cb(lambda e: self.engine.toggle_shuffle(), lv.EVENT.CLICKED, None)
        shuffle_lbl = lv.label(shuffle_btn)
        shuffle_lbl.set_text("\u21c4")
        self._shuffle_btn = shuffle_btn

        # Previous button
        prev_btn = lv.btn(controls)
        prev_btn.set_size(44, 44)
        prev_btn.set_style_radius(22, 0)
        prev_btn.add_event_cb(lambda e: self.engine.previous(), lv.EVENT.CLICKED, None)
        prev_lbl = lv.label(prev_btn)
        prev_lbl.set_text("\u23ee")

        # Play/Pause button
        play_btn = lv.btn(controls)
        play_btn.set_size(52, 52)
        play_btn.set_style_radius(26, 0)
        play_btn.set_style_bg_color(lv.color_hex(0x8B5CF6), 0)
        play_btn.add_event_cb(self._on_play_pause, lv.EVENT.CLICKED, None)
        play_lbl = lv.label(play_btn)
        play_lbl.set_text(lv.SYMBOL.PLAY)
        play_lbl.set_style_text_font(lv.font_montserrat_20, 0)
        self._play_btn = play_btn
        self._play_lbl = play_lbl

        # Next button
        next_btn = lv.btn(controls)
        next_btn.set_size(44, 44)
        next_btn.set_style_radius(22, 0)
        next_btn.add_event_cb(lambda e: self.engine.next(), lv.EVENT.CLICKED, None)
        next_lbl = lv.label(next_btn)
        next_lbl.set_text("\u23ed")

        # Repeat button
        repeat_btn = lv.btn(controls)
        repeat_btn.set_size(40, 40)
        repeat_btn.set_style_radius(20, 0)
        repeat_btn.add_event_cb(lambda e: self.engine.cycle_repeat(), lv.EVENT.CLICKED, None)
        repeat_lbl = lv.label(repeat_btn)
        repeat_lbl.set_text("\u21bb")
        self._repeat_btn = repeat_btn

        # --- Volume slider (bottom-right) ---
        vol_slider = lv.slider(scr)
        vol_slider.set_size(100, 6)
        vol_slider.align(lv.ALIGN.BOTTOM_RIGHT, -10, -55)
        vol_slider.set_range(0, 100)
        vol_slider.set_value(self.engine._volume, lv.ANIM.OFF)
        vol_slider.add_event_cb(self._on_volume, lv.EVENT.VALUE_CHANGED, None)
        self._volume_slider = vol_slider

        vol_label = lv.label(scr)
        vol_label.set_text(str(self.engine._volume))
        vol_label.set_style_text_color(lv.color_hex(0x888888), 0)
        vol_label.set_style_text_font(lv.font_montserrat_12, 0)
        vol_label.align(lv.ALIGN.BOTTOM_RIGHT, -40, -70)
        self._volume_label = vol_label

        self._screen = scr
        self._updating = False

        # Register callback for playback updates
        self.engine.add_listener(self._on_update)

        return scr

    def _lv_available(self):
        try:
            import lvgl
            return True
        except ImportError:
            return False

    def on_show(self):
        self._update_display()

    def _on_update(self, status):
        self._update_display()

    def _update_display(self):
        if not self._screen or self._updating:
            return
        self._updating = True

        try:
            import lvgl as lv
            status = self.engine.get_status()
            track = status.get("current")

            if track:
                # Title
                if self._title_label:
                    self._title_label.set_text(track.get("title", ""))

                # Artist
                if self._artist_label:
                    self._artist_label.set_text(track.get("artist", ""))

                # Cover art
                cover_path = track.get("cover")
                if cover_path and Path(cover_path).exists() and self._cover_img:
                    try:
                        self._cover_img.set_src(cover_path)
                    except Exception:
                        pass

                # Progress
                pos = status.get("position", 0)
                dur = status.get("duration", 0)
                if self._time_label:
                    self._time_label.set_text(
                        f"{self._fmt_time(pos)} / {self._fmt_time(dur)}"
                    )
                if self._progress_slider and dur > 0:
                    self._progress_slider.set_value(int(pos / dur * 1000), lv.ANIM.OFF)

                # Play/Pause icon
                if self._play_lbl:
                    if status.get("state") == "playing":
                        self._play_lbl.set_text(lv.SYMBOL.PAUSE)
                    else:
                        self._play_lbl.set_text(lv.SYMBOL.PLAY)

            # Volume
            vol = status.get("volume", self.engine._volume)
            if self._volume_slider:
                self._volume_slider.set_value(vol, lv.ANIM.OFF)
            if self._volume_label:
                self._volume_label.set_text(str(vol))

        except Exception as e:
            logger.error(f"Update error: {e}")
        finally:
            self._updating = False

    @staticmethod
    def _fmt_time(seconds):
        if seconds is None or seconds < 0:
            return "0:00"
        m = int(seconds) // 60
        s = int(seconds) % 60
        return f"{m}:{s:02d}"

    def _on_seek(self, event):
        import lvgl as lv
        slider = event.get_target()
        val = slider.get_value()
        dur = self.engine.get_status().get("duration", 0)
        if dur > 0:
            self.engine.seek(val / 1000 * dur)

    def _on_volume(self, event):
        import lvgl as lv
        slider = event.get_target()
        val = slider.get_value()
        self.engine.set_volume(val)

    def _on_play_pause(self, event):
        self.engine.toggle_pause()
