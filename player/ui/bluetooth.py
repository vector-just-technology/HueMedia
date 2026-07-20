"""Bluetooth management screen — scan, pair, connect, disconnect."""

import logging

logger = logging.getLogger("ui.bluetooth")


class BluetoothScreen:
    def __init__(self, engine, bt_manager):
        self.engine = engine
        self.bt = bt_manager
        self._screen = None
        self._list = None
        self._title = None
        self._scan_btn = None
        self._status_label = None

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

        title = lv.label(header)
        title.set_text("Bluetooth")
        title.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
        title.set_style_text_font(lv.font_montserrat_16, 0)
        title.align(lv.ALIGN.CENTER, 0, 0)
        self._title = title

        # Scan button
        scan_btn = lv.btn(header)
        scan_btn.set_size(60, 30)
        scan_btn.align(lv.ALIGN.RIGHT_MID, -10, 0)
        scan_btn.set_style_radius(15, 0)
        scan_btn.set_style_bg_color(lv.color_hex(0x8B5CF6), 0)
        scan_btn.add_event_cb(self._on_scan, lv.EVENT.CLICKED, None)
        scan_lbl = lv.label(scan_btn)
        scan_lbl.set_text("Scan")
        self._scan_btn = scan_btn

        # Status label
        status = lv.label(scr)
        status.set_text("")
        status.set_style_text_color(lv.color_hex(0x888888), 0)
        status.set_style_text_font(lv.font_montserrat_12, 0)
        status.align(lv.ALIGN.TOP_LEFT, 15, 45)
        self._status_label = status

        # Device list
        list_container = lv.list(scr)
        list_container.set_size(480, 240)
        list_container.align(lv.ALIGN.TOP_LEFT, 0, 65)
        list_container.set_style_bg_color(lv.color_hex(0x000015), 0)
        list_container.set_style_border_width(0, 0)
        self._list = list_container

        self._screen = scr
        self._bt_listener = lambda s: self._refresh_list()
        self.bt.add_listener(self._bt_listener)
        self._refresh_list()

        return scr

    def _lv_available(self):
        try:
            import lvgl
            return True
        except ImportError:
            return False

    def on_show(self):
        self._refresh_list()

    def _refresh_list(self):
        if not self._list:
            return

        import lvgl as lv

        self._list.clean()
        status = self.bt.get_status()

        # Status text
        if self._status_label:
            connected = status.get("connected")
            if connected:
                self._status_label.set_text(
                    f"Connected: {connected.get('name', '')} ({connected.get('mac', '')})"
                )
            else:
                self._status_label.set_text("No device connected")

        # Scan status
        if self._scan_btn:
            if status.get("scanning"):
                self._scan_btn.set_style_bg_color(lv.color_hex(0x22C55E), 0)
            else:
                self._scan_btn.set_style_bg_color(lv.color_hex(0x8B5CF6), 0)

        # Device list
        devices = status.get("available", [])
        connected_mac = status.get("connected", {}).get("mac") if status.get("connected") else None

        if not devices:
            no_item = lv.label(self._list)
            no_item.set_text("No devices found.\nTap Scan to discover.")
            no_item.set_style_text_color(lv.color_hex(0x888888), 0)
            no_item.set_style_text_font(lv.font_montserrat_14, 0)
            return

        for dev in devices:
            mac = dev["mac"]
            name = dev["name"]
            is_connected = mac == connected_mac

            btn = lv.btn(self._list)
            btn.set_size(460, 48)
            btn.set_style_radius(8, 0)

            if is_connected:
                btn.set_style_bg_color(lv.color_hex(0x1A3A1A), 0)
            else:
                btn.set_style_bg_color(lv.color_hex(0x1A1A2E), 0)

            btn.set_style_pad_left(15, 0)

            label = lv.label(btn)
            connect_text = "\ud83d\udd0a " if is_connected else ""
            label.set_text(f"{connect_text}{name}\n{mac}")
            label.set_style_text_color(lv.color_hex(0xDDDDDD), 0)
            label.set_style_text_font(lv.font_montserrat_14, 0)
            label.set_long_mode(lv.label.LONG.WRAP)

            btn.add_event_cb(
                lambda e, d=dev: self._on_device_click(d),
                lv.EVENT.CLICKED, None
            )

    def _on_device_click(self, dev):
        mac = dev["mac"]
        status = self.bt.get_status()
        connected = status.get("connected")

        if connected and connected["mac"] == mac:
            self.bt.disconnect()
        else:
            self.bt.pair(mac)

    def _on_scan(self, event):
        status = self.bt.get_status()
        if status.get("scanning"):
            self.bt.stop_scan()
        else:
            self.bt.start_scan()
