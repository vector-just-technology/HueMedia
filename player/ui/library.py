"""Library browser screen — lists artists, drills into songs."""

import logging

logger = logging.getLogger("ui.library")


class LibraryScreen:
    def __init__(self, engine, library, screen_manager):
        self.engine = engine
        self.library = library
        self.sm = screen_manager
        self._screen = None
        self._list = None
        self._back_btn = None
        self._current_view = "artists"
        self._current_artist = None

    def build(self):
        if not self._lv_available():
            return None

        import lvgl as lv

        scr = lv.obj()
        scr.set_style_bg_color(lv.color_hex(0x000015), 0)

        # Header
        header = lv.obj(scr)
        header.set_size(480, 40)
        header.align(lv.ALIGN.TOP_LEFT, 0, 0)
        header.set_style_bg_color(lv.color_hex(0x0D0D20), 0)
        header.set_style_pad_left(10, 0)
        header.set_style_pad_top(5, 0)

        back_btn = lv.btn(header)
        back_btn.set_size(30, 30)
        back_btn.set_style_radius(15, 0)
        back_btn.add_event_cb(self._on_back, lv.EVENT.CLICKED, None)
        back_lbl = lv.label(back_btn)
        back_lbl.set_text("\u2190")
        back_btn.set_style_bg_opa(lv.OPA.TRANSP, 0)
        self._back_btn = back_btn

        title = lv.label(header)
        title.set_text("Library")
        title.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
        title.set_style_text_font(lv.font_montserrat_16, 0)
        title.align(lv.ALIGN.CENTER, 0, 0)
        self._title = title

        # Search button
        search_btn = lv.btn(header)
        search_btn.set_size(30, 30)
        search_btn.align(lv.ALIGN.RIGHT_MID, -10, 0)
        search_btn.set_style_radius(15, 0)
        search_btn.set_style_bg_opa(lv.OPA.TRANSP, 0)
        search_btn.add_event_cb(self._on_search, lv.EVENT.CLICKED, None)
        search_lbl = lv.label(search_btn)
        search_lbl.set_text("\ud83d\udd0d")

        # Scrollable list
        list_container = lv.list(scr)
        list_container.set_size(480, 280)
        list_container.align(lv.ALIGN.TOP_LEFT, 0, 40)
        list_container.set_style_bg_color(lv.color_hex(0x000015), 0)
        list_container.set_style_border_width(0, 0)
        self._list = list_container

        self._screen = scr
        self._populate_artists()

        # Listen for library updates
        self.library.add_listener(lambda artists: self._populate_artists())

        return scr

    def _lv_available(self):
        try:
            import lvgl
            return True
        except ImportError:
            return False

    def on_show(self):
        self._populate_artists()

    def _populate_artists(self):
        if not self._list:
            return

        import lvgl as lv

        self._list.clean()
        self._current_view = "artists"
        self._title.set_text("Library")
        self._back_btn.set_style_bg_opa(lv.OPA.TRANSP, 0)

        artists = self.library.get_artists()
        if not artists:
            no_item = lv.label(self._list)
            no_item.set_text("No music found.\nAdd MP3s via SAMBA or USB.")
            no_item.set_style_text_color(lv.color_hex(0x888888), 0)
            no_item.set_style_text_font(lv.font_montserrat_14, 0)
            return

        for artist in artists:
            btn = lv.btn(self._list)
            btn.set_size(460, 48)
            btn.set_style_radius(8, 0)
            btn.set_style_bg_color(lv.color_hex(0x1A1A2E), 0)
            btn.set_style_bg_color(lv.color_hex(0x2A2A4E), lv.STATE.PRESSED)
            btn.set_style_pad_left(15, 0)

            label = lv.label(btn)
            label.set_text(
                f"{artist['name']}  "
                f"[{artist['count']} track{'s' if artist['count'] != 1 else ''}]"
            )
            label.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
            label.set_style_text_font(lv.font_montserrat_14, 0)

            artist_name = artist["name"]
            btn.add_event_cb(
                lambda e, an=artist_name: self._show_artist(an),
                lv.EVENT.CLICKED, None
            )

    def _show_artist(self, artist_name):
        if not self._list:
            return

        import lvgl as lv

        artist = self.library.get_artist(artist_name)
        if not artist:
            return

        self._current_view = "songs"
        self._current_artist = artist_name
        self._title.set_text(artist_name)
        self._back_btn.set_style_bg_color(lv.color_hex(0x333355), 0)

        self._list.clean()

        for song in artist["songs"]:
            btn = lv.btn(self._list)
            btn.set_size(460, 44)
            btn.set_style_radius(8, 0)
            btn.set_style_bg_color(lv.color_hex(0x1A1A2E), 0)
            btn.set_style_bg_color(lv.color_hex(0x2A2A4E), lv.STATE.PRESSED)
            btn.set_style_pad_left(15, 0)

            label = lv.label(btn)
            title = song.get("title", "Unknown")
            is_video = song.get("is_video", False)
            icon = "\ud83c\udfac " if is_video else ""
            label.set_text(f"{icon}{title}")
            label.set_style_text_color(lv.color_hex(0xDDDDDD), 0)
            label.set_style_text_font(lv.font_montserrat_14, 0)

            song_data = song
            btn.add_event_cb(
                lambda e, sd=song_data: self._play_song(sd),
                lv.EVENT.CLICKED, None
            )

    def _play_song(self, song):
        self.engine.play(song)

    def _on_back(self, event):
        if self._current_view == "songs":
            self._populate_artists()

    def _on_search(self, event):
        self.sm.switch("search")
