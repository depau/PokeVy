#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json

import config

from kivy.garden.mapview import MapView, MapMarker, MarkerMapLayer
from kivy.app import App
from kivy.clock import Clock
from kivy.properties import ListProperty, ObjectProperty, DictProperty
from kivy.animation import Animation
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.bubble import Bubble
from kivy.uix.label import Label



class PokeMarker(MapMarker):
    pass
    # bubble = ObjectProperty(None)

    # def on_touch_up(self, touch):
    #     pass
    #     if not self.collide_point(*touch.pos):
    #         return False
    #     self.bubble = self._build_bubble()
    #     # App.get_running_app().bubbles.append(self.bubble)
    #     # App.get_running_app().root.add_widget(self.bubble)

    # def _build_bubble(self):
    #     raise NotImplementedError

class FortMarker(PokeMarker):
    fort = DictProperty(None)

    def __init__(self, *a, **kw):
        super(FortMarker, self).__init__(*a, **kw)
        self._update_coords()
        self.bind(fort=self._update_coords)

    def _update_coords(self, *args):
        if self.fort["type"] == 1:
            if "cooldown_complete_timestamp_ms" in self.fort:
                self.source = "pokestop_used.png"
            else:
                self.source = os.path.join(config.image_path, "forts", "pokestop_near.png")
        if "latitude" in self.fort and "longitude" in self.fort:
            self.lat = self.fort["latitude"]
            self.lon = self.fort["longitude"]
            try:
                if self._layer:
                    self._layer.set_marker_position(self._layer.parent, self)
            except AttributeError:
                import traceback; traceback.print_exc();

    # def _build_bubble(self):
    #     bubble = Bubble(arrow_position="top_mid", pos=self.pos)
    #     bubble.add_widget(Label(text=json.dumps(self.fort)))
    #     print json.dumps(self.fort)
    #     return bubble

class PokemonMarker(PokeMarker):
    pokemon = DictProperty(None)

    def __init__(self, *args, **kwargs):
        super(PokemonMarker, self).__init__(*args, **kwargs)
        if "pokemon_id" in self.pokemon:
            self.source = os.path.join(config.image_path, "pokemon", "%03d.png" % self.pokemon["pokemon_id"])
        self._update_coords()
        self.bind(pokemon=self._update_coords)

    def _update_coords(self, *args):
        if "latitude" in self.pokemon and "longitude" in self.pokemon:
            self.lat = self.pokemon["latitude"]
            self.lon = self.pokemon["longitude"]
            try:
                if self._layer:
                    self._layer.set_marker_position(self._layer.parent, self)
            except AttributeError:
                import traceback; traceback.print_exc();


    # def _build_bubble(self):
    #     print json.dumps(self.pokemon)


class PokeVyApp(App):
    mapview = ObjectProperty(None)
    location = ListProperty(None)
    cells = {}
    inventory = {}
    player_marker = ObjectProperty(None)
    pokemons = {}
    forts = {}
    bubbles = ListProperty([])

    def build(self):
        self.mapview = MapView(zoom=20, lat=45.47375, lon=9.17489, map_source="thunderforest-landscape")
        mml = MarkerMapLayer()
        self.mapview.add_layer(mml)
        self.player_marker = MapMarker(lat=45.47375, lon=9.17489)
        self.mapview.add_marker(self.player_marker)
        
        self.update_map()
        Clock.schedule_once(lambda *args: self.mapview.center_on(*self.location))
        Clock.schedule_interval(self.update_map, 1)
        Clock.schedule_interval(lambda *a: mml.reposition(), 0.1)
        root = FloatLayout()
        root.add_widget(self.mapview)
        return root

    def update_map(self, *args):
        try:
            with open(config.location_file, "r") as f:
                loc = json.load(f)
                lat = loc["lat"]
                lon = loc["lng"]
                self.location = [lat, lon]
                anim = Animation(lat=lat, lon=lon, d=1) #t="in_out_cubic",
                anim.start(self.player_marker)

            with open(config.cells_file, "r") as f:
                self.cells = json.load(f)

            # print "CELLS", len(self.cells)
            self.add_remove_markers(self.cells)
        except:
            import traceback; traceback.print_exc();

    def add_remove_markers(self, cells):
        ids = []

        for cell in cells:
            if "forts" in cell:
                for fort in cell["forts"]:
                    ids.append(fort["id"])
                    if fort["id"] not in self.forts and "latitude" in fort and "longitude" in fort and "type" in fort:
                        marker = FortMarker(fort=fort)
                        self.forts[fort["id"]] = marker
                        self.mapview.add_marker(marker)
                        # print "ADD MARKER fort", fort["type"]
                    elif fort["id"] in self.forts:
                        self.forts[fort["id"]].fort = fort
            if "catchable_pokemons" in cell:
                for pokemon in cell["catchable_pokemons"]:
                    ids.append(pokemon["encounter_id"])
                    if pokemon["encounter_id"] not in self.pokemons and "latitude" in pokemon and "longitude" in pokemon:
                        marker = PokemonMarker(pokemon=pokemon)
                        self.pokemons[pokemon["encounter_id"]] = marker
                        self.mapview.add_marker(marker)
                        print "ADD MARKER", pokemon["pokemon_id"]
                    elif pokemon["encounter_id"] in self.pokemons:
                        self.pokemons[pokemon["encounter_id"]].pokemon = pokemon

        # print "IDS", ids
        for marker in self.forts.keys() + self.pokemons.keys():
            if marker not in ids:
                if marker in self.pokemons:
                    m = self.pokemons.pop(marker)
                else:
                    m = self.forts.pop(marker)
                self.mapview.remove_marker(m)
                # print "REMOVE MARKER"



PokeVyApp().run()