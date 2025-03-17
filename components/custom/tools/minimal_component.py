from langflow.custom import Component
from langflow.io import StrInput, Output
from langflow.schema import Data

class MinimalComponent(Component):
    display_name = "Minimal Component"
    description = "A minimal component for testing"
    icon = "⚙️"
    category = "Tools"

    def build(self):
        self.add_input(
            StrInput(
                id="text",
                name="Text",
                description="Text to process",
                default="Hello from Minimal Component!",
                required=True
            )
        )
        
        self.add_output(
            Output(
                id="output",
                name="Output",
                description="Result"
            )
        )
    
    def process(self, data: Data) -> dict:
        text = data["inputs"].get("text", "No input")
        return {"output": f"Processed: {text}"} 