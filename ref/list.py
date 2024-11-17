from kivy.lang import Builder

from kivymd.app import MDApp
from kivymd.uix.list import OneLineListItem, ThreeLineListItem
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
import numpy as np

KV = '''
MDScrollView:
    MDList:
        id: container
'''



class Example(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        return Builder.load_string(KV)

    def on_start(self):
        db = np.array([[1, 10, "OK"],[2, 20, "OK"],[3, 15, "OK"]])
        for i in range(3):
            self.root.ids.container.add_widget(
                # OneLineListItem(
                #     text=f"{db[i,0]}",
                #     secondary_text= f"{db[i,1]}",
                #     tertiary_text= f"{db[i,2]}",
                # ),
                MDCard(
                     MDLabel(
                        text=f"{db[i,0]}",
                        adaptive_size=True,
                        color="grey",
                        pos=("12dp", "12dp"),
                    ),
                    MDLabel(
                        text=f"{db[i,1]}",
                        adaptive_size=True,
                        color="grey",
                        pos=("12dp", "12dp"),
                    ),
                    MDLabel(
                        text=f"{db[i,2]}",
                        adaptive_size=True,
                        color="grey",
                        pos=("12dp", "12dp"),
                    ),
                    line_color=(0.2, 0.2, 0.2, 0.8),
                    padding="4dp",
                    size_hint=(None, None),
                    size=("800dp", "100dp"),
                )

            )

Example().run()