from turtle import onclick
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.card import (
    MDCardSwipe, MDCardSwipeLayerBox, MDCardSwipeFrontBox
)
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.screen import MDScreen
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.label import MDLabel
from kivymd.toast import toast
import numpy as np

class Example(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"
        return (
            MDScreen(
                MDBoxLayout(
                    MDTopAppBar(
                        elevation=4,
                        title="MDCardSwipe",
                    ),
                    MDScrollView(
                        MDList(
                            id="md_list",
                        ),
                        id="scroll",
                        scroll_timeout=100,
                    ),
                    id="box",
                    orientation="vertical",
                ),
            )
        )

    def on_start(self):
        '''Creates a list of cards.'''
        db = np.array([[1, 10, "OK"],[2, 20, "OK"],[3, 15, "OK"],[4, 35, "OK"],[5, 35, "OK"],[6, 45, "NOK"]])
        for i in range(6):
            self.root.ids.box.ids.scroll.ids.md_list.add_widget(
                MDCardSwipe(
                    MDCardSwipeLayerBox(
                        MDIconButton(
                            icon="trash-can",
                            pos_hint={"center_y": 0.5},
                            on_release = self.remove_item,
                        ),
                    ),
                    MDCardSwipeFrontBox(
                        MDLabel(text=f"{db[i,0]}",),
                        MDLabel(text=f"{db[i,1]}",),
                        MDLabel(text=f"{db[i,2]}",),
                        
                        ripple_behavior = True,
                        # onclick = self.on_click,
                        on_press = self.on_click
                    ),
                    size_hint_y=None,
                    height="52dp",
                )
            )

    def remove_item(self, instance):
        self.root.ids.box.ids.scroll.ids.md_list.remove_widget(
            instance.parent.parent
        )

    def on_click(self, instance):
        toast("click")

Example().run()