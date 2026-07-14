from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty

from shared_game_logic import generate_operation_question, generate_group_pattern

KV = """
ScreenManager:
    HomeScreen:
    OperationsScreen:
    PatternsScreen:

<HomeScreen>:
    name: "home"
    BoxLayout:
        orientation: "vertical"
        padding: "20dp"
        spacing: "12dp"
        Label:
            text: "Pattern Picnic Mobile"
            font_size: "28sp"
        Button:
            text: "Operations"
            size_hint_y: None
            height: "52dp"
            on_release: app.open_operations()
        Button:
            text: "Patterns"
            size_hint_y: None
            height: "52dp"
            on_release: app.open_patterns()

<OperationsScreen>:
    name: "operations"
    BoxLayout:
        orientation: "vertical"
        padding: "20dp"
        spacing: "12dp"
        Label:
            text: root.question_text
            font_size: "28sp"
            halign: "center"
        TextInput:
            id: answer_input
            multiline: False
            input_filter: "int"
            hint_text: "Type answer"
            size_hint_y: None
            height: "48dp"
        Label:
            text: root.feedback_text
            font_size: "20sp"
            color: (0.2, 0.7, 0.3, 1) if "Correct" in root.feedback_text else (0.9, 0.3, 0.3, 1)
        BoxLayout:
            size_hint_y: None
            height: "52dp"
            spacing: "8dp"
            Button:
                text: "Check"
                on_release: root.check_answer(answer_input.text)
            Button:
                text: "Next"
                on_release:
                    root.next_question()
                    answer_input.text = ""
        Button:
            text: "Back"
            size_hint_y: None
            height: "48dp"
            on_release: app.root.current = "home"

<PatternsScreen>:
    name: "patterns"
    BoxLayout:
        orientation: "vertical"
        padding: "20dp"
        spacing: "12dp"
        Label:
            text: root.pattern_text
            font_size: "24sp"
            halign: "center"
        Label:
            text: root.answer_text
            font_size: "24sp"
        Button:
            text: "New Pattern"
            size_hint_y: None
            height: "52dp"
            on_release: root.next_pattern()
        Button:
            text: "Back"
            size_hint_y: None
            height: "48dp"
            on_release: app.root.current = "home"
"""


class HomeScreen(Screen):
    pass


class OperationsScreen(Screen):
    question_text = StringProperty("")
    feedback_text = StringProperty("")

    def on_pre_enter(self):
        self.next_question()

    def next_question(self):
        self.question_text, self._answer = generate_operation_question("Addition", "easy")
        self.feedback_text = ""

    def check_answer(self, typed_value):
        if not typed_value.strip():
            self.feedback_text = "Type a number first"
            return
        try:
            parsed = int(typed_value)
        except ValueError:
            self.feedback_text = "Only numbers are allowed"
            return

        if parsed == self._answer:
            self.feedback_text = "Correct ✅"
        else:
            self.feedback_text = f"Try again (answer: {self._answer})"


class PatternsScreen(Screen):
    pattern_text = StringProperty("")
    answer_text = StringProperty("")

    def on_pre_enter(self):
        self.next_pattern()

    def next_pattern(self):
        values = generate_group_pattern("1-3-5", length=4, difficulty="easy")
        self.pattern_text = "Pattern: " + ", ".join(str(item) for item in values)
        if len(values) > 1:
            step = values[1] - values[0]
            self.answer_text = f"Next: {values[-1] + step}"
        else:
            self.answer_text = ""


class PatternPicnicMobileApp(App):
    def build(self):
        return Builder.load_string(KV)

    def open_operations(self):
        self.root.current = "operations"

    def open_patterns(self):
        self.root.current = "patterns"


if __name__ == "__main__":
    PatternPicnicMobileApp().run()
