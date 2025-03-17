from langflow.custom import Component
from langflow.io import StrInput, Output

class BasicComponent(Component):
    display_name = "Basic Component"
    description = "A very basic component that echoes input text."
    icon = "🔄"
    category = "Tools"

    def build(self):
        self.add_input(
            StrInput(
                id="input_text",
                name="Input Text",
                description="Text to echo back",
                default="Hello, world!",
                required=True
            )
        )
        
        self.add_output(
            Output(
                id="output",
                name="Output",
                description="Echoed text"
            )
        )
    
    def process(self, data):
        input_text = data["inputs"].get("input_text", "No input provided")
        return {"output": input_text} 